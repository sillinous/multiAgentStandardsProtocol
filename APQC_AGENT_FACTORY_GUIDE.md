# 🏭 APQC Agent Factory - Complete Guide

## Overview

The APQC Agent Factory is a **UI-driven system** for managing and generating ~840 atomic agents based on the complete APQC Process Classification Framework (PCF®) hierarchy.

**Core Principle**: Everything is configurable through the frontend UI - no manual coding, no file editing required.

## What This System Does

### Business User Perspective

- **Browse** the complete APQC PCF hierarchy (13 categories, 5 levels deep)
- **Configure** each atomic agent through an intuitive UI
- **Customize** agent behavior, resources, and integrations
- **Generate** agents on-demand or in bulk
- **Manage** the entire agentic ecosystem visually

### Admin User Perspective

- **Control** all system configuration through the dashboard
- **Monitor** agent generation status
- **Manage** API keys and integrations for each agent
- **Define** custom parameters per agent
- **Export/Import** configurations as templates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  APQC Hierarchy Explorer Component                   │   │
│  │  - 5-level tree visualization                        │   │
│  │  - Agent configuration panels                        │   │
│  │  - Real-time updates                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   REST API (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  APQC Factory API Server (apqc_factory_server.py)   │   │
│  │  - GET/PUT /api/apqc/tasks                          │   │
│  │  - POST /api/apqc/generate                          │   │
│  │  - GET /api/apqc/stats                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (Python Agent Factory)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  APQCAgentFactory (apqc_agent_factory.py)           │   │
│  │  ├─ APQCHierarchyParser                             │   │
│  │  ├─ AgentConfigurationDB (SQLite)                   │   │
│  │  └─ APQCAgentGenerator (Jinja2 templates)           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Generated Agents                           │
│  generated_agents/                                           │
│  ├── strategy/                                               │
│  │   ├── analyze_competition_strategy_agent.py              │
│  │   ├── forecast_demand_strategy_agent.py                  │
│  │   └── ...                                                 │
│  ├── finance/                                                │
│  │   ├── calculate_gross_pay_financial_agent.py             │
│  │   ├── process_invoices_financial_agent.py                │
│  │   └── ...                                                 │
│  └── ...                                                      │
│      (~840 atomic agents organized by domain)                │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. APQC PCF Complete Hierarchy (`APQC_PCF_COMPLETE_HIERARCHY.md`)

**What it is**: Complete 5-level mapping of the APQC Process Classification Framework

**Structure**:
- **Level 1**: 13 Operating Categories
- **Level 2**: ~50 Process Groups
- **Level 3**: ~150 Processes
- **Level 4**: ~500 Activities
- **Level 5**: ~840 Tasks (atomic agents)

**Example**:
```
Category 1: Develop Vision and Strategy (1.0)
  └─ 1.1 Define the Business Concept and Long-term Vision
      └─ 1.1.1 Assess the External Environment
          └─ 1.1.1.1 Analyze and evaluate competition  ← ATOMIC AGENT
```

### 2. Agent Factory Backend (`apqc_agent_factory.py`)

**What it does**: Core Python system for parsing hierarchy, managing configurations, and generating agents

**Classes**:

#### `APQCTask` (dataclass)
Represents a Level 5 APQC task with all configuration:
- APQC metadata (level1_id through level5_name)
- Agent identification (agent_id, agent_name, class_name)
- Configuration (enabled, priority, autonomous_level, etc.)
- Resources (compute_mode, memory_mode, api_budget_mode)
- Integrations (API keys, external systems)
- Custom parameters (user-defined through UI)

#### `APQCHierarchyParser`
Parses `APQC_PCF_COMPLETE_HIERARCHY.md` and extracts all ~840 Level 5 tasks

Methods:
- `parse()` - Extract all tasks from markdown
- `_generate_agent_id()` - Create unique agent IDs
- `_generate_agent_name()` - Generate clean snake_case names
- `_to_pascal_case()` - Convert to PascalCase class names

#### `AgentConfigurationDB`
SQLite database for storing all agent configurations

Tables:
- `agent_configs` - All configuration data
- `generated_agents` - Generation history

Methods:
- `save_task_config(task)` - Persist configuration
- `get_all_configs()` - Retrieve all configs
- `get_config_by_id(agent_id)` - Get specific config
- `update_config(agent_id, updates)` - Update from UI

#### `APQCAgentGenerator`
Generates agent code using Jinja2 templates

Methods:
- `generate_agent(agent_id)` - Generate single agent
- `generate_all(category_id=None)` - Bulk generation

Template variables:
- All APQCTask fields
- Generated timestamp
- Custom configuration

#### `APQCAgentFactory`
Main orchestrator combining all components

Methods:
- `initialize_from_hierarchy()` - Parse and populate database
- `get_hierarchy_summary()` - Get statistics

### 3. API Server (`apqc_factory_server.py`)

**What it does**: FastAPI server providing REST API for the factory

**Port**: 8765

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/apqc/tasks` | GET | List all task configurations |
| `/api/apqc/tasks/{agent_id}` | GET | Get specific configuration |
| `/api/apqc/tasks/{agent_id}` | PUT | Update configuration (from UI) |
| `/api/apqc/generate/{agent_id}` | POST | Generate single agent |
| `/api/apqc/generate-all` | POST | Generate all enabled agents |
| `/api/apqc/generate-category/{category_id}` | POST | Generate category agents |
| `/api/apqc/stats` | GET | Get hierarchy statistics |
| `/api/apqc/initialize` | POST | Initialize from hierarchy file |
| `/api/health` | GET | Health check |
| `/apqc` | GET | Serve APQC explorer UI |

### 4. Frontend Explorer (`dashboard_frontend/apqc_hierarchy_explorer.tsx`)

**What it is**: React component for visual hierarchy exploration and configuration

**Features**:
- **Interactive Tree**: Expand/collapse 5-level hierarchy
- **Search & Filter**: Find tasks by name, ID, category, status
- **Configuration Panel**: Edit all agent parameters through UI
- **Real-time Stats**: Live dashboard of agent counts, categories
- **Bulk Operations**: Generate all agents or by category
- **Agent Status**: Visual indicators (enabled/disabled)

**UI Elements**:
- 🎯 Category nodes (Level 1)
- 📂 Process group nodes (Level 2)
- 📄 Process nodes (Level 3)
- 📋 Activity nodes (Level 4)
- ⚙️ Task/Agent nodes (Level 5) - clickable for configuration

**Configuration Options** (all editable through UI):
- ✅ Enabled/Disabled toggle
- 🔢 Priority (low, normal, high, critical)
- 🤖 Autonomous Level (0.0 - 1.0 slider)
- 🧠 Learning Enabled checkbox
- 💻 Compute Mode (minimal, standard, intensive)
- 💾 Memory Mode (minimal, standard, large)
- 💰 API Budget Mode
- 🔑 Required API Keys (multi-select)
- 🔌 Integrations (multi-select)
- 🛠️ Custom Parameters (key-value editor)

## Quick Start

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn jinja2 pydantic
```

### Step 2: Initialize Database

```bash
# Option A: Via CLI
python apqc_agent_factory.py --init

# Option B: Via API (after starting server)
curl -X POST http://localhost:8765/api/apqc/initialize
```

**Output**:
```
✅ Initialized 840 agent configurations from APQC hierarchy
📊 Total: 840 agents
```

### Step 3: Start API Server

```bash
python apqc_factory_server.py
```

**Server logs**:
```
============================================================
🏭 APQC Agent Factory API Server
============================================================
📊 Version: 1.0.0
🌐 API Docs: http://localhost:8765/docs
🎯 APQC Explorer: http://localhost:8765/apqc
💡 Configure all ~840 APQC agents through the UI!
============================================================
✅ Database ready: 840 tasks configured
```

### Step 4: Open APQC Explorer UI

Navigate to: **http://localhost:8765/apqc**

You'll see:
- Complete APQC hierarchy tree (all 5 levels)
- 840 configurable agents
- Stats dashboard
- Search and filter controls

### Step 5: Configure an Agent

1. **Expand** hierarchy tree to find a task (e.g., "1.1.1.1 Analyze and evaluate competition")
2. **Click** on the task name
3. **Configure** in the right panel:
   - Toggle enabled/disabled
   - Set priority
   - Adjust autonomous level
   - Enable/disable learning
   - Set resource modes
   - Add API keys/integrations
4. **Click** "💾 Save Configuration"
5. **Click** "🚀 Generate Agent"

**Result**: Python agent file generated at `generated_agents/strategy/analyze_competition_strategy_agent.py`

### Step 6: Bulk Generate Agents

**Option A - Generate All**:
```bash
# Via UI: Click "🚀 Generate All Agents" button
# Or via API:
curl -X POST http://localhost:8765/api/apqc/generate-all
```

**Option B - Generate by Category**:
```bash
# Via API:
curl -X POST http://localhost:8765/api/apqc/generate-category/1.0
```

**Output**:
```json
{
  "total": 80,
  "generated": 78,
  "failed": 2,
  "failures": [...]
}
```

## Generated Agent Structure

Every generated agent follows this template:

```python
"""
AnalyzeCompetitionStrategyAgent - APQC 1.0 Agent

Analyze and evaluate competition

Category: 1.0 - Develop Vision and Strategy
Process: 1.1.1 - Assess the External Environment
Task: 1.1.1.1 - Analyze and evaluate competition

All configuration managed through UI.
"""

from dataclasses import dataclass
from typing import Dict, Any
from superstandard.agents.base.base_agent import BaseAgent

@dataclass
class AnalyzeCompetitionStrategyAgentConfig:
    """Configuration (UI-managed)"""
    apqc_level5_id: str = "1.1.1.1"
    apqc_level5_name: str = "Analyze and evaluate competition"
    # ... all UI-configured parameters

class AnalyzeCompetitionStrategyAgent(BaseAgent):
    """Atomic APQC Agent"""

    async def execute(self, task: str, context: Dict[str, Any] = None):
        """Execute APQC task: Analyze and evaluate competition"""
        # Implementation
        pass
```

## UI Configuration Workflow

### For Business Users

1. **Browse** APQC hierarchy to find relevant processes
2. **Enable/Disable** agents based on business needs
3. **Adjust** autonomy levels for each agent
4. **Configure** integrations (CRM, ERP, etc.)
5. **Generate** agents for immediate use
6. **Monitor** agent status through dashboard

### For Admin Users

1. **Manage** all ~840 agent configurations
2. **Define** API keys and credentials per agent
3. **Set** resource allocation (compute, memory, budget)
4. **Create** configuration templates
5. **Export** configurations for backup
6. **Import** configurations across environments
7. **Audit** configuration changes

## Advanced Features

### Custom Parameters

Add agent-specific parameters through the UI:

```json
{
  "custom_config": {
    "competitor_sources": ["bloomberg", "crunchbase", "pitchbook"],
    "analysis_depth": "comprehensive",
    "update_frequency": "daily",
    "alert_threshold": 0.8
  }
}
```

These become part of the agent's configuration dataclass.

### Integration Management

Configure required integrations per agent:

```json
{
  "requires_api_keys": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
  "integrations": ["salesforce", "hubspot", "google_analytics"]
}
```

### Bulk Operations

**Enable all agents in a category**:
```python
# Via API
PUT /api/apqc/tasks/bulk-update
{
  "filter": {"level1_id": "9.0"},
  "updates": {"enabled": true}
}
```

**Set priority for financial agents**:
```python
PUT /api/apqc/tasks/bulk-update
{
  "filter": {"domain": "finance"},
  "updates": {"priority": "high"}
}
```

## Database Schema

### `agent_configs` Table

```sql
CREATE TABLE agent_configs (
    agent_id TEXT PRIMARY KEY,
    level5_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    agent_class_name TEXT NOT NULL,
    level1_id TEXT,
    level1_name TEXT,
    level2_id TEXT,
    level2_name TEXT,
    level3_id TEXT,
    level3_name TEXT,
    level4_id TEXT,
    level4_name TEXT,
    level5_name TEXT,
    domain TEXT,
    description TEXT,
    enabled BOOLEAN DEFAULT 1,
    priority TEXT DEFAULT 'normal',
    autonomous_level REAL DEFAULT 0.7,
    collaboration_mode TEXT DEFAULT 'cooperative',
    learning_enabled BOOLEAN DEFAULT 1,
    compute_mode TEXT DEFAULT 'standard',
    memory_mode TEXT DEFAULT 'standard',
    api_budget_mode TEXT DEFAULT 'standard',
    requires_api_keys TEXT,  -- JSON array
    integrations TEXT,        -- JSON array
    custom_config TEXT,       -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## CLI Interface

```bash
# Initialize from hierarchy
python apqc_agent_factory.py --init

# Show summary
python apqc_agent_factory.py --summary

# List all agents
python apqc_agent_factory.py --list

# Generate single agent
python apqc_agent_factory.py --generate apqc_1_1_1_1_xxxx

# Generate all agents
python apqc_agent_factory.py --generate-all

# Generate category
python apqc_agent_factory.py --generate-category 1.0
```

## Statistics and Reporting

**Hierarchy Summary** (`/api/apqc/stats`):

```json
{
  "total_agents": 840,
  "by_category": {
    "Develop Vision and Strategy": 80,
    "Develop and Manage Products and Services": 40,
    "Market and Sell Products and Services": 70,
    "Deliver Physical Products": 90,
    "Deliver Services": 30,
    "Manage Customer Service": 40,
    "Manage Human Capital": 100,
    "Manage Information Technology": 70,
    "Manage Financial Resources": 110,
    "Acquire, Construct, and Manage Assets": 60,
    "Manage Enterprise Risk, Compliance, and Governance": 50,
    "Manage External Relationships": 40,
    "Develop and Manage Business Capabilities": 60
  },
  "categories": [...]
}
```

## Benefits

### Operational

- **Zero-code Configuration**: Business users manage agents without coding
- **Instant Generation**: Agents generated on-demand in seconds
- **Version Control Ready**: Generated code is clean, documented Python
- **Audit Trail**: All configuration changes tracked in database
- **Reproducible**: Export/import configurations across environments

### Business

- **Complete Coverage**: All ~840 APQC processes covered
- **Customizable**: Each agent configurable to business needs
- **Scalable**: Generate 1 or 840 agents with same UI
- **Transparent**: Visual hierarchy shows entire APQC framework
- **Accessible**: No technical skills required for configuration

### Technical

- **Standards-Compliant**: All agents follow architectural standards
- **Atomic**: Each agent has single responsibility (Level 5 task)
- **Composable**: Agents can be orchestrated into workflows
- **Redeployable**: Environment-based configuration
- **Vendor-Agnostic**: No vendor lock-in
- **Testable**: Generated code includes test scaffolding

## Troubleshooting

### "No tasks configured"

**Solution**: Run initialization:
```bash
python apqc_agent_factory.py --init
```

### "Template generation failed"

**Check**: Jinja2 installed:
```bash
pip install jinja2
```

### "Agent file already exists"

**Solution**: The generator overwrites existing files by default. This is intentional to support regeneration with updated configurations.

### UI not loading

**Check**:
1. Server running on port 8765
2. Frontend files in `dashboard_frontend/` directory
3. Browser console for JavaScript errors

## Next Steps

1. **Configure Agents**: Use UI to customize agents for your business
2. **Generate Agents**: Create Python agents for enabled tasks
3. **Build Workflows**: Use workflow designer to compose agents
4. **Integrate Systems**: Connect agents to CRM, ERP, etc.
5. **Deploy**: Use generated agents in production

---

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Framework**: APQC PCF 7.0.1

**Note**: All features are UI-driven. No manual file editing required!
