from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import init_db
from app.config import CORS_ORIGINS
from app.routes import auth, assessments, environment, decision

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="IrrigaSense API",
    description="Backend API for the IrrigaSense agricultural decision-support application.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(assessments.router)
app.include_router(environment.router)
app.include_router(decision.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the IrrigaSense API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
