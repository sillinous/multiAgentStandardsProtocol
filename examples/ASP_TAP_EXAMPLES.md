# ASP & TAP Protocol Examples

## Overview

This directory contains working demonstrations of the Agent Semantic Protocol (ASP) v1.0 and Temporal Agent Protocol (TAP) v1.0.

## Examples

### 1. ASP Semantic Matching Demo
**File:** `asp_semantic_matching_demo.py`

Demonstrates semantic capability discovery using APQC finance agents:
- Agent registration with ontology references
- Exact semantic type matching
- Partial/fuzzy semantic matching
- Ontology concept alignment
- Schema semantic mapping

**Run:**
```bash
PYTHONPATH=/home/user/multiAgentStandardsProtocol/src:$PYTHONPATH \
  python examples/asp_semantic_matching_demo.py
```

**Expected Output:**
- Registration of 3 APQC finance agents
- Exact match for budget planning capability
- Partial matches for finance-related capabilities
- Ontology alignments with confidence scores

### 2. TAP Time-Travel Debugging Demo
**File:** `tap_time_travel_debug_demo.py`

Demonstrates temporal reasoning for agent debugging:
- Timeline creation and event recording
- Time-travel queries to inspect past states
- Causal chain analysis
- What-if simulations
- Timeline comparison

**Run:**
```bash
PYTHONPATH=/home/user/multiAgentStandardsProtocol/src:$PYTHONPATH \
  python examples/tap_time_travel_debug_demo.py
```

**Expected Output:**
- Simulation of budget planning with error
- Time-travel to inspect state before error
- Causal chain showing root cause
- What-if simulation showing alternative outcome

## Key Features Demonstrated

### ASP (Agent Semantic Protocol)
✓ Ontology-based agent discovery
✓ Semantic type matching (exact, subsumption, partial)
✓ Cross-ontology concept alignment
✓ Schema field mapping
✓ Quality of Service specification
✓ Domain knowledge representation

### TAP (Temporal Agent Protocol)
✓ Time-travel debugging (inspect past states)
✓ Event range queries
✓ Causal chain analysis (root cause identification)
✓ Causal inference (confidence scoring)
✓ What-if simulations (alternative timelines)
✓ Timeline forking and comparison

## Integration Example

Both protocols can be used together:

```python
from superstandard.protocols import SemanticRegistry, TemporalEngine

# ASP: Find agents with budgeting capability
registry = SemanticRegistry()
# ... register agents ...
matches = registry.discover_capabilities(required_capability)

# TAP: Track selected agent's execution
engine = TemporalEngine()
# ... track events ...
state = engine.state_at_time("main", "budget", "2025-11-16T12:00:00Z")
```

## Requirements

- Python 3.8+
- No external dependencies (uses only Python standard library)

## Learn More

- ASP Implementation: `src/superstandard/protocols/asp_v1.py`
- TAP Implementation: `src/superstandard/protocols/tap_v1.py`
- ASP Tests: `tests/protocols/test_asp_v1.py`
- TAP Tests: `tests/protocols/test_tap_v1.py`
- JSON Schemas: `specifications/schemas/`

## Support

For questions or issues, see the implementation summary:
`IMPLEMENTATION_SUMMARY_ASP_TAP.md`
