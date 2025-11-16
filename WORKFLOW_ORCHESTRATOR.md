# 🎯 Visual Workflow Orchestrator - Production-Ready Documentation

## Overview

The Visual Workflow Orchestrator is a production-ready system for drag-and-drop composition of 118+ APQC agents into cross-domain business workflows. It enables business users to create novel value by visually composing agents into custom workflows without writing code.

## Vision Alignment

**Core Principle**: Agents function as employees/departments that can be orchestrated through an intuitive UI to create custom business processes.

**User Value**: Users create workflows by visually connecting specialized APQC agents, enabling:
- Cross-domain process automation
- Custom business process creation
- Real-time workflow execution monitoring
- Template-based rapid deployment

## Architecture

### Backend (FastAPI)

**File**: `workflow_engine.py` (~700 LOC)

#### Components:

1. **Workflow Definition**
   - Node-based workflow representation
   - Support for multiple node types: Agent, Trigger, Condition, Aggregator, Transformer, Output
   - Edge-based data flow between nodes
   - DAG (Directed Acyclic Graph) validation

2. **Workflow Execution Engine**
   - Async execution with topological ordering
   - Parallel node execution where possible
   - State management for running workflows
   - Error handling and recovery
   - Retry logic with configurable policies

3. **State Management**
   - Real-time execution state tracking
   - Node-level status monitoring
   - Input/output data flow tracking
   - Execution metrics collection

4. **Event Streaming**
   - Real-time workflow events
   - WebSocket integration ready
   - Event callbacks for monitoring
   - Audit trail generation

5. **Workflow Templates**
   - 10+ pre-built workflow templates
   - Template library management
   - Template save/load/export
   - Usage statistics tracking

6. **Validation & Testing**
   - Workflow structure validation
   - Cycle detection
   - Connectivity validation
   - Agent availability checking

### Frontend (React/TypeScript)

**Files**:
- `workflow_designer.tsx` (~900 LOC)
- `workflow_templates.tsx` (~300 LOC)
- `workflow_designer.html` (standalone page)

#### Components:

1. **Drag-and-Drop Canvas**
   - Pan and zoom controls
   - Visual node placement
   - Connection drawing
   - Grid background
   - Mini-map (planned)

2. **Agent Palette**
   - 118+ agents organized by 13 APQC categories
   - Searchable agent list
   - Category filtering
   - Agent health indicators
   - Drag-to-canvas functionality

3. **Property Panel**
   - Node configuration
   - Parameter editing
   - Timeout/retry settings
   - Tag management
   - Node deletion

4. **Toolbar**
   - Workflow naming
   - Save/Load operations
   - Export functionality
   - Test execution
   - Template access
   - Clear canvas

5. **Template Gallery**
   - Browse pre-built templates
   - Category filtering
   - Template preview
   - Import templates
   - Usage statistics
   - Rating system

## API Endpoints

### Workflow Management

```
GET    /api/workflows              - List all workflows
GET    /api/workflows/{id}         - Get workflow by ID
POST   /api/workflows              - Create new workflow
PUT    /api/workflows/{id}         - Update workflow
DELETE /api/workflows/{id}         - Delete workflow
```

### Workflow Execution

```
POST   /api/workflows/{id}/execute       - Execute workflow
GET    /api/workflows/executions/{id}    - Get execution status
```

### Templates

```
GET    /api/workflow-templates           - List all templates
GET    /api/workflow-templates/{id}      - Get template by ID
```

### Import/Export

```
POST   /api/workflows/import              - Import workflow (JSON/YAML)
GET    /api/workflows/{id}/export         - Export workflow (JSON/YAML)
```

## Pre-Built Templates

### 1. Financial Close + Marketing ROI Analysis
**Category**: Finance & Marketing
**Difficulty**: Intermediate
**Nodes**: 5
**Agents**: `expert_9_4`, `expert_3_3`, `expert_9_2`

Combines financial closing processes with marketing ROI analysis for comprehensive performance review.

**Use Cases**:
- Quarterly financial review
- Marketing campaign effectiveness
- Budget allocation optimization

---

### 2. Supply Chain + Customer Demand Forecasting
**Category**: Operations
**Difficulty**: Advanced
**Nodes**: 4
**Agents**: `expert_6_3`, `expert_4_1`, `expert_4_2`

Integrates supply chain operations with customer demand forecasting for optimized inventory management.

