# Changelog

All notable changes to PakOS Topic Dashboard are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-22

### ✨ Initial Release

#### Added
- **Dashboard Views**
  - Card view: Topics as grid cards with progress, status, heartbeat icons
  - List view: Sortable table with columns (Topic, Status, Progress, Heartbeat, ID)
  - Kanban view: Topics organized by workflow status (Active, Paused, Dormant, Completed)
  - Detail panel: Right sidebar with rich topic information

- **Core Features**
  - Real-time topic listing from `/root/clawd/topics/`
  - Issue tracking and inline editing (ISSUES.md sync)
  - Memory viewer showing recent session notes
  - Chat transcript preview
  - Skills inventory per topic
  - File browser for topic workspace
  - Heartbeat/cron status display

- **API Endpoints**
  - `GET /api/topics` — List all topics with metadata
  - `GET /api/topics/{topic_id}` — Detailed topic information
  - `PUT /api/topics/{topic_id}/issues` — Update issues (saves to ISSUES.md)
  - `GET /` — Main dashboard HTML
  - `GET /docs-page` — Full documentation (6 sections)
  - `GET /test-page` — Health test runner (10+ e2e tests)

- **Documentation**
  - Comprehensive `/docs-page` with API reference, views guide, data sources, FAQ
  - End-to-end test suite on `/test-page` validating API, data, system health

- **Infrastructure**
  - GitHub repository: https://github.com/pakhchau/pakos-topic-dashboard
  - Systemd service: `topic-dashboard.service` on port 8080
  - Dark theme matching PakOS brand
  - Alpine.js for interactivity (minimal JS dependencies)

- **Developer Experience**
  - Version control ready for team collaboration
  - Clear API contracts and response formats
  - Hand-off documentation for other AI agents
  - Service-based deployment for easy updates

#### Technical Details
- **Backend**: FastAPI (Python 3)
- **Frontend**: Alpine.js + Tailwind CSS
- **Data Sources**: Filesystem (`/root/clawd/topics/*/`)
- **State Management**: Alpine.js reactivity
- **Styling**: Dark mode, responsive design
- **Performance**: Sub-second API responses, efficient DOM updates

---

## [Unreleased] — Phase 2 (In Development)

### 🔄 Phase 2.1: Kanban Enhancement + Memory Browser

#### Planned
- Drag-and-drop between Kanban columns
- Snooze heartbeat feature (1h/4h/24h options)
- Memory tab enhancements: search, date filters, full-text
- Transcript viewer with message search
- Live WebSocket updates (optional)
- Performance optimizations for many topics

#### Estimated Timeline
- Phase 2.1: 1 week (Kanban drag-drop, memory search)
- Phase 2.2: 1 week (File browser, transcript viewer)
- Phase 2.3: 1 week (Live updates, polish, deploy)

---

## Version Numbering

- **Major (1.x.x)**: New views, significant features, architecture changes
- **Minor (.1.x)**: New capabilities, enhancements to existing features
- **Patch (.x.1)**: Bug fixes, optimizations, documentation updates

---

## Release Checklist

Before each release:
- [ ] All tests pass (`/test-page` shows 100% coverage)
- [ ] Documentation updated (README.md, API docs, this file)
- [ ] Git history clean with descriptive commits
- [ ] GitHub issues tagged with milestone
- [ ] Service tested on production (pakhchau.com)
- [ ] Verified no breaking API changes
- [ ] Version tag created: `git tag v1.x.x`

---

## How to Contribute

1. **Pick an issue** from GitHub or Phase 2 roadmap
2. **Create branch**: `git checkout -b feature/[name]`
3. **Make changes** with clear commits
4. **Test locally** and via systemd restart
5. **Push to GitHub** and notify maintainers
6. **Code review** before merge to master

---

## Hand-Off Notes for AI Agents

- This dashboard is designed for team maintenance
- Changes should follow the version log
- All features must pass `/test-page` tests before deployment
- API contracts are stable; breaking changes require major version bump
- Documentation stays in sync with code (no stale docs)

---

**Maintainer**: PakOS Topic Dashboard Team  
**Last Updated**: 2026-03-22  
**Next Release Target**: v1.1.0 (Phase 2.1 complete)
