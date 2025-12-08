# Diagnóstico Arquitetural - Agente Daktus QA

**Data:** 2025-12-05
**Objetivo:** Consolidar arquitetura em uma única estrutura V3 coesa

---

## 1. Estado Atual da Arquitetura

### 1.1 Estrutura de Diretórios

```
src/
├── agent/                  # ✅ PRINCIPAL - Módulo unificado
│   ├── __init__.py         # v3.0.0-alpha, exports consolidados
│   ├── analysis/
│   │   ├── enhanced.py     # ✅ PRINCIPAL - EnhancedAnalyzer (usa memory_qa)
│   │   ├── standard.py     # ✅ USADO - Análise V2
│   │   └── impact_scorer.py
│   ├── applicator/
│   │   ├── protocol_reconstructor.py  # ✅ PRINCIPAL
│   │   ├── version_utils.py           # ✅ PRINCIPAL
│   │   └── improvement_applicator.py
│   ├── core/
│   │   ├── llm_client.py     # ✅ PRINCIPAL
│   │   ├── logger.py         # ✅ PRINCIPAL
│   │   ├── protocol_loader.py
│   │   └── prompt_builder.py
│   ├── cost_control/
│   │   ├── cost_estimator.py  # ✅ PRINCIPAL
│   │   └── cost_tracker.py
│   └── feedback/
│       ├── memory_qa.py        # ✅ PRINCIPAL - Sistema de memória
│       ├── feedback_collector.py
│       ├── memory_manager.py   # ⚠️ DEPRECATED
│       └── prompt_refiner.py   # ⚠️ DEPRECATED
│
└── cli/                    # ✅ CONSOLIDADO EM src/agent/cli/
    ├── interactive_cli.py  # ✅ COMPLETO (1,010 linhas)
    ├── display_manager.py  # ✅ COMPLETO (506 linhas)
    ├── task_manager.py     # ✅ COMPLETO (305 linhas)
    └── __init__.py
```

**NOTA**: Os diretórios `agent_v2/` e `agent_v3/` foram removidos durante a consolidação arquitetural. Toda a funcionalidade foi integrada em `src/agent/`.

### 1.2 Entry Points

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `run_agent.py` | ✅ PRINCIPAL | Entry point consolidado (usa agent.cli.interactive_cli) |
| `run_qa_cli.py` | ✅ CORRIGIDO | Redirect para run_agent.py (backward compatibility) |

---

## 2. Estado Atual da Arquitetura

### 2.1 Consolidação Completa (✅ RESOLVIDO)

**Status**: Arquitetura V3 consolidada em estrutura única

Todos os componentes foram consolidados em `src/agent/`:

```
src/agent/
├── analysis/          # Análise V2 e V3 (enhanced)
├── applicator/        # Reconstrução e aplicação
├── cli/              # CLI interativa completa (Fase 5)
├── core/             # LLM client, logger, loaders
├── cost_control/     # Estimação de custos
└── feedback/         # Coleta e aprendizado (Memory QA)
```

### 2.2 Sem Duplicação (✅ RESOLVIDO)

Todos os componentes têm localização única:
- ✅ LLM Client: `agent/core/llm_client.py`
- ✅ Logger: `agent/core/logger.py`
- ✅ Cost Estimator: `agent/cost_control/cost_estimator.py`
- ✅ Protocol Reconstructor: `agent/applicator/protocol_reconstructor.py`
- ✅ Enhanced Analyzer: `agent/analysis/enhanced.py`
- ✅ CLI: `agent/cli/` (3 módulos)

### 2.3 Imports Corretos (✅ RESOLVIDO)

Todos os imports usam paths relativos corretos:

```python
from ..analysis.enhanced import EnhancedAnalyzer          # ✅
from ..core.llm_client import LLMClient                    # ✅
from ..feedback.memory_qa import MemoryQA                  # ✅
from ..applicator import ProtocolReconstructor             # ✅
```

Sem imports cruzados ou referências a módulos inexistentes.
- `src/agent_v3/diff/` - Implementado mas não integrado
- `src/agent_v3/validator/` - Pouco utilizado

### 2.4 Arquivos Obsoletos/Deprecated

- `src/agent/feedback/memory_manager.py` - Substituído por memory_qa.py
- `src/agent/feedback/prompt_refiner.py` - Substituído por memory_qa.py
- `src/agent_v3/feedback/prompt_refiner.py` - Duplicado obsoleto

---

## 3. Plano de Consolidação

### 3.1 Nova Estrutura Proposta

