# Issues & Roadmap — PakOS Topic Dashboard

**Track all work, blockers, and future features.**

---

## Phase 2.1: Kanban Enhancement + Memory Browser

### 🎯 High Priority (Sprint 1)

#### Kanban Drag-Drop
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Implement drag-and-drop between Kanban columns (Idle → Active → Blocked → Done)  
**Acceptance Criteria**:
- [ ] Cards draggable between columns
- [ ] Status updates via API
- [ ] Smooth animations
- [ ] Test passes on `/test-page`

**Implementation Path**:
1. Add drag listeners to cards in Kanban view
2. Call `PUT /api/topics/{id}/status` to update
3. Update test: "Can drag topic between statuses"

---

#### Memory Browser (Search + Filters)
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Enhance Memory tab with search, date filter, full-text search  
**Acceptance Criteria**:
- [ ] Search memory files by keyword
- [ ] Filter by date range
- [ ] Display snippet of matches
- [ ] Click to expand full content
- [ ] Test: "Memory search returns results"

**Implementation Path**:
1. Add search input to Memory tab
2. Parse memory/*.md files and index content
3. Display matches with snippet preview
4. Add date picker for filtering

---

#### Snooze Heartbeat Feature
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Right-click card → snooze 1h/4h/24h options  
**Acceptance Criteria**:
- [ ] Context menu on right-click
- [ ] Snooze options display
- [ ] API endpoint accepts snooze duration
- [ ] Visual feedback (grayed out, badge showing "snoozed")
- [ ] Test: "Can snooze heartbeat"

**Implementation Path**:
1. Add right-click handler to cards
2. Show context menu with durations
3. Call `POST /api/topics/{id}/snooze` endpoint
4. Disable heartbeat for selected duration

---

### 📌 Medium Priority (Sprint 2)

#### Transcript Viewer
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: View chat transcripts with search and filtering  
**Implementation Path**:
1. Parse `/root/.openclaw/agents/*/sessions/*.jsonl`
2. Display in Transcripts tab with timeline
3. Add search across messages
4. Show sender badges (User/Assistant)

**Tests to Add**:
- "Can load chat transcripts"
- "Can search in transcripts"
- "Transcript displays formatted messages"

---

#### File Browser (Directory Tree)
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Browse `/root/clawd/topics/{id}/` as interactive tree  
**Implementation Path**:
1. Add file listing endpoint: `GET /api/topics/{id}/files`
2. Build tree UI in Files tab
3. Show file sizes, dates
4. Click to preview/download

**Tests to Add**:
- "File tree loads correctly"
- "Can preview file contents"
- "Directory structure renders"

---

#### Cron/Heartbeat Viewer
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Show cron schedules and heartbeat logs  
**Implementation Path**:
1. Parse HEARTBEAT.md for schedule
2. Show next run times
3. Display recent heartbeat logs
4. Alert on missed heartbeats

**Tests to Add**:
- "Cron schedule displays correctly"
- "Heartbeat status shows current state"
- "Missed heartbeats highlighted"

---

### 🔵 Low Priority (Sprint 3+)

#### Live WebSocket Updates
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Real-time dashboard updates via WebSocket  
**Implementation Path**:
1. Add WebSocket endpoint to FastAPI
2. Stream topic changes (status, progress)
3. Client subscribes to updates
4. Auto-refresh views on changes

---

#### Dark/Light Theme Toggle
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Add theme switcher in header  
**Implementation Path**:
1. Add CSS variables for light theme
2. Add toggle button in header
3. Persist preference in localStorage
4. Smooth transitions

---

#### Export/Import
**Status**: 🔄 TODO  
**Assigned**: Next Agent  
**Description**: Export topic data as JSON/CSV, bulk import  
**Implementation Path**:
1. Add export button → downloads JSON
2. CSV export with selected fields
3. Bulk import wizard
4. Validation of imported data

---

## Bug Fixes & Improvements

### 🐛 Minor Issues
- [ ] Responsive design on mobile (Kanban cards too wide)
- [ ] Accessibility: Add ARIA labels to buttons
- [ ] Performance: Lazy-load large memory files
- [ ] Edge case: Handle topics with special characters in names

---

## Testing Requirements

All features must pass:
1. **Unit Tests**: Individual functions validated
2. **Integration Tests**: API + UI work together
3. **E2E Tests**: Full user flow works end-to-end
4. **Manual Tests**: On `/test-page` and production

---

## Documentation

- [ ] Update API documentation for new endpoints
- [ ] Add screenshots of new views to README
- [ ] Document Phase 2 completion in CHANGELOG
- [ ] Write deployment guide for new features

---

## Version Milestones

| Version | Target Date | Features |
|---------|-------------|----------|
| 1.0.0 | 2026-03-22 | Initial dashboard, views, docs, tests ✅ |
| 1.1.0 | 2026-03-29 | Kanban drag-drop, memory search, snooze |
| 1.2.0 | 2026-04-05 | File browser, transcripts, crons |
| 1.3.0 | 2026-04-12 | Live updates, theme toggle, export |
| 2.0.0 | 2026-05-01 | Major refactor, new architecture |

---

## How to Pick an Issue

1. **Find**: Pick one with 🔄 TODO status
2. **Claim**: Comment with "Assigning to {YourName}"
3. **Implement**: Create feature branch, push code
4. **Test**: Verify on `/test-page`
5. **Submit**: Push to GitHub, notify team

---

## Done Issues

- ✅ [1.0.0] Dashboard main views (Card, List, Kanban)
- ✅ [1.0.0] Detail panel with tabs
- ✅ [1.0.0] Issue editing
- ✅ [1.0.0] API endpoints
- ✅ [1.0.0] Documentation page
- ✅ [1.0.0] Test page with e2e tests
- ✅ [1.0.0] GitHub repository
- ✅ [1.0.0] Systemd deployment

---

**Legend**: 🔄 = In Progress | 🔵 = Planned | ⚠️ = Blocked | 🐛 = Bug | ✅ = Done

**Last Updated**: 2026-03-22  
**Maintained By**: PakOS Topic Dashboard Team
