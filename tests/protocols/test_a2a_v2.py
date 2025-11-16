"""
Unit Tests for Agent-to-Agent Protocol (A2A) v2.0

Comprehensive tests ensuring:
- Data model creation and validation
- Message envelope and payload handling
- Security features (authentication, encryption, signatures)
- Message routing and delivery
- Priority and TTL handling
- Attachment support with checksums
- Request-response patterns
- Message bus functionality
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from superstandard.protocols.a2a_v2 import (
    # Enums
    MessageType,
    Priority,
    AuthMethod,
    EncryptionAlgorithm,
    SignatureAlgorithm,
    ContentEncoding,
    ChecksumAlgorithm,

    # Data Models
    AgentInfo,
    Authentication,
    Encryption,
    Signature,
    SecurityMetadata,
    A2AEnvelope,
    ExecutionContext,
    Checksum,
    Attachment,
    A2APayload,
    A2AMessage,

    # Builders and Clients
    A2AMessageBuilder,
    A2AClient,
    A2AMessageBus,

    # Validation
    validate_a2a_message,
    create_response,
    create_error,
)


@pytest.mark.unit
class TestDataModels:
    """Test A2A data models."""

    def test_agent_info_creation(self):
        """Test creating agent info."""
        agent = AgentInfo(
            agent_id="apqc_1_0_strategic",
            agent_name="Strategic Planning Agent",
            agent_type="strategic",
            version="1.0.0",
            capabilities=["analysis", "planning"],
            endpoint="https://agent.example.com"
        )

        assert agent.agent_id == "apqc_1_0_strategic"
        assert agent.agent_name == "Strategic Planning Agent"
        assert "analysis" in agent.capabilities
        assert agent.endpoint == "https://agent.example.com"

    def test_agent_info_to_dict(self):
        """Test agent info serialization."""
        agent = AgentInfo(
            agent_id="test_agent",
            agent_name="Test Agent"
        )

        data = agent.to_dict()
        assert data['agent_id'] == "test_agent"
        assert data['agent_name'] == "Test Agent"

    def test_agent_info_from_dict(self):
        """Test agent info deserialization."""
        data = {
            'agent_id': "apqc_9_2",
            'agent_name': "Budget Agent",
            'agent_type': "financial"
        }

        agent = AgentInfo.from_dict(data)
        assert agent.agent_id == "apqc_9_2"
        assert agent.agent_name == "Budget Agent"
        assert agent.agent_type == "financial"

    def test_security_metadata_jwt(self):
        """Test security metadata with JWT."""
        auth = Authentication(
            method=AuthMethod.JWT.value,
            token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )

        security = SecurityMetadata(authentication=auth)
        data = security.to_dict()

        assert data['authentication']['method'] == "jwt"
        assert 'token' in data['authentication']

    def test_security_metadata_did(self):
        """Test security metadata with DID."""
        auth = Authentication(
            method=AuthMethod.DID.value,
            did="did:example:123456"
        )

        security = SecurityMetadata(authentication=auth)
        data = security.to_dict()

        assert data['authentication']['method'] == "did"
        assert data['authentication']['did'] == "did:example:123456"

    def test_security_metadata_signature(self):
        """Test message signature."""
        sig = Signature(
            algorithm=SignatureAlgorithm.ED25519.value,
            signature="base64_encoded_signature",
            public_key="base64_encoded_public_key"
        )

        security = SecurityMetadata(signature=sig)
        data = security.to_dict()

        assert data['signature']['algorithm'] == "ed25519"
        assert 'signature' in data['signature']
        assert 'public_key' in data['signature']

    def test_execution_context(self):
        """Test execution context."""
        context = ExecutionContext(
            conversation_id="conv_123",
            turn_number=5,
            parent_task_id="task_parent",
            workspace_path="/workspace/project"
        )

        assert context.conversation_id == "conv_123"
        assert context.turn_number == 5
        assert context.workspace_path == "/workspace/project"

    def test_attachment_with_checksum(self):
        """Test attachment with checksum."""
        checksum = Checksum(
            algorithm=ChecksumAlgorithm.SHA256.value,
            value="abc123..."
        )

        attachment = Attachment(
            filename="report.pdf",
            content_type="application/pdf",
            size=1024,
            data="base64_encoded_data",
            checksum=checksum
        )

        assert attachment.filename == "report.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size == 1024
        assert attachment.checksum.algorithm == "sha256"

    def test_attachment_to_dict(self):
        """Test attachment serialization."""
        attachment = Attachment(
            filename="data.json",
            content_type="application/json",
            data="eyJmb28iOiJiYXIifQ=="
        )

        data = attachment.to_dict()
        assert data['filename'] == "data.json"
        assert data['content_type'] == "application/json"
        assert 'data' in data


@pytest.mark.unit
class TestEnvelope:
    """Test A2A envelope functionality."""

    def test_envelope_creation(self):
        """Test creating an envelope."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="550e8400-e29b-41d4-a716-446655440000",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            message_type=MessageType.REQUEST.value
        )

        assert envelope.protocol == "A2A"
        assert envelope.version == "2.0.0"
        assert envelope.message_type == "request"
        assert envelope.priority == Priority.NORMAL.value

    def test_envelope_with_ttl(self):
        """Test envelope with TTL."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="test-msg-1",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            message_type=MessageType.REQUEST.value,
            ttl=3600
        )

        assert envelope.ttl == 3600
        assert envelope.expires_at is not None
        assert not envelope.is_expired()

    def test_envelope_expiration(self):
        """Test envelope expiration check."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        past_time = (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z'

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="test-msg-expired",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=past_time,
            message_type=MessageType.REQUEST.value,
            ttl=60  # 1 minute
        )

        assert envelope.is_expired()

    def test_envelope_priority(self):
        """Test envelope with different priorities."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        for priority in [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.CRITICAL]:
            envelope = A2AEnvelope(
                protocol="A2A",
                version="2.0.0",
                message_id=f"msg-{priority.value}",
                from_agent=from_agent,
                to_agent=to_agent,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                message_type=MessageType.REQUEST.value,
                priority=priority.value
            )

            assert envelope.priority == priority.value


@pytest.mark.unit
class TestPayload:
    """Test A2A payload functionality."""

    def test_payload_with_dict_content(self):
        """Test payload with dictionary content."""
        payload = A2APayload(
            content={'task': 'analyze', 'data': [1, 2, 3]}
        )

        assert isinstance(payload.content, dict)
        assert payload.content['task'] == 'analyze'

    def test_payload_with_string_content(self):
        """Test payload with string content."""
        payload = A2APayload(
            content="Simple text message"
        )

        assert isinstance(payload.content, str)
        assert payload.content == "Simple text message"

    def test_payload_with_metadata(self):
        """Test payload with metadata."""
        payload = A2APayload(
            content={'action': 'execute'},
            metadata={'priority': 'high', 'category': 'finance'}
        )

        assert payload.metadata['priority'] == 'high'
        assert payload.metadata['category'] == 'finance'

    def test_payload_with_context(self):
        """Test payload with execution context."""
        context = ExecutionContext(
            conversation_id="conv_456",
            turn_number=3
        )

        payload = A2APayload(
            content={'data': 'test'},
            context=context
        )

        assert payload.context.conversation_id == "conv_456"
        assert payload.context.turn_number == 3

    def test_payload_with_attachments(self):
        """Test payload with attachments."""
        attachment = Attachment(
            filename="config.json",
            content_type="application/json",
            data="eyJrZXkiOiJ2YWx1ZSJ9"
        )

        payload = A2APayload(
            content={'message': 'See attachment'},
            attachments=[attachment]
        )

        assert len(payload.attachments) == 1
        assert payload.attachments[0].filename == "config.json"


@pytest.mark.unit
class TestMessage:
    """Test complete A2A messages."""

    def test_message_creation(self):
        """Test creating a complete message."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="msg-001",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            message_type=MessageType.TASK_ASSIGNMENT.value
        )

        payload = A2APayload(
            content={'task': 'Create budget', 'deadline': '2026-01-31'}
        )

        message = A2AMessage(envelope=envelope, payload=payload)

        assert message.envelope.message_type == "task_assignment"
        assert message.payload.content['task'] == 'Create budget'

    def test_message_validation(self):
        """Test message validation."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="msg-valid",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            message_type=MessageType.REQUEST.value
        )

        payload = A2APayload(content={'query': 'status'})
        message = A2AMessage(envelope=envelope, payload=payload)

        assert message.is_valid()

    def test_message_to_json(self):
        """Test message JSON serialization."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="msg-json",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            message_type=MessageType.EVENT.value
        )

        payload = A2APayload(content={'event': 'system_start'})
        message = A2AMessage(envelope=envelope, payload=payload)

        json_str = message.to_json()
        assert isinstance(json_str, str)

        # Verify it can be parsed
        data = json.loads(json_str)
        assert data['envelope']['protocol'] == "A2A"
        assert data['payload']['content']['event'] == 'system_start'

    def test_message_from_json(self):
        """Test message JSON deserialization."""
        json_data = {
            'envelope': {
                'protocol': 'A2A',
                'version': '2.0.0',
                'message_id': 'msg-from-json',
                'from_agent': {
                    'agent_id': 'agent_1',
                    'agent_name': 'Agent 1'
                },
                'to_agent': {
                    'agent_id': 'agent_2',
                    'agent_name': 'Agent 2'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'message_type': 'notification'
            },
            'payload': {
                'content': 'Test notification'
            }
        }

        message = A2AMessage.from_dict(json_data)

        assert message.envelope.message_id == 'msg-from-json'
        assert message.envelope.message_type == 'notification'
        assert message.payload.content == 'Test notification'


@pytest.mark.unit
class TestMessageBuilder:
    """Test A2A message builder."""

    def test_builder_basic_message(self):
        """Test building a basic message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        assert message.envelope.from_agent.agent_id == "agent_1"
        assert message.envelope.to_agent.agent_id == "agent_2"
        assert message.envelope.message_type == "request"
        assert message.payload.content['query'] == 'status'

    def test_builder_with_metadata(self):
        """Test builder with metadata."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.TASK_ASSIGNMENT)
            .content({'task': 'analyze'})
            .metadata(priority='high', category='finance')
            .build()
        )

        assert message.payload.metadata['priority'] == 'high'
        assert message.payload.metadata['category'] == 'finance'

    def test_builder_with_context(self):
        """Test builder with execution context."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'data': 'test'})
            .context(conversation_id="conv_789", turn_number=2)
            .build()
        )

        assert message.payload.context.conversation_id == "conv_789"
        assert message.payload.context.turn_number == 2

    def test_builder_with_priority(self):
        """Test builder with priority."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.ERROR)
            .priority(Priority.CRITICAL)
            .content({'error': 'System failure'})
            .build()
        )

        assert message.envelope.priority == "critical"

    def test_builder_with_ttl(self):
        """Test builder with TTL."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.HEARTBEAT)
            .content({'status': 'alive'})
            .ttl(300)
            .build()
        )

        assert message.envelope.ttl == 300
        assert message.envelope.expires_at is not None

    def test_builder_with_correlation_id(self):
        """Test builder with correlation ID."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.RESPONSE)
            .correlation_id("original-request-id")
            .content({'result': 'success'})
            .build()
        )

        assert message.envelope.correlation_id == "original-request-id"

    def test_builder_with_jwt_auth(self):
        """Test builder with JWT authentication."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'data'})
            .with_jwt_auth("jwt_token_here")
            .build()
        )

        assert message.envelope.security is not None
        assert message.envelope.security.authentication.method == "jwt"
        assert message.envelope.security.authentication.token == "jwt_token_here"

    def test_builder_with_did_auth(self):
        """Test builder with DID authentication."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'data'})
            .with_did_auth("did:example:123")
            .build()
        )

        assert message.envelope.security is not None
        assert message.envelope.security.authentication.method == "did"
        assert message.envelope.security.authentication.did == "did:example:123"

    def test_builder_with_attachment(self):
        """Test builder with attachment."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'message': 'See attached file'})
            .attach(filename="doc.txt", content_type="text/plain", data="SGVsbG8gV29ybGQ=")
            .build()
        )

        assert len(message.payload.attachments) == 1
        assert message.payload.attachments[0].filename == "doc.txt"

    def test_builder_missing_required_fields(self):
        """Test builder with missing required fields."""
        with pytest.raises(ValueError):
            (A2AMessageBuilder()
                .from_agent(agent_id="agent_1", agent_name="Agent 1")
                .content({'data': 'test'})
                .build()  # Missing to_agent
            )


@pytest.mark.unit
class TestValidation:
    """Test validation functions."""

    def test_validate_valid_message(self):
        """Test validation of a valid message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        assert validate_a2a_message(message)

    def test_validate_expired_message(self):
        """Test validation of expired message."""
        from_agent = AgentInfo(agent_id="agent_1", agent_name="Agent 1")
        to_agent = AgentInfo(agent_id="agent_2", agent_name="Agent 2")

        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'

        envelope = A2AEnvelope(
            protocol="A2A",
            version="2.0.0",
            message_id="expired-msg",
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=past_time,
            message_type=MessageType.REQUEST.value,
            ttl=60
        )

        payload = A2APayload(content={'data': 'test'})
        message = A2AMessage(envelope=envelope, payload=payload)

        assert not validate_a2a_message(message)

    def test_create_response(self):
        """Test creating a response to a request."""
        request = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        response = create_response(request, {'status': 'running'})

        assert response.envelope.message_type == "response"
        assert response.envelope.from_agent.agent_id == "agent_2"
        assert response.envelope.to_agent.agent_id == "agent_1"
        assert response.envelope.correlation_id == request.envelope.message_id
        assert response.payload.content['status'] == 'running'

    def test_create_error(self):
        """Test creating an error response."""
        request = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'data'})
            .build()
        )

        error = create_error(request, "Resource not found", "NOT_FOUND")

        assert error.envelope.message_type == "error"
        assert error.envelope.priority == "high"
        assert error.payload.content['error'] == "Resource not found"
        assert error.payload.content['error_code'] == "NOT_FOUND"


