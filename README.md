# Logan Pendragon Multiverse community standards

This repository contains the default contribution, support, conduct, and security guidance for open-source projects published by Logan Pendragon Multiverse.

Individual repositories may replace a default file when their language, build process, data handling, or security model needs more specific instructions. Project-specific guidance always takes precedence.

The goal is straightforward: make small, useful software that is pleasant to understand, safe to try, and realistic to maintain. Bug reports, thoughtful proposals, documentation improvements, tests, and focused pull requests are welcome.

## Organization monitoring

GitHub itself is the notification system for the public project fleet. The maintainer account watches every public organization repository, and each repository routes pull-request review through `.github/CODEOWNERS` to `@LoganPendragonmulti`. There is no Codex schedule or background monitoring task.

Use the following GitHub views:

- [Notifications](https://github.com/notifications) for watched discussions, pull requests, issues, releases, and other repository activity.
- [Organization pull requests](https://github.com/pulls?q=is%3Aopen+org%3Aloganpendragonmultiverse) for one cross-project pull-request queue.
- [Watching](https://github.com/watching) to inspect the account's watched repositories.
- Each repository's **Insights > Traffic** page for GitHub's rolling view and clone aggregates.

`python tools/org_activity_monitor.py audit-watches` is the required read-only coverage check. Run `python tools/org_activity_monitor.py reconcile-watches` immediately after creating or transferring a public repository; it subscribes the current authenticated GitHub account to any gaps and then verifies the complete public fleet.

The same tool can capture an aggregate, local-only usage snapshot or build a Markdown digest when someone deliberately runs it. These commands never add telemetry to released projects, identify anonymous visitors, or schedule themselves. See `DEVELOPMENT.md` for the onboarding, release, and data-handling contract.
