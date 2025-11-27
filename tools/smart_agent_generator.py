#!/usr/bin/env python3
"""
Smart Agent Generator with AI Integration
==========================================

Generates intelligent agent implementations that leverage the AI service
and smart processing capabilities.

This is an enhanced version of agent_generator.py that creates agents
with AI-powered business logic.

Usage:
    python tools/smart_agent_generator.py --file <agent_file.py>
    python tools/smart_agent_generator.py --directory src/superstandard/agents/api/
    python tools/smart_agent_generator.py --all --dry-run
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentMetadata:
    """Extracted metadata from a stub agent file"""
    file_path: str
    agent_name: str
    agent_type: str
    domain: str
    apqc_category_id: str
    apqc_category_name: str
    apqc_process_id: str
    apqc_process_name: str
    capabilities: List[str]
    skills: Dict[str, float]
    inputs: List[str]
    outputs: List[str]
    process_method_name: str


# Map domains to processor classes
DOMAIN_PROCESSOR_MAP = {
    "finance": "FinanceProcessor",
    "financial": "FinanceProcessor",
    "accounting": "FinanceProcessor",
    "hr": "HRProcessor",
    "hr_management": "HRProcessor",
    "human_resources": "HRProcessor",
    "human_capital": "HRProcessor",
    "operations": "OperationsProcessor",
    "manufacturing": "OperationsProcessor",
    "logistics": "OperationsProcessor",
    "manufacturing_logistics": "OperationsProcessor",
    "supply_chain": "OperationsProcessor",
    "customer_service": "CustomerServiceProcessor",
    "customer": "CustomerServiceProcessor",
    "sales": "CustomerServiceProcessor",
    "marketing": "CustomerServiceProcessor",
    "it": "ITProcessor",
    "it_management": "ITProcessor",
    "technology": "ITProcessor",
}

# Smart processing implementation template
SMART_IMPLEMENTATION_TEMPLATE = '''
    async def {method_name}(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process {agent_type} task with AI-powered analysis.

        Implements APQC process: {apqc_process_name}
        Domain: {domain}

        Uses smart processing for intelligent analysis, recommendations,
        and decision-making capabilities.
        """
        from superstandard.services.smart_processing import get_processor
        from datetime import datetime

        task_type = input_data.get("task_type", "default")
        self.log("info", f"Processing {{task_type}} task with AI-powered analysis")

        start_time = datetime.now()

        # Get domain-specific smart processor
        processor = get_processor("{domain}")

        # Prepare context for processing
        processing_context = {{
            "apqc_process": "{apqc_process_name}",
            "apqc_id": self.APQC_PROCESS_ID,
            "agent_capabilities": self.capabilities_list,
            "input_data": input_data.get("data", {{}}),
            "task_context": input_data.get("context", {{}}),
            "priority": input_data.get("priority", "medium"),
        }}

        # Execute smart processing
        processing_result = await processor.process(processing_context, task_type)

        # Extract analysis results
        analysis_results = processing_result.get("analysis", {{}})
        if not analysis_results:
            analysis_results = {{
                "status": processing_result.get("status", "completed"),
                "domain": processing_result.get("domain", "{domain}"),
                "insights": processing_result.get("insights", [])
            }}

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
            recommendations = [{{
                "type": "process_optimization",
                "priority": "medium",
                "action": "Review analysis results and implement suggested improvements",
                "confidence": 0.75
            }}]

        # Make decisions based on context
        decisions = []
        if "decision" in processing_result or "recommendation" in processing_result:
            decisions.append({{
                "decision_type": processing_result.get("decision", processing_result.get("recommendation", "proceed")),
                "confidence": processing_result.get("confidence", 0.8),
                "rationale": processing_result.get("reasoning", "Based on AI analysis"),
                "timestamp": datetime.now().isoformat()
            }})
        else:
            decisions.append({{
                "decision_type": "proceed",
                "confidence": 0.85,
                "rationale": "Analysis complete, proceeding with standard workflow",
                "timestamp": datetime.now().isoformat()
            }})

        # Generate artifacts
        artifacts = []
        if input_data.get("generate_report", False):
            artifacts.append({{
                "type": "analysis_report",
                "name": f"{{self.config.agent_name}}_ai_report",
                "format": "json",
                "content_summary": "AI-powered analysis results",
                "generated_at": datetime.now().isoformat()
            }})

        # Compute metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = {{
            "processing_time_ms": processing_time,
            "ai_powered": True,
            "processor_used": processor.domain,
            "recommendations_count": len(recommendations),
            "decisions_count": len(decisions),
            "confidence_score": decisions[0].get("confidence", 0.8) if decisions else 0.8
        }}

        # Generate events
        events = [{{
            "event_type": "ai_task_completed",
            "agent_id": self.config.agent_id,
            "apqc_process": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "summary": f"AI-powered processing of {{task_type}} task completed",
            "ai_enhanced": True
        }}]

        return {{
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "output": {{
                "analysis": analysis_results,
                "recommendations": recommendations,
                "decisions": decisions,
                "artifacts": artifacts,
                "metrics": metrics,
                "events": events,
            }},
        }}
