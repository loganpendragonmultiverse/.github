# Development

`tools/org_activity_monitor.py` is the organization-wide, manually invoked activity and watch-coverage tool. It uses the existing authenticated GitHub CLI session and never adds telemetry to individual projects or creates a Codex schedule.

Run `python -m unittest discover -s tests -v` before publishing monitor changes. Manually captured snapshots belong in the ignored `monitoring-data/` directory and must never contain credentials. The retained data is aggregate GitHub traffic plus already-public repository activity.

## New public repository gate

Every repository created in or transferred into `loganpendragonmultiverse` must complete this gate before its initial release is considered finished:

1. Add a project-specific `.github/CODEOWNERS` containing `* @LoganPendragonmulti`.
2. Enable issues, discussions, Actions, security features, squash-only merging, automatic branch cleanup, and protected `main` according to the open-source workspace standard.
3. Run `python tools/org_activity_monitor.py reconcile-watches` while authenticated as `LoganPendragonmulti`.
4. Run `python tools/org_activity_monitor.py audit-watches` and require complete coverage with no gaps or API failures.
5. Confirm the repository appears at [github.com/watching](https://github.com/watching), then use the ordinary [GitHub Notifications inbox](https://github.com/notifications) for future activity.

The watch subscription is account-specific and uses GitHub's all-activity repository subscription. It can therefore include issues and releases in addition to discussions and pull requests. Email delivery is controlled separately in the maintainer's GitHub notification settings.

## Release and Forge gate

Every later project release must reconcile the runtime/package version, changelog, README, repository description and topics when affected, protected pull request, merged commit, semantic tag, public release, attached artifacts, and the matching Forge catalog version, repository URL, description, and exact release URL. Render and deploy the Forge catalog only after the public GitHub release exists, then run the Forge local and live SEO/release verifiers.

Run `python tools/org_activity_monitor.py audit-watches` as part of the final release/deployment verification. If a new public repository is reported as a gap, run `reconcile-watches` and repeat the audit. Neither command is scheduled; they are explicit release and onboarding steps.
