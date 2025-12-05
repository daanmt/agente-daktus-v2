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
├── agent_v2/               # ⚠️ PARCIALMENTE OBSOLETO
│   ├── __init__.py         # v2.0.0
│   ├── llm_client.py       # 🔴 DUPLICADO (mesma lógica de agent/core)
│   ├── logger.py           # 🔴 DUPLICADO
│   ├── pipeline.py         # ⚠️ USADO apenas pelo run_qa_cli.py
│   ├── protocol_loader.py  # 🔴 DUPLICADO
│   └── prompt_builder.py   # 🔴 DUPLICADO
│
├── agent_v3/               # ⚠️ PARCIALMENTE OBSOLETO
│   ├── __init__.py         # v3.0.0-alpha (vazio)
│   ├── analysis/
│   │   └── enhanced_analyzer.py  # 🔴 DUPLICADO (usa agent_v2.*)
│   ├── applicator/
│   │   └── protocol_reconstructor.py  # 🔴 DUPLICADO (usa agent_v2.*)
│   ├── cli/                 # ✅ PRINCIPAL - CLI interativa
│   │   ├── interactive_cli.py   # ✅ PRINCIPAL
│   │   ├── display_manager.py   # ✅ PRINCIPAL
│   │   └── task_manager.py      # ✅ PRINCIPAL
│   ├── cost_control/
│   │   └── cost_estimator.py    # 🔴 DUPLICADO
│   ├── feedback/
│   │   └── prompt_refiner.py    # 🔴 DUPLICADO (usa agent_v2.logger)
│   └── diff/                    # ⚠️ NÃO USADO
│
└── cli/
    └── run_qa_cli.py       # ⚠️ CLI ANTIGA (usa agent.*)
```

### 1.2 Entry Points

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `run_interactive_cli.py` | ✅ PRINCIPAL | CLI interativa avançada (V3) |
| `src/cli/run_qa_cli.py` | ⚠️ OBSOLETO | CLI antiga (deve ser removida) |

---

## 2. Problemas Identificados

### 2.1 Código Duplicado (CRÍTICO)

1. **LLM Client** - 3 cópias:
   - `src/agent/core/llm_client.py` (PRINCIPAL)
   - `src/agent_v2/llm_client.py` (DUPLICADO)
   - `src/agent_v3/applicator/llm_client.py` (DUPLICADO)

2. **Logger** - 2 cópias:
   - `src/agent/core/logger.py` (PRINCIPAL)
   - `src/agent_v2/logger.py` (DUPLICADO)

3. **Cost Estimator** - 2 cópias:
   - `src/agent/cost_control/cost_estimator.py` (PRINCIPAL)
   - `src/agent_v3/cost_control/cost_estimator.py` (DUPLICADO)

4. **Protocol Reconstructor** - 2 cópias:
   - `src/agent/applicator/protocol_reconstructor.py` (PRINCIPAL)
   - `src/agent_v3/applicator/protocol_reconstructor.py` (DUPLICADO)

5. **Enhanced Analyzer** - 2 cópias:
   - `src/agent/analysis/enhanced.py` (PRINCIPAL - usa memory_qa)
   - `src/agent_v3/analysis/enhanced_analyzer.py` (DUPLICADO - sem memory_qa)

### 2.2 Imports Cruzados (CONFUSOS)

```
agent_v3/cli/interactive_cli.py → agent.* (CORRETO)
agent_v3/analysis/enhanced_analyzer.py → agent_v2.* (INCORRETO)
agent_v3/applicator/* → agent_v2.* (INCORRETO)
agent_v3/feedback/* → agent_v2.* (INCORRETO)
```

### 2.3 Módulos Não Utilizados

- `src/agent_v3/chunking/` - Vazio
- `src/agent_v3/json_compactor/` - Vazio
- `src/agent_v3/monitoring/` - Vazio
- `src/agent_v3/scoring/` - Vazio
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

## 6. Estimativa de Tempo

| Etapa | Tempo |
|-------|-------|
| Mover CLI | 30 min |
| Atualizar imports | 1 hora |
| Criar run_agent.py | 30 min |
| Remover código obsoleto | 30 min |
| Testes | 1 hora |
| **Total** | **~3-4 horas** |

---

## 7. Benefícios Esperados

1. **Redução de 60%** no código fonte
2. **Eliminar confusão** de imports agent/agent_v2/agent_v3
3. **Single source of truth** para cada funcionalidade
4. **Manutenção simplificada** - um lugar para corrigir bugs
5. **Onboarding mais fácil** - nova estrutura clara e documentada

