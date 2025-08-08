# -*- coding: utf-8 -*-
import os
os.environ.setdefault('PYTHONIOENCODING','utf-8')

"""FastAPI Backend fuer DJ Audio-Analyse-Tool Pro"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import time
import asyncio
import signal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add backend to path
backend_root = Path(__file__).parent
sys.path.insert(0, str(backend_root))

from config.settings import settings
from api.endpoints import tracks, playlists, analysis, config

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
    app.state.last_heartbeat = time.time()
    asyncio.create_task(watchdog_task())
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


async def watchdog_task():
    # DEV: entspannter Watchdog, kein Exit
    timeout_s = int(os.getenv('WATCHDOG_TIMEOUT', '300'))
    interval_s = int(os.getenv('WATCHDOG_INTERVAL', '5'))
    logger.info(f"Watchdog-Task im Dev-Modus: {timeout_s}s timeout, {interval_s}s interval")
    while True:
        await asyncio.sleep(interval_s)
        # nur warnen, NICHT beenden
        logger.debug('Watchdog heartbeat check (dev mode); no shutdown')


# Simple health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}


# WebSocket Heartbeat Endpoint
@app.websocket("/ws/health")
async def websocket_health_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Frontend-Heartbeat-Verbindung hergestellt.")
    try:
        while True:
            # Warte auf Nachrichten (Pings) vom Frontend
            await websocket.receive_text()
            # Aktualisiere den Zeitstempel des letzten Kontakts
            app.state.last_heartbeat = time.time()
    except WebSocketDisconnect:
        logger.warning("Frontend-Heartbeat-Verbindung getrennt.")
    except Exception as e:
        logger.error(f"Fehler im Heartbeat-WebSocket: {e}")


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
            "[AUDIO] Advanced audio analysis (BPM, key, energy, mood)",
            "[PLAYLIST] Intelligent playlist generation with multiple algorithms",
            "[MIXING] Camelot Wheel harmonic mixing",
            "[MOOD] Mood classification with 8 categories",
            "[EXPORT] Multiple export formats (M3U, JSON, CSV, Rekordbox XML)",
            "[PERFORMANCE] Multiprocessing and caching for performance",
            "[ASYNC] Async operations for non-blocking API calls"
        ]
    }


# Include API routers
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


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