import { DiagConsoleLogger, DiagLogLevel, diag, metrics } from "@opentelemetry/api";
import { PrometheusExporter } from "@opentelemetry/exporter-prometheus";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { ExpressInstrumentation } from "@opentelemetry/instrumentation-express";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { AggregationType, MeterProvider } from "@opentelemetry/sdk-metrics";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.ERROR);

const DEFAULT_METRICS_PORT = 9464;
const IGNORED_TRACE_PATHS = new Set(["/-/ping", "/metrics"]);

function requestPath(url: string | undefined): string {
  if (url === undefined) {
    return "";
  }
  const queryIndex = url.indexOf("?");
  return queryIndex === -1 ? url : url.slice(0, queryIndex);
}

function metricsPort(): number {
  const value = process.env.VERDACCIO_METRICS_PORT;
  if (value === undefined) {
    return DEFAULT_METRICS_PORT;
  }
  const port = Number(value);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("VERDACCIO_METRICS_PORT must be an integer between 1 and 65535");
  }
  return port;
}

const resource = resourceFromAttributes({
  "service.name": process.env.OTEL_SERVICE_NAME || "verdaccio",
});
const meterProvider = new MeterProvider({
  resource,
  views: [
    {
      instrumentName: "verdaccio.http.request.duration",
      aggregation: {
        type: AggregationType.EXPLICIT_BUCKET_HISTOGRAM,
        options: {
          boundaries: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
          recordMinMax: true,
        },
      },
    },
  ],
  readers: [
    new PrometheusExporter({
      host: "0.0.0.0",
      port: metricsPort(),
      endpoint: "/metrics",
    }),
  ],
});
metrics.setGlobalMeterProvider(meterProvider);

let tracerProvider: NodeTracerProvider | undefined;
if (process.env.OTEL_EXPORTER_OTLP_ENDPOINT) {
  tracerProvider = new NodeTracerProvider({
    resource,
    spanProcessors: [new BatchSpanProcessor(new OTLPTraceExporter())],
  });
  tracerProvider.register();
  registerInstrumentations({
    tracerProvider,
    instrumentations: [
      new HttpInstrumentation({
        ignoreIncomingRequestHook: (request) =>
          IGNORED_TRACE_PATHS.has(requestPath(request.url)),
      }),
      new ExpressInstrumentation(),
    ],
  });
}

async function shutdown(): Promise<void> {
  const pending = [meterProvider.shutdown()];
  if (tracerProvider) {
    pending.push(tracerProvider.shutdown());
  }
  await Promise.all(pending);
}

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, () => {
    void shutdown().finally(() => {
      if (process.listenerCount(signal) === 0) {
        process.kill(process.pid, signal);
      }
    });
  });
}
