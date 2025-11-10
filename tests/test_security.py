"""
Tests for Security Module

Comprehensive tests for authentication, rate limiting, and security features.
"""

import pytest
import time
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os

from superstandard.api.security import (
    AuthLevel,
    verify_api_key,
    RateLimiter,
    verify_websocket_token,
    sanitize_string_input,
    validate_agent_id,
    generate_api_key,
    hash_api_key,
    setup_security
)


# ============================================================================
# Test Configuration
# ============================================================================

TEST_ADMIN_KEY = "test_admin_key_12345"
TEST_CLIENT_KEY = "test_client_key_67890"


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_KEY)
    monkeypatch.setenv("CLIENT_API_KEY", TEST_CLIENT_KEY)
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:8080,http://testserver")


@pytest.fixture
def test_app(mock_env):
    """Create test FastAPI app with security."""
    app = FastAPI()
    setup_security(app)

    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}

    @app.get("/protected")
    async def protected_endpoint(auth_level: str = None):
        verify_api_key(auth_level, AuthLevel.CLIENT)
        return {"message": "protected"}

    @app.get("/admin")
    async def admin_endpoint(auth_level: str = None):
        verify_api_key(auth_level, AuthLevel.ADMIN)
        return {"message": "admin"}

    return app


@pytest.fixture
def client(test_app):
    """Test client."""
    return TestClient(test_app)


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthentication:
    """Test API key authentication."""

    def test_public_endpoint_no_auth(self, client):
        """Public endpoints should work without authentication."""
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public"}

    def test_protected_endpoint_no_key(self, client):
        """Protected endpoints should reject requests without API key."""
        response = client.get("/protected")
        assert response.status_code == 401
        assert "API key is required" in response.json()["detail"]

    def test_protected_endpoint_invalid_key(self, client):
        """Protected endpoints should reject invalid API keys."""
        response = client.get(
            "/protected",
            headers={"X-API-Key": "invalid_key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_protected_endpoint_valid_client_key(self, client, mock_env):
        """Protected endpoints should accept valid client API key."""
        response = client.get(
            "/protected",
            headers={"X-API-Key": TEST_CLIENT_KEY}
        )
        assert response.status_code == 200

    def test_protected_endpoint_valid_admin_key(self, client, mock_env):
        """Protected endpoints should accept valid admin API key."""
        response = client.get(
            "/protected",
            headers={"X-API-Key": TEST_ADMIN_KEY}
        )
        assert response.status_code == 200

    def test_admin_endpoint_client_key_rejected(self, client, mock_env):
        """Admin endpoints should reject client API keys."""
        response = client.get(
            "/admin",
            headers={"X-API-Key": TEST_CLIENT_KEY}
        )
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

    def test_admin_endpoint_admin_key_accepted(self, client, mock_env):
        """Admin endpoints should accept admin API keys."""
        response = client.get(
            "/admin",
            headers={"X-API-Key": TEST_ADMIN_KEY}
        )
        assert response.status_code == 200

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert len(key1) > 20  # Should be reasonably long
        assert key1 != key2  # Should be unique
        assert isinstance(key1, str)

    def test_hash_api_key(self):
        """Test API key hashing."""
        key = "test_key"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)

        assert hash1 == hash2  # Same key should hash to same value
        assert hash1 != key  # Hash should be different from original
        assert len(hash1) == 64  # SHA256 produces 64 char hex string


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        return RateLimiter()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/test"
        return request

    def test_rate_limit_allows_initial_requests(self, rate_limiter, mock_request):
        """Rate limiter should allow initial requests."""
        for _ in range(10):
            assert rate_limiter.check_rate_limit(mock_request) is True

    def test_rate_limit_blocks_excessive_requests(self, rate_limiter, mock_request):
        """Rate limiter should block requests exceeding limit."""
        # Exhaust the token bucket
        for _ in range(100):
            rate_limiter.check_rate_limit(mock_request)

        # Next request should be blocked
        assert rate_limiter.check_rate_limit(mock_request) is False

    def test_rate_limit_refills_over_time(self, rate_limiter, mock_request):
        """Rate limiter should refill tokens over time."""
        # Exhaust tokens
        for _ in range(100):
            rate_limiter.check_rate_limit(mock_request)

        # Should be blocked
        assert rate_limiter.check_rate_limit(mock_request) is False

        # Wait for refill (simulate time passage)
        time.sleep(1)

        # Should allow some requests again
        assert rate_limiter.check_rate_limit(mock_request) is True

    def test_rate_limit_different_clients_separate(self, rate_limiter):
        """Different clients should have separate rate limits."""
        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "192.168.1.1"
        request1.url = Mock()
        request1.url.path = "/test"

        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "192.168.1.2"
        request2.url = Mock()
        request2.url.path = "/test"

        # Exhaust client1's tokens
        for _ in range(100):
            rate_limiter.check_rate_limit(request1)

        # Client1 should be blocked
        assert rate_limiter.check_rate_limit(request1) is False

        # Client2 should still be allowed
        assert rate_limiter.check_rate_limit(request2) is True

    def test_custom_endpoint_limits(self, rate_limiter, mock_request):
        """Test custom rate limits per endpoint."""
        endpoint = "/api/high-rate"
        mock_request.url.path = endpoint

        # Set custom limit: 10 requests per 10 seconds
        rate_limiter.set_limit(endpoint, limit=10, window=10)

        # Should allow up to 10 requests
        for i in range(10):
            assert rate_limiter.check_rate_limit(mock_request, endpoint=endpoint) is True

        # 11th request should be blocked
        assert rate_limiter.check_rate_limit(mock_request, endpoint=endpoint) is False


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """Test input sanitization and validation."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = sanitize_string_input("  hello world  ")
        assert result == "hello world"

    def test_sanitize_string_null_bytes(self):
        """Test removal of null bytes."""
        result = sanitize_string_input("hello\x00world")
        assert result == "helloworld"

    def test_sanitize_string_max_length(self):
        """Test max length enforcement."""
        long_string = "a" * 2000
        result = sanitize_string_input(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_invalid_type(self):
        """Test rejection of non-string types."""
        with pytest.raises(ValueError, match="Input must be a string"):
            sanitize_string_input(12345)

    def test_validate_agent_id_valid(self):
        """Test valid agent ID formats."""
        valid_ids = [
            "agent_001",
            "agent-001",
            "my-agent_123",
            "A",
            "a" * 128  # Max length
        ]
        for agent_id in valid_ids:
            assert validate_agent_id(agent_id) == agent_id

    def test_validate_agent_id_invalid(self):
        """Test invalid agent ID formats."""
        invalid_ids = [
            "",  # Empty
            "a" * 129,  # Too long
            "agent@123",  # Invalid character
            "agent 123",  # Space
            "agent/123",  # Slash
        ]
        for agent_id in invalid_ids:
            with pytest.raises(ValueError):
                validate_agent_id(agent_id)

    def test_validate_agent_id_special_chars(self):
        """Test that only allowed special chars are accepted."""
        assert validate_agent_id("agent-123_test") == "agent-123_test"

        with pytest.raises(ValueError):
            validate_agent_id("agent$123")

        with pytest.raises(ValueError):
            validate_agent_id("agent!123")


# ============================================================================
# WebSocket Authentication Tests
# ============================================================================

class TestWebSocketAuth:
    """Test WebSocket authentication."""

    def test_websocket_token_valid(self, mock_env):
        """Test WebSocket token validation with valid token."""
        assert verify_websocket_token(TEST_ADMIN_KEY) is True
        assert verify_websocket_token(TEST_CLIENT_KEY) is True

    def test_websocket_token_invalid(self, mock_env):
        """Test WebSocket token validation with invalid token."""
        assert verify_websocket_token("invalid_token") is False
        assert verify_websocket_token(None) is False
        assert verify_websocket_token("") is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestSecurityIntegration:
    """Integration tests for complete security setup."""

    def test_security_headers_added(self, client):
        """Test that security headers are added to responses."""
        response = client.get("/public")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured."""
        response = client.options(
            "/public",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert "access-control-allow-origin" in response.headers

    def test_rate_limit_headers_on_limit(self, test_app):
        """Test that rate limit headers are present when limited."""
        # This would require actually hitting the rate limit
        # Implementation depends on how rate limiter is integrated
        pass


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
