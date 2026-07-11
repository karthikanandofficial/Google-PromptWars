import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.api.webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="MonsoonSaathi", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://monsoon-saathi.vercel.app",
        "https://*.vercel.app",
        "https://frontend-9f1qvbzne-karthikanandofficial-6992s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(api_router)


@app.get("/")
async def root():
    return {"service": "MonsoonSaathi", "status": "running"}
