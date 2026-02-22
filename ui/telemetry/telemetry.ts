import { addTelemetryEvent, type TelemetryEvent } from "../storage/db";

export function recordTelemetryEvent(event: TelemetryEvent) {
  // Fire-and-forget local-only telemetry.
  void addTelemetryEvent(event);
}
