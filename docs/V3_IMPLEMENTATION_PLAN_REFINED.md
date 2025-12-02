# 🚀 Agent V3 - Plano de Implementação Refinado

**Versão**: 3.0.0-alpha-refined
**Status**: 📋 Planejamento
**Foco**: Relatórios Sofisticados + Human-in-the-Loop + CLI Amigável
**Data**: 2025-12-01
**Meta**: Sistema de análise clínica com feedback contínuo e UX excepcional

---

## 🎯 Visão Geral Estratégica

### Mudança de Paradigma

**V2 (Atual)**: Análise passiva → Relatório estático → Implementação manual (dias/semanas)

**V3 (Nova Visão)**: Análise ativa → Feedback iterativo → Auto-apply assistido → Implementação automática (minutos)

### Objetivos Principais

1. **Relatórios de Alta Qualidade**: Expandir análise do agent_v2 para gerar relatórios mais sofisticados e acionáveis
2. **Human-in-the-Loop**: Sistema de feedback para fine-tuning contínuo dos prompts
3. **Controle de Custos**: Mecanismo robusto de estimativa e autorização de consumo
4. **UX Excepcional**: CLI inspirada no Claude Code com transparência total do processo

### Princípios Fundamentais

- **Transparência Total**: Usuário vê cada etapa do processo (thinking, tasks, progresso)
- **Controle do Usuário**: Nada acontece sem autorização explícita
- **Aprendizado Contínuo**: Sistema melhora com feedback de cada análise
- **Segurança Primeiro**: Validação rigorosa em cada etapa, zero tolerância a erros

---

## 📐 Arquitetura do Sistema V3

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT V3 PIPELINE                           │
│              Análise → Feedback → Refinamento → Correção            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 1: ONBOARDING INTERATIVO                                      │
│  ✓ Apresentação amigável do sistema                                 │
│  ✓ Seleção de protocolo e playbook                                  │
│  ✓ Configuração de modelo LLM                                       │
│  ✓ Configuração de limites de custo                                 │
│  ✓ Visualização de progresso (tasks, thinking)                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 2: ANÁLISE EXPANDIDA (V2 Enhanced)                            │
│  ✓ Análise estrutural detalhada                                     │
│  ✓ Extração clínica abrangente                                      │
│  ✓ Geração de 20-50 sugestões de melhoria (vs 5-15 atual)          │
│  ✓ Priorização por impacto (Segurança, Economia, Esforço)          │
│  ✓ Rastreabilidade de evidências (playbook → sugestão)             │
│  ✓ Estimativa de custo para aplicação de cada sugestão             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 3: APRESENTAÇÃO DO RELATÓRIO                                  │
│  ✓ Relatório formatado e legível                                    │
│  ✓ Sugestões agrupadas por categoria                               │
│  ✓ Scores de impacto destacados                                     │
│  ✓ Visualização interativa (CLI rica)                              │
│  ✓ Opções: Aprovar | Editar | Rejeitar | Feedback                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 4: FEEDBACK LOOP (Human-in-the-Loop) 🆕                       │
│  ✓ Usuário revisa sugestões (relevante vs irrelevante)             │
│  ✓ Usuário fornece feedback qualitativo                            │
│  ✓ Usuário pode editar/remover sugestões                           │
│  ✓ Sistema aprende com feedback                                     │
│  ✓ Refinamento automático de system prompts                        │
│  ✓ Geração de relatório refinado                                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 5: APROVAÇÃO E CONTROLE DE CUSTOS 🆕                          │
│  ✓ Estimativa de custo para auto-apply                             │
│  ✓ Breakdown por modelo e por sugestão                             │
│  ✓ Autorização explícita do usuário                                │
│  ✓ Limites de custo configuráveis                                   │
│  ✓ Simulação "dry-run" sem consumo                                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 6: AUTO-APPLY ASSISTIDO                                       │
│  ✓ Aplicação automática de melhorias aprovadas                     │
│  ✓ Validação estrutural contínua                                    │
│  ✓ Geração de diff detalhado                                        │
│  ✓ Rastreabilidade completa                                         │
│  ✓ Rollback automático em caso de erro                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASE 7: QA FINAL E SAÍDA                                           │
│  ✓ Validação final do protocolo corrigido                          │
│  ✓ Geração de relatório de mudanças                                │
│  ✓ Versionamento automático (MAJOR.MINOR.PATCH)                    │
│  ✓ Logs de auditoria completos                                      │
│  ✓ Métricas de qualidade e custo                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Módulos e Componentes Detalhados

### 1. CLI Interativa Avançada (`src/agent_v3/cli/`)

**Inspiração**: Claude Code CLI - Transparência, thinking visível, organização de tasks

#### 1.1 `interactive_cli.py` - Motor Principal da CLI 🆕

