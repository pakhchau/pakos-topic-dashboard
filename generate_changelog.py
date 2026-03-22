#!/usr/bin/env python3
"""Generate changelog from git history with version tracking."""
import subprocess
from datetime import datetime
from pathlib import Path

def get_version():
    """Read current version from VERSION file."""
    try:
        return Path('VERSION').read_text().strip()
    except:
        return '1.0.0'

def get_git_log():
    """Get git log in reverse order."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%h | %ai | %s"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n')

def categorize_commit(message):
    """Categorize commit by type."""
    if message.startswith('Feature:'):
        return 'ADDED', 'green'
    elif message.startswith('Fix:'):
        return 'FIXED', 'orange'
    elif message.startswith('Docs:'):
        return 'DOCS', 'blue'
    elif message.startswith('UX:'):
        return 'IMPROVED', 'purple'
    elif message.startswith('Initial:'):
        return 'INITIAL', 'blue'
    return 'OTHER', 'gray'

def generate_changelog():
    """Generate HTML changelog from git commits."""
    version = get_version()
    commits = get_git_log()
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Changelog — PakOS Topic Dashboard</title>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --card: #16161f;
    --border: #22222e;
    --accent: #6c63ff;
    --green: #00d4a0;
    --orange: #f5a623;
    --text: #e8e8f0;
    --muted: #666680;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
  }

  header {
    position: sticky; top: 0; z-index: 100;
    background: rgba(10,10,15,0.92);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    height: 56px;
    display: flex; align-items: center;
  }
  .brand { display: flex; gap: 10px; align-items: center; }
  .brand-name { font-weight: 700; }
  .version-badge {
    background: var(--accent);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    margin-left: auto;
  }

  main {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
  }

  .changelog {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
  }

  h1 {
    font-size: 24px;
    margin-bottom: 8px;
    color: var(--accent);
  }

  .subtitle {
    color: var(--muted);
    margin-bottom: 24px;
  }

  nav {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  nav a {
    display: inline-block;
    padding: 8px 12px;
    margin-right: 8px;
    background: var(--surface);
    color: var(--accent);
    text-decoration: none;
    border-radius: 6px;
    font-size: 13px;
    transition: all 0.2s;
  }

  nav a:hover {
    background: var(--card);
  }

  .timeline {
    position: relative;
    padding-left: 20px;
  }

  .timeline::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, var(--accent), transparent);
  }

  .commit {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px dotted var(--border);
  }

  .commit:last-child {
    border-bottom: none;
  }

  .commit-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }

  .commit-badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
  }

  .badge-added { background: rgba(0,212,160,0.2); color: var(--green); }
  .badge-fixed { background: rgba(245,166,35,0.2); color: var(--orange); }
  .badge-docs { background: rgba(108,99,255,0.2); color: var(--accent); }
  .badge-improved { background: rgba(150,100,200,0.2); color: #d88ff0; }
  .badge-initial { background: rgba(108,99,255,0.3); color: var(--accent); }

  .commit-message {
    font-weight: 500;
    color: var(--text);
    margin-right: auto;
  }

  .commit-hash {
    font-family: monospace;
    color: var(--muted);
    font-size: 12px;
  }

  .commit-time {
    color: var(--muted);
    font-size: 12px;
    white-space: nowrap;
  }

  .stats {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  }

  .stat-item {
    text-align: center;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent);
  }

  .stat-label {
    font-size: 12px;
    color: var(--muted);
    margin-top: 4px;
  }

  .version-section {
    margin-bottom: 32px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border);
  }

  .version-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .version-number {
    background: var(--accent);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
  }

  .version-date {
    color: var(--muted);
    font-size: 14px;
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <span style="font-size: 20px;">📋</span>
    <div class="brand-name">Changelog — PakOS Topic Dashboard</div>
    <span class="version-badge">v""" + version + """</span>
  </div>
</header>

<main>
  <div class="changelog">
    <h1>📋 Complete Version History</h1>
    <p class="subtitle">All changes to PakOS Topic Dashboard, tracked by version and date.</p>

    <nav>
      <a href="/">← Back to Dashboard</a>
      <a href="/docs-page">📖 Docs</a>
      <a href="/test-page">🧪 Tests</a>
    </nav>

    <div class="stats">
      <div class="stat-item">
        <div class="stat-value">""" + str(len(commits)) + """</div>
        <div class="stat-label">Total Commits</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">v""" + version + """</div>
        <div class="stat-label">Current Version</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">""" + datetime.now().strftime("%b %d, %Y") + """</div>
        <div class="stat-label">Last Updated</div>
      </div>
    </div>

    <!-- Version Section -->
    <div class="version-section">
      <div class="version-header">
        <span class="version-number">v""" + version + """</span>
        <span style="font-size: 18px;">🚀</span>
        <span class="version-date">""" + datetime.now().strftime("%b %d, %Y") + """</span>
      </div>

      <div class="timeline">
"""
    
    # Count commits by type
    types_count = {'ADDED': 0, 'FIXED': 0, 'DOCS': 0, 'IMPROVED': 0, 'INITIAL': 0, 'OTHER': 0}
    for commit in commits:
        parts = commit.split(' | ')
        if len(parts) >= 3:
            message = parts[2]
            category, _ = categorize_commit(message)
            types_count[category] += 1
    
    # Add commits in chronological order
    for commit in commits:
        parts = commit.split(' | ')
        if len(parts) < 3:
            continue
        
        commit_hash = parts[0].strip()
        timestamp = parts[1].strip()
        message = parts[2].strip()
        
        category, color = categorize_commit(message)
        badge_class = f"badge-{category.lower().replace(' ', '-')}"
        
        # Parse timestamp
        dt = datetime.fromisoformat(timestamp.replace(' +0000', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
        date_str = dt.strftime("%b %d, %Y")
        
        html += f"""        <div class="commit">
          <div class="commit-header">
            <span class="commit-badge {badge_class}">{category}</span>
            <span class="commit-message">{message}</span>
            <span class="commit-hash">{commit_hash}</span>
          </div>
          <div style="font-size: 12px; color: var(--muted);">
            {date_str} at {time_str} UTC
          </div>
        </div>
"""
    
    html += """      </div>
    </div>

    <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px;">
      <p>All work completed on """ + datetime.now().strftime("%Y-%m-%d") + """ | <a href="https://github.com/pakhchau/pakos-topic-dashboard" target="_blank" style="color: var(--accent);">View on GitHub</a></p>
      <p style="margin-top: 8px;">Current version: <strong>v""" + version + """</strong></p>
    </div>
  </div>
</main>

</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    # Change to repo directory
    import os
    os.chdir(Path(__file__).parent)
    
    html = generate_changelog()
    Path("changelog.html").write_text(html)
    print(f"✅ Changelog generated for v{get_version()}!")
