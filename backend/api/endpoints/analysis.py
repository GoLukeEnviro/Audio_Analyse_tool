"""Analysis API Endpoints - Audio-Analyse und Cache-Management"""

import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from ..models import (
    AnalysisStartRequest, AnalysisStatusResponse, AnalysisStatus,
    CacheStatsResponse, SuccessResponse, ErrorResponse
)
from core_engine.audio_analysis.analyzer import AudioAnalyzer
from core_engine.data_management.cache_manager import CacheManager
from core_engine.mood_classifier.mood_classifier import MoodClassifier
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
_analyzer = None
_cache_manager = None
_mood_classifier = None
_active_analysis_tasks: Dict[str, Any] = {}


def get_analyzer():
    """Get AudioAnalyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AudioAnalyzer(
            db_path=settings.get("audio_analysis.db_path", "data/database.db"),
            enable_multiprocessing=settings.get("audio_analysis.enable_multiprocessing", True)
        )
    return _analyzer


def get_cache_manager():
    """Get CacheManager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(settings.get("audio_analysis.cache_dir")) # Korrigierter Import
    return _cache_manager


def get_mood_classifier():
    """Get MoodClassifier instance"""
    global _mood_classifier
    if _mood_classifier is None:
        _mood_classifier = MoodClassifier()
    return _mood_classifier


def find_audio_files(directories: List[str], recursive: bool = True, 
                    include_patterns: Optional[List[str]] = None,
                    exclude_patterns: Optional[List[str]] = None) -> List[str]:
    """Find all audio files in directories"""
    supported_formats = settings.get("audio_analysis.supported_formats", [])
    audio_files = []
    
    # Music library settings
    music_library_config = settings.get("music_library", {})
    min_file_size_kb = music_library_config.get("min_file_size_kb", 100)
    max_depth = music_library_config.get("max_depth", 10)
    exclude_patterns_default = music_library_config.get("exclude_patterns", [])
    
    # Combine exclude patterns
    all_exclude_patterns = exclude_patterns_default + (exclude_patterns or [])
    
    def should_exclude_path(path_str: str) -> bool:
        """Check if path should be excluded based on patterns"""
        for pattern in all_exclude_patterns:
            if pattern.startswith('*/'):
                # Directory pattern
                if f"/{pattern[2:]}/" in path_str or path_str.endswith(f"/{pattern[2:]}"):
                    return True
            elif '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(os.path.basename(path_str), pattern):
                    return True
            else:
                # Simple substring match
                if pattern in path_str:
                    return True
        return False
    
    for directory in directories:
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            continue
        
        if not directory_path.is_dir():
            logger.warning(f"Path is not a directory: {directory}")
            continue
        
        if should_exclude_path(str(directory_path)):
            logger.debug(f"Skipping excluded directory: {directory}")
            continue
        
        # Find files
        try:
            if recursive:
                # Use os.walk for better control over depth and exclusions
                for root, dirs, files in os.walk(directory):
                    # Check depth limit
                    depth = root[len(directory):].count(os.sep)
                    if depth >= max_depth:
                        dirs.clear()  # Don't go deeper
                        continue
                    
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = Path(os.path.join(root, file))
                        
                        # Check file extension
                        file_ext = file_path.suffix.lower()
                        if file_ext not in supported_formats:
                            continue
                        
                        # Check file size
                        try:
                            file_size_kb = file_path.stat().st_size / 1024
                            if file_size_kb < min_file_size_kb:
                                logger.debug(f"Skipping small file: {file_path} ({file_size_kb:.1f}KB)")
                                continue
                        except (OSError, PermissionError):
                            continue
                        
                        file_str = str(file_path)
                        
                        # Check exclude patterns
                        if should_exclude_path(file_str):
                            continue
                        
                        # Apply include patterns
                        if include_patterns:
                            if not any(pattern in file_str for pattern in include_patterns):
                                continue
                        
                        audio_files.append(file_str)
                        
            else:
                # Non-recursive scan
                for file_path in directory_path.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    file_ext = file_path.suffix.lower()
                    if file_ext not in supported_formats:
                        continue
                    
                    # Check file size
                    try:
                        file_size_kb = file_path.stat().st_size / 1024
                        if file_size_kb < min_file_size_kb:
                            continue
                    except (OSError, PermissionError):
                        continue
                    
                    file_str = str(file_path)
                    
                    # Check patterns
                    if should_exclude_path(file_str):
                        continue
                    
                    if include_patterns:
                        if not any(pattern in file_str for pattern in include_patterns):
                            continue
                    
                    audio_files.append(file_str)
                    
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot access directory {directory}: {e}")
            continue
    
    logger.info(f"Found {len(audio_files)} audio files in {len(directories)} directories")
    return audio_files