**Responsabilidades**:
- Gerenciar estado da sessão (onboarding → análise → feedback → auto-apply)
- Renderizar UI rica no terminal (progress bars, spinners, formatação)
- Exibir "thinking" do sistema (o que está sendo feito e por quê)
- Gerenciar tasks visíveis ao usuário (similar ao Claude Code)
- Capturar input do usuário de forma amigável

**Características**:
```python
class InteractiveCLI:
    """CLI interativa inspirada no Claude Code."""

    def __init__(self):
        self.session_state = SessionState()
        self.task_manager = TaskManager()
        self.display = RichDisplay()  # rich library para UI

    def run_onboarding(self):
        """
        Onboarding amigável:
        1. Apresentação do Agent V3
        2. Seleção de protocolo (visual, com preview)
        3. Seleção de playbook (opcional)
        4. Configuração de modelo LLM
        5. Configuração de limites de custo
        6. Resumo da configuração
        """

    def show_thinking(self, thought: str):
        """Exibe o 'pensamento' do sistema ao usuário."""

    def update_task_status(self, task_id: str, status: str):
        """Atualiza status de task visível."""

    def show_progress(self, step: str, progress: float):
        """Exibe barra de progresso com descrição."""
```

**Bibliotecas**:
- `rich` - UI rica no terminal (progress bars, tables, syntax highlighting)
- `prompt_toolkit` - Input interativo avançado
- `questionary` - Prompts amigáveis (seleção, confirmação, etc.)

#### 1.2 `task_manager.py` - Gerenciamento de Tasks Visíveis 🆕

**Responsabilidades**:
- Criar e gerenciar tasks visíveis ao usuário
- Atualizar status de tasks em tempo real
- Exibir lista de tasks (pending, in_progress, completed)

**Exemplo de Tasks**:
```
✓ Carregar protocolo JSON
✓ Carregar playbook
⚙ Gerar análise expandida (30s estimado)
⏳ Aguardando feedback do usuário
⏳ Aplicar melhorias automaticamente
⏳ Validar protocolo corrigido
```

#### 1.3 `display_manager.py` - Renderização de Conteúdo 🆕

**Responsabilidades**:
- Renderizar relatórios formatados
- Exibir tabelas de sugestões
- Mostrar diff visual de mudanças
- Formatação de custos e métricas

**Características**:
- Syntax highlighting para JSON
- Tabelas formatadas com `rich.table`
- Diff colorido (verde/vermelho)
- Formatação de valores monetários

---

### 2. Sistema de Análise Expandida (`src/agent_v3/analysis/`)

#### 2.1 `enhanced_analyzer.py` - Análise V2 Expandida 🆕

**Objetivo**: Ampliar qualidade e tamanho da análise do agent_v2

**Melhorias sobre V2**:
1. **Mais sugestões**: 20-50 sugestões (vs 5-15 atual)
2. **Categorização detalhada**: Segurança | Economia | Eficiência | Usabilidade
3. **Scores de impacto**: Cada sugestão com score 0-10 para cada categoria
4. **Rastreabilidade completa**: Cada sugestão linkada a evidência do playbook
5. **Estimativa de esforço**: Estimativa de tempo/custo para implementar cada sugestão

**Interface**:
```python
class EnhancedAnalyzer:
    """Análise expandida de protocolos clínicos."""

    def analyze_comprehensive(
        self,
        protocol_json: dict,
        playbook_content: str,
        model: str
    ) -> ExpandedAnalysisResult:
        """
        Análise abrangente com sugestões expandidas.

        Returns:
            ExpandedAnalysisResult contendo:
            - structural_analysis: Análise estrutural
            - clinical_extraction: Extração clínica
            - improvement_suggestions: 20-50 sugestões priorizadas
            - impact_scores: Scores por categoria
            - evidence_mapping: Sugestão → Evidência playbook
            - cost_estimation: Custo estimado para aplicar cada sugestão
        """
```

**Exemplo de Sugestão Expandida**:
```json
{
  "id": "SUGG-001",
  "category": "seguranca",
  "priority": "alta",
  "title": "Adicionar triagem de risco cardíaco",
  "description": "Protocolo não contempla avaliação de risco cardiovascular...",
  "rationale": "Baseado no playbook seção 3.2.1, pacientes com...",
  "impact_scores": {
    "seguranca": 9,
    "economia": 7,
    "eficiencia": 5,
    "usabilidade": 6
  },
  "evidence": {
    "playbook_section": "3.2.1 - Avaliação de Risco Cardiovascular",
    "quote": "Todos os pacientes acima de 45 anos devem..."
  },
  "implementation_effort": {
    "time_estimate_hours": 2,
    "complexity": "media",
    "breaking_change": false
  },
  "auto_apply_cost_estimate": {
    "tokens_input": 5000,
    "tokens_output": 1000,
    "cost_usd": 0.003
  }
}
```

