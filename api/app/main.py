from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chat, health, personas, plaid, simulator

app = FastAPI(title="AI Financial Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(personas.router)
app.include_router(plaid.router)
app.include_router(simulator.router)
app.include_router(chat.router)


@app.get("/")
def root() -> dict:
    return {"name": "AI Financial Planner API", "docs": "/docs"}
