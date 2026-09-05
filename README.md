# WSI Tiler QC Agent

> **Domain:** Digital Pathology & Quantitative Histopathology
> **Reference Guidelines & Standards:** College of American Pathologists (CAP) Synoptic Protocols & DICOM WSI

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**WSI Tiler QC Agent** is an advanced analytical and computational platform implementing Gigapixel Whole-Slide Imaging (WSI) Tiling, Focus Entropy Mapping & Artifact Filter. It provides multi-agent quality control for digital pathology workflows.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`TissueSegmentationAgent`**: Specialized Sub-Agent 1 for tissue segmentation QC
- **`FocusEntropyAgent`**: Specialized Sub-Agent 2 for focus quality assessment
- **`ArtifactExclusionAgent`**: Specialized Sub-Agent 3 for artifact detection and exclusion

### 🏗️ Architecture

The project consists of two main components:

1. **`agents/`** — Enterprise-grade multi-agent system with:
   - `SystemSupervisor` — Master orchestrator coordinating specialized workers
   - `InvariantQCWorker` — Primary metric boundary auditor
   - `SafetyEscalationWorker` — Safety boundary and emergency interlock worker
   - `ProtocolConformanceWorker` — Spec conformance and anomaly triage
   - `AuditLogger` — HMAC-SHA256 tamper-evident audit trail
   - `PHIGuard` — Zero-PHI outbound interceptor

2. **`wsi_tiler_qc_agent/`** — Clinical-focused agent system with:
   - `PyramidalTilingCoordinator` — Executive coordinator for clinical cases
   - `ClinicalDomainEngine` — Clinical algorithmic engine with guideline rules
   - `FocusHeatmapGenerator` — Multi-resolution focus quality heatmap generation
   - `ScannerFingerprintAgent` — DICOM WSI metadata extraction and scanner fingerprinting
   - `export_qupath_annotations` — QuPath GeoJSON annotation export

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/wsi-tiler-qc-agent.git
cd wsi-tiler-qc-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Audit
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Query Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task / case identifier
- `--target`: Entity, patient key, or target identifier
- `--primary`: Primary domain measurement or score (float)
- `--secondary`: Secondary kinetic or confidence score (float)
- `--critical`: Emergency escalation flag
- `--status`: Status code or phenotype descriptor
- `-i/--input`: Input CSV file path for batch processing
- `-o/--output`: Output CSV file path for batch processing

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Secure Key Management:** Audit signing key sourced from `AUDIT_SECRET_KEY` environment variable with secure fallback.
* **Path Traversal Protection:** Batch file operations validated to prevent directory traversal attacks.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Environment Variables

| Variable | Description | Required |
|:---------|:------------|:---------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit signing | Recommended |

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t wsi-tiler-qc-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key wsi-tiler-qc-agent
```

---

## 📁 Project Structure

```
wsi-tiler-qc-agent/
├── agents/                    # Enterprise multi-agent system
│   ├── __init__.py
│   ├── api.py                 # FastAPI REST API server
│   ├── base.py                # Security, PHI Guard, Audit Trail
│   ├── learning.py            # Bayesian calibration engine
│   ├── llm_factory.py         # LLM client factory
│   ├── metrics.py             # Prometheus metrics exporter
│   ├── models.py              # Pydantic data models
│   ├── streamer.py            # WebSocket telemetry streamer
│   ├── supervisor.py          # System supervisor orchestrator
│   └── workers.py             # Specialized domain workers
├── wsi_tiler_qc_agent/        # Clinical agent system
│   ├── __init__.py
│   ├── agents.py              # Clinical sub-agents
│   ├── cli.py                 # Clinical CLI
│   ├── engine.py              # Clinical algorithmic engine
│   ├── focus_heatmap.py       # Focus quality heatmap generator
│   ├── models.py              # Clinical data models
│   ├── qupath_export.py       # QuPath GeoJSON export
│   ├── scanner.py             # DICOM WSI scanner fingerprinting
│   └── server.py              # Clinical FastAPI server
├── tests/                     # Test suite
│   ├── test_enrichment.py
│   └── test_wsi_tiler_qc_agent.py
├── cli.py                     # Main CLI entry point
├── wsi_tiler_qc.py            # Core QC engine
├── enrichment.py              # Enrichment feature modules
├── simulator.py               # High-throughput simulator
├── sample.csv                 # Sample batch input
├── sample_payload.json        # Sample API payload
├── pyproject.toml             # Project configuration
├── Dockerfile                 # Container definition
└── docker-compose.yml         # Docker Compose configuration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
