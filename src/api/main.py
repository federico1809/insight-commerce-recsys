import logging
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from src.api.inference import (
    DatabaseConnectionError,
    FeatureContractError,
    RecommendationService,
    UserNotFoundError,
)
from src.api.schemas import (
    BatchItemResult,
    BatchRequest,
    BatchResponse,
    HealthResponse,
    RecommendationItem,
    RecommendResponse,
)

def _build_logger() -> logging.Logger:
    """Configura el logger de la API con salida exclusiva a stdout."""
    logger = logging.getLogger("api")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    return logger

logger  = _build_logger()
service = RecommendationService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Descarga artefactos desde S3 y abre el pool de conexiones a RDS al arrancar."""
    service.startup()
    logger.info(
        "startup OK | model=%s | n_features=%d",
        service.model_name,
        service.n_features,
    )
    yield
    logger.info("shutdown | cerrando pool de conexiones RDS")
    if service.engine:
        service.engine.dispose()

app = FastAPI(
    title="Insight Commerce Recsys API",
    version="1.0.0",
    description="API de recomendaciones Next Basket — AWS Fargate",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura cualquier excepción no controlada y devuelve HTTP 500."""
    logger.exception("error interno | path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor."},
    )

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check fortalecido: valida conectividad real a RDS con SELECT 1."""
    logger.info("GET /health")
    if service._artifacts is None:
        logger.error("health FAIL | artefactos no cargados")
        raise HTTPException(
            status_code=503,
            detail="Los artefactos del modelo no están disponibles.",
        )
    if service.engine is None:
        logger.error("health FAIL | engine RDS no inicializado")
        raise HTTPException(
            status_code=503,
            detail="El engine de base de datos no está inicializado.",
        )
    try:
        with service.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as err:
        logger.error("health FAIL | RDS no responde | %s", err)
        raise HTTPException(
            status_code=503,
            detail=(
                f"No se pudo conectar a PostgreSQL "
                f"(host={service._db_host}, sslmode={service._db_sslmode}). "
                "Verificar que el RDS está disponible y el Security Group permite "
                "tráfico desde el Security Group de la tarea Fargate."
            ),
        ) from err
    logger.info("health OK | model=%s | rds=%s", service.model_name, service._db_host)
    return HealthResponse(
        status="ok",
        model=service.model_name,
        n_features=service.n_features,
        artefactos=["model.pkl", "cluster_models.pkl", "model_log.json"],
    )

# IMPORTANTE: /recommend/batch debe definirse ANTES de /recommend/{user_id}.
@app.post("/recommend/batch", response_model=BatchResponse)
def recommend_batch(payload: BatchRequest) -> BatchResponse:
    """Genera recomendaciones para hasta 100 usuarios en una sola llamada."""
    logger.info("POST /recommend/batch | n_users=%d", len(payload.user_ids))
    results = []
    for user_id in payload.user_ids:
        try:
            recs, cold_start = service.recommend_user(user_id=user_id, top_k=10)
            results.append(
                BatchItemResult(
                    user_id=user_id,
                    recommendations=[RecommendationItem(**r) for r in recs],
                    cold_start=cold_start,
                )
            )
        except UserNotFoundError as err:
            logger.warning("user_not_found | user_id=%d | %s", user_id, err)
            results.append(BatchItemResult(user_id=user_id, error=str(err)))
        except FeatureContractError as err:
            raise HTTPException(status_code=400, detail=str(err)) from err
        except DatabaseConnectionError as err:
            raise HTTPException(status_code=503, detail=str(err)) from err
    return BatchResponse(results=results)

@app.post("/recommend/{user_id}", response_model=RecommendResponse)
def recommend_user(user_id: int) -> RecommendResponse:
    """Genera las top-10 recomendaciones de next-basket para un único usuario."""
    t0 = time.perf_counter()
    logger.info("POST /recommend/%d", user_id)
    try:
        recs, cold_start = service.recommend_user(user_id=user_id, top_k=10)
        recommendations = [RecommendationItem(**r) for r in recs]
    except UserNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except FeatureContractError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "recommend OK | user_id=%d | n_recs=%d | elapsed_ms=%.1f",
        user_id, len(recommendations), elapsed_ms,
    )
    return RecommendResponse(
        user_id=user_id,
        recommendations=recommendations,
        cold_start=cold_start,
    )