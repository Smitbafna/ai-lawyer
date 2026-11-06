from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, chat
from app.database.connection import engine, Base

app = FastAPI(title="AI Lawyer - Tenant Dispute Intake", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}