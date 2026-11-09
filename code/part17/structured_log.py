import logging
import json
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("inference-service")

def log_request(model: str, request_id: str, duration_ms: float, status: str):
    logger.info(
        "Inference request completed",
        extra={
            "model": model,
            "request_id": request_id,
            "duration_ms": duration_ms,
            "status": status,
        },
    )
