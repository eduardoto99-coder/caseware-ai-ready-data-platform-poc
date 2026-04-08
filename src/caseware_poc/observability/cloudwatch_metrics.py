from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def emit_embedded_metric(namespace: str, dimensions: dict[str, str], metrics: dict[str, float]) -> str:
    """Return CloudWatch Embedded Metric Format payload for structured logging."""

    return json.dumps(
        {
            "_aws": {
                "Timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": namespace,
                        "Dimensions": [list(dimensions.keys())],
                        "Metrics": [{"Name": name, "Unit": "Count"} for name in metrics],
                    }
                ],
            },
            **dimensions,
            **metrics,
        },
        sort_keys=True,
    )
