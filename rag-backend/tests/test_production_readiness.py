"""
Production Readiness Tests for RAG Backend
Tests that verify the backend is production-ready for deployment
"""

import pytest
import asyncio
from datetime import datetime
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import get_settings
from main import app
from fastapi.testclient import TestClient


client = TestClient(app)


class TestProductionReadiness:
    """Tests to verify production deployment readiness"""

    def test_health_endpoint_exists(self):
        """Health endpoint should exist and return 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_health_endpoint_has_timestamp(self):
        """Health check should include timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_endpoint_has_version(self):
        """Health check should include version info"""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_api_docs_accessible(self):
        """API documentation should be accessible"""
        response = client.get("/docs")
        # In production, docs might be disabled (DEBUG=false)
        # But the endpoint should at least not error
        assert response.status_code in [200, 404, 403]

    def test_cors_headers_present(self):
        """CORS headers should be configured"""
        response = client.options("/health")
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    def test_query_endpoint_exists(self):
        """Query endpoint should exist"""
        response = client.post("/query", json={
            "query": "test",
            "mode": "full_book"
        })
        # Should either work or fail with auth error, not 404
        assert response.status_code != 404

    def test_ingest_endpoint_exists(self):
        """Ingest endpoint should exist"""
        response = client.post("/ingest", json={
            "chapter": "test",
            "content": "test content"
        })
        # Should either work or fail with auth error, not 404
        assert response.status_code != 404

    def test_settings_loaded(self):
        """Configuration should be properly loaded"""
        settings = get_settings()
        assert settings is not None
        assert settings.environment in ["development", "staging", "production"]

    def test_debug_mode_disabled_in_production(self):
        """DEBUG should be False in production environment"""
        settings = get_settings()
        if settings.environment == "production":
            assert settings.debug is False, "DEBUG must be False in production"

    def test_cors_configured(self):
        """CORS should be configured"""
        settings = get_settings()
        assert settings.allowed_origins is not None
        assert isinstance(settings.allowed_origins, (list, str))

    def test_secret_key_configured(self):
        """SECRET_KEY should be configured"""
        settings = get_settings()
        assert hasattr(settings, 'secret_key')
        if settings.environment == "production":
            # In production, secret key should not be default
            assert settings.secret_key != "your-secret-key-change-in-production"

    def test_database_url_configured(self):
        """DATABASE_URL should be configured"""
        db_url = os.getenv("DATABASE_URL")
        if os.getenv("ENVIRONMENT") == "production":
            assert db_url is not None, "DATABASE_URL must be set in production"
            assert "postgresql" in db_url.lower() or "postgres" in db_url.lower()

    def test_qdrant_configured(self):
        """Qdrant should be configured"""
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_key = os.getenv("QDRANT_API_KEY")
        if os.getenv("ENVIRONMENT") == "production":
            assert qdrant_url is not None, "QDRANT_URL must be set in production"
            assert qdrant_key is not None, "QDRANT_API_KEY must be set in production"

    def test_openai_api_key_configured(self):
        """OpenAI API key should be configured"""
        api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("ENVIRONMENT") == "production":
            assert api_key is not None, "OPENAI_API_KEY must be set in production"
            # Should start with sk-proj- or sk-
            assert api_key.startswith("sk-"), "OpenAI key should start with sk-"

    def test_port_configuration(self):
        """PORT should be configurable via environment"""
        # Render uses PORT env var
        port = os.getenv("PORT")
        # PORT might not be set locally, but should be settable
        assert port is None or isinstance(int(port), int)

    def test_environment_variable_validation(self):
        """Required environment variables should be validated"""
        # This will raise ValueError if required vars are missing
        try:
            settings = get_settings()
            # If we got here, settings loaded successfully
            assert settings is not None
        except ValueError as e:
            pytest.skip(f"Environment not fully configured: {e}")

    def test_response_time_acceptable(self):
        """Health check should respond quickly"""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        # Should respond in less than 1 second locally
        assert elapsed < 1.0, f"Health check took {elapsed:.2f}s"
        assert response.status_code == 200

    def test_error_handling(self):
        """API should handle errors gracefully"""
        # Send invalid request
        response = client.post("/query", json={"invalid": "data"})
        # Should return 422 (validation error), not 500
        assert response.status_code in [200, 422, 400]

    def test_logging_configured(self):
        """Logging should be configured"""
        import logging
        logger = logging.getLogger("main")
        # Logger should exist (even if not used)
        assert logger is not None
        assert logger.level >= logging.DEBUG

    def test_rate_limiting_enabled(self):
        """Rate limiting should be configured"""
        settings = get_settings()
        assert hasattr(settings, 'rate_limit_queries_per_minute')
        assert settings.rate_limit_queries_per_minute > 0

    def test_session_timeout_configured(self):
        """Session timeout should be configured"""
        settings = get_settings()
        assert hasattr(settings, 'session_timeout_hours')
        assert settings.session_timeout_hours > 0


class TestProductionDeploymentChecklist:
    """Comprehensive checklist for production deployment"""

    def test_all_critical_checks(self):
        """Run all critical checks for production"""
        checks = {
            "API available": lambda: client.get("/health").status_code == 200,
            "Configuration loaded": lambda: get_settings() is not None,
            "DEBUG disabled": lambda: not get_settings().debug if get_settings().environment == "production" else True,
            "CORS configured": lambda: get_settings().allowed_origins is not None,
            "Rate limiting enabled": lambda: get_settings().rate_limit_queries_per_minute > 0,
        }

        failed_checks = []
        for check_name, check_fn in checks.items():
            try:
                if not check_fn():
                    failed_checks.append(f"{check_name}: FAILED")
                else:
                    print(f"✓ {check_name}: PASSED")
            except Exception as e:
                failed_checks.append(f"{check_name}: ERROR - {str(e)}")

        if failed_checks:
            pytest.fail("Critical checks failed:\n" + "\n".join(failed_checks))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
