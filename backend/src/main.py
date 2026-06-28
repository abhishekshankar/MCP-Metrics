"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import audit, auth_routes, blueprints, health, sites
from observability.logging import logger
from plugins.loader import plugin_loader
from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    plugin_loader.load_all()
    start_scheduler()
    logger.info("app.started")
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router)
app.include_router(blueprints.router)
app.include_router(audit.router)
app.include_router(auth_routes.router)
