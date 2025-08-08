"""Pydantic Models für API Requests und Responses"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


# Enums
class SortingAlgorithm(str, Enum):
    hybrid_smart = "hybrid_smart"
    bpm_progression = "bpm_progression"
    energy_flow = "energy_flow"
    harmonic_mixing = "harmonic_mixing"
    mood_journey = "mood_journey"


class MoodCategory(str, Enum):
    energetic = "energetic"
    happy = "happy"
    calm = "calm"
    melancholic = "melancholic"
    aggressive = "aggressive"
    neutral = "neutral"


class ExportFormat(str, Enum):
    m3u = "m3u"
    json = "json"
    csv = "csv"
    rekordbox = "rekordbox"


class AnalysisStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"
    cancelled = "cancelled"


class PlaylistGenerationStatus(str, Enum):
    loading_tracks = "loading_tracks"
    generating = "generating"
    completed = "completed"
    error = "error"


# Base Models
class AudioFeatures(BaseModel):
    """Audio features extracted from track analysis"""
    bpm: float = Field(..., gt=0, le=300, description="Beats per minute")
    energy: float = Field(..., ge=0.0, le=1.0, description="Energy level (0-1)")
    valence: float = Field(..., ge=0.0, le=1.0, description="Musical positiveness (0-1)")
    danceability: float = Field(..., ge=0.0, le=1.0, description="Danceability (0-1)")
    acousticness: float = Field(..., ge=0.0, le=1.0, description="Acousticness (0-1)")
    instrumentalness: float = Field(..., ge=0.0, le=1.0, description="Instrumentalness (0-1)")


class TrackMetadata(BaseModel):
    """Track metadata from file tags"""
    title: Optional[str] = Field(None, description="Track title")
    artist: Optional[str] = Field(None, description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    duration: float = Field(..., gt=0, description="Duration in seconds")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    format: str = Field(..., description="Audio format")
    bitrate: Optional[int] = Field(None, description="Bitrate")
    analyzed_at: float = Field(..., description="Analysis timestamp")


class CamelotInfo(BaseModel):
    """Camelot Wheel information for harmonic mixing"""
    key: str = Field(..., description="Musical key (e.g., 'C Major', '8A')")
    camelot: str = Field(..., pattern=r"^\d{1,2}[AB]$", description="Camelot notation (e.g., '8A')")
    key_confidence: float = Field(..., ge=0.0, le=1.0, description="Key detection confidence")
    compatible_keys: List[str] = Field(..., description="Harmonically compatible keys")


class DerivedMetrics(BaseModel):
    """Derived metrics calculated from features"""
    energy_level: str = Field(..., description="Energy level category (low/medium/high)")
    bpm_category: str = Field(..., description="BPM category (slow/medium/fast/very_fast)")
    estimated_mood: str = Field(..., description="Estimated mood category")
    danceability_level: str = Field(..., description="Danceability level (low/medium/high)")


class MoodAnalysis(BaseModel):
    """Mood analysis results"""
    primary_mood: MoodCategory = Field(..., description="Primary mood category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    scores: Dict[str, float] = Field(..., description="Scores for all mood categories")
    explanation: Optional[str] = Field(None, description="Human-readable explanation")


# Track Models
class Track(BaseModel):
    """Complete track information"""
    file_path: str = Field(..., description="Full path to audio file")
    filename: str = Field(..., description="File name")
    metadata: TrackMetadata = Field(..., description="Track metadata")
    features: AudioFeatures = Field(..., description="Extracted audio features")
    camelot: CamelotInfo = Field(..., description="Camelot Wheel information")
    time_series_features: Optional[Union[Dict[str, List], List[Dict]]] = Field(None, description="Time series data")
    mood: MoodAnalysis = Field(..., description="Mood analysis results")
    derived_metrics: Optional[DerivedMetrics] = Field(None, description="Derived metrics")


class TrackSummary(BaseModel):
    """Simplified track information for listings"""
    file_path: str
    filename: str
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: float
    bpm: float
    key: str = ''
    camelot: str = ''
    energy: float
    mood: Optional[str] = None
    analyzed_at: float


# Playlist Models
class PlaylistRule(BaseModel):
    """Playlist generation rule"""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    weight: float = Field(..., ge=0.0, le=1.0, description="Rule weight")
    enabled: bool = Field(default=True, description="Whether rule is active")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")


class PlaylistPresetInfo(BaseModel):
    """Playlist preset information"""
    name: str = Field(..., description="Preset name")
    description: str = Field(..., description="Preset description") 
    algorithm: SortingAlgorithm = Field(..., description="Sorting algorithm")
    energy_curve: str = Field(..., description="Energy curve type")
    mood_flow: str = Field(..., description="Mood flow type")
    target_duration_minutes: Optional[int] = Field(None, description="Target duration")
    is_default: bool = Field(..., description="Is default preset")
    created_at: str = Field(..., description="Creation timestamp")


class PlaylistPresetDetails(PlaylistPresetInfo):
    """Detailed playlist preset with rules"""
    rules: List[PlaylistRule] = Field(..., description="Playlist rules")


class PlaylistMetadata(BaseModel):
    """Playlist metadata"""
    total_tracks: int = Field(..., ge=0, description="Number of tracks")
    total_duration_seconds: float = Field(..., ge=0, description="Total duration")
    total_duration_minutes: float = Field(..., ge=0, description="Total duration in minutes")
    average_energy: float = Field(..., ge=0.0, le=1.0, description="Average energy")
    average_valence: float = Field(..., ge=0.0, le=1.0, description="Average valence")
    average_danceability: float = Field(..., ge=0.0, le=1.0, description="Average danceability")
    bpm_stats: Dict[str, float] = Field(..., description="BPM statistics")
    key_distribution: Dict[str, int] = Field(..., description="Key distribution")
    mood_distribution: Dict[str, int] = Field(..., description="Mood distribution")
    energy_progression: List[float] = Field(..., description="Energy values over time")
    preset_name: str = Field(..., description="Used preset name")
    energy_curve: str = Field(..., description="Energy curve type")
    mood_flow: str = Field(..., description="Mood flow type")


class Playlist(BaseModel):
    """Complete playlist"""
    playlist_id: str = Field(..., description="Playlist ID")
    tracks: List[Dict[str, Any]] = Field(..., description="Playlist tracks in order")
    metadata: Dict[str, Any] = Field(..., description="Playlist metadata")


# Request Models
class AnalysisStartRequest(BaseModel):
    """Request to start audio analysis"""
    directories: Optional[List[str]] = Field(None, description="Directories to scan")
    file_paths: Optional[List[str]] = Field(None, description="Specific files to analyze")
    recursive: Optional[bool] = Field(default=True, description="Scan subdirectories")
    overwrite_cache: Optional[bool] = Field(default=False, description="Overwrite existing cache")
    include_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")


class PlaylistGenerationRequest(BaseModel):
    """Request to generate playlist"""
    track_file_paths: List[str] = Field(..., min_items=3, description="Track file paths to use")
    preset_name: Optional[str] = Field(None, description="Preset name to use")
    custom_rules: Optional[List[PlaylistRule]] = Field(None, description="Custom rules")
    target_duration_minutes: Optional[int] = Field(None, gt=0, le=480, description="Target duration")
    algorithm: Optional[SortingAlgorithm] = Field(None, description="Override algorithm")
    
    @validator('track_file_paths')
    def validate_track_paths(cls, v):
        if len(v) < 3:
            raise ValueError('At least 3 tracks required for playlist generation')
        return v


class PlaylistExportRequest(BaseModel):
    """Request to export playlist"""
    playlist_data: Playlist = Field(..., description="Playlist data to export")
    format_type: ExportFormat = Field(..., description="Export format")
    filename: Optional[str] = Field(None, description="Custom filename")
    include_metadata: bool = Field(default=True, description="Include metadata in export")


class PresetCreationRequest(BaseModel):
    """Request to create custom preset"""
    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    description: str = Field(..., min_length=1, max_length=500, description="Preset description")
    algorithm: SortingAlgorithm = Field(..., description="Sorting algorithm")
    rules: List[PlaylistRule] = Field(..., min_items=1, description="Playlist rules")
    target_duration_minutes: Optional[int] = Field(None, gt=0, le=480)
    energy_curve: str = Field(default="gradual_build", description="Energy curve type")
    mood_flow: str = Field(default="coherent", description="Mood flow type")


# Response Models
class AnalysisStatusResponse(BaseModel):
    """Analysis status response"""
    status: AnalysisStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    processed_files: int = Field(..., ge=0, description="Number of processed files")
    total_files: int = Field(..., ge=0, description="Total files to process")
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


class TracksListResponse(BaseModel):
    """Paginated tracks list response"""
    tracks: List[TrackSummary] = Field(..., description="Track summaries")
    total_count: int = Field(..., ge=0, description="Total number of tracks")
    page: int = Field(..., ge=1, description="Current page")
    per_page: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class TrackDetailsResponse(BaseModel):
    """Single track details response"""
    track: Track = Field(..., description="Complete track information")


class PlaylistGenerationResponse(BaseModel):
    """Playlist generation response"""
    success: bool = Field(..., description="Generation success")
    playlist: Optional[Dict[str, Any]] = Field(None, description="Generated playlist")
    error: Optional[str] = Field(None, description="Error message")
    generation_time_seconds: float = Field(..., ge=0, description="Generation time")


class PlaylistExportResponse(BaseModel):
    """Playlist export response"""
    success: bool = Field(..., description="Export success")
    output_path: Optional[str] = Field(None, description="Export file path")
    filename: Optional[str] = Field(None, description="Export filename")
    format_type: Optional[ExportFormat] = Field(None, description="Export format")
    track_count: Optional[int] = Field(None, description="Number of tracks exported")
    file_size_bytes: Optional[int] = Field(None, description="Export file size")
    error: Optional[str] = Field(None, description="Error message")


class PresetsListResponse(BaseModel):
    """Presets list response"""
    presets: List[PlaylistPresetInfo] = Field(..., description="Available presets")
    total_count: int = Field(..., ge=0, description="Total preset count")


class PresetDetailsResponse(BaseModel):
    """Preset details response"""
    preset: PlaylistPresetDetails = Field(..., description="Detailed preset information")


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    total_files: int = Field(..., ge=0, description="Total cached files")
    total_size_bytes: int = Field(..., ge=0, description="Total cache size")
    total_size_mb: float = Field(..., ge=0, description="Total cache size in MB")
    cache_directory: str = Field(..., description="Cache directory path")
    created: float = Field(..., description="Cache creation timestamp")
    last_cleanup: float = Field(..., description="Last cleanup timestamp")
    oldest_file: float = Field(..., description="Oldest file timestamp")
    newest_file: float = Field(..., description="Newest file timestamp")


class ApiStatusResponse(BaseModel):
    """API status response"""
    api_version: str = Field(..., description="API version")
    status: str = Field(..., description="Operational status")
    uptime_info: str = Field(..., description="Uptime information")
    cache_statistics: CacheStatsResponse = Field(..., description="Cache statistics")
    system_info: Dict[str, Any] = Field(..., description="System information")
    directories: Dict[str, str] = Field(..., description="System directories")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    error_type: Optional[str] = Field(None, description="Error type")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = Field(default=True, description="Operation success")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")


# Query Parameters Models (for FastAPI dependency injection)
class TracksQueryParams(BaseModel):
    """Query parameters for tracks listing"""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=200, description="Items per page")
    key: Optional[str] = Field(None, description="Filter by key")
    camelot: Optional[str] = Field(None, pattern=r"^\d{1,2}[AB]$", description="Filter by Camelot")
    mood: Optional[MoodCategory] = Field(None, description="Filter by mood")
    min_bpm: Optional[float] = Field(None, ge=60, le=200, description="Minimum BPM")
    max_bpm: Optional[float] = Field(None, ge=60, le=200, description="Maximum BPM")
    min_energy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum energy")
    max_energy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum energy")
    artist: Optional[str] = Field(None, description="Filter by artist")
    genre: Optional[str] = Field(None, description="Filter by genre")
    search: Optional[str] = Field(None, description="Search in title/artist/filename")
    sort_by: Optional[str] = Field(default="filename", description="Sort field")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")
    
    @validator('max_bpm')
    def validate_bmp_range(cls, v, values):
        if v and 'min_bpm' in values and values['min_bpm'] and v < values['min_bpm']:
            raise ValueError('max_bpm must be greater than min_bpm')
        return v
    
    @validator('max_energy')
    def validate_energy_range(cls, v, values):
        if v and 'min_energy' in values and values['min_energy'] and v < values['min_energy']:
            raise ValueError('max_energy must be greater than min_energy')
        return v