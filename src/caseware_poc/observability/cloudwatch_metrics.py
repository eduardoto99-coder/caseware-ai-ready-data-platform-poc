from __future__ import annotations

import json
from typing import Any


def emit_embedded_metric(namespace: str, dimensions: dict[str, str], metrics: dict[str, float]) -> str:
    """Return CloudWatch Embedded Metric Format payload for structured logging."""

    return json.dumps(
        {
            "_aws": {
                "Timestamp": 0,
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
