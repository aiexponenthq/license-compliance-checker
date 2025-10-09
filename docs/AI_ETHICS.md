# AI Ethics and Responsible Use

## Overview

License Compliance Checker (LCC) includes an optional AI-powered license
classification feature. This document describes our approach to responsible
AI use, data privacy, and ethical considerations.

## AI Feature Summary

LCC can optionally use a Large Language Model (LLM) to classify software
licenses from source code headers and LICENSE files when traditional
pattern-matching fails to identify a license.

**Key design decisions:**

- AI features are **disabled by default** (opt-in only)
- No data is sent to external services unless explicitly configured
- Local LLM inference is supported for air-gapped environments
- AI results are clearly labeled and carry confidence scores

## Data Privacy

### What data is processed

When AI classification is enabled, LCC sends short text snippets (up to 2000
characters) from license files or source code headers to the configured LLM
endpoint for classification.

### Data flow

| Mode | Data destination | Network required |
|------|-----------------|-----------------|
| disabled (default) | None | No |
| local | Local LLM endpoint | Local network only |
| fireworks | Fireworks AI API | Yes (internet) |

### Enabling AI features

To enable AI-powered classification, users must explicitly set environment
variables. See the README for configuration details.

For local LLM (Ollama, vLLM, etc.):
- Set LCC_LLM_PROVIDER to "local"
- Set LCC_LLM_ENDPOINT to your local endpoint URL

For cloud-based (Fireworks AI):
- Set LCC_LLM_PROVIDER to "fireworks"
- Set LCC_FIREWORKS_API_KEY to your API key

### What is NOT sent

- Full source code files
- Repository credentials or tokens
- User identity or personal information
- Scan results or compliance decisions

## Responsible AI Principles

### 1. Transparency

- AI-derived license classifications are clearly marked in scan results
- Confidence scores are provided for all AI classifications
- The resolution path metadata shows which resolver produced each result

### 2. Human oversight

- AI classification is one input in a multi-resolver fallback chain
- Traditional pattern matching and registry lookups take priority
- Policy enforcement decisions are rule-based, not AI-driven
- Users can override any AI classification manually

### 3. Privacy by default

- AI features are disabled unless explicitly opted in
- No telemetry, analytics, or usage tracking is performed
- Scan data stays local unless the user configures an external LLM

### 4. Minimal data collection

- Only the minimum text needed for classification is sent (2000 char limit)
- No data is stored by LCC beyond the scan session
- Caching is local-only and user-controlled

### 5. Auditability

- All license resolution steps are logged and traceable
- Decision logs record which resolver produced each classification
- SBOM exports include provenance information

## Limitations

- AI classification may produce incorrect results; always verify critical findings
- LLM outputs can vary between model versions and providers
- Cloud-based LLM providers have their own data handling policies
- AI classification should not be the sole basis for legal compliance decisions

## Contact

For questions about AI ethics or data privacy in LCC, please open an issue
or contact the maintainers via [GitHub Issues](https://github.com/apundhir/license-compliance-checker/issues).
