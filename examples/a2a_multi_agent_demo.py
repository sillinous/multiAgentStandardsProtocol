"""
📨 Agent-to-Agent Protocol (A2A) v2.0 - Multi-Agent Communication Demo
========================================================================

Demonstrates A2A capabilities for direct agent-to-agent communication:
- Message routing between agents
- Different message types (task assignment, request/response, events)
- Priority handling
- Security features (JWT authentication)
- Error handling
- Request-response patterns
- Message bus for routing

This example shows a realistic scenario where a strategic planning agent
coordinates with financial and operational agents.
"""

import asyncio
import json
from datetime import datetime
from superstandard.protocols.a2a_v2 import (
    # Core functionality
    A2AClient,
    A2AMessageBus,
    A2AMessageBuilder,

    # Data models
    A2AMessage,
    AgentInfo,

    # Enums
    MessageType,
    Priority,
    AuthMethod,

    # Utilities
    create_response,
    create_error,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_message(message: A2AMessage, prefix: str = ""):
    """Pretty print an A2A message."""
    print(f"{prefix}Message Details:")
    print(f"  From: {message.envelope.from_agent.agent_name} ({message.envelope.from_agent.agent_id})")
    print(f"  To: {message.envelope.to_agent.agent_name} ({message.envelope.to_agent.agent_id})")
    print(f"  Type: {message.envelope.message_type}")
    print(f"  Priority: {message.envelope.priority}")
    print(f"  Message ID: {message.envelope.message_id}")
    print(f"  Content: {json.dumps(message.payload.content, indent=4)}")
    if message.payload.metadata:
        print(f"  Metadata: {json.dumps(message.payload.metadata, indent=4)}")
    print()


async def main():
    """Run the multi-agent communication demo."""

    print_section("A2A v2.0: Multi-Agent Communication Demo")

    # ========================================================================
    # STEP 1: Create Message Bus and Agents
    # ========================================================================

    print_section("STEP 1: Initialize Message Bus and Agents")

    # Create the message bus for routing
    message_bus = A2AMessageBus()
    print("✓ Message bus created")

    # Create Strategic Planning Agent
    strategic_agent = A2AClient(
        agent_id="apqc_1_0_strategic_001",
        agent_name="Strategic Planning Agent",
        agent_type="strategic",
        version="1.0.0",
        capabilities=["strategic_planning", "analysis", "decision_making"]
    )
    message_bus.register_client(strategic_agent)
    print(f"✓ Registered: {strategic_agent.agent_info.agent_name}")

    # Create Financial Agent
    financial_agent = A2AClient(
        agent_id="apqc_9_2_financial_001",
        agent_name="Budget Planning Agent",
        agent_type="financial",
        version="1.0.0",
        capabilities=["budgeting", "financial_analysis", "forecasting"]
    )
    message_bus.register_client(financial_agent)
    print(f"✓ Registered: {financial_agent.agent_info.agent_name}")

    # Create Operational Agent
    operational_agent = A2AClient(
        agent_id="apqc_12_1_operational_001",
        agent_name="Resource Management Agent",
        agent_type="operational",
        version="1.0.0",
        capabilities=["resource_allocation", "procurement", "logistics"]
    )
    message_bus.register_client(operational_agent)
    print(f"✓ Registered: {operational_agent.agent_info.agent_name}")

    # ========================================================================
    # STEP 2: Register Message Handlers
    # ========================================================================

    print_section("STEP 2: Register Message Handlers")

    # Financial agent handles task assignments
    async def financial_task_handler(message: A2AMessage):
        """Handle task assignments for financial agent."""
        print(f"📥 {financial_agent.agent_info.agent_name} received task assignment:")
        print_message(message, "  ")

        # Simulate processing
        await asyncio.sleep(0.5)

        # Send back a status update
        response = create_response(
            message,
            {
                'status': 'completed',
                'budget_allocation': {
                    'digital_transformation': 2500000,
                    'market_expansion': 2500000
                },
                'completion_time': datetime.utcnow().isoformat() + 'Z'
            }
        )
        await message_bus.route(response)
        print(f"✅ {financial_agent.agent_info.agent_name} sent response\n")

    financial_agent.on_message(MessageType.TASK_ASSIGNMENT, financial_task_handler)

    # Strategic agent handles responses
    async def strategic_response_handler(message: A2AMessage):
        """Handle responses for strategic agent."""
        print(f"📥 {strategic_agent.agent_info.agent_name} received response:")
        print_message(message, "  ")

    strategic_agent.on_message(MessageType.RESPONSE, strategic_response_handler)

    # Operational agent handles requests
    async def operational_request_handler(message: A2AMessage):
        """Handle requests for operational agent."""
        print(f"📥 {operational_agent.agent_info.agent_name} received request:")
        print_message(message, "  ")

        # Send response
        response = create_response(
            message,
            {
                'resource_availability': {
                    'personnel': 25,
                    'budget_capacity': 1000000,
                    'timeline': '2026-Q1'
                }
            }
        )
        await message_bus.route(response)
        print(f"✅ {operational_agent.agent_info.agent_name} sent response\n")

    operational_agent.on_message(MessageType.REQUEST, operational_request_handler)

    # Start all agents
    await strategic_agent.start()
    await financial_agent.start()
    await operational_agent.start()
    print("✓ All agents started and listening")

    # ========================================================================
    # STEP 3: Strategic Agent Assigns Task to Financial Agent
    # ========================================================================

    print_section("STEP 3: Strategic Agent Assigns Budget Task")

    task_message = (strategic_agent.create_message()
        .to_agent(
            agent_id=financial_agent.agent_info.agent_id,
            agent_name=financial_agent.agent_info.agent_name
        )
        .message_type(MessageType.TASK_ASSIGNMENT)
        .priority(Priority.HIGH)
        .content({
            'task': 'Create FY2026 strategic initiative budget',
            'requirements': {
                'timeframe': '2026-01-01 to 2026-12-31',
                'total_budget': 5000000,
                'initiatives': ['digital_transformation', 'market_expansion']
            }
        })
        .metadata(
            apqc_process='9.2',
            urgency='high',
            stakeholders=['CFO', 'CTO']
        )
        .context(
            conversation_id='conv_strategic_planning_2026',
            turn_number=1,
            parent_task_id='task_strategic_planning_2026'
        )
        .ttl(3600)
        .build()
    )

    print(f"📤 {strategic_agent.agent_info.agent_name} sending task assignment:")
    print_message(task_message, "  ")

    await message_bus.route(task_message)

    # Wait for processing
    await asyncio.sleep(1.0)

    # ========================================================================
    # STEP 4: Request-Response Pattern
    # ========================================================================

    print_section("STEP 4: Strategic Agent Requests Resource Information")

    request_message = (strategic_agent.create_message()
        .to_agent(
            agent_id=operational_agent.agent_info.agent_id,
            agent_name=operational_agent.agent_info.agent_name
        )
        .message_type(MessageType.REQUEST)
        .priority(Priority.NORMAL)
        .content({
            'query': 'resource_availability',
            'for_project': 'digital_transformation',
            'timeframe': '2026-Q1'
        })
        .build()
    )

    print(f"📤 {strategic_agent.agent_info.agent_name} sending request:")
    print_message(request_message, "  ")

    await message_bus.route(request_message)

    # Wait for processing
    await asyncio.sleep(1.0)

    # ========================================================================
    # STEP 5: Secure Communication with JWT
    # ========================================================================

    print_section("STEP 5: Secure Communication with JWT Authentication")

    secure_message = (strategic_agent.create_message()
        .to_agent(
            agent_id=financial_agent.agent_info.agent_id,
            agent_name=financial_agent.agent_info.agent_name
        )
        .message_type(MessageType.REQUEST)
        .priority(Priority.HIGH)
        .content({
            'query': 'financial_forecast',
            'year': 2026,
            'categories': ['revenue', 'expenses', 'profit']
        })
        .with_jwt_auth("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token")
        .build()
    )

    print(f"📤 Sending secure message with JWT authentication")
    print(f"  Security: {secure_message.envelope.security.authentication.method}")
    print(f"  Message Type: {secure_message.envelope.message_type}")
    print(f"  Priority: {secure_message.envelope.priority}")
    print()

    # ========================================================================
    # STEP 6: Broadcasting System Events
    # ========================================================================

    print_section("STEP 6: Broadcasting System Events")

    # Subscribe agents to system events
    message_bus.subscribe(financial_agent.agent_info.agent_id, "system.events")
    message_bus.subscribe(operational_agent.agent_info.agent_id, "system.events")

    # Create system event handler
    async def system_event_handler(message: A2AMessage):
        """Handle system events."""
        agent_name = message.envelope.to_agent.agent_name if hasattr(message.envelope.to_agent, 'agent_name') else "Unknown"
        print(f"📢 Event received by agent")
        print(f"   Event: {message.payload.content.get('event_type', 'unknown')}")

    financial_agent.on_message(MessageType.EVENT, system_event_handler)
    operational_agent.on_message(MessageType.EVENT, system_event_handler)

    # Broadcast system event
    system_event = (strategic_agent.create_message()
        .to_agent(agent_id="broadcast", agent_name="All Agents")
        .message_type(MessageType.EVENT)
        .priority(Priority.NORMAL)
        .content({
            'event_type': 'system_maintenance_scheduled',
            'maintenance_window': '2026-01-15 02:00 - 04:00 UTC',
            'affected_services': ['budget_planning', 'resource_allocation']
        })
        .build()
    )

    print(f"📢 Broadcasting system event to all subscribed agents")
    await message_bus.broadcast(system_event, "system.events")

    # Wait for processing
    await asyncio.sleep(1.0)

    # ========================================================================
    # STEP 7: Error Handling
    # ========================================================================

    print_section("STEP 7: Error Handling")

    # Create an invalid request
    error_request = (strategic_agent.create_message()
        .to_agent(
            agent_id=financial_agent.agent_info.agent_id,
            agent_name=financial_agent.agent_info.agent_name
        )
        .message_type(MessageType.REQUEST)
        .content({
            'query': 'invalid_operation',
            'parameter': 'invalid'
        })
        .build()
    )

    # Send error response
    error_response = create_error(
        error_request,
        "Invalid operation requested",
        "INVALID_OPERATION"
    )

    print(f"❌ Error response created:")
    print_message(error_response, "  ")

    # ========================================================================
    # STEP 8: Message with Attachment
    # ========================================================================

    print_section("STEP 8: Sending Message with Attachment")

    # Create message with attachment
    import base64
    attachment_data = base64.b64encode(b'{"budget": 5000000, "breakdown": "..."}').decode('utf-8')

    message_with_attachment = (strategic_agent.create_message()
        .to_agent(
            agent_id=financial_agent.agent_info.agent_id,
            agent_name=financial_agent.agent_info.agent_name
        )
        .message_type(MessageType.TASK_ASSIGNMENT)
        .content({
            'task': 'Review attached budget proposal',
            'instructions': 'Please analyze the budget breakdown in the attachment'
        })
        .attach(
            filename="budget_proposal.json",
            content_type="application/json",
            data=attachment_data,
            size=len(attachment_data)
        )
        .build()
    )

    print(f"📎 Message with attachment created:")
    print(f"  Attachments: {len(message_with_attachment.payload.attachments)}")
    print(f"  Filename: {message_with_attachment.payload.attachments[0].filename}")
    print(f"  Content Type: {message_with_attachment.payload.attachments[0].content_type}")
    print(f"  Size: {message_with_attachment.payload.attachments[0].size} bytes")
    print()

    # ========================================================================
    # STEP 9: Heartbeat Messages
    # ========================================================================

    print_section("STEP 9: Heartbeat Messages for Health Monitoring")

    heartbeat = (financial_agent.create_message()
        .to_agent(agent_id="health_monitor", agent_name="Health Monitor")
        .message_type(MessageType.HEARTBEAT)
        .content({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metrics': {
                'cpu_usage': 0.45,
                'memory_usage': 0.62,
                'active_tasks': 3
            }
        })
        .ttl(60)
        .build()
    )

    print(f"💓 Heartbeat message created:")
    print(f"  From: {heartbeat.envelope.from_agent.agent_name}")
    print(f"  Status: {heartbeat.payload.content['status']}")
    print(f"  TTL: {heartbeat.envelope.ttl} seconds")
    print()

    # ========================================================================
    # STEP 10: Summary Statistics
    # ========================================================================

    print_section("STEP 10: Demo Summary")

    print("Agents Registered:")
    print(f"  • {strategic_agent.agent_info.agent_name}")
    print(f"  • {financial_agent.agent_info.agent_name}")
    print(f"  • {operational_agent.agent_info.agent_name}")
    print()

    print("Message Types Demonstrated:")
    print(f"  • Task Assignment (with priority and TTL)")
    print(f"  • Request-Response Pattern")
    print(f"  • Secure Communication (JWT)")
    print(f"  • System Events (Broadcast)")
    print(f"  • Error Handling")
    print(f"  • Attachments")
    print(f"  • Heartbeat")
    print()

    print("Features Showcased:")
    print(f"  ✓ Message routing via bus")
    print(f"  ✓ Priority handling")
    print(f"  ✓ TTL and expiration")
    print(f"  ✓ JWT authentication")
    print(f"  ✓ Correlation IDs (request-response)")
    print(f"  ✓ Execution context")
    print(f"  ✓ Metadata")
    print(f"  ✓ Topic-based subscriptions")
    print(f"  ✓ Attachments with encoding")
    print()

    # Stop all agents
    await strategic_agent.stop()
    await financial_agent.stop()
    await operational_agent.stop()

    print("\n" + "="*80)
    print("  Demo completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