async def analyze_files_task(
    task_id: str,
    file_paths: List[str],
    overwrite_cache: bool = False
):
    """Background task for audio analysis"""
    try:
        logger.info(f"Starting analysis task {task_id} with {len(file_paths)} files")
        
        # Initialize task status
        _active_analysis_tasks[task_id] = {
            'status': AnalysisStatus.running,
            'progress': 0.0,
            'current_file': None,
            'processed_files': 0,
            'total_files': len(file_paths),
            'errors': [],
            'started_at': datetime.now().isoformat(),
            'estimated_completion': None
        }
        
        analyzer = get_analyzer()
        cache_manager = get_cache_manager()
        mood_classifier = get_mood_classifier()
        
        # Filter files if not overwriting cache
        files_to_process = []
        if not overwrite_cache:
            for file_path in file_paths:
                if not cache_manager.is_cached(file_path):
                    files_to_process.append(file_path)
                else:
                    logger.debug(f"Skipping cached file: {file_path}")
        else:
            files_to_process = file_paths
        
        logger.info(f"Processing {len(files_to_process)} files (skipped {len(file_paths) - len(files_to_process)} cached)")
        
        # Update total files to process
        _active_analysis_tasks[task_id]['total_files'] = len(files_to_process)
        
        if len(files_to_process) == 0:
            _active_analysis_tasks[task_id]['status'] = AnalysisStatus.completed
            _active_analysis_tasks[task_id]['progress'] = 100.0
            _active_analysis_tasks[task_id]['current_file'] = None
            return
        
        # Process files with progress tracking
        async def progress_callback(processed: int, total: int, current_file: str):
            if task_id in _active_analysis_tasks:
                progress = (processed / total) * 100 if total > 0 else 0
                _active_analysis_tasks[task_id]['progress'] = progress
                _active_analysis_tasks[task_id]['current_file'] = os.path.basename(current_file)
                _active_analysis_tasks[task_id]['processed_files'] = processed
                
                # Estimate completion time
                if processed > 0:
                    elapsed = (datetime.now() - datetime.fromisoformat(_active_analysis_tasks[task_id]['started_at'])).seconds
                    estimated_total_time = (elapsed / processed) * total
                    remaining_time = estimated_total_time - elapsed
                    estimated_completion = datetime.now().timestamp() + remaining_time
                    _active_analysis_tasks[task_id]['estimated_completion'] = datetime.fromtimestamp(estimated_completion).isoformat()
        
        # Analyze files using the real AudioAnalyzer
        try:
            results = await analyzer.analyze_batch_async(files_to_process, progress_callback)
            
            # Add mood classification to results
            for file_path, result in results.items():
                if result and result.get('status') == 'completed':
                    try:
                        features = result.get('features', {})
                        mood, confidence, scores = mood_classifier.classify_mood(features)
                        result['mood'] = {
                            'primary_mood': mood,
                            'confidence': confidence,
                            'scores': scores
                        }
                        
                        # Add derived metrics for API compatibility
                        bpm = features.get('bpm', 120.0)
                        energy = features.get('energy', 0.5)
                        
                        result['derived_metrics'] = {
                            'energy_level': 'high' if energy > 0.7 else 'medium' if energy > 0.4 else 'low',
                            'bpm_category': 'very_fast' if bpm > 140 else 'fast' if bpm > 120 else 'medium' if bpm > 90 else 'slow',
                            'estimated_mood': mood,
                            'danceability_level': 'high' if features.get('danceability', 0) > 0.7 else 'medium' if features.get('danceability', 0) > 0.4 else 'low'
                        }
                        
                    except Exception as e:
                        logger.warning(f"Mood classification failed for {file_path}: {e}")
                        result['mood'] = {
                            'primary_mood': 'neutral',
                            'confidence': 0.0,
                            'scores': {}
                        }
                        result['derived_metrics'] = {
                            'energy_level': 'medium',
                            'bpm_category': 'medium',
                            'estimated_mood': 'neutral',
                            'danceability_level': 'medium'
                        }
        except Exception as e:
            logger.error(f"Analysis batch failed: {e}")
            _active_analysis_tasks[task_id]['status'] = AnalysisStatus.error
            _active_analysis_tasks[task_id]['errors'].append(f"Batch analysis failed: {str(e)}")
            return
        
        # Count errors
        error_count = sum(1 for result in results.values() if result and result.get('status') == 'error')
        success_count = len(results) - error_count
        
        # Update final status
        if task_id in _active_analysis_tasks:
            _active_analysis_tasks[task_id]['status'] = AnalysisStatus.completed
            _active_analysis_tasks[task_id]['progress'] = 100.0
            _active_analysis_tasks[task_id]['current_file'] = None
            _active_analysis_tasks[task_id]['processed_files'] = len(files_to_process)
            _active_analysis_tasks[task_id]['completed_at'] = datetime.now().isoformat()
            _active_analysis_tasks[task_id]['results_summary'] = {
                'total_processed': len(files_to_process),
                'successful': success_count,
                'failed': error_count,
                'skipped_cached': len(file_paths) - len(files_to_process)
            }
        
        logger.info(f"Analysis task {task_id} completed: {success_count} successful, {error_count} failed")
        
    except Exception as e:
        logger.error(f"Analysis task {task_id} failed: {e}")
        if task_id in _active_analysis_tasks:
            _active_analysis_tasks[task_id]['status'] = AnalysisStatus.error
            _active_analysis_tasks[task_id]['errors'].append(str(e))


