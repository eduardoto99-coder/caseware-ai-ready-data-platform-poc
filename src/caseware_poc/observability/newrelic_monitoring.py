from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NewRelicConfig:
    license_key_secret_name: str
    app_name: str
    distributed_tracing_enabled: bool = True


def render_newrelic_env(config: NewRelicConfig) -> dict[str, str]:
    return {
        "NEW_RELIC_APP_NAME": config.app_name,
        "NEW_RELIC_LICENSE_KEY_SECRET_NAME": config.license_key_secret_name,
        "NEW_RELIC_DISTRIBUTED_TRACING_ENABLED": str(
            config.distributed_tracing_enabled
        ).lower(),
    }
