"""
API Integration Tests

Tests for REST API endpoints ensuring proper functionality.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_endpoint(self, api_client):
        """Test /health endpoint returns healthy status"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'protocols' in data
        assert 'features' in data

    def test_api_health_endpoint(self, api_client):
        """Test /api/health endpoint (alternative path)"""
        response = api_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert data['protocols']['anp'] == 'operational'
        assert data['protocols']['acp'] == 'operational'


@pytest.mark.api
class TestEnsembleEndpoints:
    """Test ensemble management endpoints"""

    def test_list_ensembles(self, api_client):
        """Test listing all ensembles"""
        response = api_client.get("/api/ensemble")

        assert response.status_code == 200
        data = response.json()

        assert 'ensembles' in data

    def test_get_ensemble_stats(self, api_client):
        """Test getting ensemble statistics"""
        response = api_client.get("/api/ensemble/stats")

        assert response.status_code == 200
        data = response.json()

        assert 'total_ensembles' in data


@pytest.mark.api
class TestTemplateEndpoints:
    """Test template library endpoints"""

    def test_list_templates(self, api_client):
        """Test listing all templates"""
        response = api_client.get("/api/ensemble/templates")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0  # Should have built-in templates

    def test_get_template(self, api_client):
        """Test getting specific template"""
        # First get list of templates
        list_response = api_client.get("/api/ensemble/templates")
        templates = list_response.json()

        if templates:
            template_id = templates[0]['template_id']

            response = api_client.get(f"/api/ensemble/templates/{template_id}")

            assert response.status_code == 200
            data = response.json()

            assert data['template_id'] == template_id
            assert 'name' in data
            assert 'specialists' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
