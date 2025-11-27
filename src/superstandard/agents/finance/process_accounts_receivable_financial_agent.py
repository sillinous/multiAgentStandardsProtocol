"""
ProcessAccountsReceivableFinancialAgent - APQC 8.0 Agent
8.2.2 Process Accounts Receivable
APQC Blueprint ID: apqc_8_0_d5e6f7g8
Version: 1.0.0
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ProcessAccountsReceivableFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_d5e6f7g8"
    apqc_process_id: str = "8.2.2"
    agent_name: str = "process_accounts_receivable_financial_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"
    autonomous_level: float = 0.9
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class ProcessAccountsReceivableFinancialAgent(BaseAgent, ProtocolMixin):
    """
    Skills: aging_analysis: 0.9, dso_calculation: 0.88, payment_prediction: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "8.2.2"

    def __init__(self, config: ProcessAccountsReceivableFinancialAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {"aging_analysis": 0.9, "dso_calculation": 0.88, "payment_prediction": 0.85}
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._process_accounts_receivable(input_data)
            self.state["tasks_processed"] += 1
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    
    async def _process_accounts_receivable(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process accounts_receivable task with AI-powered analysis.

        Implements APQC process: 
        Domain: default

        Uses smart processing for intelligent analysis, recommendations,
        and decision-making capabilities.
        """
        from superstandard.services.smart_processing import get_processor
        from datetime import datetime

        task_type = input_data.get("task_type", "default")
        self.log("info", f"Processing {task_type} task with AI-powered analysis")

        start_time = datetime.now()

        # Get domain-specific smart processor
        processor = get_processor("default")

        # Prepare context for processing
        processing_context = {
            "apqc_process": "",
            "apqc_id": self.APQC_PROCESS_ID,
            "agent_capabilities": self.capabilities_list,
            "input_data": input_data.get("data", {}),
            "task_context": input_data.get("context", {}),
            "priority": input_data.get("priority", "medium"),
        }

        # Execute smart processing
        processing_result = await processor.process(processing_context, task_type)

        # Extract analysis results
        analysis_results = processing_result.get("analysis", {})
        if not analysis_results:
            analysis_results = {
                "status": processing_result.get("status", "completed"),
                "domain": processing_result.get("domain", "default"),
                "insights": processing_result.get("insights", [])
            }

        # Generate recommendations if not provided
        recommendations = []
        if "recommendations" in processing_result:
            recommendations = processing_result["recommendations"]
        elif "optimization_recommendations" in processing_result:
            recommendations = processing_result["optimization_recommendations"]
        elif "resolution_recommendations" in processing_result:
            recommendations = processing_result["resolution_recommendations"]
        else:
            # Generate default recommendations based on analysis
            recommendations = [{
                "type": "process_optimization",
                "priority": "medium",
                "action": "Review analysis results and implement suggested improvements",
                "confidence": 0.75
            }]

        # Make decisions based on context
        decisions = []
        if "decision" in processing_result or "recommendation" in processing_result:
            decisions.append({
                "decision_type": processing_result.get("decision", processing_result.get("recommendation", "proceed")),
                "confidence": processing_result.get("confidence", 0.8),
                "rationale": processing_result.get("reasoning", "Based on AI analysis"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            decisions.append({
                "decision_type": "proceed",
                "confidence": 0.85,
                "rationale": "Analysis complete, proceeding with standard workflow",
                "timestamp": datetime.now().isoformat()
            })

        # Generate artifacts
        artifacts = []
        if input_data.get("generate_report", False):
            artifacts.append({
                "type": "analysis_report",
                "name": f"{self.config.agent_name}_ai_report",
                "format": "json",
                "content_summary": "AI-powered analysis results",
                "generated_at": datetime.now().isoformat()
            })

        # Compute metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = {
            "processing_time_ms": processing_time,
            "ai_powered": True,
            "processor_used": processor.domain,
            "recommendations_count": len(recommendations),
            "decisions_count": len(decisions),
            "confidence_score": decisions[0].get("confidence", 0.8) if decisions else 0.8
        }

        # Generate events
        events = [{
            "event_type": "ai_task_completed",
            "agent_id": self.config.agent_id,
            "apqc_process": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "summary": f"AI-powered processing of {task_type} task completed",
            "ai_enhanced": True
        }]

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "output": {
                "analysis": analysis_results,
                "recommendations": recommendations,
                "decisions": decisions,
                "artifacts": artifacts,
                "metrics": metrics,
                "events": events,
            },
        }

def create_process_accounts_receivable_financial_agent(
    config: Optional[ProcessAccountsReceivableFinancialAgentConfig] = None,
):
    if config is None:
        config = ProcessAccountsReceivableFinancialAgentConfig()
    return ProcessAccountsReceivableFinancialAgent(config)
