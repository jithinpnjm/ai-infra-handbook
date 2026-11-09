# code/part17/structured_logging_demo.py
import logging
from pythonjsonlogger import jsonlogger
import sys

logger = logging.getLogger("demo")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "severity"},
)
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Structured log emitted", extra={"model": "churn-model", "step": 1000})
