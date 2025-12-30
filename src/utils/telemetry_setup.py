"""
Sets up the OpenTelemetry tracer for the application.

This module attempts to register Arize Phoenix as the OpenTelemetry backend.
If Phoenix is not available, it gracefully falls back to a simple console
exporter, ensuring that the pipeline's observability does not crash the app.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)

# Safe import for Phoenix
try:
    from phoenix.otel import register as phoenix_register
except ImportError:
    phoenix_register = None


def setup_telemetry():
    """
    Configures and returns a tracer for the application.
    
    Tries to initialize Phoenix as the primary trace provider. If it fails or
    is unavailable, it falls back to a standard console exporter.
    """
    provider = None
    
    if phoenix_register:
        try:
            # Explicitly configure the OpenTelemetry OTLP exporter environment variables
            # Phoenix UI runs on 6006 and exposes its OTLP/HTTP collector at /v1/traces
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:6006"
            os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
            
            # Register Phoenix as the OTel provider
            provider = phoenix_register(
                project_name="agent-evaluator",
                auto_instrument=False,
                batch=False
            )
            print("[Observability] Phoenix tracing is successfully registered.")
        except Exception as e:
            print(f"[Observability] Failed to initialize Phoenix tracing: {e}")
            provider = None

    # If Phoenix is not registered, set up the console exporter as a fallback
    if provider is None:
        print("[Observability] Phoenix not available. Falling back to ConsoleSpanExporter.")
        provider = TracerProvider()
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    # Set the global default tracer provider
    trace.set_tracer_provider(provider)

    # Return an instance of the tracer
    return trace.get_tracer("agent-evaluator")

# Initialize and get the tracer instance for use in other modules
tracer = setup_telemetry()