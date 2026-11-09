import requests
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("http-handler")
def handle_request(request):
    # Propagate the trace context to downstream services
    headers = {}
    TraceContextTextMapPropagator().inject(headers)
    response = requests.post(
        "http://llm-inference/v1/chat/completions",
        headers=headers,
        json=request.json(),
    )
    return response.json()
