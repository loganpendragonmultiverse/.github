import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from org_activity_monitor import build_digest, new_activity, watch_audit


def sample(captured: str, downloads: int, stars: int, prs=None, discussions=None):
    return {
        "captured_at": captured,
        "repository_count": 1,
        "repositories": {
            "tool": {
                "views_14d": {"count": 10, "uniques": 4},
                "clones_14d": {"count": 3, "uniques": 2},
                "release_asset_downloads": downloads,
                "stars": stars,
            }
        },
        "pull_requests": prs or [],
        "discussions": discussions or [],
        "failures": [],
    }


class MonitorTests(unittest.TestCase):
    def test_watch_audit_reports_unsubscribed_and_ignored_repositories(self):
        repositories = [{"name": "watched"}, {"name": "missing"}, {"name": "muted"}]

        def status(repository):
            values = {
                "watched": {"subscribed": True, "ignored": False},
                "missing": {"subscribed": False, "ignored": False},
                "muted": {"subscribed": True, "ignored": True},
            }
            return repository["name"], values[repository["name"]]

        with mock.patch(
            "org_activity_monitor.repository_subscription", side_effect=status
        ):
            result = watch_audit(repositories)

        self.assertEqual(3, result["repository_count"])
        self.assertEqual(1, result["watched_count"])
        self.assertEqual(["missing", "muted"], result["gaps"])

    def test_new_activity_uses_stable_ids(self):
        old = sample("old", 1, 1, [{"id": 1}], [{"id": "a"}])
        current = sample(
            "new", 1, 1, [{"id": 1}, {"id": 2}], [{"id": "a"}, {"id": "b"}]
        )
        result = new_activity(current, old)
        self.assertEqual([2], [item["id"] for item in result["pull_requests"]])
        self.assertEqual(["b"], [item["id"] for item in result["discussions"]])

    def test_digest_reports_usage_deltas(self):
        history = [sample("old", 2, 1), sample("new", 5, 2)]
        report = build_digest(history)
        self.assertIn("| tool | 10 | 4 | 3 | +3 | +1 |", report)
        self.assertIn("New pull requests: **0**", report)
        self.assertIn("can include automation or CI", report)

    def test_digest_requires_snapshot(self):
        with self.assertRaisesRegex(ValueError, "no monitoring"):
            build_digest([])


if __name__ == "__main__":
    unittest.main()
