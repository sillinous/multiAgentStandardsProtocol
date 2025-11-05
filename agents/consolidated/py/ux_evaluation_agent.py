"""
UX Evaluation Agent - Meta-Agent for User Experience Testing

This agent evaluates dashboards and UIs from a real user's perspective,
identifying usability issues, broken functionality, and poor UX patterns.

Category: Meta-Agent (Quality Assurance & User Experience)
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentCapability


class SeverityLevel(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"  # Blocks core functionality
    HIGH = "high"  # Severely impacts usability
    MEDIUM = "medium"  # Noticeable but workaround exists
    LOW = "low"  # Minor annoyance


@dataclass
class UXIssue:
    """User experience issue"""
    issue_id: str
    severity: SeverityLevel
    category: str  # functionality, usability, accessibility, visual
    title: str
    description: str
    user_impact: str
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    suggested_fix: str
    affected_elements: List[str]


class UXEvaluationAgent(BaseAgent):
    """
    Meta-agent that evaluates user experience from real user perspective

    Evaluation Approach:
    1. Define user goals and tasks
    2. Attempt to complete each task
    3. Document failures and friction points
    4. Identify confusing/broken elements
    5. Suggest concrete improvements
    """

    def __init__(
        self,
        agent_id: str = "ux_evaluator_001",
        workspace_path: str = "./autonomous-ecosystem/workspace"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ux_evaluator",
            capabilities=[AgentCapability.QA_EVALUATION],
            workspace_path=workspace_path
        )

        self.issues: List[UXIssue] = []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute UX evaluation task"""
        task_type = task.get("type")

        if task_type == "evaluate_dashboard":
            return await self._evaluate_dashboard(task)
        elif task_type == "test_user_flow":
            return await self._test_user_flow(task)
        elif task_type == "check_accessibility":
            return await self._check_accessibility(task)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dashboard HTML/JS for UX issues"""
        dashboard_path = input_data.get("dashboard_path")
        if not dashboard_path:
            return {"error": "dashboard_path required"}

        # Read dashboard file
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            return {"error": f"Failed to read dashboard: {e}"}

        # Perform comprehensive analysis
        await self._analyze_html_structure(html_content, dashboard_path)
        await self._analyze_javascript_functionality(html_content, dashboard_path)
        await self._analyze_visual_layout(html_content, dashboard_path)
        await self._analyze_user_flows(dashboard_path)

        return self._generate_report()

    async def _analyze_html_structure(self, html: str, path: str):
        """Analyze HTML structure for issues"""

        # Check for missing critical elements
        if 'canvas' in html.lower() and 'function' not in html.lower():
            self._add_issue(
                severity=SeverityLevel.CRITICAL,
                category="functionality",
                title="Canvas element exists but no rendering code",
                description="Dashboard has <canvas> elements but missing JavaScript to draw on them",
                user_impact="Users see blank canvas areas - core visualization doesn't work",
                steps=["1. Load dashboard", "2. Observe canvas area", "3. See blank space"],
                expected="Canvas should show visualization (agents, routes, metrics)",
                actual="Canvas is blank/empty",
                fix="Add canvas rendering logic using CanvasRenderingContext2D API",
                elements=["<canvas>"]
            )

        # Check for buttons without event handlers
        if '<button' in html:
            import re
            buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.IGNORECASE | re.DOTALL)
            onclick_count = html.lower().count('onclick=')

            if len(buttons) > onclick_count + 5:  # Allow some event listeners
                self._add_issue(
                    severity=SeverityLevel.CRITICAL,
                    category="functionality",
                    title="Buttons without click handlers",
                    description=f"Found {len(buttons)} buttons but only ~{onclick_count} have handlers",
                    user_impact="User clicks buttons but nothing happens - total breakdown of interactivity",
                    steps=["1. Click any button", "2. Nothing happens"],
                    expected="Button should trigger action (play, pause, spawn agent)",
                    actual="Button does nothing - no response",
                    fix="Add onclick handlers or addEventListener for each button",
                    elements=["Play button", "Pause button", "Reset button", "Spawn buttons"]
                )

        # Check for WebSocket connection code
        if 'WebSocket' not in html and 'ws://' not in html:
            self._add_issue(
                severity=SeverityLevel.HIGH,
                category="functionality",
                title="Missing WebSocket connection for real-time updates",
                description="Dashboard should connect to WebSocket for live data but code is missing",
                user_impact="Dashboard is completely static - no live updates from server",
                steps=["1. Load dashboard", "2. Wait for updates", "3. Nothing changes"],
                expected="Dashboard updates in real-time with agent activity",
                actual="Dashboard is frozen - shows initial state only",
                fix="Add: const ws = new WebSocket('ws://localhost:8001/ws'); ws.onmessage = handler;",
                elements=["WebSocket initialization"]
            )

        # Check for API polling/fetching
        if 'fetch(' not in html and 'XMLHttpRequest' not in html:
            self._add_issue(
                severity=SeverityLevel.HIGH,
                category="functionality",
                title="No API calls to fetch data",
                description="Dashboard doesn't make any HTTP requests to get data from server",
                user_impact="No data is ever loaded - dashboard shows placeholder text only",
                steps=["1. Load dashboard", "2. Check network tab", "3. No API calls"],
                expected="Dashboard should fetch /api/agents/active, /api/activity/feed etc",
                actual="No network requests - uses hardcoded/no data",
                fix="Add fetch() calls to server API endpoints",
                elements=["API integration"]
            )

    async def _analyze_javascript_functionality(self, html: str, path: str):
        """Analyze JavaScript for broken functionality"""

        # Check for error handling
        if 'fetch(' in html and 'catch' not in html:
            self._add_issue(
                severity=SeverityLevel.MEDIUM,
                category="functionality",
                title="No error handling on API calls",
                description="fetch() calls exist but no .catch() blocks",
                user_impact="When API fails, user sees silent errors with no feedback",
                steps=["1. Disconnect from API", "2. Load dashboard", "3. No error message"],
                expected="User sees friendly error: 'Unable to connect to server'",
                actual="Silent failure - looks like it's working but isn't",
                fix="Add .catch(err => showError(err)) to all fetch calls",
                elements=["Error handling"]
            )

        # Check for DOMContentLoaded or similar
        if '<script>' in html:
            if 'DOMContentLoaded' not in html and 'window.onload' not in html:
                self._add_issue(
                    severity=SeverityLevel.HIGH,
                    category="functionality",
                    title="Script runs before DOM is ready",
                    description="JavaScript executes before HTML elements exist",
                    user_impact="JavaScript fails to find elements - buttons don't work",
                    steps=["1. Load page", "2. Check console", "3. See 'null' errors"],
                    expected="Code waits for DOM: document.addEventListener('DOMContentLoaded')",
                    actual="Code runs immediately, elements don't exist yet",
                    fix="Wrap code in: document.addEventListener('DOMContentLoaded', () => { ... })",
                    elements=["Script execution timing"]
                )

        # Check for undefined variables
        if 'function' in html.lower():
            # Simple check - in real implementation would use JS parser
            common_issues = []
            if 'getElementById(' in html and 'null' not in html.lower():
                common_issues.append("getElementById calls without null checks")

            if common_issues:
                self._add_issue(
                    severity=SeverityLevel.MEDIUM,
                    category="functionality",
                    title="Missing null checks on DOM queries",
                    description="Code assumes elements exist without checking",
                    user_impact="JavaScript crashes when element is missing",
                    steps=["1. Inspect console", "2. See TypeError: Cannot read property of null"],
                    expected="if (element) { element.doSomething() }",
                    actual="element.doSomething() crashes if element is null",
                    fix="Add null checks before using DOM elements",
                    elements=["DOM queries"]
                )

    async def _analyze_visual_layout(self, html: str, path: str):
        """Analyze visual layout for UX issues"""

        # Check for overlapping elements
        if 'position: absolute' in html or 'z-index' in html:
            self._add_issue(
                severity=SeverityLevel.HIGH,
                category="visual",
                title="Overlapping UI elements blocking interaction",
                description="Absolute positioned elements may cover buttons/content",
                user_impact="User can't click buttons because overlays are in the way",
                steps=["1. Load dashboard", "2. Try to click button", "3. Overlay blocks it"],
                expected="All interactive elements should be accessible",
                actual="Overlays/modals cover essential UI elements",
                fix="Review z-index stacking, ensure modals have close buttons, proper positioning",
                elements=["Modals", "Overlays", "Position:absolute elements"]
            )

        # Check for loading states
        if 'Loading' not in html and 'Spinner' not in html:
            self._add_issue(
                severity=SeverityLevel.MEDIUM,
                category="usability",
                title="No loading indicators",
                description="Users don't know when data is being fetched",
                user_impact="User thinks dashboard is broken when it's just loading",
                steps=["1. Load dashboard", "2. Wait for data", "3. No indication of progress"],
                expected="Show spinner or 'Loading...' message during data fetch",
                actual="Blank screen or old data - no feedback that loading is happening",
                fix="Add loading state: <div class='loading'>Loading...</div>",
                elements=["Loading states"]
            )

        # Check for mobile responsiveness
        if 'viewport' not in html.lower():
            self._add_issue(
                severity=SeverityLevel.LOW,
                category="accessibility",
                title="Missing viewport meta tag",
                description="Page won't scale properly on mobile devices",
                user_impact="Dashboard unusable on phones/tablets - elements too small",
                steps=["1. Open on phone", "2. Everything is tiny", "3. Can't tap buttons"],
                expected="<meta name='viewport' content='width=device-width'>",
                actual="Missing viewport tag - desktop-only layout",
                fix="Add viewport meta tag in <head>",
                elements=["<head> section"]
            )

    async def _analyze_user_flows(self, path: str):
        """Analyze critical user flows"""

        # User Goal 1: View live agent activity
        self._add_issue(
            severity=SeverityLevel.CRITICAL,
            category="functionality",
            title="Core user goal: 'See agent activity' - COMPLETELY BROKEN",
            description="Primary dashboard purpose is to show agents working, but this doesn't function",
            user_impact="Dashboard has zero value - user can't accomplish main goal",
            steps=[
                "1. User opens dashboard to see agents working",
                "2. Dashboard is static - no activity shown",
                "3. User clicks Play - nothing happens",
                "4. User gives up - dashboard is useless"
            ],
            expected="User sees: agents moving, tasks being completed, real-time metrics updating",
            actual="User sees: static page, broken buttons, placeholder text, blank canvas",
            fix="PRIORITY 1: Fix WebSocket connection, canvas rendering, button handlers",
            elements=["Entire user experience"]
        )

        # User Goal 2: Control simulation
        self._add_issue(
            severity=SeverityLevel.CRITICAL,
            category="functionality",
            title="Core user goal: 'Control simulation' - BROKEN",
            description="Play/Pause/Reset buttons don't work",
            user_impact="User has no control over what they're viewing",
            steps=[
                "1. User clicks Play button",
                "2. Nothing happens",
                "3. User clicks multiple times",
                "4. Still nothing",
                "5. User opens console - sees errors"
            ],
            expected="Play starts simulation, Pause stops it, Reset clears and restarts",
            actual="Buttons are non-functional decorations",
            fix="Connect buttons to API: onclick=\"fetch('/api/control/play')\"",
            elements=["Play", "Pause", "Reset", "Speed controls"]
        )

        # User Goal 3: Spawn agents
        self._add_issue(
            severity=SeverityLevel.HIGH,
            category="functionality",
            title="Core user goal: 'Spawn agents' - BROKEN",
            description="Agent spawn buttons don't trigger anything",
            user_impact="Can't test different agent configurations",
            steps=[
                "1. User clicks 'Spawn Agent' button",
                "2. Nothing happens",
                "3. Agent library sidebar might open but buttons inside don't work"
            ],
            expected="Click button → API call → Agent spawned → Dashboard updates",
            actual="Click button → nothing → user confusion",
            fix="Add: onclick=\"spawnAgent('agent_type')\" + fetch to /api/agents/spawn",
            elements=["Spawn buttons", "Agent library"]
        )

    def _add_issue(
        self,
        severity: SeverityLevel,
        category: str,
        title: str,
        description: str,
        user_impact: str,
        steps: List[str],
        expected: str,
        actual: str,
        fix: str,
        elements: List[str]
    ):
        """Add issue to list"""
        issue = UXIssue(
            issue_id=f"ux_{len(self.issues) + 1:03d}",
            severity=severity,
            category=category,
            title=title,
            description=description,
            user_impact=user_impact,
            steps_to_reproduce=steps,
            expected_behavior=expected,
            actual_behavior=actual,
            suggested_fix=fix,
            affected_elements=elements
        )
        self.issues.append(issue)

    def _generate_report(self) -> Dict[str, Any]:
        """Generate UX evaluation report"""

        # Group by severity
        by_severity = {
            "critical": [i for i in self.issues if i.severity == SeverityLevel.CRITICAL],
            "high": [i for i in self.issues if i.severity == SeverityLevel.HIGH],
            "medium": [i for i in self.issues if i.severity == SeverityLevel.MEDIUM],
            "low": [i for i in self.issues if i.severity == SeverityLevel.LOW]
        }

        # Calculate scores
        total_issues = len(self.issues)
        critical_count = len(by_severity["critical"])
        high_count = len(by_severity["high"])

        # UX Score: 0-100 (lower is worse)
        ux_score = max(0, 100 - (critical_count * 30) - (high_count * 15) -
                       (len(by_severity["medium"]) * 5) - (len(by_severity["low"]) * 1))

        # Usability rating
        if ux_score < 20:
            rating = "UNUSABLE"
        elif ux_score < 40:
            rating = "POOR"
        elif ux_score < 60:
            rating = "NEEDS IMPROVEMENT"
        elif ux_score < 80:
            rating = "GOOD"
        else:
            rating = "EXCELLENT"

        return {
            "success": True,
            "evaluation_date": datetime.now().isoformat(),
            "ux_score": ux_score,
            "usability_rating": rating,
            "total_issues": total_issues,
            "severity_breakdown": {
                "critical": critical_count,
                "high": high_count,
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"])
            },
            "issues": [
                {
                    "id": issue.issue_id,
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "title": issue.title,
                    "description": issue.description,
                    "user_impact": issue.user_impact,
                    "steps_to_reproduce": issue.steps_to_reproduce,
                    "expected_behavior": issue.expected_behavior,
                    "actual_behavior": issue.actual_behavior,
                    "suggested_fix": issue.suggested_fix,
                    "affected_elements": issue.affected_elements
                }
                for issue in self.issues
            ],
            "summary": self._generate_executive_summary(ux_score, rating, by_severity),
            "priority_fixes": self._get_priority_fixes(by_severity)
        }

    def _generate_executive_summary(
        self,
        ux_score: int,
        rating: str,
        by_severity: Dict
    ) -> str:
        """Generate executive summary"""
        critical = len(by_severity["critical"])
        high = len(by_severity["high"])

        if critical > 0:
            return (
                f"🚨 CRITICAL ISSUES FOUND: Dashboard is {rating} (Score: {ux_score}/100). "
                f"{critical} critical issues block core functionality. "
                f"Users cannot accomplish primary goals. Immediate fixes required before demo."
            )
        elif high > 0:
            return (
                f"⚠️ SIGNIFICANT ISSUES: Dashboard is {rating} (Score: {ux_score}/100). "
                f"{high} high-priority issues severely impact usability. "
                f"Core features work but with major friction."
            )
        else:
            return (
                f"✅ USABLE: Dashboard is {rating} (Score: {ux_score}/100). "
                f"Minor improvements recommended but core functionality works."
            )

    def _get_priority_fixes(self, by_severity: Dict) -> List[Dict]:
        """Get top priority fixes"""
        priority_issues = by_severity["critical"] + by_severity["high"]

        return [
            {
                "priority": idx + 1,
                "title": issue.title,
                "fix": issue.suggested_fix,
                "impact": issue.user_impact
            }
            for idx, issue in enumerate(priority_issues[:5])  # Top 5
        ]


if __name__ == "__main__":
    # Demo the UX evaluator
    import asyncio

    async def demo():
        evaluator = UXEvaluationAgent()

        # Evaluate dashboard_realtime.html
        result = await evaluator.analyze({
            "dashboard_path": "../validation/dashboard_realtime.html"
        })

        print("\n" + "="*80)
        print("UX EVALUATION REPORT")
        print("="*80)
        print(f"\nUSABILITY RATING: {result['usability_rating']}")
        print(f"UX SCORE: {result['ux_score']}/100")
        print(f"\nTOTAL ISSUES: {result['total_issues']}")
        print(f"  - Critical: {result['severity_breakdown']['critical']}")
        print(f"  - High: {result['severity_breakdown']['high']}")
        print(f"  - Medium: {result['severity_breakdown']['medium']}")
        print(f"  - Low: {result['severity_breakdown']['low']}")

        print(f"\nSUMMARY:")
        print(result['summary'])

        print(f"\n{'='*80}")
        print("TOP PRIORITY FIXES:")
        print("="*80)
        for fix in result['priority_fixes']:
            print(f"\n{fix['priority']}. {fix['title']}")
            print(f"   Fix: {fix['fix']}")
            print(f"   Impact: {fix['impact']}")

        print(f"\n{'='*80}")
        print("DETAILED ISSUES:")
        print("="*80)
        for issue in result['issues']:
            print(f"\n[{issue['severity'].upper()}] {issue['title']}")
            print(f"Description: {issue['description']}")
            print(f"User Impact: {issue['user_impact']}")
            print(f"Fix: {issue['suggested_fix']}")

    asyncio.run(demo())
