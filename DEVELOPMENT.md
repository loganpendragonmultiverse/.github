# Development

`tools/org_activity_monitor.py` is the organization-wide, read-only activity monitor. It uses the existing authenticated GitHub CLI session and never adds telemetry to individual projects.

Run `python -m unittest discover -s tests -v` before publishing monitor changes. Daily snapshots belong in the ignored `monitoring-data/` directory and must never contain credentials. The retained data is aggregate GitHub traffic plus already-public repository activity.
