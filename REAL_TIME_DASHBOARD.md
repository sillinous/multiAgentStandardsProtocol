# 📊 Real-Time Monitoring Dashboard

## Overview

The Real-Time Monitoring Dashboard provides complete operational transparency for the Agentic Standards Protocol's autonomous agent system. Watch agents execute in real-time, see opportunities discovered as they happen, and monitor system health with a beautiful, production-ready interface.

**Access**: Open `dashboard.html` in your browser
**Demo**: Run `python examples/live_dashboard_demo.py`

---

## 🌟 Features

### Live Event Stream
- **Agent Execution** - See when agents start and complete tasks
- **Opportunity Discovery** - Watch business opportunities being discovered
- **Synthesis Phases** - Monitor cross-agent data synthesis
- **Quality Scores** - Track data quality in real-time
- **Errors** - Immediate visibility into any issues
- **System Health** - CPU, memory, active agents, uptime

### Real-Time Metrics
- **Total Events** - All system events counted
- **Agents Executed** - Production agents run
- **Opportunities Found** - Business opportunities discovered
- **Avg Quality Score** - Data quality across all agents
- **Active Agents** - Currently running agents
- **System Uptime** - Time since startup

### Opportunity Cards
- **Visual Cards** - Beautiful cards for each opportunity
- **Confidence Scoring** - Color-coded confidence levels
- **Revenue Potential** - Estimated revenue ranges
- **Category Tags** - Categorized opportunities
- **Auto-Discovery** - New cards appear as opportunities are found

### Beautiful UI
- **Dark Theme** - Optimized for 24/7 monitoring
- **Smooth Animations** - Slide-in effects for new events
- **Responsive Grid** - Adapts to any screen size
- **Color-Coded** - Event severity and confidence levels
- **Live Connection** - Visual indicator of connection status

---

## 🚀 Quick Start

### 1. Run the Live Demo

```bash
# From project root
python examples/live_dashboard_demo.py
```

**Choose a demo mode:**
- **1. Single Scenario** - Technology in United States (quickest)
- **2. Multiple Scenarios** - Tech, Healthcare, Financial Services
- **3. Custom Scenario** - Enter your own parameters

The demo will:
1. ✅ Run autonomous opportunity discovery
2. ✅ Broadcast events in real-time
3. ✅ Export data to `dashboard_data.json`
4. ✅ Auto-open `dashboard.html` in your browser

### 2. View the Dashboard

The dashboard will automatically open in your browser, or you can open it manually:

```bash
# Just open dashboard.html in any browser
open dashboard.html  # macOS
xdg-open dashboard.html  # Linux
start dashboard.html  # Windows
```

### 3. See Real-Time Updates

As the demo runs, you'll see:
- 📡 Events appearing in the live stream
- 📈 Metrics updating in real-time
- 💡 Opportunity cards being created
- ✅ Quality scores for each agent
- ⏱️ Agent execution times

---

## 📖 Architecture

### Event Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomous Agents                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Competitor│ │Economics │ │Demograph.│ │ Research │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │              │             │           │
└───────┼────────────┼──────────────┼─────────────┼───────────┘
        │            │              │             │
        └────────────┴──────┬───────┴─────────────┘
                            │
                     ┌──────▼───────┐
                     │ Orchestrator │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │  Dashboard   │
                     │    State     │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────▼──────┐ ┌───▼────┐ ┌─────▼─────┐
       │   Events    │ │Metrics │ │Opportun.  │
       │   History   │ │        │ │  Storage  │
       └──────┬──────┘ └───┬────┘ └─────┬─────┘
              │            │             │
              └────────────┴──────┬──────┘
                                  │
                          ┌───────▼────────┐
                          │  Export to     │
                          │dashboard_data  │
                          │     .json      │
                          └───────┬────────┘
                                  │
                          ┌───────▼────────┐
                          │  Browser       │
                          │  Dashboard     │
                          │  (HTML/JS)     │
                          └────────────────┘
```

### Key Components

#### 1. **DashboardState** (`src/superstandard/monitoring/dashboard.py`)

Central hub for all real-time monitoring:

```python
from src.superstandard.monitoring.dashboard import get_dashboard

# Get global dashboard instance
dashboard = get_dashboard()

