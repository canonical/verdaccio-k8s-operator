import { metrics, type Meter } from "@opentelemetry/api";
import type { Application, NextFunction, Request, Response } from "express";
import { version } from "verdaccio/package.json";

export interface MetricsConfig {
  excludePaths?: string[];
}

const DEFAULT_EXCLUDED_PATHS = ["/-/ping"];

export default class VerdaccioMetricsPlugin {
  private readonly excludedPaths: ReadonlySet<string>;
  private readonly requests;
  private readonly duration;

  constructor(
    config: MetricsConfig,
    _options: unknown,
    meter: Meter = metrics.getMeter("verdaccio", version),
  ) {
    this.excludedPaths = new Set(config.excludePaths ?? DEFAULT_EXCLUDED_PATHS);
    this.requests = meter.createCounter("verdaccio.http.requests", {
      description: "Number of completed Verdaccio HTTP requests",
      unit: "{request}",
    });
    this.duration = meter.createHistogram("verdaccio.http.request.duration", {
      description: "Duration of completed Verdaccio HTTP requests",
      unit: "s",
    });
    const build = meter.createObservableGauge("verdaccio.build.info", {
      description: "Verdaccio build information",
      unit: "1",
    });
    build.addCallback((result) => result.observe(1, { version }));
  }

  register_middlewares(app: Application, _auth: unknown, _storage: unknown): void {
    app.use((request: Request, response: Response, next: NextFunction): void => {
      if (this.excludedPaths.has(request.path)) {
        next();
        return;
      }

      const started = process.hrtime.bigint();
      response.once("close", () => {
        const attributes = {
          "http.request.method": request.method,
          "http.response.status_code": response.writableFinished ? response.statusCode : 499,
        };
        this.requests.add(1, attributes);
        this.duration.record(Number(process.hrtime.bigint() - started) / 1e9, attributes);
      });
      next();
    });
  }
}
