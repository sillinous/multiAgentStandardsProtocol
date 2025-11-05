"""
Example Autonomous Agent
Demonstrates the autonomous agent framework
"""

import time
import random
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous.autonomous_agent import AutonomousAgent
from autonomous.message_bus import Message, MessagePriority


class ExampleAgent(AutonomousAgent):
    """
    Example autonomous agent that demonstrates:
    - Message sending/receiving
    - Shared memory usage
    - Consensus voting
    - Event-driven behavior
    """

    def on_start(self):
        """Initialize agent when started"""
        print(f"[{self.agent_id}] Example agent starting up...")

        # Subscribe to custom topics
        self.subscribe('market.price_update', self._handle_price_update)
        self.subscribe('alert.*', self._handle_alert)

        # Initialize state in shared memory
        self.set_memory(f'agent:{self.agent_id}:status', 'active', ttl=300)
        self.set_memory(f'agent:{self.agent_id}:start_time', datetime.now().isoformat())

        # Publish startup event
        self.publish_event('agent_started', {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat()
        })

        print(f"[{self.agent_id}] Ready!")

    def on_stop(self):
        """Cleanup when agent stops"""
        print(f"[{self.agent_id}] Shutting down...")

        # Update status in shared memory
        self.set_memory(f'agent:{self.agent_id}:status', 'stopped', ttl=60)

        # Publish shutdown event
        self.publish_event('agent_stopped', {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat()
        })

    def on_message(self, message: Message):
        """Handle incoming messages"""
        print(f"[{self.agent_id}] Received message on {message.topic} from {message.sender}")

        # Check if this is a request message
        if message.requires_response:
            self._send_response(message)

    def _handle_price_update(self, message: Message):
        """Handle price update messages"""
        price = message.data.get('price', 0)
        token = message.data.get('token', 'UNKNOWN')

        print(f"[{self.agent_id}] Price update: {token} = ${price:.2f}")

        # Store in shared memory
        self.set_memory(f'price:{token}', price, ttl=60)

        # Check if we should alert on this price
        threshold = self.config.get('price_alert_threshold', 100.0)
        if price > threshold:
            self.broadcast('price_alert', {
                'token': token,
                'price': price,
                'threshold': threshold,
                'alert_by': self.agent_id
            }, priority=MessagePriority.HIGH)

    def _handle_alert(self, message: Message):
        """Handle alert messages"""
        alert_type = message.topic.split('.')[-1]
        print(f"[{self.agent_id}] ALERT ({alert_type}): {message.data}")

    def _send_response(self, original_message: Message):
        """Send a response to a request message"""
        response_data = {
            'response_to': original_message.correlation_id,
            'status': 'processed',
            'timestamp': datetime.now().isoformat()
        }

        self.send_direct_message(
            target_agent=original_message.sender,
            data=response_data,
            priority=MessagePriority.NORMAL
        )

    def _periodic_task(self):
        """
        Periodic task that runs every loop iteration
        This demonstrates autonomous behavior
        """
        # Run every 10 seconds
        if not hasattr(self, '_last_periodic_run'):
            self._last_periodic_run = time.time()

        current_time = time.time()
        if current_time - self._last_periodic_run < 10:
            return

        self._last_periodic_run = current_time

        # Simulate autonomous decision making
        action = random.choice(['monitor', 'analyze', 'report'])

        if action == 'monitor':
            # Check shared memory for system state
            active_agents = len(self.memory.keys('agent:*:status'))
            print(f"[{self.agent_id}] Monitoring: {active_agents} active agents")

        elif action == 'analyze':
            # Analyze recent events
            recent_events = self.memory.get_events(limit=5)
            print(f"[{self.agent_id}] Analyzing: {len(recent_events)} recent events")

        elif action == 'report':
            # Broadcast status report
            stats = self.get_stats()
            self.broadcast('status_report', stats, priority=MessagePriority.LOW)
            print(f"[{self.agent_id}] Reporting: Sent {stats['messages_sent']} messages")

    def _on_vote_request(self, proposal_data: Dict[str, Any]):
        """
        Respond to consensus vote requests
        This demonstrates collaborative decision-making
        """
        proposal_id = proposal_data.get('proposal_id')
        action = proposal_data.get('action')
        proposer = proposal_data.get('proposer')

        print(f"[{self.agent_id}] Vote request: {action} by {proposer}")

        # Simple voting logic - randomly approve/reject for demo
        approve = random.random() > 0.3  # 70% approval rate
        confidence = random.uniform(0.6, 0.95)

        reasoning = f"Agent {self.agent_id} {'approves' if approve else 'rejects'} based on analysis"

        # Cast vote
        self.vote(
            proposal_id=proposal_id,
            approve=approve,
            confidence=confidence,
            reasoning=reasoning
        )

        print(f"[{self.agent_id}] Voted: {'APPROVE' if approve else 'REJECT'} (confidence: {confidence:.2f})")

    def _on_proposal_approved(self, decision_data: Dict[str, Any]):
        """React to approved proposals"""
        action = decision_data.get('action')
        approval_ratio = decision_data.get('approval_ratio', 0)

        print(f"[{self.agent_id}] Proposal APPROVED: {action} ({approval_ratio:.1%} approval)")

        # If this agent proposed it, execute the action
        if decision_data.get('proposer') == self.agent_id:
            print(f"[{self.agent_id}] Executing my approved proposal: {action}")
            self._execute_action(action, decision_data.get('data', {}))

    def _on_proposal_rejected(self, decision_data: Dict[str, Any]):
        """React to rejected proposals"""
        action = decision_data.get('action')
        approval_ratio = decision_data.get('approval_ratio', 0)

        print(f"[{self.agent_id}] Proposal REJECTED: {action} ({approval_ratio:.1%} approval)")

    def _execute_action(self, action: str, data: Dict[str, Any]):
        """Execute an approved action"""
        print(f"[{self.agent_id}] Executing action: {action}")
        print(f"[{self.agent_id}] Action data: {data}")

        # Publish event
        self.publish_event('action_executed', {
            'action': action,
            'data': data,
            'executed_by': self.agent_id
        })


