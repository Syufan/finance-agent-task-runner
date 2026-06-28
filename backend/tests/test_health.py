from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.api.routes import health_check, router  # noqa: E402


class HealthCheckTestCase(unittest.TestCase):
    def test_health_handler_returns_ok(self) -> None:
        self.assertEqual(health_check(), {"status": "ok"})

    def test_health_route_is_registered(self) -> None:
        paths = {route.path for route in router.routes if hasattr(route, "path")}

        self.assertIn("/health", paths)