@pytest.mark.asyncio
class TestA2AClient:
    """Test A2A client functionality."""

    async def test_client_creation(self):
        """Test creating an A2A client."""
        client = A2AClient(
            agent_id="test_agent",
            agent_name="Test Agent",
            agent_type="test"
        )

        assert client.agent_info.agent_id == "test_agent"
        assert client.agent_info.agent_name == "Test Agent"

    async def test_client_message_builder(self):
        """Test client message builder."""
        client = A2AClient(
            agent_id="agent_1",
            agent_name="Agent 1"
        )

        message = (client.create_message()
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        assert message.envelope.from_agent.agent_id == "agent_1"
        assert message.envelope.to_agent.agent_id == "agent_2"

    async def test_client_send_message(self):
        """Test sending a message."""
        client = A2AClient(
            agent_id="agent_1",
            agent_name="Agent 1"
        )

        message = (client.create_message()
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.HEARTBEAT)
            .content({'status': 'alive'})
            .build()
        )

        # Should not raise an exception
        await client.send(message)

    async def test_client_message_handler(self):
        """Test registering message handlers."""
        client = A2AClient(
            agent_id="agent_1",
            agent_name="Agent 1"
        )

        received_messages = []

        async def handler(message: A2AMessage):
            received_messages.append(message)

        client.on_message(MessageType.REQUEST, handler)

        # Simulate receiving a message
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_2", agent_name="Agent 2")
            .to_agent(agent_id="agent_1", agent_name="Agent 1")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        await client.receive(message)
        await client.start()

        # Give time for processing
        await asyncio.sleep(0.1)

        await client.stop()

        assert len(received_messages) > 0


