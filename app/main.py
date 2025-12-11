"""
Main application for MUDS Matching System

FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
import sys

from app.database import init_db
from app.api import sync, matchings


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO")
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="90 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting MUDS Matching System...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    logger.info("MUDS Matching System started successfully")

    yield

    # Shutdown
    logger.info("Shutting down MUDS Matching System...")


# Create FastAPI application
app = FastAPI(
    title="MUDS Matching System API",
    description="学生マッチングシステムのバックエンドAPI",
    version="1.0.0",
    lifespan=lifespan
)


# CORS configuration
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # FastAPI
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(sync.router)
app.include_router(matchings.router)


@app.get("/")
async def root():
    """
    Root endpoint

    Returns:
        Welcome message
    """
    return {
        "message": "MUDS Matching System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "MUDS Matching System"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
