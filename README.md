# lucid-agent-cpu

`lucid-agent-cpu` is a test/reference component for `lucid-agent-core`. It runs inside agent-core and publishes CPU usage and CPU temperature telemetry every 5 seconds.

This component is intentionally minimal and exists to validate:
- the LUCID component contract
- remote component installation via MQTT
- periodic telemetry publishing

## Component Identity

- `component_id`: `cpu_monitor`
- `entrypoint`: `lucid_agent_cpu.component:CpuMonitorComponent`

## Behavior

- Reads CPU usage with `psutil.cpu_percent(interval=None)`
- Reads CPU temperature with `psutil.sensors_temperatures()` when available
- Publishes telemetry every 5 seconds to:
  - `lucid/agents/{agent_id}/status/cpu_monitor/metrics`
- If temperature is unavailable, publishes `temperature_c: null` and logs once

## MQTT Install (example)

Publish to:
- `lucid/agents/{agent_id}/cmd/core/install_component`

Payload:

```json
{
  "component_id": "cpu_monitor",
  "repo": "LucidLabPlatform/lucid-agent-cpu",
  "version": "0.1.0",
  "entrypoint": "lucid_agent_cpu.component:CpuMonitorComponent",
  "mode": "restart"
}
```

## Telemetry Topic and Payload

Topic:
- `lucid/agents/{agent_id}/status/cpu_monitor/metrics`

Payload example:

```json
{
  "cpu_percent": 23.4,
  "temperature_c": 54.1,
  "timestamp": "2026-02-06T16:45:00Z"
}
```

Notes:
- `temperature_c` can be `null`
- `timestamp` is UTC ISO-8601 with `Z` suffix

## Dependencies

- `psutil`

## Build and Install

Build:

```bash
python -m build
```

Install wheel:

```bash
pip install dist/lucid_agent_cpu-0.1.0-py3-none-any.whl
```
