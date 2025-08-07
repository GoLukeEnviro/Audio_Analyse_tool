"""Backend Configuration Settings"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
PRESETS_DIR = DATA_DIR / "presets"
MODELS_DIR = DATA_DIR / "models"
EXPORTS_DIR = PROJECT_ROOT / "exports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [DATA_DIR, CACHE_DIR, PRESETS_DIR, MODELS_DIR, EXPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings:
    """Backend configuration settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else DATA_DIR / "backend_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with sensible defaults"""
        default_config = {
            # Server settings
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "workers": 1,
                "reload": True,
                "log_level": "info",
                "cors_origins": ["*"],
                "cors_methods": ["*"],
                "cors_headers": ["*"]
            },
            
            # Music library settings
            "music_library": {
                "scan_path": str(Path.home() / "Music"), # Default scan path
                "default_paths": [
                    str(Path.home() / "Music"),
                    str(Path.home() / "Documents" / "My Music"),
                    "C:/Users/Public/Music" if os.name == 'nt' else "/home/Music"
                ],
                "auto_scan_on_startup": False,
                "watch_for_changes": True,
                "recursive_scan": True,
                "exclude_patterns": [
                    ".*",  # Hidden files
                    "*/.*",  # Hidden directories
                    "*/temp/*",
                    "*/cache/*",
                    "*/Trash/*",
                    "*/Papierkorb/*"
                ],
                "include_patterns": ["*"],  # All files (filtered by supported formats)
                "min_file_size_kb": 100,  # Skip very small files
                "max_depth": 10  # Maximum directory depth to scan
            },
            
            # Audio analysis settings
            "audio_analysis": {
                "cache_dir": str(CACHE_DIR),
                "enable_multiprocessing": True,
                "max_workers": min(os.cpu_count() or 1, 8), # Absicherung für os.cpu_count()
                "supported_formats": [
                    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", 
                    ".aiff", ".aif", ".au", ".wma", ".mp4", ".3gp", ".amr", 
                    ".opus", ".webm", ".mkv"
                ],
                "max_file_size_mb": 500,
                "sample_rate": 44100,
                "enable_essentia": True,
                "fallback_to_librosa": True,
                "analysis_timeout_seconds": 300,
                "batch_size": 10,  # Files to analyze in one batch
                "enable_progress_callbacks": True
            },
            
            # Playlist engine settings
            "playlist_engine": {
                "presets_dir": str(PRESETS_DIR),
                "default_preset": "DJ Set - Harmonic Flow",
                "max_playlist_duration_minutes": 300,
                "min_tracks_for_generation": 3,
                "enable_async_generation": True
            },
            
            # Mood classifier settings
            "mood_classifier": {
                "models_dir": str(MODELS_DIR),
                "confidence_threshold": 0.5,
                "enable_ml_classifier": False,  # Disabled by default (requires training data)
                "fallback_to_heuristic": True,
                "feature_weights": {
                    "energy": 1.0,
                    "valence": 1.0,
                    "bpm": 0.8,
                    "danceability": 0.9,
                    "loudness": 0.7,
                    "spectral_centroid": 0.6,
                    "mode": 0.5
                }
            },
            
            # Cache settings
            "cache": {
                "max_age_days": 30,
                "max_size_mb": 1000,
                "cleanup_on_startup": True,
                "auto_cleanup_interval_hours": 24,
                "memory_cache_size": 1000,  # Max tracks in memory cache
                "memory_cache_ttl": 3600,  # Memory cache TTL in seconds
                "enable_compression": False,  # Compress cache files
                "cache_version": "2.0"
            },
            
            # Export settings
            "export": {
                "output_dir": str(EXPORTS_DIR),
                "supported_formats": ["m3u", "json", "csv", "rekordbox"],
                "default_format": "m3u",
                "include_metadata": True
            },
            
            # Logging settings
            "logging": {
                "level": "INFO",
                "log_dir": str(LOGS_DIR),
                "log_file": "backend.log",
                "max_file_size_mb": 100,
                "backup_count": 5,
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            
            # Performance settings
            "performance": {
                "enable_request_timeout": True,
                "request_timeout_seconds": 300,
                "max_concurrent_analysis": 5,
                "enable_rate_limiting": False,
                "rate_limit_per_minute": 100
            },
            
            # Security settings
            "security": {
                "enable_cors": True,
                "max_request_size_mb": 100,
                "allowed_extensions": [
                    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
                    ".json", ".m3u", ".csv"
                ]
            },
            
            # Development settings
            "development": {
                "debug": False,
                "enable_hot_reload": False,
                "mock_slow_operations": False,
                "log_requests": True
            }
        }
        
        # Load custom configuration if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                    default_config = self._deep_merge(default_config, custom_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return default_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'server.port')"""
        keys = path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.config.get("server", {})
    
    def get_audio_analysis_config(self) -> Dict[str, Any]:
        """Get audio analysis configuration"""
        return self.config.get("audio_analysis", {})
    
    def get_playlist_engine_config(self) -> Dict[str, Any]:
        """Get playlist engine configuration"""
        return self.config.get("playlist_engine", {})
    
    def get_mood_classifier_config(self) -> Dict[str, Any]:
        """Get mood classifier configuration"""
        return self.config.get("mood_classifier", {})
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.config.get("development", {}).get("debug", False)
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.is_development()


# Global settings instance
settings = Settings()


# Environment variable overrides
def apply_env_overrides():
    """Apply environment variable overrides"""
    
    # Server overrides
    if os.getenv("HOST"):
        settings.set("server.host", os.getenv("HOST"))
    
    port_env = os.getenv("PORT")
    if port_env:
        try:
            settings.set("server.port", int(port_env))
        except ValueError:
            print(f"Warning: Invalid PORT environment variable: {port_env}. Using default.")
    
    debug_env = os.getenv("DEBUG")
    if debug_env:
        debug_mode = debug_env.lower() in ("true", "1", "yes")
        settings.set("development.debug", debug_mode)
        settings.set("server.reload", debug_mode)
    
    # Paths overrides
    if os.getenv("MUSIC_LIBRARY_PATH"):
        settings.set("music_library.scan_path", os.getenv("MUSIC_LIBRARY_PATH"))
    if os.getenv("CACHE_DIR"):
        settings.set("audio_analysis.cache_dir", os.getenv("CACHE_DIR"))
    if os.getenv("PRESETS_DIR"):
        settings.set("playlist_engine.presets_dir", os.getenv("PRESETS_DIR"))
    if os.getenv("EXPORT_DIR"):
        settings.set("export.output_dir", os.getenv("EXPORT_DIR"))


# Apply environment overrides
apply_env_overrides()


# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate server settings
    port = settings.get("server.port")
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append(f"Invalid server port: {port}")
    
    # Validate directories
    for path_key in ["music_library.scan_path", "audio_analysis.cache_dir", "playlist_engine.presets_dir", "export.output_dir"]:
        path_value = settings.get(path_key)
        if path_value and not Path(path_value).exists(): # Check if the directory itself exists
            try:
                Path(path_value).mkdir(parents=True, exist_ok=True) # Create the directory if it doesn't exist
            except Exception as e:
                errors.append(f"Cannot create directory for {path_key}: {e}")
    
    # Validate numeric settings
    for numeric_key in ["audio_analysis.max_workers", "cache.max_age_days", "cache.max_size_mb"]:
        value = settings.get(numeric_key)
        if not isinstance(value, (int, float)) or value <= 0:
            errors.append(f"Invalid numeric value for {numeric_key}: {value}")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))


# Validate configuration on import
validate_config()