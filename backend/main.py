from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.database.database import database
from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.company import router as company_router
from backend.api.memory import router as memory_router
from backend.api.chat import router as chat_router
from backend.api.research import router as research_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to the database on startup (initializes the connection pool)
    await database.connect()
    yield
    # Disconnect from the database on shutdown (closes the pool)
    await database.disconnect()

# Initialize the core FastAPI application with the lifespan manager
app = FastAPI(title="GTM Agent API", lifespan=lifespan)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(memory_router)
app.include_router(chat_router)
app.include_router(research_router)