@pytest.mark.asyncio
class TestMessageBus:
    """Test A2A message bus functionality."""

    async def test_bus_creation(self):
        """Test creating a message bus."""
        bus = A2AMessageBus()
        assert bus is not None

    async def test_bus_register_client(self):
        """Test registering clients with the bus."""
        bus = A2AMessageBus()
        client = A2AClient(agent_id="agent_1", agent_name="Agent 1")

        bus.register_client(client)

        # Verify registration
        assert "agent_1" in bus._clients

    async def test_bus_route_message(self):
        """Test routing messages through the bus."""
        bus = A2AMessageBus()

        client1 = A2AClient(agent_id="agent_1", agent_name="Agent 1")
        client2 = A2AClient(agent_id="agent_2", agent_name="Agent 2")

        bus.register_client(client1)
        bus.register_client(client2)

        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.REQUEST)
            .content({'query': 'status'})
            .build()
        )

        await bus.route(message)

        # Verify message was received
        assert not client2._inbox.empty()

    async def test_bus_subscribe_topic(self):
        """Test topic subscription."""
        bus = A2AMessageBus()

        client = A2AClient(agent_id="agent_1", agent_name="Agent 1")
        bus.register_client(client)

        bus.subscribe("agent_1", "finance.updates")

        assert "agent_1" in bus._subscriptions["finance.updates"]

    async def test_bus_broadcast(self):
        """Test broadcasting to topic subscribers."""
        bus = A2AMessageBus()

        client1 = A2AClient(agent_id="agent_1", agent_name="Agent 1")
        client2 = A2AClient(agent_id="agent_2", agent_name="Agent 2")

        bus.register_client(client1)
        bus.register_client(client2)

        bus.subscribe("agent_1", "broadcasts")
        bus.subscribe("agent_2", "broadcasts")

        message = (A2AMessageBuilder()
            .from_agent(agent_id="system", agent_name="System")
            .to_agent(agent_id="broadcast", agent_name="Broadcast")
            .message_type(MessageType.NOTIFICATION)
            .content({'announcement': 'System maintenance'})
            .build()
        )

        await bus.broadcast(message, "broadcasts")

        # Verify both clients received the message
        assert not client1._inbox.empty()
        assert not client2._inbox.empty()


