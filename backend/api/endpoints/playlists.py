"""Playlists API Endpoints - Playlist-Generierung und Export"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from ..models import (
    PlaylistGenerationRequest, PlaylistGenerationResponse, PlaylistExportRequest, 
    PlaylistExportResponse, PlaylistPresetInfo, PlaylistPresetDetails,
    PresetsListResponse, PresetDetailsResponse, PresetCreationRequest,
    SortingAlgorithm, ExportFormat, SuccessResponse, ErrorResponse
)
from ...core_engine.playlist_engine.playlist_engine import PlaylistEngine, PlaylistPreset, PlaylistRule
from ...core_engine.export.playlist_exporter import PlaylistExporter
from ...core_engine.audio_analysis.cache_manager import CacheManager
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
_playlist_engine = None
_playlist_exporter = None
_cache_manager = None

# Background task storage for playlist generation
_active_playlist_tasks = {}


def get_playlist_engine():
    """Get PlaylistEngine instance"""
    global _playlist_engine
    if _playlist_engine is None:
        _playlist_engine = PlaylistEngine(settings.get("playlist_engine.presets_dir"))
    return _playlist_engine


def get_playlist_exporter():
    """Get PlaylistExporter instance"""
    global _playlist_exporter
    if _playlist_exporter is None:
        _playlist_exporter = PlaylistExporter(settings.get("export.output_dir"))
    return _playlist_exporter


def get_cache_manager():
    """Get CacheManager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(settings.get("audio_analysis.cache_dir"))
    return _cache_manager


async def generate_playlist_task(
    task_id: str,
    track_paths: List[str],
    preset_name: Optional[str],
    custom_rules: Optional[List[dict]],
    target_duration: Optional[int]
):
    """Background task for playlist generation"""
    try:
        logger.info(f"Starting playlist generation task {task_id}")
        _active_playlist_tasks[task_id] = {
            'status': 'loading_tracks',
            'progress': 0,
            'message': 'Loading track data...',
            'started_at': datetime.now().isoformat()
        }
        
        # Load track data from cache
        cache_manager = get_cache_manager()
        tracks = []
        
        for i, track_path in enumerate(track_paths):
            track_data = cache_manager.load_from_cache(track_path)
            if track_data:
                tracks.append(track_data)
            else:
                logger.warning(f"Track not found in cache: {track_path}")
            
            # Update progress
            progress = (i + 1) / len(track_paths) * 30  # 30% for loading
            _active_playlist_tasks[task_id]['progress'] = progress
            _active_playlist_tasks[task_id]['message'] = f'Loaded {i + 1}/{len(track_paths)} tracks'
            
            # Small delay to show progress
            await asyncio.sleep(0.01)
        
        if len(tracks) < 3:
            _active_playlist_tasks[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Not enough tracks loaded from cache: {len(tracks)}/{len(track_paths)}',
                'error': 'Insufficient tracks for playlist generation'
            }
            return
        
        # Convert custom rules if provided
        rules = None
        if custom_rules:
            rules = [PlaylistRule(**rule) for rule in custom_rules]
        
        # Generate playlist
        _active_playlist_tasks[task_id]['status'] = 'generating'
        _active_playlist_tasks[task_id]['progress'] = 40
        _active_playlist_tasks[task_id]['message'] = 'Generating playlist...'
        
        playlist_engine = get_playlist_engine()
        
        # Progress callback for playlist generation
        async def progress_callback(message: str):
            if task_id in _active_playlist_tasks:
                current_progress = _active_playlist_tasks[task_id]['progress']
                new_progress = min(90, current_progress + 5)
                _active_playlist_tasks[task_id]['progress'] = new_progress
                _active_playlist_tasks[task_id]['message'] = message
        
        # Generate playlist asynchronously
        result = await playlist_engine.create_playlist_async(
            tracks=tracks,
            preset_name=preset_name,
            custom_rules=rules,
            target_duration=target_duration,
            progress_callback=progress_callback
        )
        
        if 'error' in result:
            _active_playlist_tasks[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Playlist generation failed',
                'error': result['error']
            }
            return
        
        # Store result
        _active_playlist_tasks[task_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Playlist generated successfully',
            'result': result,
            'completed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Playlist generation task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Playlist generation task {task_id} failed: {e}")
        _active_playlist_tasks[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Playlist generation failed: {str(e)}',
            'error': str(e)
        }


@router.get("/presets", response_model=PresetsListResponse, summary="List all presets")
async def list_presets():
    """
    Gibt alle verfügbaren Playlist-Presets zurück.
    
    Enthält sowohl Standard-Presets als auch benutzerdefinierte Presets.
    """
    try:
        playlist_engine = get_playlist_engine()
        presets_data = playlist_engine.get_all_presets()
        
        presets = [PlaylistPresetInfo(**preset) for preset in presets_data]
        
        return PresetsListResponse(
            presets=presets,
            total_count=len(presets)
        )
        
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail="Failed to list presets")


