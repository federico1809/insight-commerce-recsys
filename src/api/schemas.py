from typing import Annotated, List, Optional
from pydantic import BaseModel, Field

class RecommendationItem(BaseModel):
    """Un producto recomendado con su probabilidad de recompra predicha."""
    product_key: int
    product_name: Optional[str] = None
    probability: float

class RecommendResponse(BaseModel):
    """Respuesta del endpoint POST /recommend/{user_id}.
    cold_start=True indica que se usó popularidad global o personal
    en lugar del modelo LightGBM completo.
    """
    user_id: int
    recommendations: List[RecommendationItem]
    cold_start: bool = False

class BatchRequest(BaseModel):
    """Cuerpo del request para POST /recommend/batch."""
    user_ids: Annotated[
        List[int],
        Field(min_length=1, max_length=100, description="Lista de user_id (1 a 100)"),
    ]

class BatchItemResult(BaseModel):
    """Resultado individual para un usuario dentro de una respuesta batch."""
    user_id: int
    recommendations: Optional[List[RecommendationItem]] = None
    error: Optional[str] = None
    cold_start: bool = False

class BatchResponse(BaseModel):
    """Respuesta del endpoint POST /recommend/batch."""
    results: List[BatchItemResult]

class HealthResponse(BaseModel):
    """Respuesta del endpoint GET /health."""
    status: str
    model: str
    n_features: int
    artefactos: List[str]