@pytest.mark.unit
class TestMessageTypes:
    """Test all message types."""

    def test_task_assignment_message(self):
        """Test task assignment message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="strategic", agent_name="Strategic Agent")
            .to_agent(agent_id="financial", agent_name="Financial Agent")
            .message_type(MessageType.TASK_ASSIGNMENT)
            .content({
                'task': 'Create budget',
                'deadline': '2026-01-31',
                'budget_amount': 5000000
            })
            .metadata(apqc_process='9.2', urgency='high')
            .build()
        )

        assert message.envelope.message_type == "task_assignment"
        assert message.payload.content['task'] == 'Create budget'

    def test_status_update_message(self):
        """Test status update message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="worker", agent_name="Worker Agent")
            .to_agent(agent_id="manager", agent_name="Manager Agent")
            .message_type(MessageType.STATUS_UPDATE)
            .content({'status': 'in_progress', 'completion': 0.75})
            .build()
        )

        assert message.envelope.message_type == "status_update"
        assert message.payload.content['completion'] == 0.75

    def test_negotiation_message(self):
        """Test negotiation message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="agent_1", agent_name="Agent 1")
            .to_agent(agent_id="agent_2", agent_name="Agent 2")
            .message_type(MessageType.NEGOTIATION)
            .content({
                'proposal': 'resource_allocation',
                'terms': {'cpu': 4, 'memory': '8GB'}
            })
            .build()
        )

        assert message.envelope.message_type == "negotiation"

    def test_discovery_message(self):
        """Test discovery message."""
        message = (A2AMessageBuilder()
            .from_agent(agent_id="requester", agent_name="Requester")
            .to_agent(agent_id="registry", agent_name="Registry")
            .message_type(MessageType.DISCOVERY)
            .content({
                'query': 'capabilities',
                'filter': {'domain': 'finance'}
            })
            .build()
        )

        assert message.envelope.message_type == "discovery"