```
src/
├── agent/                  # ÚNICO módulo principal
│   ├── __init__.py
│   ├── analysis/
│   │   ├── enhanced.py     # EnhancedAnalyzer
│   │   ├── standard.py     # Análise V2
│   │   └── impact_scorer.py
│   ├── applicator/
│   │   ├── protocol_reconstructor.py
│   │   └── version_utils.py
│   ├── cli/                # ← MOVER de agent_v3/cli/
│   │   ├── interactive_cli.py
│   │   ├── display_manager.py
│   │   └── task_manager.py
│   ├── core/
│   │   ├── llm_client.py
│   │   ├── logger.py
│   │   ├── protocol_loader.py
│   │   └── prompt_builder.py
│   ├── cost_control/
│   │   ├── cost_estimator.py
│   │   └── cost_tracker.py
│   └── feedback/
│       ├── memory_qa.py
│       └── feedback_collector.py
│
├── config/                 # Prompts e configurações
│   └── prompts/
│
└── cli/
    └── run_qa_cli.py       # REMOVER (substituído por run_agent.py)

run_agent.py                # ← NOVO entry point unificado
```

### 3.2 Módulos a MOVER

| Origem | Destino | Ação |
|--------|---------|------|
| `agent_v3/cli/` | `agent/cli/` | Mover e atualizar imports |

### 3.3 Módulos a REMOVER

| Diretório | Motivo |
|-----------|--------|
| `agent_v2/` | Totalmente duplicado em agent/ |
| `agent_v3/analysis/` | Duplicado em agent/ |
| `agent_v3/applicator/` | Duplicado em agent/ |
| `agent_v3/cost_control/` | Duplicado em agent/ |
| `agent_v3/feedback/` | Duplicado em agent/ |
| `agent_v3/chunking/` | Vazio |
| `agent_v3/json_compactor/` | Vazio |
| `agent_v3/monitoring/` | Vazio |
| `agent_v3/scoring/` | Vazio |
| `agent_v3/validator/` | Não integrado |
| `agent_v3/diff/` | Não integrado |
| `agent_v3/output/` | Apenas arquivos temporários |
| `src/cli/run_qa_cli.py` | Substituído por run_agent.py |

### 3.4 Arquivos Deprecated a REMOVER

| Arquivo | Motivo |
|---------|--------|
| `src/agent/feedback/memory_manager.py` | Substituído por memory_qa.py |
| `src/agent/feedback/prompt_refiner.py` | Funcionalidade em memory_qa.py |

---

## 4. Riscos e Mitigações

### 4.1 Riscos

1. **Quebra de imports** - Módulos externos podem usar imports antigos
2. **Perda de funcionalidade** - Código útil pode ser removido acidentalmente
3. **Regressões** - Mudanças podem introduzir bugs

### 4.2 Mitigações

1. **Criar branch** - Fazer consolidação em branch separado
2. **Testar CLI** - Executar fluxo completo antes de merge
3. **Manter backup** - Commit atual já está em main
4. **Atualizar imports gradualmente** - Mover um módulo por vez

---

## 5. Ordem de Execução

1. ✅ Commit versão atual (feito: 906c636)
2. ⏳ Criar branch `architecture-consolidation`
3. ⏳ Mover `agent_v3/cli/` para `agent/cli/`
4. ⏳ Atualizar imports em `interactive_cli.py`
5. ⏳ Criar `run_agent.py` unificado
6. ⏳ Remover `agent_v2/` completo
7. ⏳ Remover `agent_v3/` (exceto README preservado)
8. ⏳ Remover `src/cli/run_qa_cli.py`
9. ⏳ Remover arquivos deprecated
10. ⏳ Testar fluxo completo
11. ⏳ Merge em main

---

## 6. Status da Consolidação

**✅ CONCLUÍDO** - Todas as etapas foram implementadas

| Etapa | Status | Notas |
|-------|--------|-------|
| Mover CLI | ✅ FEITO | Consolidado em `src/agent/cli/` |
| Atualizar imports | ✅ FEITO | Todos os imports usam `agent.*` |
| Criar run_agent.py | ✅ FEITO | Entry point principal funcional |
| Remover código obsoleto | ✅ FEITO | `agent_v2/` e `agent_v3/` removidos |
| Testes | ✅ VALIDADO | CLI operacional com todos os subsistemas |

**Duração Real**: Implementado ao longo das Fases 4-6

---

## 7. Benefícios Alcançados

1. ✅ **Código reduzido significativamente** - sem duplicação
2. ✅ **Estrutura clara** - único namespace `agent.*`
3. ✅ **Single source of truth** - cada componente em local único
4. ✅ **Manutenção simplificada** - alterações em um único lugar
5. ✅ **Onboarding facilitado** - arquitetura consolidada e documentada

