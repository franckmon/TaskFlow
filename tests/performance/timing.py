import statistics
import time
from dataclasses import dataclass

from fastapi.testclient import TestClient

WARMUP_RUNS = 2
TIMING_RUNS = 7
MAX_MEDIAN_MS = 250
MAX_P95_MS = 300


@dataclass(frozen=True, slots=True)
class LatencyMeasurement:
    samples_ms: tuple[float, ...]
    median_ms: float
    p95_ms: float


def percentile_ms(samples_ms: list[float], percent: float) -> float:
    if not samples_ms:
        raise ValueError("At least one sample is required")
    if len(samples_ms) == 1:
        return samples_ms[0]

    ordered = sorted(samples_ms)
    rank = (percent / 100) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def get_tasks(
    client: TestClient,
    headers: dict[str, str],
) -> list[dict]:
    response = client.get("/tasks/", headers=headers, params={"limit": 100})
    assert response.status_code == 200
    return response.json()


def warm_up_get_tasks(
    client: TestClient,
    headers: dict[str, str],
    *,
    runs: int = WARMUP_RUNS,
) -> None:
    for _ in range(runs):
        get_tasks(client, headers)


def measure_get_tasks_latency(
    client: TestClient,
    headers: dict[str, str],
    *,
    runs: int = TIMING_RUNS,
) -> tuple[LatencyMeasurement, list[dict]]:
    """Measure only HTTP latency; caller must warm up and seed data beforehand."""
    samples_ms: list[float] = []
    payload: list[dict] = []

    for _ in range(runs):
        start = time.perf_counter()
        payload = get_tasks(client, headers)
        samples_ms.append((time.perf_counter() - start) * 1000)

    measurement = LatencyMeasurement(
        samples_ms=tuple(samples_ms),
        median_ms=statistics.median(samples_ms),
        p95_ms=percentile_ms(samples_ms, 95),
    )
    return measurement, payload


def format_latency_failure(
    measurement: LatencyMeasurement,
    *,
    median_limit_ms: float,
    p95_limit_ms: float,
) -> str:
    rounded = [round(sample, 1) for sample in measurement.samples_ms]
    return (
        f"samples_ms={rounded}, "
        f"median={measurement.median_ms:.1f}ms (limit {median_limit_ms}ms), "
        f"p95={measurement.p95_ms:.1f}ms (limit {p95_limit_ms}ms)"
    )
