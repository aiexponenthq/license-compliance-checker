
from lcc.models import ScanReport, ComponentFinding, Component, ComponentType
from lcc.reporting.attribution import AttributionReporter

def test_attribution_reporter():
    """Verify AttributionReporter grouping and text injection."""
    
    # 1. Create Dummy Report
    findings = [
        ComponentFinding(
            component=Component(type=ComponentType.PYTHON, name="requests", version="2.31.0"),
            resolved_license="Apache-2.0"
        ),
        ComponentFinding(
            component=Component(type=ComponentType.PYTHON, name="flask", version="3.0.0"),
            resolved_license="BSD-3-Clause"
        ),
        ComponentFinding(
            component=Component(type=ComponentType.PYTHON, name="pandas", version="2.0.0"),
            resolved_license="BSD-3-Clause"
        ),
        ComponentFinding(
            component=Component(type=ComponentType.PYTHON, name="unknown-lib", version="0.1.0"),
            resolved_license="UNKNOWN"
        )
    ]
    
    # Create minimal summary (fields not used by reporter but required by type)
    from lcc.models import ScanSummary
    summary = ScanSummary(component_count=4, violations=0)
    report = ScanReport(findings=findings, summary=summary)
    
    # 2. Render with Mocked Loader
    from unittest.mock import patch, MagicMock
    
    with patch("lcc.reporting.attribution.LicenseLoader") as MockLoader:
        instance = MockLoader.return_value
        instance.get_license_text.side_effect = lambda lid: f"Mock Text for {lid}" if lid != "UNKNOWN" else None
        
        reporter = AttributionReporter()
        output = reporter.render(report)
    
    # 3. Verify Output Structrue
    
    # Header
    assert "OPEN SOURCE SOFTWARE NOTICE" in output
    
    # Table of Contents
    assert "requests 2.31.0 (Apache-2.0)" in output
    assert "flask 3.0.0 (BSD-3-Clause)" in output
    
    # License Sections
    assert "License: Apache-2.0" in output
    assert "License: BSD-3-Clause" in output
    assert "License: UNKNOWN" in output
    
    # Component Grouping
    # Flask and Pandas should appear under BSD-3-Clause section
    # This check is slightly brittle to formatting but ensures they are present
    assert "flask 3.0.0" in output
    assert "pandas 2.0.0" in output
    
    # License Text Injection (Mocked)
    assert "Mock Text for Apache-2.0" in output
    assert "Mock Text for BSD-3-Clause" in output
    
    # Fallback for unknown text
    assert "[Full text for UNKNOWN not available" in output
