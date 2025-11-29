# 🔍 Agente Daktus QA

> Clinical protocol validation using AI-powered playbook analysis

**Version**: 2.3-production  
**Status**: ✅ Production Ready - Agent V2 Complete (All Phases Implemented)  
**Last Updated**: 2025-11-29

---

## 🎯 What It Does

Validates clinical protocols (JSON) against medical playbooks (text/PDF) to ensure:

- ✅ Clinical logic consistency  
- ✅ Complete symptom coverage
- ✅ Appropriate diagnostic paths
- ✅ Evidence-based recommendations

**Input**: Clinical protocol (JSON) + Medical playbook (Markdown/PDF)  
**Output**: Clinical validation report (text + JSON) with gap analysis and improvement suggestions

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenRouter

```bash
python scripts/setup_openrouter.py
```

Or manually create `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-seu-key-aqui
LLM_MODEL=anthropic/claude-sonnet-4.5
USE_SIMPLIFIED_AGENT=true  # Optional: enable Agent V2
```

**Get API key**: https://openrouter.ai/keys

### 3. Run Analysis

```bash
python run_qa_cli.py
```

Follow the prompts:
1. Select protocol JSON file from `models_json/`
2. Select playbook file (optional but recommended)
3. Choose LLM model
4. View results in `reports/`

---

## 🏗️ Architecture

### Agent V2 (Simplified Architecture) - **Recommended**

**Status**: ✅ Implemented and functional

Agent V2 is a **LLM-centric architecture** where:
- **Zero clinical logic in code** - all clinical intelligence comes from LLM
- **Single LLM call** - comprehensive analysis via super prompt
- **Specialty-agnostic** - works identically for ORL, AVC, Pediatrics, etc.
- **Focus on improvement suggestions** - actionable recommendations for protocol enhancement

**Activation**:

```bash
# Windows (PowerShell)
$env:USE_SIMPLIFIED_AGENT="true"
python run_qa_cli.py

# Linux/Mac
export USE_SIMPLIFIED_AGENT=true
python run_qa_cli.py
```

**Pipeline**:
```
Playbook + Protocol → protocol_loader (raw load)
    ↓
prompt_builder (super prompt assembly)
    ↓
llm_client → OpenRouter API (single comprehensive analysis)
    ↓
output/validator (schema validation)
    ↓
pipeline.analyze() → Unified JSON output
    ↓
CLI Report Generator → reports/*.txt, reports/*.json
```

**Estrutura Simplificada**:
- ✅ Pipeline único: `agent_v2.pipeline.analyze()`
- ✅ Zero duplicação: arquivos obsoletos removidos
- ✅ Imports limpos: sem referências quebradas
- ✅ Sistema consolidado: estrutura clara e consistente

### Legacy Architecture

**Status**: ⚠️ Deprecated (maintained for compatibility)

The legacy architecture uses multiple LLM calls and has some hardcoded clinical logic. It will be removed in Phase 3.

**When to use**: Only if Agent V2 fails or for compatibility testing.

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-seu-key-aqui

# Optional
LLM_MODEL=anthropic/claude-sonnet-4.5  # Default model
USE_SIMPLIFIED_AGENT=true              # Enable Agent V2 (default: false)
```

### Supported Models

- `anthropic/claude-sonnet-4.5` ⭐ (recommended)
- `anthropic/claude-3.5-haiku-20241022` (faster, cheaper)
- `google/gemini-2.5-flash` (alternative)
- `x-ai/grok-4.1-fast:free` (free tier)

---

## 📊 Output Format

### Report Structure

**Text Report** (`reports/*.txt`):
- Protocol structure summary
- Playbook extraction summary
- Clinical validation (coverage, gaps)
- Efficiency analysis
- Improvement suggestions
- Quality metrics

**JSON Report** (`reports/*.json`):
- Complete structured data
- All analysis results
- Metadata (timestamps, model used, processing times)
- Entity counts (syndromes, exams, treatments)

### Log Files

**Location**: `logs/qa_analysis_YYYYMMDD_HHMMSS.log`

**Contains**:
- Detailed execution logs
- LLM call details (latency, tokens)
- Error traces
- Performance metrics

---

## 🔧 Troubleshooting

### "LLM not available"

**Cause**: `OPENROUTER_API_KEY` not configured

**Fix**:
```bash
# Check .env exists
cat .env  # Linux/Mac
type .env  # Windows

# Or reconfigure
python scripts/setup_openrouter.py
```

### "No protocol files found"

**Cause**: No JSON files in `models_json/`

**Fix**: Add protocol JSON files to `models_json/` directory

### Agent V2 not activating

**Cause**: Feature flag not set or playbook_text empty

**Fix**:
```bash
# Verify feature flag
echo $env:USE_SIMPLIFIED_AGENT  # Windows PowerShell
echo $USE_SIMPLIFIED_AGENT      # Linux/Mac

# Set if needed
$env:USE_SIMPLIFIED_AGENT="true"  # Windows PowerShell
export USE_SIMPLIFIED_AGENT=true  # Linux/Mac
```

### Import errors

**Cause**: Missing dependencies or path issues

**Fix**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Validate system
python scripts/validate_system.py
```

---

## 📚 Documentation

**Official Documentation** (consolidated in 3 master files):

- **This file** (`readme.md`) - Overview and usage
- **`roadmap.md`** - Product vision and backlog
- **`dev_history.md`** - Development history (append-only log)

**Additional Resources**:

- `REVIEW_CLAUDE.txt` - Complete specification for Agent V2
- `src/agent_v2/` - Agent V2 source code
- `docs/` - Additional technical documentation (legacy, being consolidated)

---

## 🎯 Key Principles

### Agent V2 Design Principles

1. **Zero Clinical Logic in Code**
   - All clinical decisions come from LLM
   - No hardcoded rules, regex, or heuristics
   - Code is pure orchestration

2. **Single LLM Call**
   - One comprehensive super prompt
   - All analysis (extraction, structural, semantic, alignment) in one call
   - Reduces latency and cost

3. **Specialty-Agnostic**
   - Same code path for all medical specialties
   - No `if specialty == "ORL"` logic
   - Specialty-specific knowledge in playbooks, not code

4. **Fail-Fast**
   - Errors are logged and propagated immediately
   - No silent failures
   - Structured error responses (no fabricated clinical content)

---

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Compliance tests (Agent V2)
python test_agent_v2_compliance.py
```

### Test with Real Protocols

```bash
python test_agent_v2_real_protocols.py
```

---

## 📈 Performance

**Agent V2** (single LLM call):
- **Latency p95**: ≤ 60 seconds
- **Cost per analysis**: ~$0.05-0.10 (depends on model)
- **Success rate**: ≥ 95%

**Legacy** (multiple LLM calls):
- **Latency p95**: ~90-120 seconds
- **Cost per analysis**: ~$0.10-0.15
- **Success rate**: ~90%

---

## 🤝 Contributing

**Important**: Before making changes, read:
- `roadmap.md` - Product vision and priorities
- `dev_history.md` - Recent changes and context
- `REVIEW_CLAUDE.txt` - Architecture principles

**Documentation Policy**:
- All new information goes into `readme.md`, `roadmap.md`, or `dev_history.md`
- Do not create new documentation files
- Update existing master files instead

---

## 📝 License

[Add license information here]

---

## 🔗 Links

- **OpenRouter**: https://openrouter.ai
- **API Keys**: https://openrouter.ai/keys
- **Model Catalog**: https://openrouter.ai/models

---

**For detailed product roadmap, see [`roadmap.md`](roadmap.md)**  
**For development history, see [`dev_history.md`](dev_history.md)**