**Use Cases**:
- Inventory planning
- Supply chain optimization
- Demand response

---

### 3. HR Recruitment + Skills Gap Analysis
**Category**: Human Capital
**Difficulty**: Intermediate
**Nodes**: 5
**Agents**: `expert_7_3`, `expert_1_4`, `expert_7_2`

Combines recruitment processes with skills gap analysis for strategic talent acquisition.

**Use Cases**:
- Strategic hiring
- Skills development planning
- Workforce optimization

---

### 4. Cross-Domain: Strategy → Product → Marketing → Sales
**Category**: Cross-Domain
**Difficulty**: Advanced
**Nodes**: 5
**Agents**: `expert_1_2`, `expert_2_2`, `expert_3_2`, `expert_3_5`

End-to-end workflow from strategic planning through product development, marketing, and sales execution.

**Use Cases**:
- Product launch
- Go-to-market strategy
- Revenue growth initiatives

---

### 5. Customer Support + Product Feedback Loop
**Category**: Customer Experience
**Difficulty**: Intermediate
**Nodes**: 4

Continuous improvement workflow that channels customer feedback into product development.

---

### 6. Risk Assessment + Compliance Monitoring
**Category**: Risk & Compliance
**Difficulty**: Advanced
**Nodes**: 6

Integrated risk and compliance workflow for enterprise governance.

---

### 7. IT Service Management + Asset Optimization
**Category**: IT Operations
**Difficulty**: Intermediate
**Nodes**: 5

Comprehensive IT service and asset management workflow.

---

### 8. Product Launch Pipeline
**Category**: Product Management
**Difficulty**: Advanced
**Nodes**: 7

Complete product launch workflow from concept to market.

---

### 9. Financial Planning + Budget Analysis
**Category**: Finance
**Difficulty**: Intermediate
**Nodes**: 5

Comprehensive financial planning and budgeting workflow.

---

### 10. Employee Onboarding Workflow
**Category**: Human Capital
**Difficulty**: Beginner
**Nodes**: 4

End-to-end employee onboarding process.

## Getting Started

### 1. Start the Backend Server

```bash
# Start the dashboard server with workflow engine
cd /home/user/multiAgentStandardsProtocol
python dashboard_server.py
```

The server will start on `http://localhost:8765`

### 2. Access the Workflow Designer

Open in your browser:
```
http://localhost:8080/workflow_designer.html
```

Or serve the frontend:
```bash
cd dashboard_frontend
python -m http.server 8080
```

### 3. Create Your First Workflow

1. **Drag agents from the palette** onto the canvas
2. **Connect agents** by clicking on connection handles
3. **Configure nodes** using the property panel
4. **Save your workflow** using the toolbar
5. **Test execution** with the test button

## User Scenarios

### Scenario 1: Business User - Financial + Marketing Workflow

**Goal**: Create a custom workflow combining Financial Close with Marketing Campaign analysis

**Steps**:
1. Click "Templates" button
2. Select "Financial Close + Marketing ROI Analysis"
3. Click "Use Template"
4. Customize nodes as needed
5. Save and execute

**Expected Time**: 5 minutes

---

### Scenario 2: Operations User - Supply Chain + Customer Support

**Goal**: Connect Supply Chain agents with Customer Support for proactive issue resolution

**Steps**:
1. Search for "Supply Chain" in agent palette
2. Drag "Plan for and Align Supply Chain Resources" agent
3. Search for "Customer Service"
4. Drag "Measure and Evaluate Customer Service Operations" agent
5. Connect the agents
6. Add data transformation nodes if needed
7. Save and test

**Expected Time**: 10 minutes

---

### Scenario 3: Strategy User - Cross-Domain Process

**Goal**: Build a cross-domain process combining Vision/Strategy with HR and Finance

**Steps**:
1. Start with "Develop Business Strategy" agent (Category 1.0)
2. Add "Develop and Manage HR Strategy" agent (Category 7.0)
3. Add "Develop and Manage Financial Strategy" agent (Category 9.0)
4. Connect in logical order
5. Add aggregator node to combine outputs
6. Configure node properties
7. Save workflow

**Expected Time**: 15 minutes

## Features

### ✅ Implemented

