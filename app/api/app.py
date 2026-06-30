from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config.settings import settings
from app.config.logging_config import logger


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Industry-level Air Quality Monitoring API"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["http://localhost:8050"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router, prefix="/api/v1", tags=["api"])
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting API server")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down API server")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        }
    
    return app


# Create global app instance
api_app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        api_app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.DEBUG
    )
