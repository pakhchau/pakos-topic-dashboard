#!/usr/bin/env python3
"""
PakOS Topic Dashboard — Full-stack single-file server
Serves the dashboard UI + API on port 8080
"""
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="PakOS Topic Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TOPICS_DIR = Path("/root/clawd/topics")
AGENTS_DIR = Path("/root/.openclaw/agents")
OPENCLAW_CONFIG = Path("/root/.openclaw-dami/openclaw.json")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_all_topics() -> list[dict]:
    """Read topic list from topic_agent.py list output."""
    try:
        result = subprocess.run(
            ["python3", "/root/clawd/scripts/topic_agent.py", "list"],
            capture_output=True, text=True, timeout=15
        )
        topics = []
        lines = result.stdout.splitlines()
        
        # Skip header and separator lines
        for line in lines[2:]:
            if line.startswith('-'):  # Separator line
                continue
            if not line.strip():
                continue
            
            # Fixed-width columns: ID (20), Name (30), Heartbeat (12), Status
            parts = line.split()
            if len(parts) >= 4 and parts[0].startswith('topic-'):
                tid = parts[0]
                # Join all middle parts except last one (status), strip "Topic: " prefix
                status = parts[-1]
                # Everything between tid and status is name + heartbeat
                middle = ' '.join(parts[1:-1])
                
                # Find heartbeat (last non-name token before status)
                # Heartbeats are typically: off, Xh, Xm, just now, etc.
                # Split from the right to get heartbeat and name
                m = re.match(r'^(.+?)\s+(off|just\s+now|\d+[hm]|active|dormant)$', middle)
                if m:
                    name = m.group(1).replace("Topic: ", "").strip()
                    heartbeat = m.group(2)
                else:
                    # Fallback: heartbeat is last word
                    name_parts = middle.rsplit(None, 1)
                    if len(name_parts) == 2:
                        name = name_parts[0].replace("Topic: ", "").strip()
                        heartbeat = name_parts[1]
                    else:
                        name = middle.replace("Topic: ", "").strip()
                        heartbeat = "unknown"
                
                if name:  # Only include if name is non-empty
                    topics.append({
                        "id": tid,
                        "name": name,
                        "heartbeat": heartbeat,
                        "status": status,
                        "topic_id": tid.replace("topic-", ""),
                    })
        return topics
    except Exception as e:
        return []

def get_topic_dir(topic_id: str) -> Path | None:
    """Find workspace directory for a topic."""
    tid = topic_id.replace("topic-", "")
    for d in TOPICS_DIR.iterdir():
        if d.is_dir() and d.name.endswith(f"-{tid}"):
            return d
    return None

def get_topic_dates(topic_dir: Path) -> tuple[float, float]:
    """Get created and last updated timestamps for a topic (as Unix timestamps)."""
    try:
        # Creation time from folder stat
        created_time = topic_dir.stat().st_ctime
        
        # Last modified time (most recent file in the folder)
        files = list(topic_dir.rglob("*"))
        if files:
            latest_mtime = max(f.stat().st_mtime for f in files if f.is_file())
        else:
            latest_mtime = created_time
        
        return created_time, latest_mtime
    except Exception:
        return 0, 0

def read_issues(topic_dir: Path) -> list[dict]:
    issues_file = topic_dir / "ISSUES.md"
    if not issues_file.exists():
        return []
    issues = []
    current = None
    for line in issues_file.read_text().splitlines():
        # Match both "- [ ]" and "[ ]" formats
        m = re.match(r'^[-*]?\s*\[([ xX])\]\s+(.+)', line)
        if m:
            done = m.group(1).lower() == 'x'
            title = m.group(2).strip()
            current = {"title": title, "done": done, "notes": ""}
            issues.append(current)
        elif current and line.startswith("  "):
            current["notes"] += line.strip() + " "
    return issues

def read_memory(topic_dir: Path) -> list[dict]:
    mem_dir = topic_dir / "memory"
    if not mem_dir.exists():
        return []
    files = []
    for f in sorted(mem_dir.glob("*.md"), reverse=True)[:10]:
        files.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            "preview": f.read_text()[:300].strip()
        })
    return files

def read_skills(topic_dir: Path) -> list[str]:
    skills_file = topic_dir / "SKILLS.md"
    if not skills_file.exists():
        return []
    skills = []
    for line in skills_file.read_text().splitlines():
        m = re.match(r'^[-*]\s+\*?\*?([^*\n]+)', line)
        if m:
            skills.append(m.group(1).strip())
    return skills

