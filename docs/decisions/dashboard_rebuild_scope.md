# Dashboard Rebuild Scope — Migration Reference

## Current Dashboard State (Pre-Migration)

### Single file: `src/dashboard/frontend/index.html`
- 1276 lines of monolithic HTML/CSS/JS
- Dark theme "Command Center" UI with tabs
- Inline CSS (~100 lines of custom properties + styles)
- Inline JS (~600 lines) for API calls, WebSocket, DOM updates

### Existing Tabs (from legacy HTML)
1. **Overview** — system status, uptime, viewers, stream state, product
2. **Brain** — LLM provider grid, health check, test prompt, routing table
3. **Pipeline** — state machine (IDLE/SELLING/REACTING/ENGAGING/PAUSED)
4. **Stream** — start/stop stream, emergency stop/reset
5. **Products** — product list, switch product
6. **Chat** — real-time chat feed via WebSocket
7. **Health** — component health grid
8. **Diagnostics** — (linked to /diagnostic/ route)

### REST Endpoints Actually Used
| Endpoint | Method | Used By |
|---|---|---|
| `/api/status` | GET | Overview tab polling |
| `/api/metrics` | GET | Overview metrics |
| `/api/products` | GET | Products tab |
| `/api/products/{id}/switch` | POST | Product switch button |
| `/api/stream/start` | POST | Stream tab |
| `/api/stream/stop` | POST | Stream tab |
| `/api/emergency-stop` | POST | Stream tab |
| `/api/emergency-reset` | POST | Stream tab |
| `/api/pipeline/state` | GET | Pipeline tab |
| `/api/pipeline/transition` | POST | Pipeline state nodes |
| `/api/brain/stats` | GET | Brain tab |
| `/api/brain/health` | GET | Brain tab |
| `/api/brain/test` | POST | Brain test form |
| `/api/brain/config` | GET | Brain tab |
| `/api/health/summary` | GET | Health tab |
| `/api/chat/recent` | GET | Chat tab initial load |
| `/api/analytics/revenue` | GET | Overview tab |
| `/api/engine/livetalking/status` | GET | Not wired in legacy HTML |
| `/api/engine/livetalking/start` | POST | Not wired in legacy HTML |
| `/api/engine/livetalking/stop` | POST | Not wired in legacy HTML |
| `/api/engine/livetalking/logs` | GET | Not wired in legacy HTML |
| `/api/engine/livetalking/config` | GET | Not wired in legacy HTML |
| `/api/readiness` | GET | Not wired in legacy HTML |
| `/api/validate/mock-stack` | POST | Not wired in legacy HTML |
| `/api/validate/livetalking-engine` | POST | Not wired in legacy HTML |
| `/api/validate/rtmp-target` | POST | Not wired in legacy HTML |

### WebSocket Endpoints
| Endpoint | Used By |
|---|---|
| `/api/ws/dashboard` | Overview real-time updates (1s interval) |
| `/api/ws/chat` | Chat real-time feed |

### Features That Are Real (connected to backend)
- System status display
- LLM provider health check and test
- Pipeline state machine transitions
- Stream start/stop/emergency
- Product list and switching
- Real-time chat via WebSocket
- Component health grid

### Features That Are Cosmetic / Not Wired
- LiveTalking engine control (endpoints exist but not in UI)
- Readiness checks (endpoint exists but not in UI)
- Validation workflows (endpoints exist but not in UI)
- FFmpeg readiness display
- Requested vs resolved model/avatar display

### What Must Survive Migration
1. All existing API integrations (status, metrics, products, stream, brain, health, chat)
2. WebSocket real-time updates
3. Pipeline state machine UI
4. Dark theme control-room aesthetic
5. `/dashboard` route via FastAPI

### What Must Be Added in Migration
1. LiveTalking engine panel (start/stop/status/logs/config)
2. Readiness panel with blocking issues
3. Requested vs resolved model/avatar display
4. Vendor debug links (8010 pages)
5. FFmpeg readiness display
6. RTMP validation
7. Port collision error display

### Non-goals
- No Next.js/NestJS
- No SSR
- No auth system
- No marketing site styling
