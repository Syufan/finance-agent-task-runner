from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.api.routes import create_router


class _DummyRunner:
    def run(self, user_request: str):
        raise AssertionError("run should not be called in health tests")


class _DummyTraceStore:
    def get(self, trace_id: str):
        raise AssertionError("get should not be called in health tests")


class HealthCheckTestCase(unittest.TestCase):
    def test_router_registers_health_route(self) -> None:
        router = create_router(_DummyRunner(), _DummyTraceStore())
        paths = {route.path for route in router.routes if hasattr(route, "path")}

        self.assertIn("/health", paths)

    def test_health_endpoint_returns_ok(self) -> None:
        router = create_router(_DummyRunner(), _DummyTraceStore())
        route = next(route for route in router.routes if getattr(route, "path", None) == "/health")

        self.assertEqual(route.endpoint(), {"status": "ok"})
