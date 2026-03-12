from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.test_routes import router as test_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive Diagnostic Engine",
        description="1D IRT-based adaptive diagnostic backend for GRE-style questions.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(test_router, prefix="/api")

    return app


app = create_app()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}

