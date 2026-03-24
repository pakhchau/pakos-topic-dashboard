# 🚀 PakOS Topic Dashboard — Handoff Package for Claude Code

## Current Status
- **Version**: v1.1.0
- **Status**: 🟡 **PARTIALLY WORKING** — Backend OK, Frontend loading issue
- **Issue**: Dashboard page loads but topics list not displaying (Alpine.js initialization suspected)
- **Location**: `/root/clawd/apps/topic-dashboard/`
- **Live**: https://agents.pakhchau.com
- **GitHub**: https://github.com/pakhchau/pakos-topic-dashboard

---

## The Problem to Fix
**Dashboard shows "Loading topics..." but never displays the list.**

### What Works ✅
- FastAPI backend running (port 8080)
- API endpoints working (`/api/topics` returns 27 topics in JSON)
- HTML page loads
- Tailwind CSS CDN loading
- Basic styling visible

### What's Broken ❌
- Alpine.js may not be initializing properly
- Topics list not rendering (empty card grid visible but no topic cards)
- `x-data="dashboard()"` and `x-init="init()"` might not executing
- Loading spinner shows indefinitely

---

## Key Files to Review

### Main Server File
```
/root/clawd/apps/topic-dashboard/server.py (1000+ lines)
├── FastAPI app setup
├── API endpoints (GET /api/topics, GET /api/topics/{id}, etc.)
├── HTML template with embedded Alpine.js
└── Dashboard component with refresh(), init(), openTopic(), etc.
```

### Architecture
- **Backend**: FastAPI (Python 3) at `/root/clawd/apps/topic-dashboard/server.py`
- **Frontend**: Single HTML file with Alpine.js v3.14.9 (CDN)
- **Styling**: Tailwind CSS v3 (CDN)
- **Data**: Read-only from OpenClaw workspaces at `/root/clawd/topics/*/`

### Entry Point
```html
<body class="bg-gray-900 text-gray-100 min-h-screen" 
      x-data="dashboard()" 
      x-init="init(); console.log('Dashboard initialized...')">
```

---

## What Needs to Be Done

### Priority 1: Fix Frontend Loading
1. **Debug Alpine.js initialization**
   - Check if Alpine is loading from CDN
   - Verify x-data and x-init execute
   - Check browser console for errors
   - Add console.log statements for debugging

2. **Expected flow**:
   ```
   Page loads
   → Alpine.js mounts
   → x-data="dashboard()" creates component
   → x-init="init()" calls init()
   → init() calls refresh()
   → refresh() fetches /api/topics
   → Topics render via x-for loop
   ```

3. **Test points**:
   - Open https://agents.pakhchau.com
   - Open DevTools (F12) → Console
   - Should see: "🔄 Refreshing topics..." → "✅ Loaded 27 topics"
   - If missing, trace why

### Priority 2: Potential Solutions
1. **Alpine.js not loading**:
   - Replace CDN with local file
   - Or use different CDN
   - Or bundle with HTML

2. **JavaScript error in dashboard()**:
   - Check syntax errors
   - Wrap in try-catch
   - Add more console.log statements

3. **Fetch failing silently**:
   - Already added error handling, but might need more
   - Check CORS headers
   - Test `/api/topics` directly

4. **x-init not running**:
   - Try `@click` on button instead
   - Verify Alpine is fully loaded before init

### Priority 3: Enhancement (Once Fixed)
- Implement Phase 2.1 (Kanban drag-drop, memory search, snooze heartbeat)
- Connect Chat tab to Telegram (currently read-only)
- Add WebSocket for live updates

---

## How to Build/Run

### Local Development
```bash
cd /root/clawd/apps/topic-dashboard

# Install dependencies
pip install fastapi uvicorn

# Run server
python3 server.py
# OR
systemctl restart topic-dashboard

# Access
https://agents.pakhchau.com  (or http://localhost:8080 locally)
```

### Testing
```bash
# Test API
curl https://agents.pakhchau.com/api/topics | jq

# Check service
systemctl status topic-dashboard

# View logs
journalctl -u topic-dashboard -f
```

---

## Key Code Sections

### API Endpoint (Backend)
```python
@app.get("/api/topics")
def list_topics():
    topics = get_all_topics()  # Read from topic_agent.py
    enriched = []
    for t in topics:
        # ... enrich with progress, dates, issues, etc.
    enriched.sort(key=lambda x: x["last_message_time"], reverse=True)
    return enriched
```