@router.get("/presets/{preset_name}", response_model=PresetDetailsResponse, summary="Get preset details")
async def get_preset_details(preset_name: str):
    """
    Gibt detaillierte Informationen zu einem spezifischen Preset zurück.
    """
    try:
        playlist_engine = get_playlist_engine()
        preset_data = playlist_engine.get_preset_details(preset_name)
        
        if not preset_data:
            raise HTTPException(status_code=404, detail="Preset not found")
        
        preset = PlaylistPresetDetails(**preset_data)
        
        return PresetDetailsResponse(preset=preset)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preset details")


@router.post("/presets", response_model=SuccessResponse, summary="Create custom preset")
async def create_preset(preset_request: PresetCreationRequest):
    """
    Erstellt ein neues benutzerdefiniertes Preset.
    """
    try:
        playlist_engine = get_playlist_engine()
        
        # Convert request to dict format expected by playlist engine
        preset_data = {
            'name': preset_request.name,
            'description': preset_request.description,
            'algorithm': preset_request.algorithm.value,
            'rules': [rule.dict() for rule in preset_request.rules],
            'target_duration_minutes': preset_request.target_duration_minutes,
            'energy_curve': preset_request.energy_curve,
            'mood_flow': preset_request.mood_flow
        }
        
        success = playlist_engine.save_custom_preset(preset_data)
        
        if success:
            return SuccessResponse(
                message=f"Preset '{preset_request.name}' created successfully",
                data={'preset_name': preset_request.name}
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create preset")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail="Failed to create preset")


@router.delete("/presets/{preset_name}", response_model=SuccessResponse, summary="Delete custom preset")
async def delete_preset(preset_name: str):
    """
    Löscht ein benutzerdefiniertes Preset.
    Standard-Presets können nicht gelöscht werden.
    """
    try:
        playlist_engine = get_playlist_engine()
        success = playlist_engine.delete_custom_preset(preset_name)
        
        if success:
            return SuccessResponse(
                message=f"Preset '{preset_name}' deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Preset not found or cannot be deleted")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete preset")


@router.post("/generate", response_model=dict, summary="Generate playlist")
async def generate_playlist(
    request: PlaylistGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Startet die Playlist-Generierung als Hintergrundaufgabe.
    
    Dieser Endpunkt ist der Kern der Playlist-Engine. Er:
    1. Validiert die Track-Daten
    2. Startet die Generierung als async Background Task
    3. Gibt sofort eine Task-ID zurück
    4. Client kann Progress über /generate/{task_id}/status abfragen
    """
    try:
        # Validate tracks exist in cache
        cache_manager = get_cache_manager()
        valid_tracks = []
        
        for track_path in request.track_file_paths:
            if cache_manager.is_cached(track_path):
                valid_tracks.append(track_path)
            else:
                logger.warning(f"Track not found in cache: {track_path}")
        
        if len(valid_tracks) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient analyzed tracks: {len(valid_tracks)}/{len(request.track_file_paths)}. "
                       f"Please analyze tracks first using /api/analysis/start"
            )
        
        # Generate unique task ID
        task_id = f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(_active_playlist_tasks)}"
        
        # Start background task
        background_tasks.add_task(
            generate_playlist_task,
            task_id=task_id,
            track_paths=valid_tracks,
            preset_name=request.preset_name,
            custom_rules=[rule.dict() for rule in request.custom_rules] if request.custom_rules else None,
            target_duration=request.target_duration_minutes
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Playlist generation started",
            "valid_tracks_count": len(valid_tracks),
            "total_requested": len(request.track_file_paths),
            "status_url": f"/api/playlists/generate/{task_id}/status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting playlist generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start playlist generation")


@router.get("/generate/{task_id}/status", summary="Get playlist generation status")
async def get_generation_status(task_id: str):
    """
    Gibt den aktuellen Status der Playlist-Generierung zurück.
    """
    if task_id not in _active_playlist_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = _active_playlist_tasks[task_id]
    
    # Clean up completed/failed tasks after some time
    if task_info['status'] in ['completed', 'error']:
        # Keep task info for 1 hour after completion
        if 'completed_at' in task_info:
            completed_time = datetime.fromisoformat(task_info['completed_at'])
            if (datetime.now() - completed_time).seconds > 3600:
                del _active_playlist_tasks[task_id]
                raise HTTPException(status_code=404, detail="Task expired")
    
    return task_info


@router.get("/generate/{task_id}/result", response_model=PlaylistGenerationResponse, summary="Get playlist generation result")
async def get_generation_result(task_id: str):
    """
    Gibt das Ergebnis der Playlist-Generierung zurück (nur wenn abgeschlossen).
    """
    if task_id not in _active_playlist_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = _active_playlist_tasks[task_id]
    
    if task_info['status'] == 'completed':
        result = task_info['result']
        return PlaylistGenerationResponse(
            success=True,
            playlist=result,
            generation_time_seconds=0  # Could be calculated from timestamps
        )
    elif task_info['status'] == 'error':
        return PlaylistGenerationResponse(
            success=False,
            error=task_info.get('error', 'Unknown error'),
            generation_time_seconds=0
        )
    else:
        raise HTTPException(
            status_code=202,  # Accepted but not ready
            detail=f"Task still {task_info['status']}: {task_info['message']}"
        )


@router.post("/export", response_model=PlaylistExportResponse, summary="Export playlist")
async def export_playlist(request: PlaylistExportRequest):
    """
    Exportiert eine generierte Playlist in das gewünschte Format.
    
    Unterstützte Formate:
    - **m3u**: Standard M3U Playlist für Media Player
    - **json**: Vollständige Daten im JSON-Format
    - **csv**: Tabellarische Daten für Analyse
    - **rekordbox**: Rekordbox XML für Pioneer DJ-Software
    """
    try:
        playlist_exporter = get_playlist_exporter()
        
        # Convert playlist to dict format
        playlist_dict = request.playlist_data.dict()
        tracks = playlist_dict['tracks']
        metadata = playlist_dict.get('metadata')
        
        # Export playlist
        result = playlist_exporter.export_playlist(
            tracks=tracks,
            format_type=request.format_type.value,
            output_filename=request.filename,
            metadata=metadata if request.include_metadata else None
        )
        
        if result['success']:
            return PlaylistExportResponse(
                success=True,
                output_path=result['output_path'],
                filename=result['filename'],
                format_type=request.format_type,
                track_count=result['track_count'],
                file_size_bytes=result['file_size_bytes']
            )
        else:
            return PlaylistExportResponse(
                success=False,
                error=result['error']
            )
            
    except Exception as e:
        logger.error(f"Error exporting playlist: {e}")
        return PlaylistExportResponse(
            success=False,
            error=str(e)
        )


@router.get("/exports", summary="List exported playlists")
async def list_exports():
    """
    Gibt eine Liste aller exportierten Playlists zurück.
    """
    try:
        playlist_exporter = get_playlist_exporter()
        exports = playlist_exporter.list_exports()
        
        return {
            "exports": exports,
            "total_count": len(exports),
            "supported_formats": playlist_exporter.get_supported_formats()
        }
        
    except Exception as e:
        logger.error(f"Error listing exports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list exports")


@router.delete("/exports/{filename}", response_model=SuccessResponse, summary="Delete exported playlist")
async def delete_export(filename: str):
    """
    Löscht eine exportierte Playlist-Datei.
    """
    try:
        playlist_exporter = get_playlist_exporter()
        success = playlist_exporter.delete_export(filename)
        
        if success:
            return SuccessResponse(
                message=f"Export '{filename}' deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Export file not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete export")


@router.get("/algorithms", summary="List available sorting algorithms")
async def list_algorithms():
    """
    Gibt Informationen über alle verfügbaren Playlist-Algorithmen zurück.
    """
    try:
        playlist_engine = get_playlist_engine()
        algorithms_info = playlist_engine.get_algorithm_info()
        
        return {
            "algorithms": algorithms_info,
            "total_count": len(algorithms_info),
            "default_algorithm": "hybrid_smart"
        }
        
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        raise HTTPException(status_code=500, detail="Failed to list algorithms")


@router.post("/validate", summary="Validate tracks for playlist generation")
async def validate_tracks_for_playlist(track_paths: List[str]):
    """
    Validiert ob Tracks für Playlist-Generierung geeignet sind.
    """
    try:
        cache_manager = get_cache_manager()
        playlist_exporter = get_playlist_exporter()
        
        # Check which tracks are available
        available_tracks = []
        missing_tracks = []
        track_data = []
        
        for track_path in track_paths:
            if cache_manager.is_cached(track_path):
                track = cache_manager.load_from_cache(track_path)
                if track:
                    available_tracks.append(track_path)
                    track_data.append(track)
                else:
                    missing_tracks.append(track_path)
            else:
                missing_tracks.append(track_path)
        
        # Validate track data quality
        validation_result = playlist_exporter.validate_tracks(track_data)
        
        return {
            "total_requested": len(track_paths),
            "available_tracks": len(available_tracks),
            "missing_tracks": len(missing_tracks),
            "missing_track_paths": missing_tracks[:10],  # Show first 10
            "validation": validation_result,
            "ready_for_generation": len(available_tracks) >= 3 and validation_result['valid'],
            "recommendation": (
                "Ready for playlist generation" 
                if len(available_tracks) >= 3 and validation_result['valid']
                else f"Analyze {len(missing_tracks)} missing tracks first"
            )
        }
        
    except Exception as e:
        logger.error(f"Error validating tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate tracks")


@router.get("/stats/generation", summary="Get playlist generation statistics")
async def get_generation_stats():
    """
    Gibt Statistiken über Playlist-Generierungen zurück.
    """
    try:
        # Current task statistics
        total_tasks = len(_active_playlist_tasks)
        completed_tasks = len([t for t in _active_playlist_tasks.values() if t['status'] == 'completed'])
        running_tasks = len([t for t in _active_playlist_tasks.values() if t['status'] in ['loading_tracks', 'generating']])
        failed_tasks = len([t for t in _active_playlist_tasks.values() if t['status'] == 'error'])
        
        # Preset usage statistics
        playlist_engine = get_playlist_engine()
        presets = playlist_engine.get_all_presets()
        
        return {
            "current_session": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "running_tasks": running_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "available_presets": len(presets),
            "available_algorithms": len(playlist_engine.get_algorithm_info()),
            "active_tasks": [
                {
                    'task_id': task_id,
                    'status': info['status'],
                    'progress': info.get('progress', 0),
                    'message': info.get('message', '')
                }
                for task_id, info in _active_playlist_tasks.items()
                if info['status'] in ['loading_tracks', 'generating']
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get generation statistics")