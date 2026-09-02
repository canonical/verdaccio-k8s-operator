import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import test from "node:test";

import type { Meter, ObservableResult } from "@opentelemetry/api";
import type { Application, NextFunction, Request, Response } from "express";

import VerdaccioMetricsPlugin from "../metrics-plugin/index";

interface Measurement {
  value: number;
  attributes: Record<string, string | number>;
}

function setup(path: string, writableFinished = true): {
  counts: Measurement[];
  durations: Measurement[];
  build: Measurement[];
  close: () => void;
} {
  const counts: Measurement[] = [];
  const durations: Measurement[] = [];
  const build: Measurement[] = [];
  let observeBuild: ((result: ObservableResult) => void) | undefined;
  const meter = {
    createCounter: () => ({
      add: (value: number, attributes: Measurement["attributes"]) =>
        counts.push({ value, attributes }),
    }),
    createHistogram: () => ({
      record: (value: number, attributes: Measurement["attributes"]) =>
        durations.push({ value, attributes }),
    }),
    createObservableGauge: () => ({
      addCallback: (callback: (result: ObservableResult) => void) => {
        observeBuild = callback;
      },
    }),
  } as unknown as Meter;
  const plugin = new VerdaccioMetricsPlugin(
    { excludePaths: ["/-/ping"] },
    {},
    meter,
  );
  let middleware: ((request: Request, response: Response, next: NextFunction) => void) | undefined;
  const app = {
    use: (handler: typeof middleware) => {
      middleware = handler;
    },
  } as unknown as Application;
  plugin.register_middlewares(app, {}, {});

  const response = Object.assign(new EventEmitter(), {
    statusCode: 200,
    writableFinished,
  }) as unknown as Response;
  assert.ok(middleware);
  middleware({ method: "GET", path } as Request, response, () => undefined);
  assert.ok(observeBuild);
  observeBuild({
    observe: (value: number, attributes?: Record<string, string | number>) =>
      build.push({ value, attributes: attributes ?? {} }),
  } as ObservableResult);

  return {
    counts,
    durations,
    build,
    close: () => response.emit("close"),
  };
}

test("records bounded request metrics and build information", () => {
  const result = setup("/package");
  result.close();

  assert.deepEqual(result.counts, [
    {
      value: 1,
      attributes: {
        "http.request.method": "GET",
        "http.response.status_code": 200,
      },
    },
  ]);
  assert.equal(result.durations.length, 1);
  assert.ok(result.durations[0].value >= 0);
  assert.deepEqual(result.durations[0].attributes, result.counts[0].attributes);
  assert.deepEqual(result.build, [{ value: 1, attributes: { version: "6.10.1" } }]);
});

test("does not record the health endpoint", () => {
  const result = setup("/-/ping");
  result.close();

  assert.deepEqual(result.counts, []);
  assert.deepEqual(result.durations, []);
});


test("records an aborted request with a bounded status label", () => {
  const result = setup("/package", false);
  result.close();

  assert.equal(result.counts.length, 1);
  assert.equal(result.counts[0].attributes["http.response.status_code"], 499);
  assert.equal(result.durations.length, 1);
});
