"""Warning analysis and explanation for license compliance."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WarningType(str, Enum):
    """Types of license warnings."""
    COMPLEX_LICENSE = "complex_license"
    COPYLEFT_LICENSE = "copyleft_license"
    UNKNOWN_LICENSE = "unknown_license"
    DUAL_LICENSE = "dual_license"
    DEPRECATED_LICENSE = "deprecated_license"
    WEAK_COPYLEFT = "weak_copyleft"
    UNCOMMON_LICENSE = "uncommon_license"


class WarningSeverity(str, Enum):
    """Warning severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WarningDetail(BaseModel):
    """Detailed warning information."""
    component_name: str
    component_version: Optional[str] = None
    license: str
    warning_type: WarningType
    severity: WarningSeverity
    message: str
    explanation: str
    recommendation: str
    details: Dict[str, object] = Field(default_factory=dict)
    learn_more_url: Optional[str] = None


class WarningsSummary(BaseModel):
    """Summary of all warnings."""
    total_warnings: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    warnings: List[WarningDetail] = Field(default_factory=list)


class WarningAnalyzer:
    """Analyze components and generate warning explanations."""

    # Known copyleft licenses
    COPYLEFT_LICENSES = {
        "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later",
        "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
        "AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later",
    }

    WEAK_COPYLEFT_LICENSES = {
        "LGPL-2.0", "LGPL-2.1", "LGPL-3.0",
        "LGPL-2.0-only", "LGPL-2.1-only", "LGPL-3.0-only",
        "LGPL-2.0-or-later", "LGPL-2.1-or-later", "LGPL-3.0-or-later",
        "MPL-2.0", "MPL-1.1", "EPL-1.0", "EPL-2.0"
    }

    UNKNOWN_MARKERS = {"UNKNOWN", "NOASSERTION", "NONE", ""}

    DEPRECATED_LICENSES = {
        "GPL-1.0", "GPL-2.0", "LGPL-2.0", "Apache-1.0", "Apache-1.1"
    }

    @staticmethod
    def analyze_component(
        name: str,
        version: Optional[str],
        license_str: str,
        status: str
    ) -> Optional[WarningDetail]:
        """Analyze a component and return warning if applicable."""
        if status != "warning":
            return None

        # Normalize license string
        license_str = license_str.strip()

        # Check for complex license expressions
        if " AND " in license_str or " OR " in license_str:
            return WarningAnalyzer._create_complex_license_warning(
                name, version, license_str
            )

        # Check for unknown licenses
        if any(marker in license_str.upper() for marker in WarningAnalyzer.UNKNOWN_MARKERS):
            return WarningAnalyzer._create_unknown_license_warning(
                name, version, license_str
            )

        # Check for strong copyleft
        if any(gpl in license_str for gpl in WarningAnalyzer.COPYLEFT_LICENSES):
            return WarningAnalyzer._create_copyleft_warning(
                name, version, license_str, strong=True
            )

        # Check for weak copyleft
        if any(lgpl in license_str for lgpl in WarningAnalyzer.WEAK_COPYLEFT_LICENSES):
            return WarningAnalyzer._create_copyleft_warning(
                name, version, license_str, strong=False
            )

        # Check for deprecated licenses
        if any(dep in license_str for dep in WarningAnalyzer.DEPRECATED_LICENSES):
            return WarningAnalyzer._create_deprecated_warning(
                name, version, license_str
            )

        # Generic warning
        return WarningDetail(
            component_name=name,
            component_version=version,
            license=license_str,
            warning_type=WarningType.UNCOMMON_LICENSE,
            severity=WarningSeverity.LOW,
            message="Uncommon or non-standard license",
            explanation=f"This component uses '{license_str}' which may require review.",
            recommendation="Review the license terms to ensure compatibility with your project.",
            details={"license_text": license_str}
        )

    @staticmethod
    def _create_complex_license_warning(
        name: str,
        version: Optional[str],
        license_str: str
    ) -> WarningDetail:
        """Create warning for complex license expressions."""
        licenses = [
            lic.strip()
            for lic in license_str.replace(" AND ", "|").replace(" OR ", "|").split("|")
        ]

        has_copyleft = any(
            any(gpl in lic for gpl in WarningAnalyzer.COPYLEFT_LICENSES | WarningAnalyzer.WEAK_COPYLEFT_LICENSES)
            for lic in licenses
        )

        has_unknown = any(
            any(marker in lic.upper() for marker in WarningAnalyzer.UNKNOWN_MARKERS)
            for lic in licenses
        )

        severity = WarningSeverity.HIGH if has_copyleft else WarningSeverity.MEDIUM
        if has_unknown:
            severity = WarningSeverity.HIGH

        explanation = (
            f"This component uses a complex license expression combining multiple licenses. "
            f"{'AND' if ' AND ' in license_str else 'OR'} expressions mean you must "
            f"{'comply with ALL licenses listed' if ' AND ' in license_str else 'choose ONE compatible license'}."
        )

        if has_copyleft:
            explanation += " This includes copyleft licenses which may require source code distribution."

        return WarningDetail(
            component_name=name,
            component_version=version,
            license=license_str,
            warning_type=WarningType.COMPLEX_LICENSE,
            severity=severity,
            message="Complex license expression with multiple licenses",
            explanation=explanation,
            recommendation=(
                "Review each license requirement carefully. "
                "Ensure compliance with all licenses if using AND expression, "
                "or choose a compatible license if using OR expression. "
                "Consider legal review for commercial use."
            ),
            details={
                "licenses_involved": licenses,
                "has_copyleft": has_copyleft,
                "has_unknown": has_unknown,
                "operator": "AND" if " AND " in license_str else "OR"
            },
            learn_more_url="https://spdx.org/licenses/license-expressions"
        )

    @staticmethod
    def _create_copyleft_warning(
        name: str,
        version: Optional[str],
        license_str: str,
        strong: bool
    ) -> WarningDetail:
        """Create warning for copyleft licenses."""
        if strong:
            warning_type = WarningType.COPYLEFT_LICENSE
            severity = WarningSeverity.HIGH
            message = "Strong copyleft license detected (GPL/AGPL)"
            explanation = (
                f"This component uses {license_str}, a strong copyleft license. "
                "This means any derivative work must also be licensed under the same terms, "
                "and source code must be made available to users."
            )
            recommendation = (
                "Review GPL/AGPL requirements carefully. "
                "If distributing: (1) Make source code available, "
                "(2) License derivative works under GPL/AGPL, "
                "(3) Include copyright notices. "
                "Consider alternatives or legal consultation."
            )
        else:
            warning_type = WarningType.WEAK_COPYLEFT
            severity = WarningSeverity.MEDIUM
            message = "Weak copyleft license detected (LGPL/MPL/EPL)"
            explanation = (
                f"This component uses {license_str}, a weak copyleft license. "
                "Modifications to the library must be shared, but your own code "
                "can remain proprietary if properly separated."
            )
            recommendation = (
                "Review LGPL/MPL requirements. "
                "If dynamically linking (recommended), your code can remain proprietary. "
                "If statically linking or modifying the library, you must share those changes. "
                "Include copyright notices and license text."
            )

        return WarningDetail(
            component_name=name,
            component_version=version,
            license=license_str,
            warning_type=warning_type,
            severity=severity,
            message=message,
            explanation=explanation,
            recommendation=recommendation,
            details={
                "copyleft_type": "strong" if strong else "weak",
                "requires_source_distribution": strong,
                "allows_proprietary_linking": not strong
            },
            learn_more_url=(
                "https://www.gnu.org/licenses/gpl-3.0.html" if strong
                else "https://www.gnu.org/licenses/lgpl-3.0.html"
            )
        )

    @staticmethod
    def _create_unknown_license_warning(
        name: str,
        version: Optional[str],
        license_str: str
    ) -> WarningDetail:
        """Create warning for unknown licenses."""
        return WarningDetail(
            component_name=name,
            component_version=version,
            license=license_str,
            warning_type=WarningType.UNKNOWN_LICENSE,
            severity=WarningSeverity.HIGH,
            message="Unknown or unspecified license",
            explanation=(
                "This component's license could not be determined. "
                "It may be unlicensed (all rights reserved), use a custom license, "
                "or have incomplete license metadata."
            ),
            recommendation=(
                "1. Check the component's repository for a LICENSE file, "
                "2. Review package documentation for license information, "
                "3. Contact the package maintainer for clarification, "
                "4. Consider using an alternative with a clear license. "
                "Do not use in production without knowing the license terms."
            ),
            details={
                "no_license_found": True,
                "risk_level": "high"
            },
            learn_more_url="https://choosealicense.com/"
        )

    @staticmethod
    def _create_deprecated_warning(
        name: str,
        version: Optional[str],
        license_str: str
    ) -> WarningDetail:
        """Create warning for deprecated licenses."""
        return WarningDetail(
            component_name=name,
            component_version=version,
            license=license_str,
            warning_type=WarningType.DEPRECATED_LICENSE,
            severity=WarningSeverity.MEDIUM,
            message="Deprecated license version",
            explanation=(
                f"This component uses {license_str}, which is a deprecated version. "
                "Newer versions of the license may have important clarifications or fixes."
            ),
            recommendation=(
                "Check if a newer version of this component uses an updated license. "
                "Review the current license terms for any known issues. "
                "Consider updating to a newer version if available."
            ),
            details={
                "deprecated": True,
                "license_family": license_str.split("-")[0]
            }
        )

    @staticmethod
    def analyze_scan(components: List[Dict]) -> WarningsSummary:
        """Analyze all components and generate warnings summary.

        Args:
            components: List of component result dictionaries with structure:
                {
                    "component": {"name": str, "version": str, ...},
                    "status": str ("pass", "warning", "violation", "error"),
                    "licenses": [{"license_expression": str, ...}],
                    ...
                }
        """
        warnings: List[WarningDetail] = []

        for comp_result in components:
            # Extract component info from component_result structure
            component = comp_result.get("component", {})
            status = comp_result.get("status", "unknown")

            # Get license from first license evidence if available
            licenses = comp_result.get("licenses", [])
            license_str = licenses[0].get("license_expression", "UNKNOWN") if licenses else "UNKNOWN"

            warning = WarningAnalyzer.analyze_component(
                name=component.get("name", "Unknown"),
                version=component.get("version"),
                license_str=license_str,
                status=status
            )
            if warning:
                warnings.append(warning)

        # Count by type and severity
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for warning in warnings:
            by_type[warning.warning_type] = by_type.get(warning.warning_type, 0) + 1
            by_severity[warning.severity] = by_severity.get(warning.severity, 0) + 1

        return WarningsSummary(
            total_warnings=len(warnings),
            by_type=by_type,
            by_severity=by_severity,
            warnings=warnings
        )
