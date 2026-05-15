from fastapi import FastAPI

from apps.api.investigation_api import router as investigation_router

app = FastAPI(title="Marlowe Agent", version="0.1.0")
app.include_router(investigation_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
