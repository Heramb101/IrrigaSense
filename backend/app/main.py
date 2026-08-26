from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.connection import init_db
from app.routes import assessments

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

app.include_router(assessments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the IrrigaSense API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
