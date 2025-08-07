"""Tracks API Endpoints - Track-Management und Suche"""

import os
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ..models import (
    Track, TrackSummary, TracksListResponse, TrackDetailsResponse,
    TracksQueryParams, ErrorResponse, MoodCategory
)
from ...core_engine.audio_analysis.analyzer import AudioAnalyzer
from ...core_engine.audio_analysis.cache_manager import CacheManager
from ...core_engine.mood_classifier.mood_classifier import MoodClassifier
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances (initialized on first use)
_analyzer = None
_cache_manager = None
_mood_classifier = None


def get_analyzer():
    """Get AudioAnalyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AudioAnalyzer(
            cache_dir=settings.get("audio_analysis.cache_dir"),
            enable_multiprocessing=settings.get("audio_analysis.enable_multiprocessing", True)
        )
    return _analyzer


def get_cache_manager():
    """Get CacheManager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(settings.get("audio_analysis.cache_dir"))
    return _cache_manager


def get_mood_classifier():
    """Get MoodClassifier instance"""
    global _mood_classifier
    if _mood_classifier is None:
        _mood_classifier = MoodClassifier()
    return _mood_classifier


def parse_query_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    key: Optional[str] = Query(None, description="Filter by key"),
    camelot: Optional[str] = Query(None, regex=r"^\d{1,2}[AB]$", description="Filter by Camelot"),
    mood: Optional[MoodCategory] = Query(None, description="Filter by mood"),
    min_bpm: Optional[float] = Query(None, ge=60, le=200, description="Minimum BPM"),
    max_bpm: Optional[float] = Query(None, ge=60, le=200, description="Maximum BPM"),
    min_energy: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum energy"),
    max_energy: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum energy"),
    artist: Optional[str] = Query(None, description="Filter by artist"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    search: Optional[str] = Query(None, description="Search in title/artist/filename"),
    sort_by: str = Query("filename", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order")
) -> TracksQueryParams:
    """Parse query parameters"""
    return TracksQueryParams(
        page=page, per_page=per_page, key=key, camelot=camelot, mood=mood,
        min_bpm=min_bpm, max_bpm=max_bpm, min_energy=min_energy, max_energy=max_energy,
        artist=artist, genre=genre, search=search, sort_by=sort_by, sort_order=sort_order
    )


def get_cached_tracks() -> List[dict]:
    """Get all cached tracks"""
    cache_manager = get_cache_manager()
    cached_files = cache_manager.get_cached_files()
    
    tracks = []
    for cached_file in cached_files:
        try:
            track_data = cache_manager.load_from_cache(cached_file['file_path'])
            if track_data:
                tracks.append(track_data)
        except Exception as e:
            logger.warning(f"Error loading cached track {cached_file['file_path']}: {e}")
    
    return tracks


def filter_tracks(tracks: List[dict], params: TracksQueryParams) -> List[dict]:
    """Filter tracks based on query parameters"""
    filtered = tracks
    
    # Filter by key
    if params.key:
        filtered = [t for t in filtered if t.get('camelot', {}).get('key', '').lower() == params.key.lower()]
    
    # Filter by Camelot
    if params.camelot:
        filtered = [t for t in filtered if t.get('camelot', {}).get('camelot') == params.camelot]
    
    # Filter by mood
    if params.mood:
        filtered = [t for t in filtered if t.get('derived_metrics', {}).get('estimated_mood') == params.mood.value]
    
    # Filter by BPM range
    if params.min_bpm is not None:
        filtered = [t for t in filtered if t.get('features', {}).get('bpm', 0) >= params.min_bpm]
    if params.max_bpm is not None:
        filtered = [t for t in filtered if t.get('features', {}).get('bpm', 999) <= params.max_bpm]
    
    # Filter by energy range
    if params.min_energy is not None:
        filtered = [t for t in filtered if t.get('features', {}).get('energy', 0) >= params.min_energy]
    if params.max_energy is not None:
        filtered = [t for t in filtered if t.get('features', {}).get('energy', 1) <= params.max_energy]
    
    # Filter by artist
    if params.artist:
        filtered = [t for t in filtered 
                   if params.artist.lower() in t.get('metadata', {}).get('artist', '').lower()]
    
    # Filter by genre
    if params.genre:
        filtered = [t for t in filtered 
                   if params.genre.lower() in t.get('metadata', {}).get('genre', '').lower()]
    
    # Search filter
    if params.search:
        search_lower = params.search.lower()
        def matches_search(track):
            metadata = track.get('metadata', {})
            return (search_lower in metadata.get('title', '').lower() or
                    search_lower in metadata.get('artist', '').lower() or
                    search_lower in track.get('filename', '').lower())
        
        filtered = [t for t in filtered if matches_search(t)]
    
    return filtered


def sort_tracks(tracks: List[dict], sort_by: str, sort_order: str) -> List[dict]:
    """Sort tracks"""
    reverse = sort_order == "desc"
    
    if sort_by == "filename":
        return sorted(tracks, key=lambda t: t.get('filename', ''), reverse=reverse)
    elif sort_by == "title":
        return sorted(tracks, key=lambda t: t.get('metadata', {}).get('title', ''), reverse=reverse)
    elif sort_by == "artist":
        return sorted(tracks, key=lambda t: t.get('metadata', {}).get('artist', ''), reverse=reverse)
    elif sort_by == "bpm":
        return sorted(tracks, key=lambda t: t.get('features', {}).get('bpm', 0), reverse=reverse)
    elif sort_by == "energy":
        return sorted(tracks, key=lambda t: t.get('features', {}).get('energy', 0), reverse=reverse)
    elif sort_by == "key":
        return sorted(tracks, key=lambda t: t.get('camelot', {}).get('key', ''), reverse=reverse)
    elif sort_by == "duration":
        return sorted(tracks, key=lambda t: t.get('metadata', {}).get('duration', 0), reverse=reverse)
    elif sort_by == "analyzed_at":
        return sorted(tracks, key=lambda t: t.get('metadata', {}).get('analyzed_at', 0), reverse=reverse)
    else:
        # Default to filename
        return sorted(tracks, key=lambda t: t.get('filename', ''), reverse=reverse)


def track_to_summary(track_data: dict) -> TrackSummary:
    """Convert track data to TrackSummary"""
    metadata = track_data.get('metadata', {})
    features = track_data.get('features', {})
    camelot = track_data.get('camelot', {})
    derived_metrics = track_data.get('derived_metrics', {})
    
    return TrackSummary(
        file_path=track_data.get('file_path', ''),
        filename=track_data.get('filename', ''),
        title=metadata.get('title'),
        artist=metadata.get('artist'),
        duration=metadata.get('duration', 0),
        bpm=features.get('bpm', 0),
        key=camelot.get('key', ''),
        camelot=camelot.get('camelot', ''),
        energy=features.get('energy', 0),
        mood=derived_metrics.get('estimated_mood'),
        analyzed_at=metadata.get('analyzed_at', 0)
    )


@router.get("", response_model=TracksListResponse, summary="List all tracks")
async def list_tracks(params: TracksQueryParams = Depends(parse_query_params)):
    """
    Gibt eine paginierte Liste aller analysierten Tracks zurück.
    
    Unterstützt Filter und Suche:
    - **key**: Tonart-Filter (z.B. "C Major")
    - **camelot**: Camelot Wheel Filter (z.B. "8A")  
    - **mood**: Stimmungsfilter
    - **min_bpm/max_bpm**: BPM-Bereich
    - **min_energy/max_energy**: Energie-Bereich
    - **artist/genre**: Text-Filter
    - **search**: Volltext-Suche in Titel/Artist/Dateiname
    """
    try:
        # Get all cached tracks
        all_tracks = get_cached_tracks()
        
        if not all_tracks:
            return TracksListResponse(
                tracks=[],
                total_count=0,
                page=params.page,
                per_page=params.per_page,
                total_pages=0,
                has_next=False,
                has_prev=False
            )
        
        # Filter tracks
        filtered_tracks = filter_tracks(all_tracks, params)
        
        # Sort tracks
        sorted_tracks = sort_tracks(filtered_tracks, params.sort_by, params.sort_order)
        
        # Pagination
        total_count = len(sorted_tracks)
        total_pages = (total_count + params.per_page - 1) // params.per_page
        start_idx = (params.page - 1) * params.per_page
        end_idx = start_idx + params.per_page
        
        paginated_tracks = sorted_tracks[start_idx:end_idx]
        
        # Convert to summaries
        track_summaries = [track_to_summary(track) for track in paginated_tracks]
        
        return TracksListResponse(
            tracks=track_summaries,
            total_count=total_count,
            page=params.page,
            per_page=params.per_page,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1
        )
        
    except Exception as e:
        logger.error(f"Error listing tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tracks")


@router.get("/{track_id:path}", response_model=TrackDetailsResponse, summary="Get track details")
async def get_track_details(track_id: str):
    """
    Gibt detaillierte Informationen zu einem einzelnen Track zurück.
    
    Der track_id ist der file_path des Tracks (URL-encoded).
    """
    try:
        # Decode track_id (it's the file path)
        file_path = track_id
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Track file not found")
        
        # Try to load from cache first
        cache_manager = get_cache_manager()
        track_data = cache_manager.load_from_cache(file_path)
        
        if not track_data:
            # If not cached, analyze the track
            logger.info(f"Track not in cache, analyzing: {file_path}")
            analyzer = get_analyzer()
            track_data = analyzer.analyze_track(file_path)
            
            if track_data.get('status') == 'error':
                raise HTTPException(status_code=422, detail=f"Track analysis failed: {track_data.get('errors', [])}")
        
        # Add mood analysis if not present
        if 'mood' not in track_data or not track_data['mood']:
            try:
                mood_classifier = get_mood_classifier()
                mood, confidence, scores = mood_classifier.classify_mood(track_data.get('features', {}))
                track_data['mood'] = {
                    'primary_mood': mood,
                    'confidence': confidence,
                    'scores': scores,
                    'explanation': f"Classified as {mood} with {confidence:.1%} confidence"
                }
            except Exception as e:
                logger.warning(f"Mood classification failed for {file_path}: {e}")
        
        return TrackDetailsResponse(track=Track(**track_data))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track details for {track_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get track details")


@router.get("/search/similar", response_model=TracksListResponse, summary="Find similar tracks")
async def find_similar_tracks(
    track_path: str = Query(..., description="Reference track file path"),
    limit: int = Query(10, ge=1, le=50, description="Number of similar tracks to return"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
):
    """
    Findet ähnliche Tracks basierend auf Audio-Features.
    
    Verwendet einen einfachen Ähnlichkeits-Algorithmus basierend auf:
    - BPM-Ähnlichkeit
    - Energie-Ähnlichkeit  
    - Camelot Wheel Kompatibilität
    - Mood-Ähnlichkeit
    """
    try:
        # Get reference track
        cache_manager = get_cache_manager()
        reference_track = cache_manager.load_from_cache(track_path)
        
        if not reference_track:
            raise HTTPException(status_code=404, detail="Reference track not found in cache")
        
        # Get all tracks
        all_tracks = get_cached_tracks()
        similar_tracks = []
        
        ref_features = reference_track.get('features', {})
        ref_camelot = reference_track.get('camelot', {})
        ref_mood = reference_track.get('derived_metrics', {}).get('estimated_mood', '')
        
        for track in all_tracks:
            if track.get('file_path') == track_path:
                continue  # Skip reference track itself
            
            # Calculate similarity score
            similarity_score = calculate_similarity(reference_track, track)
            
            if similarity_score >= similarity_threshold:
                track_summary = track_to_summary(track)
                similar_tracks.append({
                    'track': track_summary,
                    'similarity_score': similarity_score
                })
        
        # Sort by similarity score (descending)
        similar_tracks.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results
        limited_tracks = similar_tracks[:limit]
        
        return TracksListResponse(
            tracks=[item['track'] for item in limited_tracks],
            total_count=len(similar_tracks),
            page=1,
            per_page=limit,
            total_pages=1,
            has_next=False,
            has_prev=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar tracks")


def calculate_similarity(track1: dict, track2: dict) -> float:
    """Calculate similarity score between two tracks"""
    features1 = track1.get('features', {})
    features2 = track2.get('features', {})
    
    camelot1 = track1.get('camelot', {})
    camelot2 = track2.get('camelot', {})
    
    mood1 = track1.get('derived_metrics', {}).get('estimated_mood', '')
    mood2 = track2.get('derived_metrics', {}).get('estimated_mood', '')
    
    similarity_scores = []
    
    # BPM similarity (weight: 0.3)
    bpm1 = features1.get('bpm', 120)
    bpm2 = features2.get('bpm', 120)
    bpm_diff = abs(bpm1 - bpm2)
    bpm_similarity = max(0, 1 - (bpm_diff / 40))  # 40 BPM difference = 0 similarity
    similarity_scores.append(bpm_similarity * 0.3)
    
    # Energy similarity (weight: 0.25)
    energy1 = features1.get('energy', 0.5)
    energy2 = features2.get('energy', 0.5)
    energy_similarity = 1 - abs(energy1 - energy2)
    similarity_scores.append(energy_similarity * 0.25)
    
    # Valence similarity (weight: 0.2)
    valence1 = features1.get('valence', 0.5)
    valence2 = features2.get('valence', 0.5)
    valence_similarity = 1 - abs(valence1 - valence2)
    similarity_scores.append(valence_similarity * 0.2)
    
    # Camelot compatibility (weight: 0.15)
    camelot_sim = 0.0
    camelot1_key = camelot1.get('camelot', '')
    camelot2_key = camelot2.get('camelot', '')
    
    if camelot1_key and camelot2_key:
        compatible_keys = camelot1.get('compatible_keys', [])
        if camelot1_key == camelot2_key:
            camelot_sim = 1.0
        elif camelot2_key in compatible_keys:
            camelot_sim = 0.8
        else:
            camelot_sim = 0.0
    
    similarity_scores.append(camelot_sim * 0.15)
    
    # Mood similarity (weight: 0.1)
    mood_sim = 1.0 if mood1 == mood2 else 0.0
    similarity_scores.append(mood_sim * 0.1)
    
    return sum(similarity_scores)


@router.get("/stats/overview", summary="Get tracks overview statistics")
async def get_tracks_statistics():
    """
    Gibt Überblick-Statistiken über alle analysierten Tracks zurück.
    """
    try:
        all_tracks = get_cached_tracks()
        
        if not all_tracks:
            return {
                "total_tracks": 0,
                "statistics": {}
            }
        
        # Calculate statistics
        total_tracks = len(all_tracks)
        total_duration = sum(t.get('metadata', {}).get('duration', 0) for t in all_tracks)
        
        # BPM statistics
        bpms = [t.get('features', {}).get('bpm', 0) for t in all_tracks]
        avg_bpm = sum(bpms) / len(bpms) if bpms else 0
        
        # Energy statistics  
        energies = [t.get('features', {}).get('energy', 0) for t in all_tracks]
        avg_energy = sum(energies) / len(energies) if energies else 0
        
        # Key distribution
        key_distribution = {}
        for track in all_tracks:
            camelot = track.get('camelot', {}).get('camelot', 'Unknown')
            key_distribution[camelot] = key_distribution.get(camelot, 0) + 1
        
        # Mood distribution
        mood_distribution = {}
        for track in all_tracks:
            mood = track.get('derived_metrics', {}).get('estimated_mood', 'unknown')
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        # Genre distribution
        genre_distribution = {}
        for track in all_tracks:
            genre = track.get('metadata', {}).get('genre', 'Unknown')
            genre_distribution[genre] = genre_distribution.get(genre, 0) + 1
        
        return {
            "total_tracks": total_tracks,
            "total_duration_hours": total_duration / 3600,
            "statistics": {
                "average_bpm": round(avg_bpm, 1),
                "average_energy": round(avg_energy, 3),
                "bpm_range": {
                    "min": min(bpms) if bpms else 0,
                    "max": max(bpms) if bpms else 0
                },
                "energy_range": {
                    "min": min(energies) if energies else 0,
                    "max": max(energies) if energies else 0
                }
            },
            "distributions": {
                "keys": key_distribution,
                "moods": mood_distribution,
                "genres": dict(list(genre_distribution.items())[:10])  # Top 10 genres
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting tracks statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tracks statistics")