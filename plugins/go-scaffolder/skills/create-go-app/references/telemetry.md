# Telemetry posture (env-driven)

The scaffolder bootstrap reads OTLP exporter posture from environment variables — no code change is needed to retarget collectors or SaaS backends. Defaults preserve the local-collector / sidecar workflow.

| Env var | Default | Purpose |
|---|---|---|
| `OTEL_ENDPOINT` | `localhost:4317` | OTLP endpoint, `host:port` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | `grpc` or `http/protobuf` |
| `OTEL_EXPORTER_OTLP_INSECURE` | `true` | `true` for local sidecar; `false` requires TLS at the destination |
| `OTEL_EXPORTER_OTLP_HEADERS` | `""` | CSV of `k=v` pairs, e.g. `api-key=<license>,x-tenant=acme` |
| `OTEL_LOG_BRIDGE_ENABLED` | `false` | When `true`, slog records at `>= OTEL_LOG_MIN_SEVERITY` are also pushed to OTLP. Stdout JSON is unchanged. |
| `OTEL_LOG_MIN_SEVERITY` | `error` | Filter for the bridge: `error` · `warn` · `info` · `debug` |

## Common configurations

| Setup | Variables to set |
|---|---|
| Local OTel Collector / DataKit / NR Infra agent (default) | leave defaults; `OTEL_ENDPOINT` points at the local agent |
| New Relic direct (US) | `OTEL_ENDPOINT=otlp.nr-data.net:4317`, `OTEL_EXPORTER_OTLP_INSECURE=false`, `OTEL_EXPORTER_OTLP_HEADERS=api-key=$NEW_RELIC_LICENSE_KEY` |
| New Relic direct (EU) | as above, swap endpoint to `otlp.eu01.nr-data.net:4317` |
| Truewatch via DataKit | leave defaults; `OTEL_ENDPOINT=<datakit-host>:4317` |
| Errors-only OTel logs | `OTEL_LOG_BRIDGE_ENABLED=true` (default min severity is `error`) |
| Warn+ OTel logs | `OTEL_LOG_BRIDGE_ENABLED=true`, `OTEL_LOG_MIN_SEVERITY=warn` |

The bridge is additive — stdout JSON stays the source of truth for log aggregators. Only records at or above the configured severity travel over OTLP, so volume on the SaaS side stays predictable.
