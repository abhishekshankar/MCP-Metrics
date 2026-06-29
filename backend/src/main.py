"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from api.routes import audit, auth_routes, blueprints, health, sites
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from observability.logging import logger
from plugins.loader import plugin_loader
from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    from config import get_settings

    settings = get_settings()

    # Warn if running in mock mode (not for production)
    if settings.mock_google_apis:
        logger.warning(
            "app.running_in_mock_mode",
            message=(
                "MOCK_GOOGLE_APIS is enabled. "
                "Google API calls will use fake data. NOT FOR PRODUCTION."
            ),
        )

    plugin_loader.load_all()
    start_scheduler()
    logger.info("app.started", mock_mode=settings.mock_google_apis)
    yield
    stop_scheduler()
    logger.info("app.stopped")


app = FastAPI(
    title="Analytics MCP",
    description="One-click GA4 + GTM analytics automation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Web UI dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router)
app.include_router(blueprints.router)
app.include_router(audit.router)
app.include_router(auth_routes.router)
