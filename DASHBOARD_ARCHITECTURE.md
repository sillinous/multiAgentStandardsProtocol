# 🏗️ APQC Dashboard - System Architecture

Complete technical architecture for the real-time agent monitoring dashboard.

---

## 📐 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Web Browser (Chrome, Firefox, etc.)              │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │  Overview   │  │ Categories  │  │   All Agents        │  │  │
│  │  │    View     │  │    View     │  │     View            │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│  │                                                               │  │
│  │  Real-Time Dashboard (React 18.2 + TypeScript)               │  │
│  │  • Agent Grid • Category Cards • Event Stream • Metrics      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                ↕
        ┌──────────────── WebSocket (ws://) ──────────────────┐
        │                  REST API (http://)                  │
        └──────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               FastAPI Server (Python 3.8+)                   │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │  WebSocket   │  │  REST API    │  │   Background     │  │  │
│  │  │   Handler    │  │  Endpoints   │  │     Tasks        │  │  │
│  │  │              │  │              │  │                  │  │  │
│  │  │ • Connect    │  │ • /agents    │  │ • Monitoring     │  │  │
│  │  │ • Broadcast  │  │ • /categories│  │ • Metrics        │  │  │
│  │  │ • Heartbeat  │  │ • /workflows │  │ • Cleanup        │  │  │
│  │  │ • Events     │  │ • /metrics   │  │ • Discovery      │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐│  │
│  │  │             Agent Monitor Engine                        ││  │
│  │  │  • Agent Discovery  • Status Tracking  • Metrics        ││  │
│  │  └─────────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Database Manager (SQLite)                        │  │
│  │                                                               │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐│  │
│  │  │   Agents   │  │ Workflows  │  │  Metrics   │  │ Events ││  │
│  │  │   Table    │  │   Table    │  │   Table    │  │ Table  ││  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────┘│  │
│  │                                                               │  │
│  │  • Indexes  • Constraints  • Backups  • Cleanup             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │          APQC Agent Specialization Framework                  │  │
│  │                                                               │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │  │
│  │  │Cat 1 │ │Cat 2 │ │Cat 3 │ │ ...  │ │Cat12│ │Cat13│     │  │
│  │  │4 agts│ │3 agts│ │5 agts│ │      │ │4 agts│ │5 agts│     │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │  │
│  │                                                               │  │
│  │  Total: 118+ Agents across 13 APQC Categories                │  │
│  │  Protocols: A2A, A2P, ACP, ANP, MCP                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### Real-Time Update Flow

```
1. Agent Status Change
   ↓
2. Monitor Engine Detects
   ↓
3. Database Updated
   ↓
4. WebSocket Broadcast
   ↓
5. Frontend Receives
   ↓
6. UI Auto-Updates
```

### REST API Flow

```
1. Browser Request
   ↓
2. FastAPI Endpoint
   ↓
3. Database Query
   ↓
4. JSON Response
   ↓
5. Frontend Renders
```

---

## 🗄️ Database Schema

### Agents Table
```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    agent_name TEXT,
    category_id TEXT,
    category_name TEXT,
    process_id TEXT,
    status TEXT,
    health_score REAL,
    last_heartbeat TIMESTAMP,
    tasks_processed INTEGER,
    error_count INTEGER,
    avg_response_time REAL,
    memory_usage REAL,
    cpu_usage REAL,
    protocols TEXT,
    capabilities TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Workflows Table
```sql
CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    workflow_name TEXT,
    workflow_type TEXT,
    status TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    progress REAL,
    agents_involved TEXT,
    current_stage TEXT,
    stages_completed INTEGER,
    total_stages INTEGER,
    metrics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Metrics Table
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    timestamp TIMESTAMP,
    tasks_completed INTEGER,
    tasks_failed INTEGER,
    avg_response_time REAL,
    success_rate REAL,
    throughput REAL,
    error_rate REAL,
    resource_usage TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

### Events Table
```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT,
    agent_id TEXT,
    timestamp TIMESTAMP,
    severity TEXT,
    message TEXT,
    details TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

---

## 🔌 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint (status) |
| GET | `/api/agents` | Get all agents |
| GET | `/api/agents/{id}` | Get specific agent |
| POST | `/api/agents/{id}/status` | Update agent status |
| GET | `/api/categories` | Get category metrics |
| GET | `/api/workflows` | Get all workflows |
| GET | `/api/metrics/summary` | Get summary metrics |
| GET | `/docs` | OpenAPI documentation |

### WebSocket

| Event Type | Direction | Description |
|------------|-----------|-------------|
| `initial` | Server → Client | Initial data on connect |
| `agent_update` | Server → Client | Agent status changed |
| `heartbeat` | Server → Client | Keep-alive ping |
| `ping` | Client → Server | Connection test |
| `pong` | Server → Client | Ping response |

---

## 🎯 Component Hierarchy

### Frontend Components

```
Dashboard (Root)
│
├── DashboardHeader
│   ├── Title
│   ├── ConnectionStatus
│   └── AgentCount
│
├── StatsGrid
│   └── StatCard × 6
│
├── ViewSelector
│   ├── Overview Button
│   ├── Categories Button
│   └── Agents Button
│
├── OverviewView
│   ├── CategoryGrid
│   │   └── CategoryCard × 13
│   │       └── AgentCard × (1-6)
│   └── EventStream
│       └── EventItem × N
│
├── CategoriesView
│   └── CategoryCard × 13
│       └── AgentCard × (all)
│
├── AgentsView
│   ├── SearchBar
│   └── AgentGrid
│       └── AgentCard × 118+
│
└── AgentDetailModal (conditional)
    ├── AgentInfo
    ├── MetricsDisplay
    ├── ProtocolBadges
    └── CapabilitiesList
```

### Backend Components

```
FastAPI Application
│
├── Lifespan Manager
│   ├── Startup Tasks
│   └── Shutdown Tasks
│
├── Middleware
│   └── CORS
│
├── WebSocket Handler
│   ├── Connection Manager
│   ├── Broadcast Engine
│   └── Message Router
│
├── REST API Routes
│   ├── Agents Endpoints
│   ├── Categories Endpoints
│   ├── Workflows Endpoints
│   └── Metrics Endpoints
│
├── Agent Monitor
│   ├── APQC Integration
│   ├── Agent Discovery
│   ├── Status Tracker
│   └── Metrics Collector
│
├── Database Manager
│   ├── Schema Manager
│   ├── CRUD Operations
│   ├── Query Builder
│   └── Backup Manager
│
└── Background Tasks
    ├── Monitoring Loop
    ├── Metrics Collection
    ├── Cleanup Task
    └── Discovery Task
```

---

## 🔐 Security Architecture

### Authentication (Optional)
```
User Request
    ↓
API Key Check → Valid? → Proceed
    ↓              ↓
  Invalid        Yes
    ↓
  401 Error
```

### CORS Configuration
```yaml
allowed_origins: ["*"]  # Configure for production
allowed_methods: [GET, POST, PUT, DELETE, OPTIONS]
allowed_headers: ["*"]
allow_credentials: true
```

### Rate Limiting
```
Per IP: 1000 requests/minute
Per API Key: Custom limits
WebSocket: 1000 concurrent connections
```

---

## 📊 Performance Architecture

### Caching Strategy
```
┌─────────────┐
│   Browser   │ ← Cache static files
└─────────────┘
      ↓
┌─────────────┐
│   Server    │ ← In-memory cache (60s TTL)
└─────────────┘
      ↓
┌─────────────┐
│  Database   │ ← Indexed queries
└─────────────┘
```

### Connection Pooling
```
FastAPI → SQLite Connection Pool (10 connections)
WebSocket → Connection Manager (1000 max)
```

### Update Batching
```
Agent Updates (100 updates) → Batch → Single DB Write
Metrics (100 metrics) → Batch → Bulk Insert
Events (100 events) → Batch → Bulk Insert
```

---

## 🔄 State Management

### Frontend State
```
React Hooks:
├── useState (local component state)
├── useEffect (side effects, WebSocket)
├── useMemo (computed values)
└── Custom Hooks
    ├── useWebSocket (real-time connection)
    └── useAPI (REST calls)
```

### Backend State
```
In-Memory:
├── Active Agents (Dict)
├── Active Workflows (Dict)
├── WebSocket Connections (Set)
└── Metrics Cache (Dict)

Persistent:
└── SQLite Database
```

---

## 🌐 Network Protocol

### WebSocket Protocol

**Connection:**
```
Client → ws://localhost:8765/ws → Server
Server → Accept → Connected
Server → Send: initial data
```

**Heartbeat:**
```
Every 10s: Server → Client (heartbeat message)
Every 30s: Server → Client (ping)
Within 10s: Client → Server (pong required)
Timeout: 300s → Disconnect
```

**Messages:**
```javascript
{
  type: "initial" | "agent_update" | "heartbeat" | "ping" | "pong",
  data: { ... },
  timestamp: "ISO-8601"
}
```

---

## 🚀 Deployment Architecture

### Development
```
┌─────────────────┐
│  Local Machine  │
│                 │
│  Backend:8765   │
│  Frontend:8080  │
└─────────────────┘
```

### Production (Recommended)
```
Internet
    ↓
┌──────────────┐
│    Nginx     │ (Reverse Proxy, SSL/TLS)
│   Port 80    │
└──────────────┘
    ↓
┌──────────────────────────────┐
│        Application Server     │
│                               │
│  ┌────────────────────────┐  │
│  │  Gunicorn (4 workers)  │  │
│  │  FastAPI:8765          │  │
│  └────────────────────────┘  │
│                               │
│  ┌────────────────────────┐  │
│  │  Static Files          │  │
│  │  Frontend              │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

### High Availability
```
         ┌──────────────┐
         │Load Balancer │
         └──────────────┘
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│Server 1 │ │Server 2 │ │Server 3 │
└─────────┘ └─────────┘ └─────────┘
    ↓           ↓           ↓
         ┌──────────────┐
         │   Database   │
         │  (Clustered) │
         └──────────────┘
```

---

## 📈 Scalability Plan

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Enable caching
- Compress responses

### Horizontal Scaling
- Multiple backend instances
- Load balancing
- Distributed WebSocket
- Redis for shared state

### Database Scaling
- Database sharding by category
- Read replicas
- Time-series optimization
- Archive old data

---

## 🔧 Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** |
| Framework | React | 18.2 | UI components |
| Language | JavaScript/TypeScript | ES6+ | Logic |
| Charts | Chart.js | 4.4.0 | Visualizations |
| HTTP Server | Python http.server | 3.8+ | Dev server |
| **Backend** |
| Framework | FastAPI | 0.104+ | API server |
| Server | Uvicorn | 0.24+ | ASGI server |
| WebSocket | websockets | 12.0 | Real-time |
| Validation | Pydantic | 2.5+ | Data models |
| Config | PyYAML | 6.0+ | Configuration |
| **Database** |
| Database | SQLite | 3.x | Persistence |
| Async | aiosqlite | 0.19+ | Async ops |
| **Production** |
| Server | Gunicorn | 21.2+ | Production |
| Proxy | Nginx | 1.x | Reverse proxy |
| Process | Systemd | - | Service |

---

## 📝 Configuration Files

### dashboard_config.yaml
```yaml
server:        # Server settings
websocket:     # WebSocket config
monitoring:    # Monitoring parameters
database:      # Database settings
alerts:        # Alert thresholds
security:      # Security options
apqc:          # APQC categories & workflows
ui:            # Dashboard UI settings
logging:       # Logging configuration
features:      # Feature flags
debug:         # Debug options
production:    # Production optimizations
```

---

## 🎯 Key Design Decisions

1. **SQLite over PostgreSQL**: Simplicity, no external dependencies
2. **React from CDN**: No build step, faster development
3. **WebSocket + REST**: Real-time + standard API
4. **Dark Theme**: Optimized for 24/7 monitoring
5. **Mock Agents**: Fallback for testing without APQC framework
6. **Auto-Reconnect**: Resilient WebSocket connections
7. **Background Tasks**: Non-blocking monitoring
8. **Configuration File**: Easy customization without code changes

---

**Architecture Version**: 1.0.0
**Last Updated**: 2025-11-16
**Status**: Production-Ready ✅