- [x] Drag-and-drop canvas with pan/zoom
- [x] Agent palette with 118+ APQC agents
- [x] 13 category organization
- [x] Node property configuration
- [x] Workflow save/load
- [x] JSON/YAML export
- [x] 10+ pre-built templates
- [x] Template gallery with preview
- [x] Search and filtering
- [x] Backend execution engine
- [x] Workflow validation (DAG, connectivity)
- [x] State management
- [x] Event streaming
- [x] API endpoints
- [x] Error handling

### 🚧 Planned

- [ ] Real-time collaboration (multiplayer editing)
- [ ] Workflow versioning
- [ ] Template marketplace
- [ ] Visual execution debugger
- [ ] Performance analytics
- [ ] A/B testing workflows
- [ ] Workflow scheduling
- [ ] Mobile app
- [ ] AI-assisted workflow suggestions

## Keyboard Shortcuts

- `Ctrl/Cmd + S` - Save workflow
- `Ctrl/Cmd + T` - Show templates
- `Escape` - Deselect node
- `Delete` - Delete selected node (planned)
- `Ctrl/Cmd + Z` - Undo (planned)
- `Ctrl/Cmd + Y` - Redo (planned)

## Integration Guide

### Integrating with Existing Dashboard

Add to `app.tsx`:

```typescript
import { WorkflowDesigner } from './workflow_designer';
import { WorkflowTemplates } from './workflow_templates';

// Add navigation item
<button onClick={() => setView('workflows')}>
  Workflows
</button>

// Add view
{view === 'workflows' && <WorkflowDesigner />}
```

### Using the Backend API

```python
import requests

# Create workflow
workflow = {
    "id": "my_workflow",
    "name": "My Custom Workflow",
    "nodes": [...],
    "edges": [...]
}

response = requests.post(
    "http://localhost:8765/api/workflows",
    json=workflow
)

# Execute workflow
execution = requests.post(
    f"http://localhost:8765/api/workflows/{workflow_id}/execute",
    json={"inputs": {...}}
)

# Monitor execution
status = requests.get(
    f"http://localhost:8765/api/workflows/executions/{execution_id}"
)
```

### Custom Node Types

Extend `NodeType` enum:

```python
class NodeType(str, Enum):
    AGENT = "agent"
    TRIGGER = "trigger"
    # Add your custom type
    CUSTOM = "custom"
```

Implement execution logic:

```python
async def _execute_custom_node(self, node, inputs):
    # Your custom logic
    return result
```

## Performance Considerations

### Backend

- **Async execution**: All workflow execution is async for scalability
- **Parallel nodes**: Nodes execute in parallel when dependencies allow
- **Timeout handling**: Configurable timeouts prevent hanging workflows
- **Resource limits**: Configurable memory/CPU limits per node

### Frontend

- **Virtual scrolling**: Large agent lists use virtual scrolling
- **Lazy loading**: Templates loaded on demand
- **Debounced search**: Search input debounced for performance
- **Memoization**: Heavy computations memoized with React hooks

## Security Considerations

1. **Input Validation**: All workflow definitions validated before execution
2. **Agent Authorization**: Agent access controlled by permissions
3. **Execution Sandboxing**: Workflows run in isolated environments
4. **Rate Limiting**: API endpoints rate-limited to prevent abuse
5. **Audit Logging**: All workflow operations logged for compliance

## Troubleshooting

### Workflow Won't Execute

**Symptoms**: Workflow fails validation

**Solutions**:
- Check for cycles in the workflow graph
- Ensure all nodes are connected
- Verify required agents are available
- Check node configuration

### Frontend Won't Load

**Symptoms**: Blank screen or loading error

**Solutions**:
- Check browser console for errors
- Verify React/Babel CDN links are accessible
- Clear browser cache
- Check network connectivity to backend API

### Template Import Fails

**Symptoms**: Template doesn't appear in designer

**Solutions**:
- Verify JSON/YAML format
- Check all referenced agents exist
- Validate workflow structure
- Check browser console for errors

## Support

For issues and questions:
- GitHub Issues: [Link to repository]
- Documentation: [Link to docs]
- Email: workflow-support@example.com

## License

MIT License - See LICENSE file for details

## Version History

### v1.0.0 (2025-11-16)
- Initial release
- 118+ APQC agents support
- 10 pre-built templates
- Full workflow orchestration engine
- Visual designer with drag-and-drop
- Template gallery
- Import/export functionality
- Real-time execution monitoring

---

**Built with**: FastAPI, React, TypeScript, Pydantic, SQLite
**Total Lines of Code**: ~1,900 LOC
**Production Ready**: Yes ✅
