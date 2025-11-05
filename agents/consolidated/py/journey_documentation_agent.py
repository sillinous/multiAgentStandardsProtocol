"""
Journey Documentation Agent
Tracks the evolution of the project for internal alignment and decision context
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class JourneyDocumentationAgent:
    """
    Maintains living documentation of the project journey:
    - Decisions and rationale
    - Pivots and why
    - Learnings and patterns
    - Current state and next steps
    """

    def __init__(self, project_name: str = "Graytonomous"):
        self.name = "JourneyDocumentationAgent"
        self.project_name = project_name
        self.journey_log = []
        self.decision_log = []
        self.pivot_history = []
        self.current_state = {}

    def log_event(self, event: Dict) -> Dict:
        """
        Log any journey event with full context

        Args:
            event: {
                'category': 'decision'|'milestone'|'pivot'|'learning'|'blocker'|'opportunity',
                'title': str,
                'description': str,
                'context': Dict (what led to this),
                'outcome': str (what happened),
                'next_steps': List[str],
                'metadata': Dict
            }
        """
        entry = {
            'id': f"journey_{len(self.journey_log) + 1}",
            'timestamp': datetime.now().isoformat(),
            'category': event['category'],
            'title': event['title'],
            'description': event.get('description', ''),
            'context': event.get('context', {}),
            'outcome': event.get('outcome', ''),
            'next_steps': event.get('next_steps', []),
            'metadata': event.get('metadata', {}),
            'state_snapshot': self._capture_state_snapshot()
        }

        self.journey_log.append(entry)

        # Update specialized logs
        if event['category'] == 'decision':
            self._log_decision(entry)
        elif event['category'] == 'pivot':
            self._log_pivot(entry)

        # Update current state
        self._update_current_state(entry)

        return entry

    def _log_decision(self, entry: Dict):
        """Log a decision with full rationale"""
        decision = {
            'id': entry['id'],
            'timestamp': entry['timestamp'],
            'decision': entry['title'],
            'rationale': entry['description'],
            'alternatives_considered': entry.get('context', {}).get('alternatives', []),
            'deciding_factors': entry.get('context', {}).get('factors', []),
            'expected_outcome': entry['outcome'],
            'actual_outcome': None,  # To be filled later
            'would_decide_same_again': None  # Retrospective
        }
        self.decision_log.append(decision)

    def _log_pivot(self, entry: Dict):
        """Log a pivot with reasoning"""
        pivot = {
            'id': entry['id'],
            'timestamp': entry['timestamp'],
            'from': entry.get('context', {}).get('original_direction', ''),
            'to': entry['title'],
            'why': entry['description'],
            'trigger': entry.get('context', {}).get('trigger', ''),
            'impact': entry['outcome'],
            'lessons': entry.get('metadata', {}).get('lessons', [])
        }
        self.pivot_history.append(pivot)

    def _capture_state_snapshot(self) -> Dict:
        """Capture current project state"""
        return {
            'timestamp': datetime.now().isoformat(),
            'phase': self.current_state.get('phase', 'unknown'),
            'focus': self.current_state.get('focus', 'unknown'),
            'blockers': self.current_state.get('blockers', []),
            'active_work': self.current_state.get('active_work', []),
            'next_milestones': self.current_state.get('next_milestones', [])
        }

    def _update_current_state(self, entry: Dict):
        """Update current state based on new event"""
        # Extract state updates from entry
        if 'state_updates' in entry.get('metadata', {}):
            self.current_state.update(entry['metadata']['state_updates'])

    def generate_status_update(self) -> Dict:
        """Generate current status summary for team alignment"""
        recent_events = self.journey_log[-10:]  # Last 10 events

        return {
            'generated_at': datetime.now().isoformat(),
            'project': self.project_name,
            'current_phase': self.current_state.get('phase', 'Building'),
            'current_focus': self.current_state.get('focus', 'Development'),

            'recent_progress': [
                {
                    'title': e['title'],
                    'category': e['category'],
                    'outcome': e['outcome']
                }
                for e in recent_events
                if e['category'] in ['milestone', 'decision']
            ],

            'active_blockers': self.current_state.get('blockers', []),

            'key_decisions': [
                {
                    'decision': d['decision'],
                    'rationale': d['rationale'],
                    'when': d['timestamp']
                }
                for d in self.decision_log[-5:]  # Last 5 decisions
            ],

            'recent_pivots': [
                {
                    'from': p['from'],
                    'to': p['to'],
                    'why': p['why']
                }
                for p in self.pivot_history[-3:]  # Last 3 pivots
            ],

            'next_steps': self.current_state.get('next_milestones', [])
        }

    def generate_context_brief(self, for_new_team_member: bool = True) -> Dict:
        """
        Generate comprehensive context brief
        Perfect for onboarding new people or AI agents
        """
        return {
            'project_overview': {
                'name': self.project_name,
                'mission': 'Build autonomous agent ecosystem that improves itself',
                'current_state': self.current_state,
                'started': self.journey_log[0]['timestamp'] if self.journey_log else 'Unknown'
            },

            'the_journey_so_far': self._summarize_journey(),

            'key_decisions': [
                {
                    'what': d['decision'],
                    'why': d['rationale'],
                    'when': d['timestamp'],
                    'outcome': d.get('actual_outcome', 'In progress')
                }
                for d in self.decision_log
            ],

            'pivots_and_learnings': [
                {
                    'original_plan': p['from'],
                    'new_direction': p['to'],
                    'insight': p['why'],
                    'lessons': p['lessons']
                }
                for p in self.pivot_history
            ],

            'current_priorities': self.current_state.get('active_work', []),

            'where_we_are_now': {
                'phase': self.current_state.get('phase', ''),
                'focus': self.current_state.get('focus', ''),
                'blockers': self.current_state.get('blockers', []),
                'opportunities': self.current_state.get('opportunities', [])
            },

            'how_to_help': self._generate_help_wanted()
        }

    def _summarize_journey(self) -> List[Dict]:
        """Summarize key journey milestones"""
        milestones = [e for e in self.journey_log if e['category'] == 'milestone']

        return [
            {
                'milestone': m['title'],
                'achieved': m['timestamp'],
                'impact': m['outcome']
            }
            for m in milestones
        ]

    def _generate_help_wanted(self) -> List[Dict]:
        """Generate list of ways people can help"""
        blockers = self.current_state.get('blockers', [])
        opportunities = self.current_state.get('opportunities', [])

        help_wanted = []

        for blocker in blockers:
            help_wanted.append({
                'type': 'blocker',
                'need': blocker,
                'how_to_help': f"Help solve: {blocker}"
            })

        for opp in opportunities:
            help_wanted.append({
                'type': 'opportunity',
                'need': opp,
                'how_to_help': f"Contribute to: {opp}"
            })

        return help_wanted

    def export_full_journey(self, filepath: str):
        """Export complete journey documentation"""
        full_doc = {
            'project': self.project_name,
            'generated_at': datetime.now().isoformat(),
            'journey_log': self.journey_log,
            'decision_log': self.decision_log,
            'pivot_history': self.pivot_history,
            'current_state': self.current_state,
            'context_brief': self.generate_context_brief()
        }

        with open(filepath, 'w') as f:
            json.dump(full_doc, f, indent=2, default=str)

    def set_current_state(self, state: Dict):
        """Manually update current state"""
        self.current_state.update(state)


# Example usage
if __name__ == "__main__":
    agent = JourneyDocumentationAgent("Graytonomous")

    # Set initial state
    agent.set_current_state({
        'phase': 'Validation',
        'focus': 'Proving multi-car routing capability for Gerd partnership',
        'active_work': [
            'Validate multi-agent routing can solve real-world problems',
            'Prepare response to Gerd with confidence',
            'Build documentation agents for context preservation'
        ],
        'blockers': [],
        'opportunities': [
            'Gerd partnership (German mobility startup)',
            'Investor exposure at October meeting',
            'European market entry'
        ]
    })

    # Log validation milestone
    agent.log_event({
        'category': 'milestone',
        'title': 'Multi-Car Routing POC Validation Complete',
        'description': 'Successfully validated that autonomous agents can solve Gerd\'s multi-car hopping challenge',
        'context': {
            'challenge': 'Real-time 3-hop routing with traffic and timing constraints',
            'approach': '5-agent system (Route Discovery, Traffic Prediction, Matching, Handoff, Consensus)'
        },
        'outcome': 'Found 68 routes, selected optimal 3-hop solution in 72.7min, $22.92 cost, 75% confidence',
        'next_steps': [
            'Document results for Gerd',
            'Draft confident response',
            'Prepare for partnership discussion'
        ],
        'metadata': {
            'state_updates': {
                'phase': 'Partnership Development',
                'blockers': []  # Validation blocker removed!
            }
        }
    })

    # Log decision
    agent.log_event({
        'category': 'decision',
        'title': 'Pursue Gerd Partnership (Non-Cash Equity Deal)',
        'description': 'Decided to accept equity-based partnership for exposure and network access',
        'context': {
            'alternatives': [
                'Wait for cash-paying clients',
                'Focus only on public building',
                'Negotiate for cash payment'
            ],
            'factors': [
                'Gerd is well-connected in German investment scene',
                'Exposure at October investor meeting is priceless',
                'Real-world validation trumps immediate cash',
                'European market entry opportunity'
            ]
        },
        'outcome': 'Expected: Network access, investor intros, case study, market entry worth >$350k in opportunities',
        'next_steps': [
            'Validate technical capability (DONE)',
            'Respond to Gerd with confidence',
            'Negotiate visibility and role in October meeting'
        ]
    })

    # Generate and print status update
    print("="*80)
    print("STATUS UPDATE")
    print("="*80)
    status = agent.generate_status_update()
    print(json.dumps(status, indent=2))

    print("\n\n" + "="*80)
    print("CONTEXT BRIEF (For New Team Member / AI Agent)")
    print("="*80)
    brief = agent.generate_context_brief()
    print(json.dumps(brief, indent=2))

    # Export
    agent.export_full_journey('journey_documentation.json')
    print("\n\n[Exported full journey to journey_documentation.json]")
