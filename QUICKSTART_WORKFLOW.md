# 🚀 Quick Start Guide - Visual Workflow Orchestrator

Get started with the Visual Workflow Orchestrator in 5 minutes!

## Prerequisites

- Python 3.8+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection (for CDN resources)

## Installation

No installation required! The workflow orchestrator is already integrated into the APQC Dashboard system.

## Step 1: Start the Backend Server

```bash
cd /home/user/multiAgentStandardsProtocol
python dashboard_server.py
```

Expected output:
```
✅ APQC framework initialized
✅ Workflow engine loaded successfully
🚀 Starting APQC Dashboard Server...
📊 Monitoring X agents across 13 categories
🌐 Dashboard: http://localhost:8765
```

## Step 2: Start the Frontend Server

Open a new terminal:

```bash
cd /home/user/multiAgentStandardsProtocol/dashboard_frontend
python -m http.server 8080
```

## Step 3: Open the Workflow Designer

Open your browser and navigate to:

```
http://localhost:8080/workflow_designer.html
```

You should see the Visual Workflow Designer interface with:
- Agent palette on the left (118+ agents)
- Canvas in the center
- Property panel on the right

## Step 4: Create Your First Workflow

### Option A: Use a Template (Recommended for Beginners)

1. Click the **"Templates"** button in the toolbar
2. Browse the template gallery
3. Click **"Preview"** on any template to see details
4. Click **"Use Template"** to load it into the designer
5. Customize as needed
6. Click **"Save"** to save your workflow

### Option B: Build from Scratch

1. **Search for an agent** in the left palette (e.g., "Financial")
2. **Drag an agent** onto the canvas
3. **Drag another agent** onto the canvas
4. **Connect them** by clicking the connection handles (circles on nodes)
5. **Configure nodes** by clicking on them and using the property panel
6. **Save your workflow** using the toolbar

## Step 5: Test Your Workflow

1. Click the **"Test"** button in the toolbar
2. Provide any required inputs (if prompted)
3. Watch the execution progress
4. Review the results

## Common Workflows to Try

### 1. Financial Analysis Workflow
**Time**: 2 minutes
**Steps**:
1. Search "Financial Resources" in agent palette
2. Drag "Manage Accounting and Financial Reporting" (Category 9.0)
3. Drag "Manage Financial Planning and Budgeting" (Category 9.0)
4. Connect them
5. Save as "My Financial Analysis"

### 2. Cross-Domain Workflow
**Time**: 5 minutes
**Steps**:
1. Use the "Cross-Domain: Strategy → Product → Marketing → Sales" template
2. Customize agent configurations
3. Add additional nodes if needed
4. Save and test

### 3. HR Recruitment Workflow
**Time**: 3 minutes
**Steps**:
1. Use the "HR Recruitment + Skills Gap Analysis" template
2. Review the workflow structure
3. Modify node properties
4. Save as "Custom Recruitment Process"

## Keyboard Shortcuts

- `Ctrl/Cmd + S` - Save workflow
- `Ctrl/Cmd + T` - Show templates
- `Escape` - Deselect node

## API Testing (Optional)

Test the workflow API using curl:

```bash
# List all workflows
curl http://localhost:8765/api/workflows

# List all templates
curl http://localhost:8765/api/workflow-templates

# Get agents
curl http://localhost:8765/api/agents
```

## Demo Script

Run the demo script to see programmatic workflow creation:

```bash
python demo_workflow_orchestrator.py
```

This will demonstrate:
- Creating workflows programmatically
- Using templates
- Executing workflows
- Workflow validation
- Template library features

## Troubleshooting

### Issue: Blank Screen

**Solution**: Check browser console for errors. Verify CDN resources are loading.

```bash
# Check if server is running
curl http://localhost:8765/
curl http://localhost:8080/workflow_designer.html
```

### Issue: Agents Not Loading

**Solution**: Ensure the dashboard server is running and agents are initialized.

```bash
# Check agents endpoint
curl http://localhost:8765/api/agents
```

### Issue: Workflow Won't Save

**Solution**: Check browser console. Verify workflow has valid structure (no cycles, all nodes connected).

## Next Steps

1. **Explore Templates**: Browse all 10+ pre-built templates
2. **Create Custom Workflows**: Build workflows specific to your needs
3. **Integrate with Your Systems**: Use the API to integrate with your applications
4. **Share Workflows**: Export workflows and share with your team

## Resources

- **Full Documentation**: `WORKFLOW_ORCHESTRATOR.md`
- **API Documentation**: See backend API endpoints in documentation
- **Support**: Check troubleshooting section in main documentation

## Example: Complete Workflow Creation

Here's a complete example from start to finish:

```python
# Run this in Python to create a workflow programmatically

import asyncio
from workflow_engine import (
    WorkflowManager,
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    NodePosition,
    NodeType
)

async def create_example_workflow():
    manager = WorkflowManager()

    workflow = WorkflowDefinition(
        id="example_workflow",
        name="Example: Financial Analysis",
        description="Simple financial analysis workflow",
        nodes=[
            WorkflowNode(
                id="node_1",
                type=NodeType.AGENT,
                label="Data Collection",
                position=NodePosition(x=100, y=100),
                agent_id="expert_9_4"
            ),
            WorkflowNode(
                id="node_2",
                type=NodeType.AGENT,
                label="Analysis",
                position=NodePosition(x=400, y=100),
                agent_id="expert_9_2"
            )
        ],
        edges=[
            WorkflowEdge(
                id="edge_1",
                source="node_1",
                target="node_2"
            )
        ]
    )

    workflow_id = manager.create_workflow(workflow)
    execution = await manager.execute_workflow(workflow_id, {})

    print(f"Workflow executed: {execution.status}")
    print(f"Duration: {execution.duration:.2f}s")

asyncio.run(create_example_workflow())
```

## Success!

You're now ready to create powerful cross-domain workflows using the Visual Workflow Orchestrator!

**Happy orchestrating!** 🎯
