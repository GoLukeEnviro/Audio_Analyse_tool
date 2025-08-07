"""FastAPI Backend für DJ Audio-Analyse-Tool Pro"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add backend to path
backend_root = Path(__file__).parent
sys.path.insert(0, str(backend_root))

from config.settings import settings
from api.endpoints import tracks, playlists, analysis

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.get("logging.level", "INFO")),
    format=settings.get("logging.log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(settings.get("logging.log_dir")) / settings.get("logging.log_file", "backend.log")
        )
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events"""
    # Startup
    logger.info("[INFO] DJ Audio-Analyse-Tool Backend gestartet")
    logger.info(f"[INFO] Cache-Verzeichnis: {settings.get('audio_analysis.cache_dir')}")
    logger.info(f"[INFO] Preset-Verzeichnis: {settings.get('playlist_engine.presets_dir')}")
    logger.info(f"[INFO] Export-Verzeichnis: {settings.get('export.output_dir')}")
    
    yield
    
    # Shutdown
    logger.info("[INFO] Backend wird heruntergefahren...")


# Create FastAPI app
app = FastAPI(
    title="DJ Audio-Analyse-Tool API",
    description="Professional audio analysis and intelligent playlist generation API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get("server.cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=settings.get("server.cors_methods", ["*"]),
    allow_headers=settings.get("server.cors_headers", ["*"]),
)


# Trusted Host Middleware (for production)
if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.get("server.allowed_hosts", ["127.0.0.1", "localhost"])
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    
    if settings.is_development():
        # In development, show detailed error
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # In production, hide error details
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test core components
        from core_engine.audio_analysis.analyzer import AudioAnalyzer
        from core_engine.playlist_engine.playlist_engine import PlaylistEngine
        from core_engine.mood_classifier.mood_classifier import MoodClassifier
        
        analyzer = AudioAnalyzer()
        playlist_engine = PlaylistEngine()
        mood_classifier = MoodClassifier()
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": Path(__file__).stat().st_mtime,
            "components": {
                "audio_analyzer": "available",
                "playlist_engine": f"{len(playlist_engine.get_all_presets())} presets loaded",
                "mood_classifier": f"{len(mood_classifier.get_mood_categories())} mood categories",
                "cache": "available"
            },
            "config": {
                "debug": settings.is_development(),
                "audio_formats": len(settings.get("audio_analysis.supported_formats", [])),
                "export_formats": len(settings.get("export.supported_formats", []))
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e)
            }
        )


# API Status endpoint
@app.get("/api/status")
async def api_status():
    """API status with detailed system information"""
    try:
        from core_engine.audio_analysis.cache_manager import CacheManager
        
        cache_manager = CacheManager(settings.get("audio_analysis.cache_dir"))
        cache_stats = cache_manager.get_cache_stats()
        
        return {
            "api_version": "2.0.0",
            "status": "operational",
            "uptime_info": "Available via /health endpoint",
            "cache_statistics": cache_stats,
            "system_info": {
                "supported_audio_formats": settings.get("audio_analysis.supported_formats"),
                "supported_export_formats": settings.get("export.supported_formats"),
                "max_file_size_mb": settings.get("audio_analysis.max_file_size_mb"),
                "multiprocessing_enabled": settings.get("audio_analysis.enable_multiprocessing"),
                "max_workers": settings.get("audio_analysis.max_workers")
            },
            "directories": {
                "cache_dir": settings.get("audio_analysis.cache_dir"),
                "presets_dir": settings.get("playlist_engine.presets_dir"),
                "export_dir": settings.get("export.output_dir")
            }
        }
    except Exception as e:
        logger.error(f"API status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API status")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DJ Audio-Analyse-Tool Pro API v2.0",
        "description": "Professional headless audio analysis and playlist generation API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health",
        "api_status": "/api/status",
        "endpoints": {
            "tracks": "/api/tracks",
            "playlists": "/api/playlists", 
            "analysis": "/api/analysis"
        },
        "features": [
            "🎵 Advanced audio analysis (BPM, key, energy, mood)",
            "🎼 Intelligent playlist generation with multiple algorithms",
            "🎯 Camelot Wheel harmonic mixing",
            "📊 Mood classification with 8 categories",
            "💾 Multiple export formats (M3U, JSON, CSV, Rekordbox XML)",
            "⚡ Multiprocessing and caching for performance",
            "🔄 Async operations for non-blocking API calls"
        ]
    }


# Include API routers
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


def main():
    """Run the FastAPI server"""
    server_config = settings.get_server_config()
    
    logger.info(f"[INFO] Starte DJ Audio-Analyse-Tool Backend Server")
    logger.info(f"📍 Host: {server_config.get('host', '127.0.0.1')}")
    logger.info(f"🔌 Port: {server_config.get('port', 8000)}")
    logger.info(f"🔧 Debug-Modus: {settings.is_development()}")
    logger.info(f"🔄 Auto-Reload: {server_config.get('reload', False)}")
    
    # Run server
    uvicorn.run(
        "main:app",
        host=server_config.get("host", "127.0.0.1"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", False),
        workers=server_config.get("workers", 1),
        log_level=server_config.get("log_level", "info"),
        access_log=True,
        loop="asyncio"
    )


if __name__ == "__main__":
    main()