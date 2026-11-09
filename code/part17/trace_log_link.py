import logging
from opentelemetry import trace

logger = logging.getLogger("inference-service")
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("inference-request")
def handle_inference(prompt: str):
    # Add the trace id to the log line
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x")
    logger.info(
        "Inference request started",
        extra={"trace_id": trace_id, "prompt_length": len(prompt)},
    )
