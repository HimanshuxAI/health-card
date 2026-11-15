from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from services.shared.db import Base, make_db

DB_PATH = os.getenv("SOS_DB", "sos.db")
engine, SessionLocal = make_db(DB_PATH)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="sos-service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from app.routes import router  # noqa: E402

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "sos"}
