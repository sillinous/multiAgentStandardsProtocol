"""
APQC PCF Agent Library

Complete implementation of APQC Process Classification Framework (PCF) agents
with BPMN 2.0 integration for Business Process as a Service (BPaaS).

Key Features:
- 5,000+ business process agents across 13 categories
- BPMN 2.0 model generation
- BPM system integration (Camunda, Activiti, IBM, SAP, etc.)
- Standards-compliant (APQC PCF 7.4)
- Industry variant support
- KPI tracking and APQC benchmarking

Version: 1.0.0
"""

from .base.pcf_base_agent import (
    PCFBaseAgent,
    PCFMetadata,
    PCFAgentConfig,
    KPITracker,
    CategoryAgentBase,
    ProcessGroupAgentBase,
    ProcessAgentBase,
    ActivityAgentBase,
    TaskAgentBase
)

__all__ = [
    'PCFBaseAgent',
    'PCFMetadata',
    'PCFAgentConfig',
    'KPITracker',
    'CategoryAgentBase',
    'ProcessGroupAgentBase',
    'ProcessAgentBase',
    'ActivityAgentBase',
    'TaskAgentBase',
]

__version__ = '1.0.0'
__pcf_version__ = '7.4'