@router.post("/start", summary="Start audio analysis")
async def start_analysis(
    request: AnalysisStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Startet den Scan und die Analyse der Musikbibliothek.
    
    Dieser Prozess läuft als Hintergrundaufgabe und kann mehrere Minuten dauern.
    Der API-Call kehrt sofort mit einer Task-ID zurück.
    
    **Parameter:**
    - **directories**: Liste von Verzeichnissen zum Scannen
    - **file_paths**: Optional spezifische Dateien (überschreibt directories)
    - **recursive**: Unterverzeichnisse scannen
    - **overwrite_cache**: Vorhandenen Cache überschreiben
    - **include_patterns**: Nur Dateien mit diesen Mustern einschließen
    - **exclude_patterns**: Dateien mit diesen Mustern ausschließen
    """
    try:
        # Determine files to analyze
        if request.file_paths:
            # Use specific file paths
            files_to_analyze = request.file_paths
            logger.info(f"Analyzing {len(files_to_analyze)} specific files")
        else:
            # Scan directories, use configured scan_path if no directories are provided
            directories_to_scan = request.directories if request.directories else [settings.get("music_library.scan_path")]
            files_to_analyze = find_audio_files(
                directories=directories_to_scan,
                recursive=request.recursive,
                include_patterns=request.include_patterns,
                exclude_patterns=request.exclude_patterns
            )
            logger.info(f"Found {len(files_to_analyze)} audio files in {len(directories_to_scan)} directories")
        
        if not files_to_analyze:
            raise HTTPException(
                status_code=400,
                detail="No audio files found in specified directories"
            )
        
        # Validate file paths
        valid_files = []
        invalid_files = []
        
        for file_path in files_to_analyze:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                invalid_files.append(file_path)
        
        if not valid_files:
            raise HTTPException(
                status_code=400,
                detail=f"No valid audio files found. {len(invalid_files)} files do not exist."
            )
        
        # Generate unique task ID
        task_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(_active_analysis_tasks)}"
        
        # Start background analysis
        background_tasks.add_task(
            analyze_files_task,
            task_id=task_id,
            file_paths=valid_files,
            overwrite_cache=request.overwrite_cache
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Audio analysis started",
            "total_files": len(valid_files),
            "invalid_files": len(invalid_files),
            "directories_scanned": len(request.directories) if not request.file_paths else 0,
            "status_url": f"/api/analysis/{task_id}/status",
            "overwrite_cache": request.overwrite_cache
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start audio analysis")


@router.get("/{task_id}/status", response_model=AnalysisStatusResponse, summary="Get analysis status")
async def get_analysis_status(task_id: str):
    """
    Gibt den aktuellen Status des Analyseprozesses zurück.
    
    **Status-Werte:**
    - **pending**: Wartend auf Start
    - **running**: Analyse läuft
    - **completed**: Erfolgreich abgeschlossen  
    - **error**: Fehler aufgetreten
    - **cancelled**: Abgebrochen
    """
    if task_id not in _active_analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis task not found")
    
    task_info = _active_analysis_tasks[task_id]
    
    return AnalysisStatusResponse(
        status=task_info['status'],
        progress=task_info['progress'],
        current_file=task_info.get('current_file'),
        processed_files=task_info['processed_files'],
        total_files=task_info['total_files'],
        errors=task_info['errors'],
        started_at=task_info.get('started_at'),
        estimated_completion=task_info.get('estimated_completion')
    )


@router.post("/{task_id}/cancel", response_model=SuccessResponse, summary="Cancel analysis")
async def cancel_analysis(task_id: str):
    """
    Bricht eine laufende Analyse ab.
    """
    if task_id not in _active_analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis task not found")
    
    task_info = _active_analysis_tasks[task_id]
    
    if task_info['status'] not in [AnalysisStatus.running]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel task with status: {task_info['status']}"
        )
    
    # Update task status
    _active_analysis_tasks[task_id]['status'] = AnalysisStatus.cancelled
    _active_analysis_tasks[task_id]['current_file'] = None
    
    return SuccessResponse(
        message=f"Analysis task {task_id} cancelled",
        data={"task_id": task_id}
    )


@router.get("/cache/stats", response_model=CacheStatsResponse, summary="Get cache statistics")
async def get_cache_stats():
    """
    Gibt detaillierte Cache-Statistiken zurück.
    """
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_cache_stats()
        
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.post("/cache/cleanup", response_model=SuccessResponse, summary="Clean up cache")
async def cleanup_cache(
    max_age_days: int = Query(30, ge=1, le=365, description="Maximum age in days"),
    max_size_mb: int = Query(1000, ge=100, le=10000, description="Maximum size in MB")
):
    """
    Bereinigt den Analyse-Cache basierend auf Alter und Größe.
    
    **Parameter:**
    - **max_age_days**: Dateien älter als X Tage löschen
    - **max_size_mb**: Cache auf maximale Größe begrenzen
    """
    try:
        cache_manager = get_cache_manager()
        result = cache_manager.cleanup_cache(max_age_days, max_size_mb)
        
        return SuccessResponse(
            message=f"Cache cleanup completed: {result['removed_files']} files removed, "
                   f"{result['freed_mb']:.1f} MB freed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")


@router.post("/cache/clear", response_model=SuccessResponse, summary="Clear entire cache")
async def clear_cache():
    """
    Löscht den gesamten Analyse-Cache.
    
    ⚠️ **Achtung:** Diese Operation löscht alle gespeicherten Analyse-Ergebnisse!
    """
    try:
        cache_manager = get_cache_manager()
        count = cache_manager.clear_cache()
        
        return SuccessResponse(
            message=f"Cache cleared: {count} files deleted",
            data={"deleted_files": count}
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.post("/cache/optimize", response_model=SuccessResponse, summary="Optimize cache")
async def optimize_cache():
    """
    Optimiert den Cache durch Entfernung ungültiger Einträge.
    
    Entfernt Cache-Einträge für:
    - Nicht mehr existierende Dateien
    - Veränderte Dateien (basierend auf Änderungsdatum)
    - Defekte Cache-Dateien
    """
    try:
        cache_manager = get_cache_manager()
        result = cache_manager.optimize_cache()
        
        return SuccessResponse(
            message=f"Cache optimization completed: {result['removed_entries']} entries removed, "
                   f"{result['freed_mb']:.1f} MB freed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error optimizing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize cache")


@router.get("/formats", summary="Get supported audio formats")
async def get_supported_formats():
    """
    Gibt alle unterstützten Audio-Formate zurück.
    """
    try:
        analyzer = get_analyzer()
        supported_formats = analyzer.get_supported_formats()
        
        # Categorize formats
        lossless_formats = [f for f in supported_formats if f in ['.flac', '.wav', '.aiff', '.aif', '.au']]
        compressed_formats = [f for f in supported_formats if f in ['.mp3', '.aac', '.ogg', '.m4a', '.wma', '.amr']]
        other_formats = [f for f in supported_formats if f not in lossless_formats + compressed_formats]
        
        return {
            "supported_formats": supported_formats,
            "total_count": len(supported_formats),
            "description": "Audio formats supported for analysis with librosa and optionally Essentia",
            "categories": {
                "lossless": lossless_formats,
                "compressed": compressed_formats,
                "other": other_formats
            },
            "recommendations": {
                "best_quality": "FLAC or WAV for highest analysis accuracy",
                "common_formats": "MP3, AAC, M4A are well supported",
                "avoid": "Very compressed or exotic formats may have reduced accuracy"
            },
            "essentia_available": analyzer.feature_extractor.use_essentia if hasattr(analyzer.feature_extractor, 'use_essentia') else False
        }
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get supported formats")


@router.get("/stats", summary="Get analysis statistics")
async def get_analysis_stats():
    """
    Gibt Statistiken über Audio-Analysen zurück.
    """
    try:
        analyzer = get_analyzer()
        cache_manager = get_cache_manager()
        
        # Get analysis statistics from analyzer
        analyzer_stats = analyzer.get_analysis_stats()
        
        # Get cache statistics
        cache_stats = cache_manager.get_cache_stats()
        
        # Current session task statistics
        total_tasks = len(_active_analysis_tasks)
        completed_tasks = len([t for t in _active_analysis_tasks.values() if t['status'] == AnalysisStatus.completed])
        running_tasks = len([t for t in _active_analysis_tasks.values() if t['status'] == AnalysisStatus.running])
        failed_tasks = len([t for t in _active_analysis_tasks.values() if t['status'] == AnalysisStatus.error])
        cancelled_tasks = len([t for t in _active_analysis_tasks.values() if t['status'] == AnalysisStatus.cancelled])
        
        # Calculate cache hit rate
        total_analyzed = analyzer_stats.get('total_analyzed', 0)
        cache_hits = analyzer_stats.get('cache_hits', 0)
        cache_hit_rate = (cache_hits / (total_analyzed + cache_hits) * 100) if (total_analyzed + cache_hits) > 0 else 0
        
        return {
            "analyzer_stats": {
                "total_analyzed": total_analyzed,
                "cache_hits": cache_hits,
                "cache_hit_rate": round(cache_hit_rate, 1),
                "errors": analyzer_stats.get('errors', 0),
                "processing_time_total": analyzer_stats.get('processing_time', 0.0),
                "average_processing_time": (analyzer_stats.get('processing_time', 0.0) / total_analyzed) if total_analyzed > 0 else 0
            },
            "cache_stats": {
                "total_cached_files": cache_stats.get('total_files', 0),
                "cache_size_mb": cache_stats.get('total_size_mb', 0),
                "cache_directory": cache_stats.get('cache_directory'),
                "oldest_cached": cache_stats.get('oldest_file', 0),
                "newest_cached": cache_stats.get('newest_file', 0)
            },
            "current_session": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "running_tasks": running_tasks,
                "failed_tasks": failed_tasks,
                "cancelled_tasks": cancelled_tasks,
                "success_rate": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
            },
            "active_tasks": [
                {
                    'task_id': task_id,
                    'status': info['status'].value if hasattr(info['status'], 'value') else str(info['status']),
                    'progress': round(info.get('progress', 0), 1),
                    'current_file': os.path.basename(info.get('current_file', '')) if info.get('current_file') else None,
                    'processed_files': info.get('processed_files', 0),
                    'total_files': info.get('total_files', 0),
                    'started_at': info.get('started_at'),
                    'estimated_completion': info.get('estimated_completion')
                }
                for task_id, info in _active_analysis_tasks.items()
                if info.get('status') == AnalysisStatus.running
            ],
            "system_info": {
                "essentia_available": analyzer.feature_extractor.use_essentia if hasattr(analyzer.feature_extractor, 'use_essentia') else False,
                "multiprocessing_enabled": analyzer.enable_multiprocessing,
                "max_workers": analyzer.max_workers,
                "supported_formats_count": len(analyzer.get_supported_formats())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis statistics")


@router.get("/validate/directory", summary="Validate directory for analysis")
async def validate_directory(
    directory: str = Query(..., description="Directory path to validate"),
    recursive: bool = Query(True, description="Include subdirectories")
):
    """
    Validiert ein Verzeichnis für Audio-Analyse.
    
    Prüft:
    - Existenz und Zugriff auf Verzeichnis
    - Anzahl Audio-Dateien
    - Geschätzte Analysezeit
    - Festplattenspeicher-Anforderungen
    """
    try:
        directory_path = Path(directory)
        
        # Validate directory
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail="Directory does not exist")
        
        if not directory_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        try:
            # Test directory access
            list(directory_path.iterdir())
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied to access directory")
        
        # Find audio files
        audio_files = find_audio_files([directory], recursive=recursive)
        
        # Check cache status
        cache_manager = get_cache_manager()
        cached_files = 0
        total_file_size = 0
        
        for file_path in audio_files:
            if cache_manager.is_cached(file_path):
                cached_files += 1
            
            try:
                total_file_size += os.path.getsize(file_path)
            except OSError:
                pass  # Ignore files we can't access
        
        uncached_files = len(audio_files) - cached_files
        
        # Estimate analysis time (rough estimate: 1 second per minute of audio)
        estimated_analysis_minutes = uncached_files * 0.5  # Assume average 3-minute tracks
        
        return {
            "directory": directory,
            "valid": True,
            "audio_files_found": len(audio_files),
            "cached_files": cached_files,
            "uncached_files": uncached_files,
            "total_file_size_mb": round(total_file_size / 1024 / 1024, 1),
            "estimated_analysis_time_minutes": round(estimated_analysis_minutes, 1),
            "recursive_scan": recursive,
            "ready_for_analysis": uncached_files > 0,
            "recommendation": (
                f"Ready to analyze {uncached_files} new files" 
                if uncached_files > 0
                else "All files already analyzed"
            ),
            "subdirectories_found": len([p for p in directory_path.iterdir() if p.is_dir()]) if recursive else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating directory {directory}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate directory")