#### 2.2 `impact_scorer.py` - Scoring de Impacto Detalhado

**Responsabilidades**:
- Calcular scores de impacto para cada sugestão
- Categorias: Segurança (0-10), Economia (L/M/A), Eficiência (L/M/A), Usabilidade (0-10)
- Priorização automática baseada em scores

**Algoritmo de Priorização**:
```python
def calculate_priority(scores: dict) -> str:
    """
    Alta: Segurança ≥8 OU (Economia=A E Segurança≥5)
    Média: Segurança 5-7 OU Economia M/A
    Baixa: Demais casos
    """
```

---

### 3. Sistema de Feedback e Fine-Tuning (`src/agent_v3/feedback/`) 🆕

**Este é o diferencial do V3** - Sistema de aprendizado contínuo baseado em feedback humano

#### 3.1 `feedback_collector.py` - Captura de Feedback do Usuário 🆕

**Responsabilidades**:
- Apresentar sugestões ao usuário para revisão
- Capturar feedback: Relevante | Irrelevante | Editar | Comentário
- Armazenar feedback estruturado

**Interface**:
```python
class FeedbackCollector:
    """Coleta feedback do usuário sobre sugestões."""

    def collect_feedback_interactive(
        self,
        suggestions: List[Suggestion]
    ) -> FeedbackSession:
        """
        Apresenta sugestões interativamente e coleta feedback.

        Para cada sugestão:
        1. Exibe sugestão formatada
        2. Pergunta: Relevante? (S/N/Editar/Comentar)
        3. Se Editar: permite edição inline
        4. Se Comentar: captura comentário qualitativo
        5. Armazena feedback estruturado
        """
```

**Formato de Feedback**:
```json
{
  "session_id": "fb-20251201-001",
  "timestamp": "2025-12-01T14:30:00Z",
  "protocol_name": "UNIMED_ORL_v0.1.2",
  "model_used": "anthropic/claude-sonnet-4.5",
  "suggestions_feedback": [
    {
      "suggestion_id": "SUGG-001",
      "user_verdict": "relevant",
      "user_comment": "Excelente sugestão, crítica para segurança",
      "edited": false
    },
    {
      "suggestion_id": "SUGG-002",
      "user_verdict": "irrelevant",
      "user_comment": "Já contemplado em outro nó, redundante",
      "edited": false
    },
    {
      "suggestion_id": "SUGG-003",
      "user_verdict": "relevant",
      "user_comment": null,
      "edited": true,
      "edited_version": {
        "title": "Adicionar triagem de diabetes (editado)",
        "description": "..."
      }
    }
  ],
  "general_feedback": "Muitas sugestões redundantes. Melhorar detecção de nós existentes.",
  "quality_rating": 7
}
```

#### 3.2 `prompt_refiner.py` - Refinamento Automático de Prompts 🆕

**Responsabilidades**:
- Analisar feedback coletado
- Identificar padrões de erro (ex: muitas sugestões irrelevantes sobre tema X)
- Gerar ajustes nos system prompts
- Aplicar ajustes de forma incremental e rastreável

**Lógica de Refinamento**:
```python
class PromptRefiner:
    """Refina system prompts baseado em feedback."""

    def analyze_feedback_patterns(
        self,
        feedback_sessions: List[FeedbackSession]
    ) -> List[Pattern]:
        """
        Identifica padrões:
        - Categorias de sugestões frequentemente rejeitadas
        - Tipos de erro recorrentes
        - Áreas onde prompts precisam melhorar
        """

    def generate_prompt_adjustments(
        self,
        patterns: List[Pattern]
    ) -> List[PromptAdjustment]:
        """
        Gera ajustes nos prompts:
        - Adicionar restrições (ex: "Evite sugerir X se Y já existe")
        - Melhorar instruções de categorização
        - Ajustar thresholds de relevância
        """

    def apply_adjustments(
        self,
        adjustments: List[PromptAdjustment]
    ) -> None:
        """
        Aplica ajustes de forma incremental:
        - Versiona prompts (v1.0.0 → v1.0.1)
        - Registra mudanças em changelog
        - Permite rollback se necessário
        """
```

**Exemplo de Ajuste de Prompt**:
```
Feedback Pattern Detectado:
- 15 de 20 sugestões sobre "adicionar nó X" foram rejeitadas
- Usuário comentou: "Nó já existe com nome diferente"

Ajuste de Prompt Gerado:
ANTES:
"Identifique nós faltantes no protocolo..."

DEPOIS:
"Identifique nós faltantes no protocolo. IMPORTANTE: Antes de sugerir
adicionar um nó, verifique se já existe um nó similar com nome ou
propósito equivalente. Liste nós existentes relevantes antes de sugerir
adição."

Versão: v1.0.0 → v1.0.1
Changelog: "Melhorar detecção de nós existentes antes de sugerir adição"
```

