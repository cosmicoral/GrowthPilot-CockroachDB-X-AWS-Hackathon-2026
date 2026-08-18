from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analytics import router as analytics_router
from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.company import router as company_router
from backend.api.growthgraph import router as growthgraph_router
from backend.api.health import router as health_router
from backend.api.memory import router as memory_router
from backend.api.research import router as research_router
from backend.api.traces import router as traces_router
from backend.auth_config import get_auth_settings
from backend.database.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to the database on startup (initializes the connection pool)
    await database.connect()
    yield
    # Disconnect from the database on shutdown (closes the pool)
    await database.disconnect()

# Initialize the core FastAPI application with the lifespan manager
app = FastAPI(title="GTM Agent API", lifespan=lifespan)

# Cookie-authenticated browser requests must use explicit origins. Wildcard
# CORS cannot be combined safely with credentials.
auth_settings = get_auth_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=auth_settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(memory_router)
app.include_router(growthgraph_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(research_router)
app.include_router(traces_router)