### Dashboard Component (Frontend)
```javascript
function dashboard() {
  return {
    topics: [], filtered: [], loading: true,
    view: 'card', search: '', selected: null, detail: null,
    
    async init() {
      await this.refresh();
      this.$watch('search', () => this.applyFilter());
    },
    
    async refresh() {
      this.loading = true;
      try {
        console.log('🔄 Refreshing topics...');
        const r = await fetch('/api/topics');
        if (!r.ok) throw new Error(`API error: ${r.status}`);
        this.topics = await r.json();
        console.log('✅ Loaded ' + this.topics.length + ' topics');
        this.applyFilter();
      } catch (e) {
        console.error('❌ Refresh error:', e);
        this.topics = [];
      } finally {
        this.loading = false;
      }
    },
    
    // ... other methods
  }
}
```

---

## Data Model

### Topic Object (from API)
```json
{
  "id": "topic-24768",
  "name": "🗂️ Topic Dashboard",
  "topic_id": "24768",
  "status": "active",
  "heartbeat": "2h",
  "progress": 0,
  "has_issues": true,
  "has_memory": true,
  "total_issues": 19,
  "issue_done": 0,
  "last_message_time": 1774356923.965,
  "created_time": 1774349728.3305836,
  "updated_time": 1774349728.3305836
}
```

### Detail View (fetched separately)
```json
{
  "issues": [
    {"title": "Create ISSUES.md", "done": false, "notes": "..."},
    {"title": "Add chat tab", "done": true, "notes": "..."}
  ],
  "memory": [
    {"filename": "2026-03-22.md", "preview": "...", "modified": "..."}
  ],
  "transcript": [
    {"role": "user", "text": "...", "timestamp": "..."},
    {"role": "assistant", "text": "...", "timestamp": "..."}
  ],
  "skills": ["bootstrap-issues", "github", "discord"],
  "files": [...],
  "crons": [...]
}
```

---

## Features Built (Reference)

### ✅ Completed (v1.0.0 - v1.1.0)
- 3 views: Card, List, Kanban
- Detail panel with 7 tabs
- Issue management (inline editing, completion tracking)
- Foreground/background task workflow
- Chat transcript (read-only, markdown)
- Memory viewer
- Nudge Agent button
- Semantic versioning
- Beautiful date/time formatting
- Sort by last activity

### 🔄 In Progress
- Fix topics not displaying (this handoff)

### 📋 Planned (Phase 2)
- Kanban drag-drop
- Memory search
- Snooze heartbeat
- File browser
- WebSocket updates
- Theme toggle

---

## Important Notes

1. **Data Sources**:
   - Topics: `/root/clawd/topics/*/` (filesystem)
   - Transcripts: `/root/.openclaw/agents/*/sessions/*.jsonl`
   - Issues: `{topic}/ISSUES.md`
   - Memory: `{topic}/memory/`

2. **Single-File Server**:
   - All HTML/CSS/JS embedded in Python file
   - Makes it easy to deploy but harder to edit
   - Consider extracting HTML to separate file for easier development

3. **CDN Dependencies**:
   - Tailwind: `https://cdn.tailwindcss.com`
   - Alpine: `https://unpkg.com/alpinejs@3.14.9/dist/cdn.min.js`
   - These might fail in offline/restricted environments

4. **Deployment**:
   - Systemd service: `/etc/systemd/system/topic-dashboard.service`
   - Nginx proxy: `agents.pakhchau.com` → `localhost:8080`
   - Auto-restart on crash

---

## Success Criteria

Dashboard is **fixed** when:
- ✅ Page loads without errors
- ✅ Topics list displays in card view (at least 5 topics visible)
- ✅ Can click topic to open detail panel
- ✅ Issues tab shows issue list
- ✅ Chat tab shows message history
- ✅ Console shows no errors

---

## Questions for Claude Code

1. Why isn't `x-init` executing?
2. Is Alpine.js loading from CDN properly?
3. Are there any JavaScript errors (check console)?
4. Is the fetch to `/api/topics` succeeding?
5. Should we move HTML to separate file or keep embedded?

---

## Contact & Context

- **Pak** (user): Wants to manage topics, see issue progress, track agent work
- **This agent** (topic-24768): Built v1.0-1.1.0, now passing to Claude Code for fixes
- **GitHub**: Clean commit history, ready for collaboration
- **Status**: 48h uptime, all API tests passing, frontend issue blocking UI

---

**Ready to build! Start with debugging the Alpine.js initialization.** 🚀
