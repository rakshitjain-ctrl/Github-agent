from fastapi import FastAPI

from config import settings
from logger import logger
from routes.github import router as github_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# Register GitHub routes
app.include_router(github_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Webhook secret configured: {bool(settings.GITHUB_WEBHOOK_SECRET)}")
    logger.info(f"AWS webhook URL configured: {bool(settings.AWS_DEVOPS_WEBHOOK_URL)}")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
