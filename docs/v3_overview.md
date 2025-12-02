# Agent V3 - Visão Geral e Guia Completo

**Versão**: 3.0.0-alpha
**Status**: 🚧 Em Desenvolvimento
**Última Atualização**: 2025-12-01

---

## 📑 Índice

1. [Sumário Executivo](#sumário-executivo)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Os 7 Estágios do Pipeline](#os-7-estágios-do-pipeline)
4. [Estrutura de Módulos](#estrutura-de-módulos)
5. [Roadmap Completo](#roadmap-completo)
6. [Como Contribuir](#como-contribuir)
7. [Como Testar](#como-testar)
8. [FAQ](#faq)

---

## Sumário Executivo

### O Que é o Agent V3?

O Agent V3 é uma **evolução transformacional** do Agent V2, mudando de **auditoria passiva** para **correção ativa** de protocolos clínicos.

**V2 (Atual)**: Análise passiva → Relatório estático → Implementação manual (dias/semanas)

**V3 (Novo)**: Análise ativa → Feedback iterativo → Auto-apply assistido → Implementação automática (minutos)

### Objetivos Principais

1. **Relatórios de Alta Qualidade**: 20-50 sugestões vs 5-15 da V2
2. **Human-in-the-Loop**: Sistema de feedback para fine-tuning contínuo
3. **Controle de Custos**: Estimativa e autorização rigorosas
4. **UX Excepcional**: CLI inspirada no Claude Code

### Métricas de Sucesso

- ✅ 20-50 sugestões por análise (vs 5-15)
- ✅ 90%+ de sugestões relevantes (após fine-tuning)
- ✅ Estimativa de custo com 90%+ precisão
- ✅ Zero execuções sem autorização
- ✅ Taxa de sucesso >95% no auto-apply

---

## Arquitetura do Sistema

### Princípios Fundamentais

1. **Transparência Total**: Usuário vê cada etapa do processo
2. **Controle do Usuário**: Nada acontece sem autorização explícita
3. **Aprendizado Contínuo**: Sistema melhora com feedback
4. **Segurança Primeiro**: Validação rigorosa, zero tolerância a erros

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT V3 PIPELINE                        │
│         Análise → Feedback → Refinamento → Correção         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────┐                   ┌──────────────────┐
│  ENTRADA         │                   │  SAÍDA           │
│  • Protocolo JSON│                   │  • Protocolo v++ │
│  • Playbook MD   │                   │  • Diff visual   │
│  • Configurações │                   │  • Relatórios    │
└──────────────────┘                   └──────────────────┘
```

---

## Os 7 Estágios do Pipeline

### FASE 1: Onboarding Interativo

**Objetivo**: Configurar sessão de forma amigável e clara

**Componentes**:
- `cli/interactive_cli.py`: Motor principal
- `cli/display_manager.py`: UI rica
- `cli/task_manager.py`: Gerenciamento de tasks

**Fluxo**:
1. Apresentação do Agent V3
2. Seleção de protocolo (com preview)
3. Seleção de playbook (opcional)
4. Configuração de modelo LLM
5. Configuração de limites de custo
6. Resumo e confirmação

**Exemplo de Saída**:
```
╔═══════════════════════════════════════════════════╗
║   🔍 Agent V3 - Análise Clínica Inteligente      ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  Vamos começar!                                   ║
║                                                   ║
║  ✓ Analisar protocolo clínico                    ║
║  ✓ Gerar 20-50 sugestões de melhoria             ║
║  ✓ Aprender com seu feedback                     ║
║  ✓ Aplicar melhorias automaticamente (opcional)  ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

---

### FASE 2: Análise Expandida

**Objetivo**: Gerar 20-50 sugestões de melhoria com rastreabilidade completa

**Componentes**:
- `analysis/enhanced_analyzer.py`: Análise expandida
- `analysis/impact_scorer.py`: Scoring de impacto

**Melhorias sobre V2**:
- **Quantidade**: 20-50 sugestões (vs 5-15)
- **Qualidade**: Cada sugestão com scores de impacto
- **Rastreabilidade**: Link para evidência do playbook
- **Estimativa**: Custo para aplicar cada sugestão

**Exemplo de Sugestão**:
```json
{
  "id": "SUGG-001",
  "category": "seguranca",
  "priority": "alta",
  "title": "Adicionar triagem de risco cardíaco",
  "description": "Protocolo não contempla avaliação...",
  "impact_scores": {
    "seguranca": 9,
    "economia": "A",
    "eficiencia": "M",
    "usabilidade": 6
  },
  "evidence": {
    "playbook_section": "3.2.1",
    "quote": "Todos os pacientes acima de 45..."
  },
  "auto_apply_cost_estimate": {
    "cost_usd": 0.003
  }
}
```

---

### FASE 3: Apresentação do Relatório

**Objetivo**: Apresentar sugestões de forma clara e interativa

**Componentes**:
- `cli/display_manager.py`: Formatação rica
- Tabelas com `rich.Table`
- Syntax highlighting

**Formato**:
```
[1/32] 🔴 ALTA PRIORIDADE

  Categoria: Segurança
  Título: Adicionar triagem de risco cardíaco

  Impacto:
    Segurança:   ████████░░ 9/10
    Economia:    Alta
    Esforço:     2 horas
```

---

### FASE 4: Feedback Loop (Human-in-the-Loop) 🆕

**Objetivo**: Capturar feedback do usuário e refinar prompts automaticamente

**Componentes**:
- `feedback/feedback_collector.py`: Coleta de feedback
- `feedback/prompt_refiner.py`: Refinamento de prompts
- `feedback/feedback_storage.py`: Persistência

**Fluxo**:
1. Usuário revisa cada sugestão: Relevante | Irrelevante | Editar
2. Sistema captura feedback estruturado
3. Sistema detecta padrões de erro
4. Sistema ajusta prompts automaticamente
5. Sistema gera relatório refinado

**Exemplo de Feedback**:
```
Esta sugestão é relevante? (S/n/Editar/Comentar): n
💬 Comentário: "Caminho rápido já existe no nó 12"

✓ Feedback registrado
```

**Refinamento Automático**:
```
Padrão Detectado:
- 15 de 20 sugestões sobre "adicionar nó X" foram rejeitadas
- Motivo: "Nó já existe com nome diferente"

Ajuste de Prompt:
"Antes de sugerir adicionar um nó, verifique se já existe
um nó similar com nome ou propósito equivalente."

Versão: v1.0.0 → v1.0.1
```

---

### FASE 5: Controle de Custos e Autorização 🆕

**Objetivo**: Estimativa precisa e autorização obrigatória

**Componentes**:
- `cost_control/cost_estimator.py`: Estimativa de custos
- `cost_control/authorization_manager.py`: Autorização
- `cost_control/cost_tracker.py`: Rastreamento

**Fluxo**:
1. Estimar custo da operação
2. Apresentar estimativa ao usuário
3. Validar contra limites configurados
4. Solicitar autorização se necessário
5. Registrar decisão

**Exemplo de Autorização**:
```
╔═══════════════════════════════════════════════════╗
║        ESTIMATIVA DE CUSTO - AUTO-APPLY           ║
╠═══════════════════════════════════════════════════╣
║ Modelo: Claude Sonnet 4.5                         ║
║ Tokens: ~50,000 entrada, ~60,000 saída            ║
║                                                   ║
║ Custo estimado: $1.05                             ║
║ Status: ⚠️  ACIMA DO LIMITE ($1.00)               ║
╚═══════════════════════════════════════════════════╝

Opções:
  1. Continuar mesmo assim
  2. Aplicar apenas alta prioridade (8 sugestões, $0.52)
  3. Cancelar
```

---

### FASE 6: Auto-Apply Assistido

**Objetivo**: Aplicar melhorias automaticamente com segurança

**Componentes**:
- `applicator/improvement_applicator.py`: Motor de aplicação
- `applicator/llm_client.py`: Cliente LLM
- `validator/structural_validator.py`: Validação

**Fluxo**:
1. Aplicar melhorias via LLM
2. Validar a cada mudança
3. Registrar custo real
4. Comparar com estimativa
5. Rollback se erro

**Garantias**:
- ✅ Taxa de sucesso >95%
- ✅ Zero JSON quebrado
- ✅ Rastreabilidade completa
- ✅ Rollback automático

---

### FASE 7: QA Final e Saída

**Objetivo**: Validação final e geração de outputs

**Componentes**:
- `validator/structural_validator.py`: Validação estrutural
- `diff/diff_generator.py`: Geração de diff
- `diff/formatter.py`: Formatação

**Outputs**:
- Protocolo corrigido (versionado)
- Diff visual de mudanças
- Relatório completo (JSON)
- Logs de auditoria
- Métricas de custo e qualidade

---

## Estrutura de Módulos

### `/analysis` - Análise Expandida

**Arquivos**:
- `enhanced_analyzer.py`: Análise V2 expandida
- `impact_scorer.py`: Scoring de impacto

**Status**: FASE 1 (4-6 dias)

**Responsabilidades**:
- Gerar 20-50 sugestões
- Categorizar por tipo
- Calcular scores de impacto
- Rastrear evidências

---

### `/feedback` - Human-in-the-Loop 🆕

**Arquivos**:
- `feedback_collector.py`: Coleta de feedback
- `prompt_refiner.py`: Refinamento de prompts
- `feedback_storage.py`: Persistência

**Status**: FASE 2 (5-7 dias)

**Responsabilidades**:
- Capturar feedback do usuário
- Detectar padrões de erro
- Ajustar prompts automaticamente
- Armazenar histórico

---

### `/cost_control` - Controle de Custos 🆕

**Arquivos**:
- `cost_estimator.py`: Estimativa de custos
- `authorization_manager.py`: Autorização
- `cost_tracker.py`: Rastreamento

**Status**: FASE 3 (3-4 dias)

**Responsabilidades**:
- Estimar custo pré-execução
- Solicitar autorização
- Rastrear custo real
- Detectar anomalias

---

### `/cli` - CLI Interativa 🆕

**Arquivos**:
- `interactive_cli.py`: Motor principal
- `task_manager.py`: Gerenciamento de tasks
- `display_manager.py`: Renderização

**Status**: FASE 4 (5-7 dias)

**Responsabilidades**:
- Onboarding amigável
- Thinking visível
- Tasks em tempo real
- Formatação rica

---

### `/applicator` - Auto-Apply

**Arquivos**:
- `improvement_applicator.py`: Motor de aplicação
- `llm_client.py`: Cliente LLM

**Status**: FASE 5 (3-5 dias)

**Responsabilidades**:
- Aplicar melhorias via LLM
- Integrar com autorização
- Rastrear custo real
- Rollback automático

---

### `/validator` - Validação

**Arquivos**:
- `structural_validator.py`: Validação estrutural
- `schema_validator.py`: Validação de schema

**Status**: FASE 6 (2-3 dias)

**Responsabilidades**:
- Validar JSON
- Validar schema
- Validar integridade
- Zero protocolos quebrados

---

### `/diff` - Geração de Diff

**Arquivos**:
- `diff_generator.py`: Geração de diff
- `formatter.py`: Formatação

**Status**: FASE 7 (2-3 dias)

**Responsabilidades**:
- Gerar diff estruturado
- Formatar para exibição
- Rastreabilidade completa

---

## Roadmap Completo

### ✅ FASE 0: Setup e Validação (COMPLETO)
- [x] Estrutura de pastas
- [x] Arquivos skeleton
- [x] Documentação
- [x] Decisão: PROSSEGUIR

### 🔥 FASE 1: Análise Expandida (4-6 dias)
- [ ] `enhanced_analyzer.py`
- [ ] `impact_scorer.py`
- [ ] Prompts expandidos
- [ ] Testes com 5+ protocolos

### 🔥 FASE 2: Feedback Loop (5-7 dias)
- [ ] `feedback_collector.py`
- [ ] `prompt_refiner.py`
- [ ] `feedback_storage.py`
- [ ] Versionamento de prompts

### 🔥 FASE 3: Controle de Custos (3-4 dias)
- [ ] `cost_estimator.py`
- [ ] `authorization_manager.py`
- [ ] `cost_tracker.py`
- [ ] Relatórios de custo

### 🔥 FASE 4: CLI Interativa (5-7 dias)
- [ ] `interactive_cli.py`
- [ ] `task_manager.py`
- [ ] `display_manager.py`
- [ ] Onboarding completo

### ⏳ FASE 5: Auto-Apply (3-5 dias)
- [ ] `improvement_applicator.py`
- [ ] `llm_client.py`
- [ ] Integração com autorização

### ⏳ FASE 6: Validação (2-3 dias)
- [ ] `structural_validator.py`
- [ ] `schema_validator.py`

### ⏳ FASE 7: Diff (2-3 dias)
- [ ] `diff_generator.py`
- [ ] `formatter.py`

### ⏳ FASE 8: Pipeline Integration (3-5 dias)
- [ ] `pipeline.py` completo
- [ ] Integração de todos os módulos

### ⏳ FASE 9: Testes Intensivos (3-4 dias)
- [ ] 15-20 protocolos reais
- [ ] Validação de métricas
- [ ] Correção de bugs

### ⏳ FASE 10: Production Deploy (1-2 dias)
- [ ] Documentação final
- [ ] Deploy em produção

**Tempo Total Estimado**: 30-45 dias úteis

---

## Como Contribuir

### Ambiente de Desenvolvimento

```bash
# 1. Clone o repositório
git clone <repo-url>
cd AgenteV2

# 2. Instalar dependências
pip install -r requirements.txt

# Dependências V3 adicionais:
pip install rich prompt_toolkit questionary

# 3. Configurar .env
echo "OPENROUTER_API_KEY=sk-or-v1-sua-chave" > .env

# 4. Criar branch
git checkout -b feature/v3-<modulo>
```

### Padrões de Código

1. **Docstrings Completas**: Todas as classes e métodos
2. **Type Hints**: Usar typing para todos os parâmetros
3. **TODOs Claros**: Marcar implementações pendentes
4. **Testes**: Cobrir todas as funcionalidades

### Workflow

1. Escolher uma FASE do roadmap
2. Implementar módulo completo
3. Escrever testes
4. Documentar
5. Pull Request

---

## Como Testar

### Testes Unitários

```bash
# Rodar todos os testes
pytest tests/agent_v3/

# Rodar testes de um módulo específico
pytest tests/agent_v3/test_enhanced_analyzer.py

# Com coverage
pytest --cov=src/agent_v3
```

### Testes de Integração

```bash
# Testar pipeline completo
python -m tests.agent_v3.test_pipeline_integration

# Testar com protocolo real
python -m tests.agent_v3.test_real_protocol
```

### Testes de UX

```bash
# Testar CLI interativa
python run_v3_cli.py

# Modo dry-run (sem consumo real)
python run_v3_cli.py --dry-run
```

---

## FAQ

### Q: Quando o V3 estará disponível?
**A**: Estimativa de 30-45 dias úteis a partir de 2025-12-01.

### Q: O V3 substituirá o V2?
**A**: Não. V2 continuará disponível. V3 será uma opção adicional.

### Q: Quanto custará usar o V3?
**A**: Custo estimado: $0.01-$0.02 por protocolo (com controle rigoroso).

### Q: Posso usar o V3 sem feedback loop?
**A**: Sim. Feedback é opcional mas recomendado para melhor qualidade.

### Q: Como funciona o controle de custos?
**A**: Estimativa pré-execução + autorização obrigatória + limites configuráveis.

### Q: O que é "thinking visível"?
**A**: Sistema mostra em tempo real o que está fazendo (similar ao Claude Code).

### Q: Posso desativar o auto-apply?
**A**: Sim. V3 pode funcionar apenas com análise expandida + feedback.

---

## Recursos Adicionais

- **Plano Completo**: `V3_IMPLEMENTATION_PLAN_REFINED.md`
- **README Principal**: `README.md`
- **README V3**: `src/agent_v3/README.md`
- **Roadmap**: `roadmap.md`

---

**Última Atualização**: 2025-12-01
**Status**: 📋 Documentação Completa - Pronto para Desenvolvimento
