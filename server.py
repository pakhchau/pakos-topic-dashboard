#!/usr/bin/env python3
"""Simplified PakOS Topic Dashboard - Fixed Version"""
import json
import subprocess
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TOPICS_DIR = Path("/root/clawd/topics")

def get_all_topics():
    """Read topics from topic_agent.py"""
    try:
        result = subprocess.run(["python3", "/root/clawd/scripts/topic_agent.py", "list"],
                              capture_output=True, text=True, timeout=15)
        topics = []
        for line in result.stdout.splitlines()[2:]:
            if line.startswith('-'): continue
            if not line.strip(): continue
            parts = line.split()
            if len(parts) >= 4 and parts[0].startswith('topic-'):
                tid = parts[0]
                status = parts[-1]
                heartbeat = parts[-2]
                middle = ' '.join(parts[1:-2])
                name = middle.replace("Topic: ", "").strip()
                if name:
                    topics.append({"id": tid, "name": name, "heartbeat": heartbeat, 
                                 "status": status, "topic_id": tid.replace("topic-", "")})
        return sorted(topics, key=lambda x: x['name'])
    except:
        return []

def get_topic_dates(topic_dir):
    try:
        created = int(topic_dir.stat().st_ctime)
        files = list(topic_dir.rglob("*"))
        updated = max((f.stat().st_mtime for f in files if f.is_file()), default=created)
        return created, int(updated)
    except:
        return 0, 0

@app.get("/api/topics", response_model=list)
def list_topics():
    topics = get_all_topics()
    enriched = []
    for t in topics:
        tid = t["id"].replace("topic-", "")
        for d in TOPICS_DIR.iterdir():
            if d.is_dir() and d.name.endswith(f"-{tid}"):
                created, updated = get_topic_dates(d)
                issues_file = d / "ISSUES.md"
                issues = []
                if issues_file.exists():
                    for line in issues_file.read_text().splitlines():
                        if '[x]' in line or '[ ]' in line:
                            issues.append({"done": '[x]' in line, "title": line.split(']')[1].strip() if ']' in line else ""})
                t["progress"] = int((len([i for i in issues if i["done"]]) / len(issues) * 100)) if issues else 0
                t["total_issues"] = len(issues)
                t["issue_done"] = len([i for i in issues if i["done"]])
                t["created_time"] = created
                t["updated_time"] = updated
                t["has_issues"] = len(issues) > 0
                t["last_message_time"] = updated
                break
        enriched.append(t)
    return enriched

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PakOS Topics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0a0a0f; color: #e8e8f0; }
        .topic-card { background: #16161f; border: 1px solid #22222e; transition: all 0.2s; }
        .topic-card:hover { border-color: #6c63ff; transform: translateY(-2px); }
        .loading { display: none; }
        .loaded { display: block; }
    </style>
</head>
<body class="min-h-screen">
    <div class="max-w-6xl mx-auto px-6 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-white mb-2">🗂️ PakOS Topics</h1>
            <p class="text-gray-400">Manage all topics and track agent progress</p>
        </div>
        
        <div id="loading" class="loading text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p class="mt-4 text-gray-400">Loading topics...</p>
        </div>
        
        <div id="content" class="loaded grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        </div>
    </div>

    <script>
        async function loadTopics() {
            try {
                const res = await fetch('/api/topics');
                const topics = await res.json();
                console.log('✅ Loaded', topics.length, 'topics');
                
                const content = document.getElementById('content');
                content.innerHTML = topics.map(t => `
                    <div class="topic-card p-4 rounded-lg cursor-pointer">
                        <h3 class="text-white font-semibold mb-2">${t.name}</h3>
                        <div class="mb-3">
                            <div class="flex justify-between text-xs text-gray-400 mb-1">
                                <span>Progress</span>
                                <span>${t.progress}%</span>
                            </div>
                            <div class="w-full h-2 bg-gray-700 rounded">
                                <div class="h-2 bg-blue-500 rounded" style="width:${t.progress}%"></div>
                            </div>
                        </div>
                        <div class="text-xs text-gray-500">
                            <div>Status: ${t.status}</div>
                            <div>Issues: ${t.issue_done}/${t.total_issues}</div>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'grid';
            } catch (e) {
                console.error('❌ Error:', e);
                document.getElementById('content').innerHTML = '<p class="text-red-500">Error loading topics: ' + e.message + '</p>';
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        loadTopics();
    </script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
