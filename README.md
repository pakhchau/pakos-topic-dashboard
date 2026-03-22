# PakOS Topic Dashboard

**Visual management interface for all Telegram topics in PakOS ecosystem.**

**Live**: https://agents.pakhchau.com  
**GitHub**: https://github.com/pakhchau/pakos-topic-dashboard  
**Status**: 🚀 Phase 2 (Dashboard Views) — In Development

---

## Overview

A real-time dashboard for managing all PakOS topics with multiple views, live data integration, and issue tracking.

### Current Features (v1.0)
- ✅ Card view with topic metadata
- ✅ List view with sortable columns
- ✅ Kanban view by status
- ✅ Detailed topic inspection
- ✅ Issue editing (inline ISSUES.md)
- ✅ Documentation page (`/docs-page`)
- ✅ Health test runner (`/test-page`)
- ✅ Real-time API endpoints

### Planned Features (Phase 2)
- 🔄 Enhanced Kanban with drag-drop
- 🔄 Memory viewer with search
- 🔄 Transcript browser with filters
- 🔄 File explorer (directory tree)
- 🔄 Heartbeat/cron viewer
- 🔄 Live WebSocket updates

---

## Tech Stack

- **Backend**: FastAPI (Python 3)
- **Frontend**: HTML/CSS/JavaScript (Alpine.js for interactivity)
- **Data**: Direct filesystem + API integration
- **Deployment**: Systemd service on pakhchau.com
- **Version Control**: GitHub (this repo)

---

## Project Structure

```
/root/clawd/apps/topic-dashboard/
├── server.py              # FastAPI backend
├── docs.html              # Documentation page
├── test.html              # E2E test runner
├── CHANGELOG.md           # Version history
├── README.md              # This file
└── .gitignore             # Git exclusions
```

---

## Development Workflow

### 1. Make Changes
Edit `server.py`, `docs.html`, or `test.html` locally.

### 2. Test Locally
```bash
cd /root/clawd/apps/topic-dashboard
python3 server.py
# Visit http://localhost:8080
```

### 3. Commit to Git
```bash
git add .
git commit -m "Feature: [description]"
git push origin master
```

### 4. Deploy
```bash
systemctl restart topic-dashboard
# Service auto-reloads from /root/clawd/apps/topic-dashboard/
```

---

## API Endpoints

### Topics
- `GET /api/topics` — List all topics
- `GET /api/topics/{topic_id}` — Get topic details
- `PUT /api/topics/{topic_id}/issues` — Update issues

### Pages
- `GET /` — Main dashboard
- `GET /docs-page` — Documentation
- `GET /test-page` — Health tests

---

## Version Log

See `CHANGELOG.md` for detailed version history and release notes.

**Current Version**: 1.0.0 (2026-03-22)
- ✅ Initial release with docs + tests
- ✅ GitHub repository created
- ✅ Systemd service deployed

**Next**: Phase 2.1 — Kanban view improvements + memory browser

---

## Hand-Off Instructions

This dashboard is ready for other AI agents to extend or maintain:

1. **Clone the repo**: `git clone https://github.com/pakhchau/pakos-topic-dashboard.git`
2. **Read CHANGELOG.md**: Understand what's been built
3. **Check ISSUES.md**: See planned work
4. **Start with Phase 2.1**: Kanban view enhancements

### Code Style
- **Python**: FastAPI conventions, type hints
- **HTML/CSS**: Tailwind-friendly, dark theme
- **JS**: Alpine.js for reactivity, minimal dependencies
- **Commits**: Feature/fix + descriptive messages

### For Extending
1. Create a feature branch: `git checkout -b feature/kanban-drag`
2. Implement changes
3. Test via `systemctl restart topic-dashboard`
4. Push to GitHub: `git push origin feature/kanban-drag`
5. Submit findings via PR or message

---

## Dashboard Views

### Card View
Topics as grid cards with progress, status, and quick stats.

### List View  
Sortable table for scanning many topics at once.

### Kanban View
Topics organized by workflow status (Idle, Active, Blocked, Done).

### Detail Panel
Click topic → sidebar with tabs: Issues, Memory, Transcripts, Files, Crons, Heartbeats.

---

## Support

- **Documentation**: https://agents.pakhchau.com/docs-page
- **Tests**: https://agents.pakhchau.com/test-page
- **GitHub Issues**: https://github.com/pakhchau/pakos-topic-dashboard/issues
- **Service Logs**: `systemctl status topic-dashboard` or `journalctl -u topic-dashboard -f`

---

**Agent**: topic-24768  
**Last Updated**: 2026-03-22  
**Maintainer**: PakOS Team
