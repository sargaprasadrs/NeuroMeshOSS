import logging
from fastapi import FastAPI
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.config.settings import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    """Configures OpenTelemetry tracing, metrics, and FastAPI middlewares."""
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.warning("OTEL exporter endpoint not defined. Telemetry remains disabled.")
        return

    # Define Resource settings
    resource = Resource.create(attributes={"service.name": settings.OTEL_SERVICE_NAME})

    # 1. Tracing configuration
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    # 2. Metrics configuration
    metric_exporter = OTLPMetricExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # FastAPI Instrumentation hook
    FastAPIInstrumentor.instrument_app(app)
    logger.info("OpenTelemetry instrumentation completed successfully.")
