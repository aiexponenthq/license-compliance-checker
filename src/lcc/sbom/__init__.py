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

"""SBOM generation subsystem for LCC."""

from lcc.sbom.cyclonedx import CycloneDXGenerator

# from lcc.sbom.validator import SBOMValidator  # TODO: Update for cyclonedx-python-lib v11.x API
from lcc.sbom.signer import SBOMSigner
from lcc.sbom.spdx import SPDXGenerator

__all__ = [
    "CycloneDXGenerator",
    "SPDXGenerator",
    # "SBOMValidator",  # TODO: Re-enable after v11.x migration
    "SBOMSigner",
]