#### 3.3 `feedback_storage.py` - Armazenamento de Feedback 🆕

**Responsabilidades**:
- Persistir feedback em formato estruturado
- Facilitar análise de feedback histórico
- Suportar queries para análise de padrões

**Storage**:
- Formato: JSON (fácil de versionar e analisar)
- Localização: `feedback_sessions/`
- Estrutura: `feedback_sessions/YYYYMM/session_id.json`

---

### 4. Sistema de Controle de Custos (`src/agent_v3/cost_control/`) 🆕

**Funcionalidade crítica** - Controle rigoroso de consumo de tokens e custos

#### 4.1 `cost_estimator.py` - Estimativa de Custos 🆕

**Responsabilidades**:
- Estimar consumo de tokens para cada operação
- Calcular custo em USD baseado no modelo selecionado
- Gerar estimativas pré-execução
- Rastrear custos reais pós-execução

**Interface**:
```python
class CostEstimator:
    """Estimativa e rastreamento de custos."""

    def estimate_analysis_cost(
        self,
        protocol_size: int,
        playbook_size: int,
        model: str
    ) -> CostEstimate:
        """Estima custo da análise V2 expandida."""

    def estimate_auto_apply_cost(
        self,
        protocol_size: int,
        suggestions: List[Suggestion],
        model: str
    ) -> CostEstimate:
        """Estima custo do auto-apply."""

    def track_actual_cost(
        self,
        tokens_used: dict,
        model: str
    ) -> ActualCost:
        """Registra custo real após execução."""
```

**Formato de Estimativa**:
```json
{
  "operation": "auto_apply",
  "model": "anthropic/claude-sonnet-4.5",
  "estimated_tokens": {
    "input": 50000,
    "output": 60000
  },
  "estimated_cost_usd": {
    "input": 0.15,
    "output": 0.90,
    "total": 1.05
  },
  "confidence": "medium"
}
```

#### 4.2 `authorization_manager.py` - Autorização de Consumo 🆕

**Responsabilidades**:
- Apresentar estimativa de custo ao usuário
- Solicitar autorização explícita
- Validar limites de custo configurados
- Registrar decisões de autorização

**Fluxo de Autorização**:
```python
class AuthorizationManager:
    """Gerencia autorização de consumo."""

    def request_authorization(
        self,
        cost_estimate: CostEstimate,
        user_limits: UserLimits
    ) -> AuthorizationDecision:
        """
        Fluxo:
        1. Exibe estimativa formatada
        2. Verifica se está dentro dos limites
        3. Se acima: alerta e pede confirmação explícita
        4. Se muito acima: rejeita automaticamente
        5. Registra decisão
        """
```

**Exemplo de Autorização**:
```
╔═══════════════════════════════════════════════════════════╗
║            ESTIMATIVA DE CUSTO - AUTO-APPLY               ║
╠═══════════════════════════════════════════════════════════╣
║ Modelo: Claude Sonnet 4.5                                 ║
║ Tokens de entrada: ~50,000                                ║
║ Tokens de saída:   ~60,000                                ║
║                                                           ║
║ Custo estimado:                                           ║
║   • Entrada:  $0.15                                       ║
║   • Saída:    $0.90                                       ║
║   • Total:    $1.05                                       ║
║                                                           ║
║ Status: ⚠️  ACIMA DO LIMITE ($0.50)                       ║
╚═══════════════════════════════════════════════════════════╝

⚠️  Este custo está acima do limite configurado.
   Deseja continuar? (s/N):
```

#### 4.3 `cost_tracker.py` - Rastreamento de Custos 🆕

**Responsabilidades**:
- Rastrear custos de todas as operações
- Gerar relatórios de custo por sessão/dia/mês
- Alertar sobre anomalias de custo

**Métricas Rastreadas**:
- Custo por protocolo analisado
- Custo por sugestão aplicada
- Custo total por dia/mês
- Economia via cache (prompt caching)

---

### 5. Motor de Auto-Apply (`src/agent_v3/applicator/`)

**Mantém a arquitetura já planejada** com melhorias de integração

#### 5.1 Melhorias em `improvement_applicator.py`

**Adições**:
- Integração com sistema de autorização
- Rastreamento de custo real vs estimado
- Aplicação incremental com validação a cada sugestão
- Rollback automático em caso de erro

**Interface Atualizada**:
```python
class ImprovementApplicator:
    """Aplicação automática de melhorias com controle de custo."""

    def apply_improvements_with_authorization(
        self,
        protocol_json: dict,
        suggestions: List[Suggestion],
        model: str,
        cost_limit: float
    ) -> ApplyResult:
        """
        Fluxo:
        1. Estima custo total
        2. Solicita autorização
        3. Se autorizado: aplica melhorias
        4. Valida a cada mudança
        5. Registra custo real
        6. Compara real vs estimado
        """
```