def read_transcript(topic_id: str, limit: int = 50) -> list[dict]:
    """Read chat transcript from .jsonl session file."""
    tid = topic_id.replace("topic-", "")
    agent_id = f"topic-{tid}"
    agent_dir = AGENTS_DIR / agent_id / "sessions"
    if not agent_dir.exists():
        return []
    # Get most recent session
    sessions = sorted(agent_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not sessions:
        return []
    messages = []
    for line in sessions[0].read_text().splitlines()[-200:]:
        try:
            obj = json.loads(line)
            # Handle both message object format and flat format
            if obj.get("type") == "message" and "message" in obj:
                msg = obj["message"]
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = obj.get("role", "")
                content = obj.get("content", "")
            
            if role in ("user", "assistant"):
                if isinstance(content, list):
                    text = " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
                else:
                    text = str(content)
                if text.strip():
                    messages.append({"role": role, "text": text[:500]})
        except Exception:
            pass
    return messages[-limit:]

def read_files(topic_dir: Path) -> list[dict]:
    files = []
    for f in sorted(topic_dir.rglob("*"))[:50]:
        if f.is_file() and not any(p.startswith(".") for p in f.parts):
            rel = str(f.relative_to(topic_dir))
            files.append({
                "path": rel,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    return files

def compute_progress(topic_dir: Path) -> int:
    """Estimate % done from issues."""
    issues = read_issues(topic_dir)
    if not issues:
        return 0
    done = sum(1 for i in issues if i["done"])
    return int(done / len(issues) * 100)

def get_crons(topic_id: str) -> list[dict]:
    """Extract cron/heartbeat config for this agent."""
    tid = topic_id.replace("topic-", "")
    agent_id = f"topic-{tid}"
    try:
        cfg = json.loads(OPENCLAW_CONFIG.read_text())
        crons = cfg.get("crons", [])
        result = []
        for c in crons:
            if agent_id in str(c.get("target", "")):
                result.append(c)
        return result
    except Exception:
        return []

# ─── API ──────────────────────────────────────────────────────────────────────

def get_last_message_time(topic_id: str) -> float:
    """Get timestamp of last message in transcript, for sorting."""
    tid = topic_id.replace("topic-", "")
    agent_id = f"topic-{tid}"
    try:
        agent_dir = AGENTS_DIR / agent_id / "sessions"
        if not agent_dir.exists():
            return 0
        sessions = sorted(agent_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not sessions:
            return 0
        for line in reversed(sessions[0].read_text().splitlines()):
            try:
                obj = json.loads(line)
                if obj.get("type") == "message":
                    ts = obj.get("timestamp", "")
                    if ts:
                        # Parse ISO format timestamp
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        return dt.timestamp()
            except Exception:
                pass
        return 0
    except Exception:
        return 0

@app.get("/api/topics")
def list_topics():
    topics = get_all_topics()
    enriched = []
    for t in topics:
        d = get_topic_dir(t["id"])
        # Skip topics without workspace folders or valid names
        if not d or not t["name"].strip():
            continue
        t["progress"] = compute_progress(d) if d else 0
        t["has_issues"] = bool(d and (d / "ISSUES.md").exists())
        t["has_memory"] = bool(d and (d / "memory").exists())
        t["last_message_time"] = get_last_message_time(t["id"])
        created_time, updated_time = get_topic_dates(d)
        t["created_time"] = created_time  # Unix timestamp
        t["updated_time"] = updated_time  # Unix timestamp
        
        # Count issue completion ratio
        if t["has_issues"]:
            issues = read_issues(d)
            t["total_issues"] = len(issues)
            t["issue_done"] = sum(1 for i in issues if i.get("done"))
        else:
            t["total_issues"] = 0
            t["issue_done"] = 0
        
        enriched.append(t)
    # Sort by last message time (descending = most recent first)
    enriched.sort(key=lambda x: x["last_message_time"], reverse=True)
    return enriched

@app.get("/api/topics/{topic_id}")
def get_topic(topic_id: str):
    topics = get_all_topics()
    meta = next((t for t in topics if t["id"] == topic_id), None)
    if not meta:
        raise HTTPException(404, "Topic not found")
    d = get_topic_dir(topic_id)
    return {
        **meta,
        "progress": compute_progress(d) if d else 0,
        "issues": read_issues(d) if d else [],
        "memory": read_memory(d) if d else [],
        "skills": read_skills(d) if d else [],
        "files": read_files(d) if d else [],
        "transcript": read_transcript(topic_id),
        "crons": get_crons(topic_id),
    }

@app.put("/api/topics/{topic_id}/issues")
def update_issues(topic_id: str, payload: dict):
    d = get_topic_dir(topic_id)
    if not d:
        raise HTTPException(404, "Topic dir not found")
    issues = payload.get("issues", [])
    lines = ["# Issues\n"]
    for i in issues:
        check = "x" if i.get("done") else " "
        lines.append(f"- [{check}] {i['title']}")
        if i.get("notes"):
            lines.append(f"  {i['notes']}")
    (d / "ISSUES.md").write_text("\n".join(lines))
    return {"ok": True}

@app.get("/")
def serve_ui():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/changelog")
def serve_changelog():
    try:
        changelog_file = Path(__file__).parent / "changelog.html"
        if changelog_file.exists():
            return HTMLResponse(changelog_file.read_text())
        return HTMLResponse("<h1>Changelog not found</h1>")
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading changelog: {e}</h1>")

# ─── Frontend HTML ─────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PakOS Topic Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
<style>
  [x-cloak] { display: none !important; }
  .scrollbar-thin::-webkit-scrollbar { width: 4px; }
  .scrollbar-thin::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }
  .transcript-user { background: #eff6ff; border-left: 3px solid #3b82f6; }
  .transcript-assistant { background: #f0fdf4; border-left: 3px solid #22c55e; }
  .progress-bar { transition: width 0.4s ease; }
  .card-hover { transition: all 0.2s ease; }
  .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }
</style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen" x-data="dashboard()" x-init="init()">

<!-- Header -->
<div class="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
  <div class="max-w-screen-xl mx-auto px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <span class="text-2xl">🗂️</span>
      <div>
        <h1 class="text-lg font-bold text-white">PakOS Topics</h1>
        <p class="text-xs text-gray-400" x-text="topics.length + ' topics'"></p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <!-- Search -->
      <input x-model="search" type="text" placeholder="Search topics..."
        class="px-3 py-1.5 text-sm bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48">
      <!-- View switcher -->
      <div class="flex bg-gray-700 rounded-lg p-1 gap-1">
        <button @click="view='card'" :class="view==='card' ? 'bg-gray-600 shadow text-blue-400' : 'text-gray-400'"
          class="px-3 py-1 rounded text-sm font-medium">Cards</button>
        <button @click="view='list'" :class="view==='list' ? 'bg-gray-600 shadow text-blue-400' : 'text-gray-400'"
          class="px-3 py-1 rounded text-sm font-medium">List</button>
        <button @click="view='kanban'" :class="view==='kanban' ? 'bg-gray-600 shadow text-blue-400' : 'text-gray-400'"
          class="px-3 py-1 rounded text-sm font-medium">Kanban</button>
      </div>
      <button @click="refresh()" class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        ↻ Refresh
      </button>
    </div>
  </div>
</div>

<!-- Loading -->
<div x-show="loading" class="flex items-center justify-center py-20">
  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
  <p class="ml-4 text-gray-400">Loading topics...</p>
</div>

<!-- Empty State -->
<div x-show="!loading && filtered.length === 0" class="flex flex-col items-center justify-center py-20">
  <p class="text-gray-500 text-lg">No topics found</p>
  <p class="text-gray-600 text-sm mt-2">Try adjusting your search</p>
</div>

<!-- Card View -->
<div x-show="!loading && view==='card'" class="max-w-screen-xl mx-auto px-6 py-6">
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <template x-for="t in filtered" :key="t.id">
      <div @click="openTopic(t)" class="card-hover bg-gray-800 rounded-xl border border-gray-700 p-5 cursor-pointer hover:border-gray-600">
        <div class="flex items-start justify-between mb-3">
          <h3 class="font-semibold text-white text-sm leading-tight" x-text="t.name"></h3>
          <span :class="t.status === 'active' ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-400'"
            class="text-xs px-2 py-0.5 rounded-full ml-2 shrink-0" x-text="t.status"></span>
        </div>
        <!-- Progress + Issues Ratio -->
        <div class="mb-3">
          <div class="flex justify-between text-xs text-gray-400 mb-1">
            <span>Issues</span>
            <span class="font-semibold text-blue-400" x-show="t.has_issues">
              <span x-text="(t.issue_done || 0) + '/' + (t.total_issues || 0)"></span>
            </span>
            <span class="text-gray-500" x-show="!t.has_issues">—</span>
          </div>
          <div class="bg-gray-700 rounded-full h-1.5">
            <div class="progress-bar bg-green-500 h-1.5 rounded-full" :style="'width:' + t.progress + '%'"></div>
          </div>
        </div>
        <!-- Meta -->
        <div class="flex items-center gap-3 text-xs text-gray-500">
          <span x-show="t.has_issues">📋 Issues</span>
          <span x-show="t.has_memory">🧠 Memory</span>
          <span class="ml-auto" :title="new Date(t.last_message_time * 1000).toLocaleString()" x-text="formatLastActivity(t.last_message_time)"></span>
        </div>
        <div class="mt-2 text-xs text-gray-400" x-text="'#' + t.topic_id"></div>
      </div>
    </template>
  </div>
</div>

<!-- List View -->
<div x-show="!loading && view==='list'" class="max-w-screen-xl mx-auto px-6 py-6">
  <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
    <table class="w-full">
      <thead class="bg-gray-900 text-xs text-gray-400 uppercase">
        <tr>
          <th class="px-4 py-3 text-left">Topic</th>
          <th class="px-4 py-3 text-left">Status</th>
          <th class="px-4 py-3 text-left">Progress</th>
          <th class="px-4 py-3 text-left">Created</th>
          <th class="px-4 py-3 text-left">Updated</th>
          <th class="px-4 py-3 text-left">Last Activity</th>
          <th class="px-4 py-3 text-left">Heartbeat</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <template x-for="t in filtered" :key="t.id">
          <tr @click="openTopic(t)" class="hover:bg-gray-700 cursor-pointer">
            <td class="px-4 py-3 text-sm font-medium text-white" x-text="t.name"></td>
            <td class="px-4 py-3">
              <span :class="t.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                class="text-xs px-2 py-0.5 rounded-full" x-text="t.status"></span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="bg-gray-100 rounded-full h-1.5 w-20">
                  <div class="progress-bar bg-blue-500 h-1.5 rounded-full" :style="'width:' + t.progress + '%'"></div>
                </div>
                <span class="text-xs text-gray-500" x-text="t.progress + '%'"></span>
              </div>
            </td>
            <td class="px-4 py-3 text-xs text-gray-400" :title="new Date(t.created_time * 1000).toISOString()" x-text="formatDatetime(t.created_time)"></td>
            <td class="px-4 py-3 text-xs text-gray-400" :title="new Date(t.updated_time * 1000).toISOString()" x-text="formatDatetime(t.updated_time)"></td>
            <td class="px-4 py-3 text-xs text-gray-400" :title="new Date(t.last_message_time * 1000).toLocaleString()" x-text="formatLastActivity(t.last_message_time)"></td>
            <td class="px-4 py-3 text-xs text-gray-500" x-text="t.heartbeat"></td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</div>

<!-- Kanban View -->
<div x-show="!loading && view==='kanban'" class="max-w-screen-xl mx-auto px-6 py-6">
  <div class="flex gap-4 overflow-x-auto pb-4">
    <template x-for="col in ['active','dormant']" :key="col">
      <div class="shrink-0 w-72">
        <div class="flex items-center gap-2 mb-3">
          <div :class="col === 'active' ? 'bg-green-500' : 'bg-gray-400'" class="w-2 h-2 rounded-full"></div>
          <h3 class="text-sm font-semibold text-gray-700 capitalize" x-text="col"></h3>
          <span class="text-xs text-gray-400 ml-auto" x-text="filtered.filter(t => t.status === col).length"></span>
        </div>
        <div class="space-y-2">
          <template x-for="t in filtered.filter(t => t.status === col)" :key="t.id">
            <div @click="openTopic(t)" class="card-hover bg-gray-800 rounded-lg border border-gray-700 p-3 cursor-pointer">
              <p class="text-sm font-medium text-white mb-2" x-text="t.name"></p>
              <div class="bg-gray-100 rounded-full h-1 mb-2">
                <div class="progress-bar bg-blue-500 h-1 rounded-full" :style="'width:' + t.progress + '%'"></div>
              </div>
              <div class="flex justify-between text-xs text-gray-400">
                <span x-text="'#' + t.topic_id"></span>
                <span x-text="t.progress + '%'"></span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</div>

<!-- Topic Detail Drawer -->
<div x-show="selected" x-cloak class="fixed inset-0 z-50 flex" @keydown.escape.window="selected = null">
  <!-- Backdrop (click to close) -->
  <div class="flex-1 bg-black bg-opacity-50 cursor-pointer hover:bg-opacity-60 transition-colors" @click="selected = null"></div>
  <!-- Drawer -->
  <div class="w-full max-w-2xl bg-gray-800 h-full overflow-y-auto shadow-2xl scrollbar-thin" x-show="selected">
    <template x-if="selected">
      <div>
        <!-- Drawer header -->
        <div class="sticky top-0 bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 class="text-lg font-bold text-white" x-text="selected.name"></h2>
            <p class="text-xs text-gray-500" x-text="'#' + selected.topic_id + ' · ' + selected.status + ' · ♥ ' + selected.heartbeat"></p>
          </div>
          <button @click="selected = null" class="text-gray-400 hover:text-white text-3xl leading-none font-light">✕</button>
        </div>

        <!-- Tabs -->
        <div class="border-b border-gray-700 px-6">
          <div class="flex gap-1">
            <template x-for="tab in ['overview','issues','memory','chat','skills','files','crons']" :key="tab">
              <button @click="activeTab = tab"
                :class="activeTab === tab ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'"
                class="px-3 py-2.5 text-sm font-medium capitalize">
                <span x-text="tabIcon(tab) + ' ' + tab"></span>
              </button>
            </template>
          </div>
        </div>

        <!-- Tab: Overview -->
        <div x-show="activeTab === 'overview'" class="p-6">
          <!-- Key Stats -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-400 mb-4 uppercase">Key Stats</h3>
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-gray-700 rounded-lg p-4">
                <p class="text-3xl font-bold text-blue-400" x-text="detail?.progress + '%'"></p>
                <p class="text-xs text-gray-500 mt-1">Progress</p>
                <div class="bg-gray-600 rounded-full h-2 mt-2">
                  <div class="bg-blue-500 h-2 rounded-full" :style="'width:' + (detail?.progress || 0) + '%'"></div>
                </div>
              </div>
              <div class="bg-gray-700 rounded-lg p-4">
                <p class="text-3xl font-bold text-green-400" x-text="(detail?.issues || []).filter(i => i.done).length + '/' + (detail?.issues?.length || 0)"></p>
                <p class="text-xs text-gray-500 mt-1">Issues Done</p>
              </div>
            </div>
          </div>

          <!-- Metadata -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-400 mb-3 uppercase">Timeline</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between items-start">
                <span class="text-gray-400">Created:</span>
                <span class="text-right text-gray-200" :title="new Date(selected.created_time * 1000).toISOString()" x-text="formatDatetime(selected.created_time)"></span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-gray-400">Updated:</span>
                <span class="text-right text-gray-200" :title="new Date(selected.updated_time * 1000).toISOString()" x-text="formatDatetime(selected.updated_time)"></span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-gray-400">Last Activity:</span>
                <span class="text-right text-gray-200" :title="new Date(selected.last_message_time * 1000).toISOString()" x-text="formatLastActivity(selected.last_message_time)"></span>
              </div>
            </div>
          </div>

          <!-- Content Stats -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-400 mb-3 uppercase">Content</h3>
            <div class="grid grid-cols-3 gap-2">
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'issues'">
                <p class="text-2xl font-bold text-blue-400" x-text="detail?.issues?.length || 0"></p>
                <p class="text-xs text-gray-500">Issues</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'memory'">
                <p class="text-2xl font-bold text-purple-400" x-text="detail?.memory?.length || 0"></p>
                <p class="text-xs text-gray-500">Memory</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'chat'">
                <p class="text-2xl font-bold text-green-400" x-text="detail?.transcript?.length || 0"></p>
                <p class="text-xs text-gray-500">Messages</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'skills'">
                <p class="text-2xl font-bold text-yellow-400" x-text="detail?.skills?.length || 0"></p>
                <p class="text-xs text-gray-500">Skills</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'files'">
                <p class="text-2xl font-bold text-orange-400" x-text="detail?.files?.length || 0"></p>
                <p class="text-xs text-gray-500">Files</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3 text-center hover:bg-gray-600 transition cursor-pointer" @click="activeTab = 'crons'">
                <p class="text-2xl font-bold text-pink-400" x-text="detail?.crons?.length || 0"></p>
                <p class="text-xs text-gray-500">Crons</p>
              </div>
            </div>
          </div>

          <!-- Status Badges -->
          <div class="mb-4">
            <h3 class="text-sm font-semibold text-gray-400 mb-3 uppercase">Status</h3>
            <div class="flex flex-wrap gap-2">
              <span class="px-3 py-1 bg-blue-900 text-blue-200 text-xs rounded-full">Status: <span x-text="selected.status"></span></span>
              <span class="px-3 py-1 bg-purple-900 text-purple-200 text-xs rounded-full">Heartbeat: <span x-text="selected.heartbeat"></span></span>
              <span x-show="selected.has_issues" class="px-3 py-1 bg-green-900 text-green-200 text-xs rounded-full">📋 Has Issues</span>
              <span x-show="selected.has_memory" class="px-3 py-1 bg-indigo-900 text-indigo-200 text-xs rounded-full">🧠 Has Memory</span>
            </div>
          </div>

          <!-- Nudge Agent Button (for topics without issues) -->
          <div x-show="!selected.has_issues">
            <button @click="nudgeAgent(selected)" 
              class="w-full py-3 px-4 bg-yellow-600 text-white text-sm font-bold rounded-lg hover:bg-yellow-700 transition">
              👋 Nudge Agent: Create Issue List
            </button>
            <p class="text-xs text-gray-500 mt-2">This will send a message asking the agent to bootstrap their ISSUES.md with your approval.</p>
          </div>
        </div>

        <!-- Tab: Issues / Todo List (Agent Workspace Interface) -->
        <div x-show="activeTab === 'issues'" class="p-6 flex flex-col h-full">
          <!-- Info banner -->
          <div class="mb-6 p-4 bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg text-xs text-blue-200">
            <p><strong>💡 Agent Interface:</strong> Edit issues here. The topic agent reads and manages this list throughout the session.</p>
          </div>

          <!-- Header with stats -->
          <div class="mb-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-bold text-white">Work Items</h2>
              <button @click="addIssue()" class="text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">+ Add Task</button>
            </div>
            
            <!-- Progress bar + summary -->
            <div class="mb-4">
              <div class="flex justify-between text-sm mb-2">
                <span class="text-gray-400">Progress</span>
                <span class="font-bold text-blue-400" x-text="Math.round(((detail?.issues || []).filter(i => i.done).length / ((detail?.issues?.length || 1))) * 100) + '%'"></span>
              </div>
              <div class="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 transition-all" :style="'width: ' + Math.round(((detail?.issues || []).filter(i => i.done).length / ((detail?.issues?.length || 1))) * 100) + '%'"></div>
              </div>
            </div>

            <!-- Stats grid -->
            <div class="grid grid-cols-3 gap-2">
              <div class="bg-gray-700 rounded-lg p-3">
                <p class="text-xl font-bold text-white" x-text="detail?.issues?.length || 0"></p>
                <p class="text-xs text-gray-500 mt-0.5">Total Tasks</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3">
                <p class="text-xl font-bold text-green-400" x-text="(detail?.issues || []).filter(i => i.done).length"></p>
                <p class="text-xs text-gray-500 mt-0.5">Done</p>
              </div>
              <div class="bg-gray-700 rounded-lg p-3">
                <p class="text-xl font-bold text-yellow-400" x-text="(detail?.issues || []).filter(i => !i.done).length"></p>
                <p class="text-xs text-gray-500 mt-0.5">Remaining</p>
              </div>
            </div>
          </div>

          <!-- Workflow explanation -->
          <div class="mb-4 p-3 bg-gray-700 rounded text-xs text-gray-300 border-l-4 border-blue-500">
            <p><strong>💡 Workflow:</strong> Foreground = interactive with you. Background = async subagents/cron. Use issue notes to mark!</p>
          </div>

          <!-- Quick filters -->
          <div class="flex gap-2 mb-4 pb-4 border-b border-gray-700 flex-wrap">
            <button @click="issueFilter = 'open'" :class="issueFilter === 'open' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              class="text-xs px-3 py-1.5 rounded-full font-medium transition">
              <span x-text="'📌 Open (' + ((detail?.issues || []).filter(i => !i.done).length) + ')'"></span>
            </button>
            <button @click="issueFilter = 'done'" :class="issueFilter === 'done' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              class="text-xs px-3 py-1.5 rounded-full font-medium transition">
              <span x-text="'✓ Done (' + ((detail?.issues || []).filter(i => i.done).length) + ')'"></span>
            </button>
            <button @click="issueFilter = 'foreground'" :class="issueFilter === 'foreground' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              class="text-xs px-3 py-1.5 rounded-full font-medium transition">👤 Foreground</button>
            <button @click="issueFilter = 'background'" :class="issueFilter === 'background' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              class="text-xs px-3 py-1.5 rounded-full font-medium transition">⚙️ Background</button>
            <button @click="issueFilter = 'all'" :class="issueFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              class="text-xs px-3 py-1.5 rounded-full font-medium transition">All</button>
          </div>

          <!-- Empty state -->
          <div x-show="!detail?.issues?.length" class="text-center py-12 flex-1 flex flex-col items-center justify-center">
            <p class="text-5xl mb-3">📝</p>
            <p class="text-gray-400 text-sm">No tasks yet.</p>
            <p class="text-gray-500 text-xs mt-2">Add items for the agent to work on.</p>
          </div>

          <!-- Tasks list -->
          <div class="space-y-2 flex-1 overflow-y-auto pr-2">
            <template x-for="(issue, i) in (detail?.issues || []).filter(issue => {
              if (issueFilter === 'all') return true;
              if (issueFilter === 'done') return issue.done;
              if (issueFilter === 'open') return !issue.done;
              if (issueFilter === 'foreground') return !issue.done && !issue.notes?.toLowerCase().includes('[background]');
              if (issueFilter === 'background') return !issue.done && issue.notes?.toLowerCase().includes('[background]');
              return true;
            })" :key="i">
              <div :class="issue.done ? 'bg-gray-700 border-l-green-500' : (issue.notes?.toLowerCase().includes('[background]') ? 'bg-gray-800 border-l-indigo-500' : 'bg-gray-800 border-l-yellow-500 hover:border-l-blue-400')"
                class="border-l-4 p-4 rounded transition relative">
                
                <!-- Checkbox + Title + Badge -->
                <div class="flex items-start gap-3 mb-2">
                  <input type="checkbox" :checked="issue.done" @change="toggleIssue(i)"
                    class="mt-1 h-5 w-5 text-blue-500 rounded cursor-pointer flex-shrink-0">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <input type="text" :value="issue.title" @input="issue.title = $event.target.value"
                        :class="issue.done ? 'line-through text-gray-500' : 'text-white'"
                        class="flex-1 bg-transparent text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 px-2 py-1 rounded -mx-2 transition"
                        placeholder="Task name...">
                      <span x-show="!issue.done && issue.notes?.toLowerCase().includes('[background]')" class="text-xs px-2 py-0.5 bg-indigo-900 text-indigo-200 rounded-full flex-shrink-0">⚙️ Async</span>
                      <span x-show="!issue.done && !issue.notes?.toLowerCase().includes('[background]')" class="text-xs px-2 py-0.5 bg-purple-900 text-purple-200 rounded-full flex-shrink-0">👤 Now</span>
                    </div>
                  </div>
                  <button @click="removeIssue(i)" 
                    class="text-gray-600 hover:text-red-400 text-xs flex-shrink-0 transition">✕</button>
                </div>
                
                <!-- Notes/Description -->
                <div class="ml-8">
                  <textarea :value="issue.notes" @input="issue.notes = $event.target.value"
                    class="w-full text-xs p-2 bg-gray-700 text-gray-200 rounded border border-gray-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none transition"
                    rows="2"
                    placeholder="Notes. Add '[background]' to mark as async work..."></textarea>
                  <p class="text-xs text-gray-500 mt-1">💡 Tip: Add <code class="bg-gray-700 px-1 rounded">[background]</code> to mark as async work</p>
                </div>
              </div>
            </template>
          </div>

          <!-- Save button (sticky) -->
          <div class="mt-4 pt-4 border-t border-gray-700">
            <button @click="saveIssues()"
              class="w-full py-3 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition">
              💾 Save to ISSUES.md
            </button>
          </div>
        </div>

        <!-- Tab: Memory -->
        <div x-show="activeTab === 'memory'" class="p-6 flex flex-col h-full">
          <h3 class="font-semibold text-white mb-4">Memory Files</h3>
          <div x-show="!detail?.memory?.length" class="text-center py-12 flex flex-col items-center justify-center flex-1">
            <p class="text-5xl mb-3">🧠</p>
            <p class="text-gray-400 text-sm">No memory files yet</p>
          </div>
          <div class="space-y-4 flex-1 overflow-y-auto pr-2">
            <template x-for="f in (detail?.memory || [])" :key="f.filename">
              <div class="border border-gray-700 rounded-lg overflow-hidden bg-gray-800">
                <!-- Header -->
                <div class="flex items-center justify-between px-4 py-3 bg-gray-700 border-b border-gray-600">
                  <span class="text-sm font-semibold text-white" x-text="f.filename"></span>
                  <span class="text-xs text-gray-400" x-text="f.modified"></span>
                </div>
                <!-- Preview (readable) -->
                <div class="p-4 max-h-64 overflow-y-auto scrollbar-thin">
                  <pre class="text-sm text-gray-200 whitespace-pre-wrap break-words font-mono leading-relaxed" x-text="f.preview"></pre>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Tab: Chat (Reverse Chronological) -->
        <div x-show="activeTab === 'chat'" class="p-6 flex flex-col h-full">
          <!-- Info banner -->
          <div class="mb-4 p-3 bg-blue-900 bg-opacity-30 border border-blue-700 rounded text-xs text-blue-200">
            <p>💬 Latest messages appear at the top. Scroll down for conversation history.</p>
          </div>

          <!-- Input area at top (reverse of typical) -->
          <div class="border-b border-gray-700 pb-4 mb-4">
            <div class="flex gap-2">
              <textarea x-model="chatInput"
                @keydown.enter.shift="sendChatMessage()"
                class="flex-1 p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none text-sm"
                rows="2"
                placeholder="Type your message here... (Shift+Enter to send)"></textarea>
              <button @click="sendChatMessage()" :disabled="!chatInput.trim() || chatStreaming"
                :class="!chatInput.trim() || chatStreaming ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'"
                class="px-4 py-3 bg-blue-600 text-white rounded-lg font-medium transition flex-shrink-0">
                📤 Send
              </button>
            </div>
          </div>

          <!-- Chat history (reverse chronological) -->
          <div class="flex-1 overflow-y-auto space-y-3 pr-2">
            <!-- Empty state -->
            <div x-show="!detail?.transcript?.length" class="text-center py-12 flex flex-col items-center justify-center">
              <p class="text-5xl mb-3">💬</p>
              <p class="text-gray-400 text-sm">No messages yet. Start a conversation!</p>
            </div>

            <!-- Messages in reverse order (latest first) -->
            <template x-for="(msg, i) in [...(detail?.transcript || [])].reverse()" :key="i">
              <div :class="msg.role === 'user' ? 'justify-end' : 'justify-start'" class="flex">
                <div :class="msg.role === 'user' ? 'bg-blue-600 text-white rounded-l-xl rounded-tr-xl' : 'bg-gray-700 text-gray-100 rounded-r-xl rounded-tl-xl'"
                  class="max-w-sm lg:max-w-md px-4 py-3">
                  
                  <!-- Message content -->
                  <div class="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    <p x-text="msg.text"></p>
                  </div>
                  
                  <!-- Artifacts -->
                  <template x-if="msg.artifact">
                    <div class="mt-3 p-3 bg-gray-600 bg-opacity-50 rounded border border-gray-500 max-h-40 overflow-y-auto">
                      <p class="text-xs font-semibold text-gray-200 mb-2">📦 <span x-text="msg.artifact.type"></span></p>
                      <pre class="text-xs text-gray-300 overflow-x-auto font-mono"><code x-text="msg.artifact.content.substring(0, 300) + (msg.artifact.content.length > 300 ? '...' : '')"></code></pre>
                    </div>
                  </template>
                  
                  <!-- Timestamp -->
                  <p class="text-xs mt-2 opacity-50" x-text="msg.timestamp ? new Date(msg.timestamp).toLocaleString('en-US', {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}) : ''"></p>
                </div>
              </div>
            </template>

            <!-- Streaming indicator (newest) -->
            <div x-show="chatStreaming" class="flex justify-start">
              <div class="bg-gray-700 text-gray-100 rounded-r-xl rounded-tl-xl px-4 py-3">
                <p class="text-xs font-semibold uppercase mb-2 opacity-60">🤖 Agent (typing...)</p>
                <div class="flex gap-1">
                  <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.1s;"></div>
                  <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s;"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Skills -->
        <div x-show="activeTab === 'skills'" class="p-6">
          <h3 class="font-semibold text-white mb-4">Skills</h3>
          <div x-show="!detail?.skills?.length" class="text-sm text-gray-400 text-center py-8">No skills registered</div>
          <div class="flex flex-wrap gap-2">
            <template x-for="s in (detail?.skills || [])" :key="s">
              <span class="px-3 py-1 bg-purple-50 text-purple-700 text-sm rounded-full" x-text="s"></span>
            </template>
          </div>
        </div>

        <!-- Tab: Files -->
        <div x-show="activeTab === 'files'" class="p-6">
          <h3 class="font-semibold text-white mb-4">Workspace Files</h3>
          <div x-show="!detail?.files?.length" class="text-sm text-gray-400 text-center py-8">No files</div>
          <div class="space-y-1">
            <template x-for="f in (detail?.files || [])" :key="f.path">
              <div class="flex items-center justify-between py-1.5 px-2 hover:bg-gray-700 rounded text-sm">
                <span class="text-gray-700 font-mono text-xs" x-text="f.path"></span>
                <span class="text-xs text-gray-400 ml-4 shrink-0" x-text="f.modified"></span>
              </div>
            </template>
          </div>
        </div>

        <!-- Tab: Crons -->
        <div x-show="activeTab === 'crons'" class="p-6">
          <h3 class="font-semibold text-white mb-4">Cron Jobs & Heartbeats</h3>
          <div x-show="!detail?.crons?.length" class="text-sm text-gray-400 text-center py-8">No crons configured</div>
          <div class="space-y-3">
            <template x-for="(c, i) in (detail?.crons || [])" :key="i">
              <div class="bg-gray-700 rounded-lg p-3">
                <p class="text-sm font-medium text-white" x-text="c.label || c.id || 'Cron ' + i"></p>
                <p class="text-xs text-gray-500 mt-0.5" x-text="c.schedule || c.cron || JSON.stringify(c)"></p>
              </div>
            </template>
          </div>
        </div>

      </div>
    </template>
  </div>
</div>

<script>
function dashboard() {
  return {
    topics: [], filtered: [], loading: true,
    view: 'card', search: '', selected: null, detail: null,
    activeTab: 'overview', detailLoading: false,
    issueFilter: 'all', editingIssue: null,
    chatInput: '', chatStreaming: false,

    async init() {
      await this.refresh();
      this.$watch('search', () => this.applyFilter());
    },

    async refresh() {
      this.loading = true;
      try {
        const r = await fetch('/api/topics');
        this.topics = await r.json();
        this.applyFilter();
      } finally {
        this.loading = false;
      }
    },

    applyFilter() {
      const q = this.search.toLowerCase();
      this.filtered = q
        ? this.topics.filter(t => t.name.toLowerCase().includes(q) || t.topic_id.includes(q))
        : [...this.topics];
    },

    formatLastActivity(timestamp) {
      if (!timestamp) return 'Unknown';
      const now = Date.now() / 1000;
      const diff = now - timestamp;
      if (diff < 60) return 'Just now';
      if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
      if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
      if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
      return new Date(timestamp * 1000).toLocaleDateString();
    },

    formatDatetime(timestamp) {
      if (!timestamp) return 'Unknown';
      const date = new Date(timestamp * 1000);
      // Format: "Fri, Mar 22, 2026 at 12:18:45 PM"
      const dayOfWeek = date.toLocaleString('en-US', { weekday: 'short' });
      const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      };
      const dateStr = date.toLocaleString('en-US', options);
      return `${dayOfWeek}, ${dateStr}`;
    },

    async openTopic(t) {
      this.selected = t;
      this.activeTab = 'overview';
      this.detail = null;
      this.detailLoading = true;
      try {
        const r = await fetch('/api/topics/' + t.id);
        this.detail = await r.json();
      } finally {
        this.detailLoading = false;
      }
    },

    toggleIssue(i) {
      if (this.detail?.issues?.[i] !== undefined) {
        this.detail.issues[i].done = !this.detail.issues[i].done;
      }
    },

    removeIssue(i) {
      if (i >= 0 && i < this.detail.issues.length) {
        this.detail.issues.splice(i, 1);
      }
    },

    addIssue() {
      const title = prompt('New issue title:');
      if (title) {
        if (!this.detail.issues) this.detail.issues = [];
        this.detail.issues.push({ title, done: false, notes: '' });
      }
    },

    async saveIssues() {
      await fetch('/api/topics/' + this.selected.id + '/issues', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issues: this.detail.issues })
      });
      alert('Saved ✓');
    },

    async sendChatMessage() {
      if (!this.chatInput.trim() || this.chatStreaming) return;
      
      const message = this.chatInput;
      this.chatInput = '';
      this.chatStreaming = true;
      
      try {
        // Add user message to transcript
        if (!this.detail.transcript) this.detail.transcript = [];
        this.detail.transcript.push({
          role: 'user',
          text: message,
          timestamp: new Date().toISOString()
        });
        
        // TODO: Send to agent via Telegram or API
        // For now, just add a placeholder agent response
        setTimeout(() => {
          this.detail.transcript.push({
            role: 'assistant',
            text: '(Agent will respond here)',
            timestamp: new Date().toISOString()
          });
          this.chatStreaming = false;
        }, 500);
      } finally {
        this.chatStreaming = false;
      }
    },

    async nudgeAgent(topic) {
      const message = `Hi! 👋

I'm noticing you don't have an ISSUES.md file yet. Let's create one together!

**Here's what I need:**
1. Look at your SOUL.md mission brief
2. Break it down into 3-5 concrete, actionable tasks
3. Draft an ISSUES.md with those tasks
4. Show me the list and ask if I approve before you start

**Use the Bootstrap Issues skill** (/root/clawd/skills/bootstrap-issues/) for guidance.

This is how we'll track progress. Once you have the list, I can oversee everything from the dashboard.

Ready? Let me know what you come up with! 💪`;

      try {
        // Send nudge via Telegram to the topic
        const response = await fetch('/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'send',
            channel: 'telegram',
            target: '-1003736525734',
            threadId: topic.topic_id,
            message: message
          })
        });
        
        if (response.ok) {
          alert('✅ Nudge sent! Agent will see it in their Telegram topic.');
        } else {
          alert('❌ Failed to send nudge. Try manually.');
        }
      } catch (e) {
        console.error('Nudge error:', e);
        alert('Error sending nudge: ' + e.message);
      }
    },

    tabIcon(tab) {
      return { overview:'📊', issues:'📋', memory:'🧠', chat:'💬', skills:'⚡', files:'📁', crons:'⏰' }[tab] || '';
    }
  }
}
</script>
</body>
</html>
"""

@app.get("/docs-page")
async def docs_page():
    from fastapi.responses import HTMLResponse
    html = (Path(__file__).parent / "docs.html").read_text()
    return HTMLResponse(html)

@app.get("/test-page")
async def test_page_route():
    from fastapi.responses import HTMLResponse
    html = (Path(__file__).parent / "test.html").read_text()
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