def main():
    """
    Run example agent standalone
    Demonstrates autonomous agent in action
    """
    print("=" * 60)
    print("Example Autonomous Agent Demo")
    print("=" * 60)

    # Import infrastructure
    from autonomous.message_bus import get_message_bus
    from autonomous.shared_memory import get_shared_memory
    from autonomous.consensus import ConsensusManager

    # Initialize infrastructure
    print("\n[SETUP] Initializing infrastructure...")
    bus = get_message_bus(use_redis=False)  # Use in-memory for demo
    memory = get_shared_memory(use_redis=False)
    consensus = ConsensusManager(bus, memory)

    # Create multiple example agents to demonstrate collaboration
    print("\n[SETUP] Creating agents...")
    agents = []

    for i in range(3):
        agent_id = f'example_agent_{i+1}'
        agent = ExampleAgent(
            agent_id=agent_id,
            message_bus=bus,
            shared_memory=memory,
            consensus_manager=consensus,
            config={'price_alert_threshold': 95.0}
        )
        agents.append(agent)

    # Start all agents
    print("\n[SETUP] Starting agents...")
    for agent in agents:
        agent.start()
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Agents are now running autonomously!")
    print("Watch them communicate and collaborate...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    try:
        # Let agents run for a bit
        time.sleep(5)

        # Demonstrate message broadcasting
        print("\n[DEMO] Broadcasting price update...")
        agents[0].broadcast('market.price_update', {
            'token': 'SOL',
            'price': 102.50,
            'volume': 1000000
        }, priority=MessagePriority.NORMAL)

        time.sleep(3)

        # Demonstrate consensus voting
        print("\n[DEMO] Proposing action for consensus vote...")
        proposal_id = agents[1].propose_consensus(
            action='close_position',
            data={'token': 'SOL', 'reason': 'High risk detected'},
            min_votes=2,
            threshold=0.6,
            timeout_seconds=10
        )

        time.sleep(12)

        # Check proposal result
        result = consensus.get_proposal_status(proposal_id)
        print(f"\n[DEMO] Proposal result: {result}")

        # Let agents continue autonomous behavior
        print("\n[DEMO] Agents continuing autonomous operation...")
        time.sleep(20)

        # Show final statistics
        print("\n" + "=" * 60)
        print("Final Agent Statistics:")
        print("=" * 60)
        for agent in agents:
            stats = agent.get_stats()
            print(f"\n{agent.agent_id}:")
            print(f"  Messages Sent: {stats['messages_sent']}")
            print(f"  Messages Received: {stats['messages_received']}")
            print(f"  Votes Cast: {stats['votes_cast']}")
            print(f"  Subscribed Topics: {stats['subscribed_topics']}")

        # Memory statistics
        print("\n" + "=" * 60)
        print("Shared Memory Statistics:")
        print("=" * 60)
        mem_stats = memory.get_stats()
        print(f"  Type: {mem_stats['type']}")
        print(f"  Total Keys: {mem_stats['total_keys']}")

        # Message bus statistics
        print("\n" + "=" * 60)
        print("Message Bus Statistics:")
        print("=" * 60)
        bus_stats = bus.get_stats()
        print(f"  Total Topics: {bus_stats['total_topics']}")
        print(f"  Total Subscribers: {bus_stats['total_subscribers']}")
        print(f"  Message History Size: {bus_stats['message_history_size']}")

    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping agents...")

    finally:
        # Stop all agents
        for agent in agents:
            agent.stop()

        # Stop infrastructure
        bus.stop()

        print("\n[SHUTDOWN] All agents stopped")
        print("=" * 60)


if __name__ == '__main__':
    main()