---

### 6. Sistema de Validação (`src/agent_v3/validator/`)

**Mantém a arquitetura já planejada** - Validação estrutural rigorosa

---

### 7. Geração de Diff (`src/agent_v3/diff/`)

**Mantém a arquitetura já planejada** - Diff visual detalhado

---

## 📅 Roadmap de Implementação - Refinado

### ✅ FASE 0: Setup e Validação (COMPLETO)
- [x] Estrutura de pastas
- [x] Validação de auto-apply (GO/NO-GO)
- [x] Decisão: PROSSEGUIR

---

### ✅ FASE 1: Sistema de Análise Expandida (COMPLETA)

**Duração**: 4-6 dias
**Objetivo**: Gerar relatórios mais sofisticados e acionáveis

**Entregas**:
- [x] `src/agent/analysis/enhanced.py` ✅
- [x] `src/agent/analysis/impact_scorer.py` ✅ (MVP com lógica placeholder)
- [x] Novo prompt template para análise expandida ✅
- [x] Testes com 5+ protocolos reais ✅

**Critérios de Sucesso**:
- ✅ Gerar 20-50 sugestões (vs 5-15 atual) - **ATENDIDO**
- ✅ Cada sugestão com scores de impacto - **ATENDIDO**
- ✅ Rastreabilidade completa (sugestão → evidência) - **ATENDIDO**
- ✅ Estimativa de custo por sugestão - **ATENDIDO**

**Dependências**: Nenhuma

**Status**: ✅ **COMPLETA E FUNCIONAL**

---

### ✅ FASE 2: Sistema de Feedback e Fine-Tuning (COMPLETA)

**Duração**: 5-7 dias
**Objetivo**: Implementar human-in-the-loop para melhoria contínua

**Entregas**:
- [x] `src/agent/feedback/feedback_collector.py` ✅
- [x] `src/agent/feedback/prompt_refiner.py` ✅
- [x] `src/agent/feedback/feedback_storage.py` ✅
- [x] Sistema de versionamento de prompts ✅
- [x] Interface CLI para feedback ✅

**Critérios de Sucesso**:
- ✅ Captura de feedback estruturado - **ATENDIDO**
- ✅ Identificação automática de padrões de erro - **ATENDIDO**
- ✅ Ajuste automático de prompts - **ATENDIDO**
- ✅ Rastreabilidade de mudanças em prompts - **ATENDIDO**
- ⏳ Melhoria mensurável após 3-5 sessões de feedback - **EM VALIDAÇÃO**

**Dependências**: FASE 1 ✅

**Status**: ✅ **COMPLETA E FUNCIONAL**

---

### ✅ FASE 3: Sistema de Controle de Custos (COMPLETA)

**Duração**: 3-4 dias
**Objetivo**: Controle rigoroso de consumo e autorização

**Entregas**:
- [x] `src/agent/cost_control/cost_estimator.py` ✅
- [x] `src/agent/cost_control/authorization_manager.py` ✅ (removido, apenas informativo)
- [ ] `src/agent/cost_control/cost_tracker.py` ⚠️ (Skeleton, não crítico para MVP)
- [x] Configuração de limites por usuário/sessão ✅
- [ ] Relatórios de custo ⚠️ (Parcial, via cost_tracker)

**Status**: ✅ **COMPLETA E FUNCIONAL** (CostTracker é skeleton não crítico)

**Critérios de Sucesso**:
- ✅ Estimativa de custo pré-execução com 90%+ precisão - **ATENDIDO**
- ✅ Exibição informativa de custos - **ATENDIDO** (autorização removida conforme requisito)
- ⚠️ Rastreamento de custo real vs estimado (CostTracker é skeleton, não crítico)
- ⚠️ Alertas de anomalias (não implementado ainda)

**Dependências**: FASE 1

---

### ⏳ FASE 6: CLI Interativa Avançada (PRIORIDADE ALTA)

**Duração**: 5-7 dias
**Objetivo**: UX excepcional inspirada no Claude Code

**Entregas**:
- [ ] `src/agent/cli/interactive_cli.py`
- [ ] `src/agent/cli/task_manager.py`
- [ ] `src/agent/cli/display_manager.py`
- [ ] Onboarding interativo
- [ ] Visualização de thinking e tasks
- [ ] Progress bars e spinners

**Critérios de Sucesso**:
- ✅ Onboarding claro e amigável
- ✅ Transparência total do processo (thinking visível)
- ✅ Tasks atualizadas em tempo real
- ✅ Feedback qualitativo: "melhor CLI que já usei"

**Dependências**: FASES 1, 2, 3 ✅

