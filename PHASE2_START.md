# Phase 2: Getting Started

**Ready to build the next features? Start here.**

---

## Quick Setup

```bash
cd /root/clawd/apps/topic-dashboard
git checkout -b feature/[feature-name]
```

## Pick a Feature

See `ISSUES.md` for all options. Here are the top 3 starters:

### 1. Kanban Drag-Drop (Recommended First)
**Why**: High impact, builds on existing Kanban view  
**Files to Edit**: `server.py` (backend), main dashboard HTML (frontend)  
**Tests to Add**: "Can drag topic between statuses"

**Steps**:
1. Open `server.py`, find the Kanban view rendering
2. Add `draggable` attribute to cards
3. Add `@app.put(/api/topics/{id}/status)` endpoint
4. Add drag event listeners in HTML
5. Test: Drag a card, check API call, verify status updated

**Time**: 2-4 hours

---

### 2. Memory Search (Recommended Second)
**Why**: Useful feature, builds search UI  
**Files to Edit**: `server.py` (add search endpoint), dashboard HTML (UI)  
**Tests to Add**: "Can search memory files"

**Steps**:
1. Add `@app.get(/api/topics/{id}/memory/search?q=keyword)` endpoint
2. Read memory/*.md files, search for keyword
3. Return matching lines with context
4. Add search input to Memory tab in dashboard
5. Display results with snippet preview

**Time**: 2-3 hours

---

### 3. Snooze Heartbeat (Recommended Third)
**Why**: User-facing feature, improves UX  
**Files to Edit**: `server.py` (add endpoint), dashboard HTML (context menu)  
**Tests to Add**: "Can snooze heartbeat"

**Steps**:
1. Add right-click context menu to cards
2. Show snooze options (1h, 4h, 24h)
3. Add `@app.post(/api/topics/{id}/snooze)` endpoint
4. Update heartbeat status in detail panel
5. Show visual indicator (badge, grayed out card)

**Time**: 2-3 hours

---

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/kanban-drag-drop
```

### 2. Edit Files
- Backend: Add API endpoints in `server.py`
- Frontend: Update HTML/JS in `server.py` or separate HTML files
- Tests: Add new test case to `/test-page`

### 3. Test Locally
```bash
# Option A: Run directly
python3 server.py
# Visit http://localhost:8080

# Option B: Use systemd
systemctl restart topic-dashboard
# Visit https://agents.pakhchau.com
```

### 4. Verify on Test Page
Open https://agents.pakhchau.com/test-page  
Click "Run All Tests" → ensure new test passes

### 5. Commit & Push
```bash
git add .
git commit -m "Feature: Implement kanban drag-drop"
git push origin feature/kanban-drag-drop
```

### 6. Deploy
```bash
systemctl restart topic-dashboard
# Verify on https://agents.pakhchau.com
```

---

## Code Patterns

### Adding an API Endpoint

```python
@app.put("/api/topics/{topic_id}/status")
async def update_topic_status(topic_id: str, status: str):
    """Update topic status (Idle, Active, Blocked, Done)"""
    topic_dir = Path("/root/clawd/topics") / topic_id
    if not topic_dir.exists():
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update logic here
    # Write to file, update state, etc.
    
    return {"success": True, "id": topic_id, "status": status}
```

### Adding a Test Case

```javascript
{
  name: '✓ Can drag topic between statuses',
  category: 'apiTests',
  fn: async () => {
    const res = await fetch(`/api/topics`);
    const topics = await res.json();
    if (topics.length === 0) throw new Error('No topics');
    
    // Test the drag/status endpoint
    const res2 = await fetch(`/api/topics/${topics[0].id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Active' })
    });
    if (res2.status !== 200) throw new Error('Status update failed');
  }
}
```

### Adding HTML Elements

Edit the dashboard HTML in `server.py` (around line 150-600):

```html
<!-- Add search input to Memory tab -->
<div class="tab-content" x-show="detail && activeTab === 'memory'">
  <input x-model="memorySearch" 
         placeholder="Search memory..."
         class="search-input">
  <div x-show="memoryResults">
    <template x-for="result in memoryResults">
      <div class="memory-result" x-text="result.snippet"></div>
    </template>
  </div>
</div>
```

---

## Debugging Tips

### Check Logs
```bash
systemctl status topic-dashboard
journalctl -u topic-dashboard -f  # Follow logs
```

### Test API Directly
```bash
curl http://localhost:8080/api/topics
curl http://localhost:8080/api/topics/topic-24768
```

### Browser Console
Press F12 → Console tab → check for errors  
Use `console.log()` in JavaScript to debug

### Reload Service
```bash
systemctl restart topic-dashboard
# or while developing:
python3 server.py  # in terminal
```

---

## Common Issues

### "Module not found"
Ensure Python FastAPI is installed:
```bash
pip install fastapi uvicorn
```

### "Port already in use"
```bash
lsof -i :8080
kill -9 <PID>
```

### Tests fail on `/test-page`
1. Check error message in test
2. Verify API endpoint exists
3. Verify response format matches expected
4. Check systemd logs for backend errors

### Changes not showing
1. Restart service: `systemctl restart topic-dashboard`
2. Clear browser cache: Ctrl+Shift+Delete
3. Check git diff: `git diff`

---

## Writing Clean Code

### Python (server.py)
- Add type hints: `async def get_topic_detail(topic_id: str) -> dict:`
- Use docstrings: `"""Get detailed data for a specific topic"""`
- Return consistent JSON: `{"success": bool, "data": Any}`

### JavaScript (HTML)
- Use Alpine.js conventions: `x-data`, `x-show`, `@click`
- Minimize dependencies (no jQuery, avoid heavy libs)
- Comment complex logic

### CSS
- Follow Tailwind conventions
- Dark theme: Use CSS variables from `--bg`, `--card`, etc.
- Mobile-first: Stack on small screens

---

## When You're Done

1. Push to GitHub: `git push origin feature/[name]`
2. Note the commit hash
3. Tell the team: "Feature ready for review"
4. Get code review before merging to master
5. Update CHANGELOG.md with new feature

---

## Questions?

- Check `/docs-page` for API reference
- See `/test-page` for working examples
- Read existing code in `server.py`
- Check ISSUES.md for implementation notes

---

**Happy coding! 🚀**

Pick a feature from ISSUES.md and submit your first PR!
