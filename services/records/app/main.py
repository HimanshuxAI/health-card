from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from services.shared.db import Base, make_db

DB_PATH = os.getenv("RECORDS_DB", "records.db")
engine, SessionLocal = make_db(DB_PATH)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="records-service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from app.routes_records import router as records_router  # noqa: E402
from app.routes_emergency import router as emergency_router  # noqa: E402

app.include_router(records_router)
app.include_router(emergency_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "records"}
