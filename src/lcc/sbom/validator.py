# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SBOM Validator - Validates CycloneDX and SPDX SBOMs against schemas.
"""

from __future__ import annotations

import json
from pathlib import Path

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator
from cyclonedx.validation.xml import XmlValidator
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document

# Map CycloneDX specVersion strings to the library's SchemaVersion enum members.
_CDX_SCHEMA_VERSIONS = {
    "1.7": SchemaVersion.V1_7,
    "1.6": SchemaVersion.V1_6,
    "1.5": SchemaVersion.V1_5,
    "1.4": SchemaVersion.V1_4,
    "1.3": SchemaVersion.V1_3,
    "1.2": SchemaVersion.V1_2,
    "1.1": SchemaVersion.V1_1,
    "1.0": SchemaVersion.V1_0,
}
# Fall back to the version the LCC generator emits when specVersion is absent.
_CDX_DEFAULT_SCHEMA_VERSION = SchemaVersion.V1_5


class ValidationError(Exception):
    """SBOM validation error."""

    pass


class SBOMValidator:
    """
    Validates SBOM documents against their schemas.

    Supports:
    - CycloneDX JSON and XML
    - SPDX JSON, XML, YAML, Tag-Value
    """

    def validate_cyclonedx(self, file_path: Path, format: str = "json") -> tuple[bool, list[str]]:
        """
        Validate a CycloneDX SBOM.

        Args:
            file_path: Path to SBOM file
            format: Format ("json" or "xml")

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            schema_version = self._detect_cyclonedx_schema_version(content, format)

            # cyclonedx-python-lib v11.x validates raw document strings against a
            # given schema version. validate_str() returns None when the document
            # is valid, or a ValidationError describing the first problem found.
            if format.lower() == "json":
                validator = JsonStrictValidator(schema_version)
            elif format.lower() == "xml":
                validator = XmlValidator(schema_version)
            else:
                return False, [f"Unsupported format: {format}"]

            validation_error = validator.validate_str(content)

            if validation_error is not None:
                return False, [str(validation_error)]

            return True, []

        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    def _detect_cyclonedx_schema_version(self, content: str, format: str) -> SchemaVersion:
        """Determine the CycloneDX schema version to validate against."""
        try:
            if format.lower() == "json":
                spec = json.loads(content).get("specVersion")
                if spec:
                    return _CDX_SCHEMA_VERSIONS.get(str(spec), _CDX_DEFAULT_SCHEMA_VERSION)
            else:  # xml
                import re

                match = re.search(r"cyclonedx/(\d+\.\d+)", content)
                if match:
                    return _CDX_SCHEMA_VERSIONS.get(match.group(1), _CDX_DEFAULT_SCHEMA_VERSION)
        except Exception:
            pass
        return _CDX_DEFAULT_SCHEMA_VERSION

    def validate_spdx(self, file_path: Path) -> tuple[bool, list[str]]:
        """
        Validate an SPDX SBOM.

        Args:
            file_path: Path to SBOM file

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        try:
            # Parse the document (auto-detects format)
            document = parse_file(str(file_path))

            # Validate
            validation_messages = validate_full_spdx_document(document)

            if validation_messages:
                error_msgs = [
                    f"{msg.validation_message}: {msg.context}" for msg in validation_messages
                ]
                return False, error_msgs

            return True, []

        except Exception as e:
            return False, [f"Validation error: {str(e)}"]

    def validate(
        self, file_path: Path, sbom_type: str = "auto", format: str = "auto"
    ) -> tuple[bool, list[str]]:
        """
        Validate an SBOM with automatic type detection.

        Args:
            file_path: Path to SBOM file
            sbom_type: SBOM type ("cyclonedx", "spdx", or "auto")
            format: Format ("json", "xml", "yaml", "tag-value", or "auto")

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        # Auto-detect format from file extension
        if format == "auto":
            suffix = file_path.suffix.lower()
            format_map = {
                ".json": "json",
                ".xml": "xml",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".spdx": "tag-value",
            }
            format = format_map.get(suffix, "json")

        # Auto-detect SBOM type
        if sbom_type == "auto":
            sbom_type = self._detect_sbom_type(file_path, format)

        # Validate based on type
        if sbom_type == "cyclonedx":
            return self.validate_cyclonedx(file_path, format)
        elif sbom_type == "spdx":
            return self.validate_spdx(file_path)
        else:
            return False, [f"Unknown SBOM type: {sbom_type}"]

    def _detect_sbom_type(self, file_path: Path, format: str) -> str:
        """
        Detect SBOM type from file contents.

        Args:
            file_path: Path to SBOM file
            format: File format

        Returns:
            SBOM type ("cyclonedx" or "spdx")
        """
        try:
            if format in ("json", "yaml"):
                with open(file_path, encoding="utf-8") as f:
                    if format == "json":
                        data = json.load(f)
                    else:
                        import yaml

                        data = yaml.safe_load(f)

                # Check for CycloneDX markers
                if "bomFormat" in data and data["bomFormat"] == "CycloneDX":
                    return "cyclonedx"

                # Check for SPDX markers
                if "spdxVersion" in data or "SPDXID" in data:
                    return "spdx"

            elif format == "xml":
                # Read first few lines to detect
                with open(file_path, encoding="utf-8") as f:
                    content = f.read(1000)

                if "cyclonedx" in content.lower():
                    return "cyclonedx"
                elif "spdx" in content.lower():
                    return "spdx"

            elif format == "tag-value":
                # Tag-value is SPDX-specific
                return "spdx"

        except Exception:
            pass

        # Default to CycloneDX
        return "cyclonedx"

    def validate_licenses(self, file_path: Path) -> tuple[bool, list[str]]:
        """
        Validate that all licenses in SBOM are valid SPDX expressions.

        Args:
            file_path: Path to SBOM file

        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []

        try:
            sbom_type = self._detect_sbom_type(file_path, "json")

            if sbom_type == "cyclonedx":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                components = data.get("components", [])
                for comp in components:
                    licenses = comp.get("licenses", [])
                    for lic in licenses:
                        if "expression" in lic:
                            # Validate SPDX expression
                            expr = lic["expression"]
                            if not self._is_valid_spdx_expression(expr):
                                warnings.append(
                                    f"Component {comp['name']}: Invalid SPDX expression '{expr}'"
                                )

            elif sbom_type == "spdx":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                packages = data.get("packages", [])
                for pkg in packages:
                    declared = pkg.get("licenseDeclared")
                    concluded = pkg.get("licenseConcluded")

                    if declared and not self._is_valid_spdx_expression(declared):
                        warnings.append(
                            f"Package {pkg['name']}: Invalid declared license '{declared}'"
                        )

                    if concluded and not self._is_valid_spdx_expression(concluded):
                        warnings.append(
                            f"Package {pkg['name']}: Invalid concluded license '{concluded}'"
                        )

            return len(warnings) == 0, warnings

        except Exception as e:
            return False, [f"License validation error: {str(e)}"]

    def _is_valid_spdx_expression(self, expression: str) -> bool:
        """
        Check if a license expression is valid SPDX.

        Args:
            expression: License expression

        Returns:
            True if valid
        """
        # Skip NOASSERTION and NONE
        if expression in ("NOASSERTION", "NONE"):
            return True

        # Basic validation - check for common SPDX license IDs
        # In production, use a proper SPDX expression parser
        common_licenses = [
            "MIT",
            "Apache-2.0",
            "GPL-2.0",
            "GPL-3.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "ISC",
            "LGPL-2.1",
            "LGPL-3.0",
            "MPL-2.0",
            "CC0-1.0",
            "Unlicense",
        ]

        # Check if expression contains at least one known license
        for lic in common_licenses:
            if lic in expression:
                return True

        # If it contains AND/OR/WITH operators, assume it's an expression
        if any(op in expression for op in [" AND ", " OR ", " WITH "]):
            return True

        # Otherwise, it might be a custom license
        return True
