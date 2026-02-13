"""
FastAPI Server

Main server application setup and configuration
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import router, initialize_services
from ..utils.config import Config
from ..utils.logger import setup_logger

# Setup logging
logger = setup_logger("Server", logging.INFO)

# Create FastAPI app
app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="Desktop YouTube downloader with smart deduplication"
)

# CORS middleware (for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only localhost in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount static files (frontend)
if Config.FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(Config.FRONTEND_DIR)), name="static")
    logger.info(f"Static files mounted from: {Config.FRONTEND_DIR}")


@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks

    - Initialize services
    - Check yt-dlp version
    """
    logger.info("=" * 60)
    logger.info(f"{Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info("=" * 60)

    # Initialize API services
    initialize_services()

    # Log startup info
    logger.info(f"Server running on http://{Config.HOST}:{Config.PORT}")
    logger.info(f"Downloads directory: {Config.DOWNLOADS_DIR}")

    # Check yt-dlp (will auto-update on first run)
    from ..services.updater import updater
    current_version = updater.get_current_version()
    if current_version:
        logger.info(f"yt-dlp version: {current_version}")
    else:
        logger.warning("yt-dlp not found - will update on first use")

    logger.info("Application started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down application...")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML"""
    index_path = Config.FRONTEND_DIR / "index.html"

    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {
            "app": Config.APP_NAME,
            "version": Config.APP_VERSION,
            "status": "Frontend not found",
            "api_docs": "/docs"
        }


def start_server(host: str = None, port: int = None, reload: bool = False):
    """
    Start the FastAPI server

    Args:
        host: Server host (default: from config)
        port: Server port (default: from config)
        reload: Enable auto-reload for development
    """
    host = host or Config.HOST
    port = port or Config.PORT

    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # Run server directly
    start_server(reload=True)