**Nota**: A CLI atual (`src/cli/run_qa_cli.py`) já suporta ambos os modos (Standard e Enhanced), mas pode ser melhorada com UX mais rica.

---

### ⏳ FASE 5: Motor de Auto-Apply (Mantém Planejamento Original)

**Duração**: 3-5 dias
**Objetivo**: Aplicação automática de melhorias aprovadas

**Entregas**:
- [ ] `src/agent_v3/applicator/improvement_applicator.py`
- [ ] `src/agent_v3/applicator/llm_client.py`
- [ ] Integração com sistema de autorização
- [ ] Rastreamento de custo real

**Critérios de Sucesso**:
- ✅ Taxa de sucesso >95%
- ✅ Custo real dentro de ±10% do estimado
- ✅ Rollback automático em caso de erro

**Dependências**: FASES 1, 3, 4 ✅

---

### ⏳ FASE 7: Sistema de Validação Avançada (PRIORIDADE MÉDIA)

**Duração**: 2-3 dias
**Entregas**:
- [ ] `src/agent/validator/structural_validator.py`
- [ ] `src/agent/validator/schema_validator.py`

**Critérios de Sucesso**:
- ✅ Zero protocolos quebrados salvos
- ✅ Detecção de 100% dos erros estruturais

**Dependências**: FASE 5

---

### ⏳ FASE 8: Geração de Diff Visual (PRIORIDADE BAIXA)

**Duração**: 2-3 dias
**Entregas**:
- [ ] `src/agent/diff/diff_generator.py`
- [ ] `src/agent/diff/formatter.py`

**Critérios de Sucesso**:
- ✅ Diff completo e legível
- ✅ Rastreabilidade 100%

**Dependências**: FASE 5

---

### ⏳ FASE 9: Pipeline Integration Completo

**Duração**: 3-5 dias
**Entregas**:
- [ ] `src/agent/pipeline.py` (completo)
- [ ] Integração de todos os módulos

**Critérios de Sucesso**:
- ✅ Pipeline completo funcional
- ✅ Fluxo end-to-end sem erros
- ✅ Feedback loop operacional

**Dependências**: FASES 1-8

---

### ⏳ FASE 10: Testes Intensivos

**Duração**: 3-4 dias
**Entregas**:
- [ ] Testes com 15-20 protocolos reais
- [ ] Validação de métricas
- [ ] Correção de bugs

**Critérios de Sucesso**:
- ✅ Taxa de sucesso >95%
- ✅ Feedback de usuários positivo
- ✅ Melhoria mensurável após feedback loop

**Dependências**: FASE 9

---

### ⏳ FASE 11: Production Deploy

**Duração**: 1-2 dias
**Entregas**:
- [ ] Documentação completa
- [ ] README atualizado
- [ ] Deploy em produção

**Critérios de Sucesso**:
- ✅ Sistema em produção
- ✅ Usuários usando
- ✅ Feedback positivo

**Dependências**: FASE 9

---

## 🎯 Métricas de Sucesso do V3

### Obrigatórias

**Qualidade de Relatórios**:
- ✅ 20-50 sugestões por análise (vs 5-15 atual)
- ✅ 100% das sugestões com rastreabilidade
- ✅ 90%+ de sugestões relevantes (após fine-tuning)

**Feedback Loop**:
- ✅ Sistema aprende com feedback
- ✅ Melhoria mensurável após 3-5 sessões
- ✅ Taxa de sugestões irrelevantes reduz 50%+

**Controle de Custos**:
- ✅ Estimativa de custo com 90%+ precisão
- ✅ Zero execuções sem autorização
- ✅ Custo médio <$0.02 por protocolo

**UX**:
- ✅ Onboarding <3 minutos
- ✅ Transparência total do processo
- ✅ Feedback qualitativo positivo

**Auto-Apply**:
- ✅ Taxa de sucesso >95%
- ✅ Zero protocolos quebrados
- ✅ Rastreabilidade completa

---

## 📊 Exemplo de Fluxo Completo (User Journey)

### 1. Início da Sessão

```
╔═══════════════════════════════════════════════════════════╗
║         🔍 Agent V3 - Análise Clínica Inteligente         ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Bem-vindo ao Agent V3! Este sistema irá:                 ║
║                                                           ║
║  ✓ Analisar seu protocolo clínico                        ║
║  ✓ Gerar 20-50 sugestões de melhoria                     ║
║  ✓ Aprender com seu feedback                             ║
║  ✓ Aplicar melhorias automaticamente (opcional)          ║
║                                                           ║
║  Vamos começar!                                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Etapa 1/5: Seleção de Protocolo
────────────────────────────────

Protocolos disponíveis:
  1. UNIMED_ORL_v0.1.2.json (65KB)
  2. AMIL_Reumatologia_v0.2.1.json (113KB)
  3. UNIMED_Testosterona_v0.1.2.json (15KB)

Selecione um protocolo (1-3): _
```

