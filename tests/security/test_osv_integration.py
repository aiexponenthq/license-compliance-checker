
import pytest
from unittest.mock import MagicMock, patch
from lcc.security.osv_client import OSVClient
from lcc.security.scanner import SecurityScanner
from lcc.models import ComponentType, Component, ComponentFinding

@pytest.fixture
def mock_response():
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "vulns": [
            {"id": "CVE-2023-1234", "summary": "Test Vulnerability"}
        ]
    }
    return resp

def test_osv_client_query(mock_response):
    """Verify OSVClient constructs correct payload and parses response."""
    with patch("requests.Session.post", return_value=mock_response) as mock_post:
        client = OSVClient()
        vulns = client.query_package("requests", "2.19.0", "PyPI")
        
        assert len(vulns) == 1
        assert vulns[0]["id"] == "CVE-2023-1234"
        
        # Check payload
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["package"]["name"] == "requests"
        assert kwargs["json"]["package"]["ecosystem"] == "PyPI"
        assert kwargs["json"]["version"] == "2.19.0"

def test_security_scanner_integration(mock_response):
    """Verify SecurityScanner maps components and calls client."""
    
    findings = [
        ComponentFinding(
            component=Component(type=ComponentType.PYTHON, name="flask", version="0.12")
        ),
        ComponentFinding(
            component=Component(type=ComponentType.GENERIC, name="unk", version="1.0")
        )
    ]
    
    with patch("requests.Session.post", return_value=mock_response) as mock_post:
        scanner = SecurityScanner()
        count = scanner.scan_findings(findings)
        
        # Python component should be scanned
        assert count == 1
        assert findings[0].component.metadata["security"]["vulnerabilities"][0]["id"] == "CVE-2023-1234"
        
        # Generic component should be skipped
        assert "security" not in findings[1].component.metadata