# Broadcast events
await dashboard.agent_started(
    agent_id="agent-123",
    agent_name="IdentifyCompetitorsAgent",
    task_description="Analyzing competitive landscape"
)

await dashboard.agent_completed(
    agent_id="agent-123",
    agent_name="IdentifyCompetitorsAgent",
    task_description="Analyzing competitive landscape",
    duration_ms=1234.5,
    success=True,
    quality_score=98.5
)

await dashboard.opportunity_discovered(
    opportunity_id="opp-001",
    title="AI-Powered Market Research Platform",
    description="Strong demand for automated market research...",
    confidence_score=0.89,
    revenue_potential="$500K-$2M ARR",
    category="SaaS Product"
)
```

#### 2. **OpportunityDiscoveryOrchestrator** (Integrated)

The orchestrator automatically broadcasts events throughout the discovery process:

```python
from src.superstandard.orchestration.opportunity_discovery import (
    OpportunityDiscoveryOrchestrator
)
from src.superstandard.monitoring.dashboard import get_dashboard

# Create orchestrator with dashboard
dashboard = get_dashboard()
orchestrator = OpportunityDiscoveryOrchestrator(
    dashboard_state=dashboard
)

# Discovery automatically broadcasts events
opportunities = await orchestrator.discover_opportunities(
    industry="technology",
    geography="United States",
    min_confidence=0.75
)
```

#### 3. **Dashboard HTML** (`dashboard.html`)

Browser-based visualization with:
- Real-time event rendering
- Metrics display
- Opportunity cards
- Connection status
- Auto-load exported data

---

## 📋 Event Types

The dashboard supports these event types:

### Agent Events

**agent_execution_started**
```python
await dashboard.agent_started(
    agent_id="agent-123",
    agent_name="IdentifyCompetitorsAgent",
    task_description="Analyzing competitive landscape"
)
```

**agent_execution_completed**
```python
await dashboard.agent_completed(
    agent_id="agent-123",
    agent_name="IdentifyCompetitorsAgent",
    task_description="Analyzing competitive landscape",
    duration_ms=1234.5,
    success=True,
    data_source="SimilarWeb API",
    quality_score=98.5
)
```

### Discovery Events

**opportunity_discovered**
```python
await dashboard.opportunity_discovered(
    opportunity_id="opp-001",
    title="AI-Powered Market Research Platform",
    description="Strong demand for automated market research tools...",
    confidence_score=0.89,
    revenue_potential="$500K-$2M ARR",
    category="SaaS Product"
)
```

### Synthesis Events

**synthesis_started**
```python
await dashboard.synthesis_started(
    phase="Data Collection",
    description="Executing 4 agents in parallel"
)
```

**synthesis_completed**
```python
await dashboard.synthesis_completed(
    phase="Cross-Agent Synthesis",
    duration_ms=2500,
    patterns_found=12
)
```

### Quality Events

**quality_score_updated**
```python
await dashboard.quality_score_updated(
    source="OpportunityDiscovery",
    overall_score=97.3,
    dimension_scores={
        "accuracy": 98.5,
        "completeness": 96.0,
        "timeliness": 99.0,
        "consistency": 97.0,
        "validity": 98.0,
        "uniqueness": 95.5
    }
)
```

### System Events

**system_health_updated**
```python
await dashboard.system_health_updated(
    cpu_percent=15.0,
    memory_percent=45.0,
    active_agents=4
)
```

**error_occurred**
```python
await dashboard.error_occurred(
    source="IdentifyCompetitorsAgent",
    error_message="API rate limit exceeded",
    error_type="RateLimitError"
)
```

---

## 🎯 Use Cases

### 1. Development & Debugging

**Watch your agents in real-time:**
```bash
# Run discovery with dashboard
python examples/live_dashboard_demo.py

# Open dashboard.html in browser
# See exactly what each agent is doing
# Identify bottlenecks
# Debug quality issues
```

### 2. Stakeholder Demos

**Show autonomous operations:**
- Beautiful, professional UI
- Real-time visualization
- Impressive opportunity discovery
- Production-ready quality monitoring

### 3. Production Monitoring

**24/7 operational visibility:**
- System health monitoring
- Error tracking
- Performance metrics
- Quality assurance

### 4. Integration Testing

**Verify multi-agent collaboration:**
- See agent execution order
- Monitor synthesis phases
- Validate opportunity extraction
- Check quality scores

---

## 📊 Dashboard Metrics

### Total Events
Total number of events broadcast by the system.

### Agents Executed
Number of production agents that have completed execution.

### Opportunities Found
Total business opportunities discovered.

### Avg Quality Score
Average data quality score across all agent executions (6-dimension framework).

### Active Agents
Number of agents currently running.

### System Uptime
Time since the dashboard was initialized.

---

## 🔧 Configuration

### Dashboard State Configuration

```python
from src.superstandard.monitoring.dashboard import DashboardState