### 2. Configuração

```
Etapa 2/5: Configuração
───────────────────────

✓ Protocolo: UNIMED_ORL_v0.1.2.json
? Playbook (opcional): [Selecionar arquivo / Pular]
? Modelo LLM:
  > Claude Sonnet 4.5 (Recomendado - melhor qualidade)
    Gemini 2.5 Flash (Mais rápido)
    Grok 4 Fast (Mais barato)

? Limite de custo por operação: [$1.00]

────────────────────────────────────────────────────────────
Configuração:
  • Protocolo: UNIMED_ORL_v0.1.2.json
  • Playbook: playbook_orl.md
  • Modelo: Claude Sonnet 4.5
  • Limite de custo: $1.00
────────────────────────────────────────────────────────────

Tudo certo? (S/n): _
```

### 3. Análise com Thinking Visível

```
Etapa 3/5: Análise Expandida
─────────────────────────────

💭 Pensando: Carregando protocolo JSON...
✓ Protocolo carregado (65KB, 42 nós)

💭 Pensando: Carregando playbook...
✓ Playbook carregado (15 páginas)

💭 Pensando: Estimando custo da análise...
✓ Custo estimado: $0.45

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Análise concluída em 18s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Relatório de Análise:

Encontradas 32 sugestões de melhoria:
  • 8 Alta prioridade (Segurança ≥8)
  • 15 Média prioridade
  • 9 Baixa prioridade

Pressione Enter para visualizar relatório detalhado...
```

### 4. Apresentação de Sugestões

```
╔═══════════════════════════════════════════════════════════╗
║                  SUGESTÕES DE MELHORIA                    ║
╚═══════════════════════════════════════════════════════════╝

[1/32] 🔴 ALTA PRIORIDADE

  Categoria: Segurança
  Título: Adicionar triagem de risco cardíaco em otoplastia

  Descrição:
  O protocolo não contempla avaliação de risco cardiovascular
  para pacientes acima de 45 anos submetidos a otoplastia sob
  anestesia geral.

  Evidência (Playbook):
  Seção 3.2.1 - "Todos os pacientes acima de 45 anos devem
  passar por avaliação cardiovascular antes de procedimentos
  sob anestesia geral."

  Impacto:
    Segurança:   ████████░░ 9/10
    Economia:    Alta (evita eventos adversos)
    Esforço:     2 horas (baixo)

  Custo para aplicar: $0.003

────────────────────────────────────────────────────────────
  Esta sugestão é relevante? (S/n/Editar/Comentar): _
```

### 5. Coleta de Feedback

```
Feedback coletado para sugestão #1:
  ✓ Relevante
  💬 Comentário: "Excelente, crítico para segurança"

────────────────────────────────────────────────────────────

[2/32] 🟡 MÉDIA PRIORIDADE

  Categoria: Eficiência
  Título: Adicionar caminho rápido para casos simples

  (...)

  Esta sugestão é relevante? (S/n/Editar/Comentar): n

────────────────────────────────────────────────────────────

Feedback coletado para sugestão #2:
  ✗ Irrelevante
  💬 Comentário: "Caminho rápido já existe no nó 12"

────────────────────────────────────────────────────────────

Progresso: [████████████░░░░░░░░░░░░░░░░] 2/32

(Continua...)
```

### 6. Fine-Tuning e Relatório Refinado

```
Etapa 4/5: Refinamento Baseado em Feedback
───────────────────────────────────────────

💭 Pensando: Analisando padrões de feedback...
✓ Identificados 3 padrões de erro

💭 Pensando: Ajustando prompts...
✓ Prompts refinados (v1.0.0 → v1.0.1)

💭 Pensando: Gerando relatório refinado...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ Relatório refinado gerado

────────────────────────────────────────────────────────────

📊 Resumo do Refinamento:

  Sugestões originais: 32
  Rejeitadas por você: 8
  Removidas após refinamento: 5
  Sugestões finais: 19

  Ajustes nos prompts:
    • Melhorar detecção de nós existentes
    • Evitar sugestões redundantes sobre caminhos rápidos
    • Priorizar sugestões de segurança

────────────────────────────────────────────────────────────

Relatório refinado salvo em:
  reports/UNIMED_ORL_v0.1.2_refined_20251201.txt

Deseja aplicar melhorias automaticamente? (S/n): _
```

### 7. Auto-Apply com Autorização