'''


def extract_metadata(file_path: str) -> Optional[AgentMetadata]:
    """Extract metadata from a stub agent file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already using smart processing
        if "smart_processing" in content or "get_processor" in content:
            return None  # Already upgraded

        # Extract from docstring and class attributes
        agent_name = ""
        agent_type = "operational"
        domain = "default"
        apqc_category_id = ""
        apqc_category_name = ""
        apqc_process_id = ""
        apqc_process_name = ""
        capabilities = []
        skills = {}
        inputs = []
        outputs = []
        process_method_name = "_process_operational"

        # Extract domain from docstring
        domain_match = re.search(r'Domain:\s*(\w+)', content)
        if domain_match:
            domain = domain_match.group(1)

        # Extract agent type
        type_match = re.search(r'Type:\s*(\w+)', content)
        if type_match:
            agent_type = type_match.group(1)
            process_method_name = f"_process_{agent_type}"

        # Find actual _process_* method name in the file
        actual_method_match = re.search(r'async def (_process_\w+)\(self,', content)
        if actual_method_match:
            process_method_name = actual_method_match.group(1)

        # Extract APQC info
        cat_id_match = re.search(r'apqc_category_id:\s*str\s*=\s*["\']([^"\']+)["\']', content)
        if cat_id_match:
            apqc_category_id = cat_id_match.group(1)

        cat_name_match = re.search(r'apqc_category_name:\s*str\s*=\s*["\']([^"\']+)["\']', content)
        if cat_name_match:
            apqc_category_name = cat_name_match.group(1)

        proc_id_match = re.search(r'apqc_process_id:\s*str\s*=\s*["\']([^"\']+)["\']', content)
        if proc_id_match:
            apqc_process_id = proc_id_match.group(1)

        proc_name_match = re.search(r'apqc_process_name:\s*str\s*=\s*["\']([^"\']+)["\']', content)
        if proc_name_match:
            apqc_process_name = proc_name_match.group(1)

        # Extract agent name from class
        class_match = re.search(r'class\s+(\w+Agent)', content)
        if class_match:
            agent_name = class_match.group(1)

        # Extract capabilities
        cap_match = re.search(r'self\.capabilities_list\s*=\s*\[([\s\S]*?)\]', content)
        if cap_match:
            cap_str = cap_match.group(1)
            capabilities = re.findall(r'["\'](\w+)["\']', cap_str)

        # Extract skills
        skills_match = re.search(r'self\.skills\s*=\s*\{([\s\S]*?)\}', content)
        if skills_match:
            skills_str = skills_match.group(1)
            skill_pairs = re.findall(r'["\'](\w+)["\']\s*:\s*([\d.]+)', skills_str)
            skills = {k: float(v) for k, v in skill_pairs}

        return AgentMetadata(
            file_path=file_path,
            agent_name=agent_name,
            agent_type=agent_type,
            domain=domain,
            apqc_category_id=apqc_category_id,
            apqc_category_name=apqc_category_name,
            apqc_process_id=apqc_process_id,
            apqc_process_name=apqc_process_name,
            capabilities=capabilities,
            skills=skills,
            inputs=[],
            outputs=[],
            process_method_name=process_method_name,
        )

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return None


def generate_smart_implementation(metadata: AgentMetadata) -> str:
    """Generate smart AI-powered implementation"""
    method_suffix = metadata.process_method_name.replace("_process_", "")

    implementation = SMART_IMPLEMENTATION_TEMPLATE.format(
        method_name=metadata.process_method_name,
        agent_type=method_suffix,
        apqc_process_name=metadata.apqc_process_name,
        domain=metadata.domain,
    )

    return implementation


def update_agent_file(metadata: AgentMetadata, dry_run: bool = False) -> Tuple[bool, str]:
    """Update agent file with smart implementation"""
    try:
        with open(metadata.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the method to replace
        method_pattern = rf'(async def {metadata.process_method_name}\(self,[\s\S]*?"""[\s\S]*?""")[\s\S]*?(return \{{[\s\S]*?\}})'

        # Find the start of the method
        method_start = content.find(f"async def {metadata.process_method_name}")
        if method_start == -1:
            return False, f"Could not find method {metadata.process_method_name}"

        # Find the end of the method
        remaining = content[method_start:]
        lines = remaining.split('\n')
        method_indent = len(lines[0]) - len(lines[0].lstrip())

        method_end_offset = 0
        for i, line in enumerate(lines[1:], 1):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= method_indent and (stripped.startswith('async def ') or stripped.startswith('def ') or stripped.startswith('class ')):
                    method_end_offset = sum(len(l) + 1 for l in lines[:i])
                    break
        else:
            method_end_offset = len(remaining)

        method_end = method_start + method_end_offset

        # Generate new implementation
        new_implementation = generate_smart_implementation(metadata)

        # Build new content
        new_content = content[:method_start] + new_implementation + '\n' + content[method_end:]

        if dry_run:
            return True, f"Would upgrade {metadata.file_path} with AI processing"

        with open(metadata.file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True, f"Upgraded {metadata.file_path} with AI processing"

    except Exception as e:
        return False, f"Error updating {metadata.file_path}: {e}"


def find_upgradeable_agents(directory: str) -> List[str]:
    """Find agents that can be upgraded to smart processing"""
    upgradeable = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_agent.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Check if it's already using smart processing
                    if 'smart_processing' not in content and 'get_processor' not in content:
                        # Check if it has a _process_ method
                        if 'async def _process_' in content:
                            upgradeable.append(file_path)
                except Exception:
                    pass
    return upgradeable


def main():
    parser = argparse.ArgumentParser(description='Upgrade agents to use AI-powered smart processing')
    parser.add_argument('--file', type=str, help='Single agent file to upgrade')
    parser.add_argument('--directory', type=str, help='Directory of agents to upgrade')
    parser.add_argument('--all', action='store_true', help='Upgrade all agents')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--list', action='store_true', help='List agents that can be upgraded')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of agents to upgrade')

    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent / 'src' / 'superstandard' / 'agents'

    if args.list:
        upgradeable = find_upgradeable_agents(str(base_dir))
        print(f"\nFound {len(upgradeable)} agents that can be upgraded to smart processing:\n")
        for f in upgradeable[:20]:
            print(f"  - {f}")
        if len(upgradeable) > 20:
            print(f"  ... and {len(upgradeable) - 20} more")
        return

    files_to_process = []

    if args.file:
        files_to_process = [args.file]
    elif args.directory:
        files_to_process = find_upgradeable_agents(args.directory)
    elif args.all:
        files_to_process = find_upgradeable_agents(str(base_dir))
    else:
        parser.print_help()
        return

    if args.limit > 0:
        files_to_process = files_to_process[:args.limit]

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Upgrading {len(files_to_process)} agents to smart processing...\n")

    success_count = 0
    error_count = 0

    for file_path in files_to_process:
        metadata = extract_metadata(file_path)
        if metadata:
            success, message = update_agent_file(metadata, dry_run=args.dry_run)
            print(f"{'[OK]' if success else '[FAIL]'} {message}")
            if success:
                success_count += 1
            else:
                error_count += 1
        else:
            print(f"[SKIP] {file_path} - Already upgraded or could not extract metadata")

    print(f"\n{'Dry run complete' if args.dry_run else 'Complete'}: {success_count} upgraded, {error_count} failed")


if __name__ == '__main__':
    main()