# Custom history size
dashboard = DashboardState(max_history=200)  # Default: 100

# Access metrics
stats = dashboard.get_dashboard_stats()
print(f"Total events: {stats['metrics']['total_events']}")

# Get recent events
recent = dashboard.get_recent_events(limit=20)

# Get opportunities
opportunities = dashboard.get_opportunities()
```

### HTML Dashboard Configuration

Edit `dashboard.html` JavaScript:

```javascript
const config = {
    simulateEvents: false,  // Set to false for live data
    maxEvents: 100,         // Max events to display
    dataFile: 'dashboard_data.json'  // Exported data file
};
```

---

## 📁 File Structure

```
multiAgentStandardsProtocol/
├── dashboard.html                          # Dashboard UI
├── dashboard_data.json                     # Exported data (generated)
├── src/superstandard/monitoring/
│   ├── __init__.py
│   └── dashboard.py                        # Dashboard state & events
├── src/superstandard/orchestration/
│   └── opportunity_discovery.py            # Integrated with dashboard
└── examples/
    ├── live_dashboard_demo.py              # Live demo script
    └── autonomous_opportunity_discovery_demo.py  # Original demo
```

---

## 🎨 Customization

### Color Themes

Edit CSS in `dashboard.html`:

```css
/* Event severity colors */
.event-item.success { border-left-color: #4caf50; }  /* Green */
.event-item.warning { border-left-color: #ff9800; }  /* Orange */
.event-item.error { border-left-color: #f44336; }    /* Red */
.event-item { border-left-color: #667eea; }          /* Blue (default) */

/* Confidence colors */
.confidence-high { color: #4caf50; }    /* >= 80% */
.confidence-medium { color: #ff9800; }  /* 60-80% */
.confidence-low { color: #f44336; }     /* < 60% */
```

### Animation Speed

```css
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Adjust duration (currently 0.3s) */
.event-item {
    animation: slideIn 0.3s ease;
}
```

---

## 🚀 Advanced Usage

### WebSocket Integration (Production)

For production real-time updates, implement WebSocket:

```javascript
function connectWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data);
    };

    ws.onopen = () => {
        updateConnectionStatus(true);
        console.log('WebSocket connected');
    };

    ws.onclose = () => {
        updateConnectionStatus(false);
        console.log('WebSocket disconnected');
        // Implement reconnection logic
        setTimeout(connectWebSocket, 5000);
    };
}
```

### REST API Integration

```javascript
async function pollEvents() {
    try {
        const response = await fetch('/api/dashboard/events?since=' + lastEventId);
        const events = await response.json();

        events.forEach(event => handleEvent(event));

        if (events.length > 0) {
            lastEventId = events[events.length - 1].event_id;
        }
    } catch (error) {
        console.error('Failed to poll events:', error);
    }

    setTimeout(pollEvents, 1000);  // Poll every second
}
```

### Custom Event Handlers

```javascript
function handleEvent(event) {
    // Custom logic before standard handling
    if (event.event_type === 'opportunity_discovered') {
        // Custom notification
        if (event.data.confidence_score >= 0.9) {
            showNotification('High-confidence opportunity discovered!');
        }
    }

    // Standard handling
    state.events.unshift(event);
    // ... rest of standard logic
}
```

---

## 🎯 Best Practices

### 1. Event Broadcasting

**DO:**
- ✅ Broadcast at key milestones (start, complete, errors)
- ✅ Include relevant context (agent name, duration, scores)
- ✅ Use appropriate severity levels
- ✅ Keep descriptions concise but informative

**DON'T:**
- ❌ Broadcast too frequently (avoid spam)
- ❌ Include sensitive data in events
- ❌ Block on dashboard operations (use async)
- ❌ Forget to handle errors in broadcasts

### 2. Data Export

**Export regularly:**
```python
# After major operations
await demo.export_dashboard_state()
```

**Use for:**
- Offline analysis
- Debugging
- Sharing results
- Audit trails

### 3. Performance

**Optimize event handling:**
- Limit event history (default: 100)
- Use appropriate polling intervals
- Implement event batching for high-frequency updates
- Clean up old opportunities periodically

---

## 📈 Metrics & Analytics

### Export Dashboard Metrics

```python
from src.superstandard.monitoring.dashboard import get_dashboard

dashboard = get_dashboard()
stats = dashboard.get_dashboard_stats()

print(f"""
Dashboard Statistics:
- Total Events: {stats['metrics']['total_events']}
- Agents Executed: {stats['metrics']['total_agents_executed']}
- Opportunities: {stats['metrics']['total_opportunities_discovered']}
- Avg Quality: {stats['metrics']['avg_quality_score']:.1f}%
- Uptime: {stats['system_uptime_seconds']:.0f}s
""")
```

### Analyze Event History

```python
dashboard = get_dashboard()

# Get recent events
events = dashboard.get_recent_events(limit=100)

# Filter by type
agent_events = [e for e in events if e['event_type'] == 'agent_execution_completed']

# Calculate average duration
avg_duration = sum(e['data']['duration_ms'] for e in agent_events) / len(agent_events)
print(f"Average agent duration: {avg_duration:.0f}ms")

# Quality analysis
quality_scores = [e['data']['quality_score'] for e in agent_events if 'quality_score' in e['data']]
print(f"Quality scores: min={min(quality_scores):.1f}, max={max(quality_scores):.1f}")
```

---

## 🎉 Success Criteria

The Real-Time Dashboard is successful when:

- ✅ **Operational Transparency** - Every autonomous operation is visible
- ✅ **Real-Time Updates** - Events appear instantly (< 1s latency)
- ✅ **Beautiful UI** - Professional, production-ready interface
- ✅ **Comprehensive Metrics** - All key metrics tracked and displayed
- ✅ **Error Visibility** - Issues immediately visible
- ✅ **Demo-Ready** - Impresses stakeholders
- ✅ **Production-Ready** - Can be deployed for 24/7 monitoring

---

## 🤝 Integration Examples

### Integrate with Your Agent

```python
from src.superstandard.monitoring.dashboard import get_dashboard

class MyCustomAgent(ActivityAgentBase):
    def __init__(self):
        super().__init__()
        self.dashboard = get_dashboard()

    async def execute(self, input_data):
        agent_id = f"agent-{id(self)}"

        # Broadcast start
        await self.dashboard.agent_started(
            agent_id=agent_id,
            agent_name=self.__class__.__name__,
            task_description=input_data.get('task', 'Custom task')
        )

        try:
            # Your agent logic
            result = await self._do_work(input_data)

            # Broadcast completion
            await self.dashboard.agent_completed(
                agent_id=agent_id,
                agent_name=self.__class__.__name__,
                task_description=input_data.get('task', 'Custom task'),
                duration_ms=1000,  # Calculate actual duration
                success=True,
                quality_score=95.0  # Your quality metric
            )

            return result

        except Exception as e:
            # Broadcast error
            await self.dashboard.error_occurred(
                source=self.__class__.__name__,
                error_message=str(e),
                error_type=type(e).__name__
            )
            raise
```

---

## 📚 Learn More

- **Opportunity Discovery**: See `AUTONOMOUS_BUSINESS_OPPORTUNITY_DISCOVERY.md`
- **Production Agents**: See agent files in `src/superstandard/agents/pcf/`
- **Services**: See `src/superstandard/services/`
- **Quality Framework**: 6-dimension quality assessment in agents

---

## 🎊 Conclusion

The Real-Time Monitoring Dashboard transforms the Agentic Standards Protocol from a "black box" autonomous system into a **transparent, observable, production-ready platform**.

**You can now:**
- 👀 **See** what your autonomous agents are doing
- 📊 **Monitor** system health and performance
- 💡 **Discover** opportunities in real-time
- ✅ **Validate** quality at every step
- 🎯 **Demo** to stakeholders with confidence

**This is the future of autonomous AI systems** - transparent, trustworthy, and production-ready.

---

**Built with ❤️ by the Agentic Standards Protocol Team**

For questions or support, see the main project documentation.