```
Etapa 5/5: Aplicação Automática de Melhorias
─────────────────────────────────────────────

💭 Pensando: Estimando custo para aplicar 19 sugestões...

╔═══════════════════════════════════════════════════════════╗
║            ESTIMATIVA DE CUSTO - AUTO-APPLY               ║
╠═══════════════════════════════════════════════════════════╣
║ Modelo: Claude Sonnet 4.5                                 ║
║ Sugestões: 19                                             ║
║                                                           ║
║ Tokens estimados:                                         ║
║   • Entrada:  ~55,000                                     ║
║   • Saída:    ~65,000                                     ║
║                                                           ║
║ Custo estimado:                                           ║
║   • Entrada:  $0.17                                       ║
║   • Saída:    $0.98                                       ║
║   • Total:    $1.15                                       ║
║                                                           ║
║ Status: ⚠️  ACIMA DO LIMITE ($1.00)                       ║
╚═══════════════════════════════════════════════════════════╝

⚠️  Este custo está 15% acima do limite configurado.

Opções:
  1. Continuar mesmo assim
  2. Aplicar apenas sugestões de alta prioridade (8 sugestões, $0.52)
  3. Cancelar

Escolha (1/2/3): 2

────────────────────────────────────────────────────────────

✓ Autorizado: Aplicar 8 sugestões de alta prioridade

💭 Pensando: Aplicando melhorias...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

✓ 8 sugestões aplicadas com sucesso
✓ Protocolo validado
✓ Versionamento: v0.1.2 → v0.1.3

────────────────────────────────────────────────────────────

📊 Resumo Final:

  Custo real: $0.54 (vs $0.52 estimado, +3.8%)
  Tempo total: 2m 15s

  Arquivos gerados:
    • Protocolo corrigido:
      models_json/UNIMED_ORL_v0.1.3_20251201.json
    • Diff de mudanças:
      reports/UNIMED_ORL_v0.1.2_to_v0.1.3_diff.html
    • Relatório completo:
      reports/UNIMED_ORL_v0.1.2_analysis_20251201.json

  Próximos passos:
    • Revisar diff visual
    • Validar clinicamente
    • Deploy em produção

────────────────────────────────────────────────────────────

✨ Sessão concluída com sucesso!

Obrigado por usar o Agent V3. Seu feedback foi registrado
e ajudará a melhorar futuras análises.
```

---

## 🛠️ Tecnologias e Dependências

### Bibliotecas Python Necessárias

**UI/CLI**:
- `rich` - Terminal UI rica (progress bars, tables, syntax highlighting)
- `prompt_toolkit` - Input interativo avançado
- `questionary` - Prompts amigáveis

**Existentes** (já no projeto):
- `openai` / `anthropic` - LLM clients
- `requests` - HTTP para OpenRouter
- `jsonschema` - Validação de schema
- `python-dotenv` - Env vars

**Adicionar ao `requirements.txt`**:
```txt
rich>=13.7.0
prompt_toolkit>=3.0.43
questionary>=2.0.1
```

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Feedback loop não melhora prompts | Médio | Alto | Algoritmos simples inicialmente, iteração rápida |
| Usuários não fornecem feedback | Alto | Médio | Tornar feedback rápido e fácil, incentivar com melhorias visíveis |
| Custo explode sem controle | Baixo | Crítico | Limites rigorosos, autorização obrigatória |
| CLI complexa demais | Médio | Médio | Testes de UX, simplificação iterativa |
| Prompts refinados pioram | Baixo | Alto | Versionamento, rollback fácil, validação A/B |

---

## 📚 Próximos Passos Imediatos

### Para Desenvolvedores

1. **FASE 1** - Análise Expandida (começar AGORA)
   - Criar `src/agent_v3/analysis/`
   - Implementar `enhanced_analyzer.py`
   - Expandir prompt template
   - Testar com 5 protocolos

2. **FASE 2** - Feedback Loop (paralelo com FASE 1)
   - Criar `src/agent_v3/feedback/`
   - Implementar `feedback_collector.py`
   - Projetar formato de feedback

3. **FASE 3** - Controle de Custos (após FASE 1)
   - Criar `src/agent_v3/cost_control/`
   - Implementar `cost_estimator.py`
   - Testar precisão de estimativas

4. **FASE 4** - CLI Interativa (após FASES 1-3)
   - Criar `src/agent_v3/cli/`
   - Implementar `interactive_cli.py`
   - Testes de UX

### Para Stakeholders

1. Revisar este planejamento
2. Aprovar priorização de fases
3. Definir limites de custo aceitáveis
4. Preparar protocolos para testes

---

## ✅ Checklist de Aprovação

Antes de começar a implementação, validar:

- [ ] Arquitetura revisada e aprovada
- [ ] Priorização de fases acordada
- [ ] Requisitos de UX claros
- [ ] Limites de custo definidos
- [ ] Formato de feedback aprovado
- [ ] Estratégia de fine-tuning validada
- [ ] Stakeholders alinhados

---

**Status**: 📋 Aguardando aprovação para início da implementação
**Próximo Marco**: FASE 1 - Enhanced Analyzer (4-6 dias)
**Data de Revisão**: 2025-12-01
