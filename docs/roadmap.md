# 🗺️ Roadmap - Agente Daktus | QA

**Última Atualização**: 2025-12-01  
**Status Atual**: ✅ Projeto Unificado | 🔥 V3 Sprint em Desenvolvimento

---

## 🎯 Visão do Produto

**Missão**: Validação e correção automatizadas de protocolos clínicos contra playbooks baseados em evidências.

**Evolução**:
- **Modo Standard (Anterior V2)**: Validação inteligente via LLM → ✅ **Produção**
- **Modo Enhanced (V3 Sprint)**: Correção automatizada de protocolos JSON → 🔥 **Transformacional**

**Transformação fundamental**: De **auditoria passiva** (identifica problemas) para **correção ativa** (resolve automaticamente).

> **Nota**: O projeto foi consolidado em um único repositório. O versionamento é feito via tags/branches Git, não via estrutura de pastas separadas.

---

## ✅ Status Atual - Modo Standard

### O Que Funciona
- ✅ Validação de protocolos JSON contra playbooks (MD/PDF)
- ✅ Análise de gaps clínicos e sugestões de melhoria (5-15 sugestões)
- ✅ Arquitetura LLM-first, agnóstica a especialidades
- ✅ Performance: 60s latência, R$ 0,25-0,50/análise, 95% sucesso
- ✅ Prompt caching funcional (reduz até 90% do custo)

### Limitações (Resolvidas no Modo Enhanced)
1. ⚠️ Análise limitada (5-15 sugestões)
2. ⚠️ Correção manual (dias/semanas de implementação)
3. ⚠️ Sem priorização por impacto real
4. ⚠️ Sem aprendizado contínuo
5. ⚠️ ROI difícil de quantificar

---

## 🔥 V3 Sprint - Modo Enhanced (Em Desenvolvimento)

### Ganhos Esperados

| Métrica | Standard | Enhanced | Ganho |
|---------|----------|----------|-------|
| **Sugestões por análise** | 5-15 | 20-50 | **+233%** |
| **Tempo de implementação** | Dias | Minutos | **-90%** |
| **Precisão de sugestões** | ~80% | 90%+ (após feedback) | **+10pp** |
| **ROI** | Subjetivo | Quantificado (scores) | **Mensurável** |
| **Aprendizado contínuo** | Não | Sim (feedback loop) | **∞** |

---

## 🚀 Fases de Desenvolvimento V3 Sprint

### ✅ FASE 1: Sistema de Análise Expandida (COMPLETA)

**Duração**: 4-6 dias  
**Status**: ✅ **COMPLETA E FUNCIONAL**

**Entregas**:
- ✅ `src/agent/analysis/enhanced.py` - Enhanced Analyzer
- ✅ `src/agent/analysis/impact_scorer.py` - Impact Scoring
- ✅ Prompt template expandido para 20-50 sugestões
- ✅ Testes com protocolos reais validados

**Critérios de Sucesso**:
- ✅ Gerar 20-50 sugestões (vs 5-15 do Standard) - **ATENDIDO**
- ✅ Cada sugestão com scores de impacto - **ATENDIDO**
- ✅ Rastreabilidade completa (sugestão → evidência) - **ATENDIDO**
- ✅ Estimativa de custo por sugestão - **ATENDIDO**

**Dependências**: Nenhuma

---

### ✅ FASE 2: Sistema de Feedback e Fine-Tuning (COMPLETA)

**Duração**: 5-7 dias  
**Status**: ✅ **COMPLETA E FUNCIONAL**

**Entregas**:
- ✅ `src/agent/feedback/feedback_collector.py` - Coleta interativa de feedback
- ✅ `src/agent/feedback/prompt_refiner.py` - Refinamento automático de prompts
- ✅ `src/agent/feedback/feedback_storage.py` - Persistência de feedback
- ✅ Sistema de versionamento de prompts
- ✅ Interface CLI para feedback integrada

**Critérios de Sucesso**:
- ✅ Captura de feedback estruturado - **ATENDIDO**
- ✅ Identificação automática de padrões de erro - **ATENDIDO**
- ✅ Ajuste automático de prompts - **ATENDIDO**
- ✅ Rastreabilidade de mudanças em prompts - **ATENDIDO**
- ⏳ Melhoria mensurável após 3-5 sessões - **EM VALIDAÇÃO**

**Dependências**: FASE 1 ✅

---

### ✅ FASE 3: Sistema de Controle de Custos (COMPLETA)

**Duração**: 3-4 dias  
**Status**: ✅ **COMPLETA E FUNCIONAL**

**Entregas**:
- ✅ `src/agent/cost_control/cost_estimator.py` - Estimativa de custos
- ✅ `src/agent/cost_control/authorization_manager.py` - Autorização (removida, apenas informativa)
- ⚠️ `src/agent/cost_control/cost_tracker.py` - Skeleton (não crítico para MVP)
- ✅ Configuração de modelos e preços atualizados
- ✅ Exibição informativa de custos (sem autorização obrigatória)

**Critérios de Sucesso**:
- ✅ Estimativa de custo pré-execução com 90%+ precisão - **ATENDIDO**
- ✅ Exibição informativa de custos - **ATENDIDO**
- ⚠️ Rastreamento de custo real vs estimado - **Skeleton (não crítico)**
- ⚠️ Alertas de anomalias - **Não implementado (não crítico)**

**Dependências**: FASE 1 ✅

**Nota**: Sistema de autorização foi removido conforme requisito do usuário. Apenas exibição informativa de custos é mantida.

---

### ✅ FASE 4: Reconstrução de Protocolo (COMPLETA - MVP)

**Duração**: 3-5 dias  
**Status**: ✅ **COMPLETA E FUNCIONAL (MVP)**

**Entregas**:
- ✅ `src/agent/applicator/protocol_reconstructor.py` - Reconstrução via LLM
- ✅ `src/agent/applicator/version_utils.py` - Versionamento automático
- ✅ Integração com sistema de custos
- ✅ Validação estrutural básica
- ✅ Versionamento MAJOR.MINOR.PATCH
- ✅ Timestamp padronizado (DD-MM-YYYY-HHMM)

**Critérios de Sucesso**:
- ✅ Reconstrução funcional de protocolos - **ATENDIDO**
- ✅ Versionamento automático correto - **ATENDIDO**
- ✅ Validação estrutural básica - **ATENDIDO**
- ✅ Timestamp padronizado - **ATENDIDO**
- ⏳ Taxa de sucesso >95% - **EM VALIDAÇÃO**

**Dependências**: FASES 1, 3 ✅

---

### ⏳ FASE 5: CLI Interativa Avançada (PRIORIDADE ALTA)

**Duração**: 5-7 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] `src/agent/cli/interactive_cli.py` - CLI avançada
- [ ] `src/agent/cli/task_manager.py` - Gerenciamento de tarefas
- [ ] `src/agent/cli/display_manager.py` - Formatação rica
- [ ] Onboarding interativo
- [ ] Visualização de thinking e tasks
- [ ] Progress bars e spinners

**Critérios de Sucesso**:
- [ ] Onboarding claro e amigável (<3 minutos)
- [ ] Transparência total do processo (thinking visível)
- [ ] Tasks atualizadas em tempo real
- [ ] Feedback qualitativo: "melhor CLI que já usei"

**Dependências**: FASES 1, 2, 3 ✅

**Nota**: A CLI atual (`src/cli/run_qa_cli.py`) já suporta ambos os modos (Standard e Enhanced), mas pode ser melhorada com UX mais rica.

---

### ⏳ FASE 6: Motor de Auto-Apply Completo (PRIORIDADE MÉDIA)

**Duração**: 3-5 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] `src/agent/applicator/improvement_applicator.py` - Motor completo
- [ ] `src/agent/applicator/llm_client.py` - Cliente especializado
- [ ] Integração com sistema de autorização (se necessário)
- [ ] Rastreamento de custo real
- [ ] Rollback automático

**Critérios de Sucesso**:
- [ ] Taxa de sucesso >95%
- [ ] Custo real dentro de ±10% do estimado
- [ ] Rollback automático em caso de erro

**Dependências**: FASES 1, 3, 4 ✅

**Nota**: A FASE 4 já implementa reconstrução básica. Esta fase expandiria para auto-apply completo com rollback e validação avançada.

---

### ⏳ FASE 7: Sistema de Validação Avançada (PRIORIDADE MÉDIA)

**Duração**: 2-3 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] `src/agent/validator/structural_validator.py` - Validação estrutural avançada
- [ ] `src/agent/validator/schema_validator.py` - Validação de schema completo
- [ ] Testes automáticos de integridade

**Critérios de Sucesso**:
- [ ] Zero protocolos quebrados salvos
- [ ] Detecção de 100% dos erros estruturais

**Dependências**: FASE 6

---

### ⏳ FASE 8: Geração de Diff Visual (PRIORIDADE BAIXA)

**Duração**: 2-3 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] `src/agent/diff/diff_generator.py` - Geração de diff
- [ ] `src/agent/diff/formatter.py` - Formatação HTML/texto
- [ ] Visualização side-by-side

**Critérios de Sucesso**:
- [ ] Diff completo e legível
- [ ] Rastreabilidade 100%

**Dependências**: FASE 6

---

### ⏳ FASE 9: Pipeline Integration Completo

**Duração**: 3-5 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] `src/agent/pipeline.py` (completo)
- [ ] Integração de todos os módulos
- [ ] Fluxo end-to-end otimizado

**Critérios de Sucesso**:
- [ ] Pipeline completo funcional
- [ ] Fluxo end-to-end sem erros
- [ ] Feedback loop operacional

**Dependências**: FASES 1-8

---

### ⏳ FASE 10: Testes Intensivos

**Duração**: 3-4 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] Testes com 15-20 protocolos reais
- [ ] Validação de métricas
- [ ] Correção de bugs

**Critérios de Sucesso**:
- [ ] Taxa de sucesso >95%
- [ ] Feedback de usuários positivo
- [ ] Melhoria mensurável após feedback loop

**Dependências**: FASE 9

---

### ⏳ FASE 11: Production Deploy

**Duração**: 1-2 dias  
**Status**: ⏳ **PENDENTE**

**Entregas**:
- [ ] Documentação completa
- [ ] README atualizado
- [ ] Deploy em produção

**Critérios de Sucesso**:
- [ ] Sistema em produção
- [ ] Usuários usando
- [ ] Feedback positivo

**Dependências**: FASE 10

---

## 📊 Resumo do Status

### ✅ Completas (4 fases)
- **FASE 1**: Análise Expandida ✅
- **FASE 2**: Feedback Loop ✅
- **FASE 3**: Controle de Custos ✅
- **FASE 4**: Reconstrução de Protocolo (MVP) ✅

### ⏳ Pendentes (7 fases)
- **FASE 5**: CLI Interativa Avançada
- **FASE 6**: Motor de Auto-Apply Completo
- **FASE 7**: Sistema de Validação Avançada
- **FASE 8**: Geração de Diff Visual
- **FASE 9**: Pipeline Integration Completo
- **FASE 10**: Testes Intensivos
- **FASE 11**: Production Deploy

### 🎯 Próximos Passos Recomendados

1. **Validar FASES 1-4** com uso real
2. **Priorizar FASE 5** (CLI Avançada) para melhorar UX
3. **Expandir FASE 4** para FASE 6 (Auto-Apply Completo)
4. **Implementar FASE 7** (Validação Avançada) para garantir qualidade

---

## 🎯 Métricas de Sucesso do V3 Sprint

### Obrigatórias

**Qualidade de Relatórios**:
- ✅ 20-50 sugestões por análise (vs 5-15 atual) - **ATENDIDO**
- ✅ 100% das sugestões com rastreabilidade - **ATENDIDO**
- ⏳ 90%+ de sugestões relevantes (após fine-tuning) - **EM VALIDAÇÃO**

**Feedback Loop**:
- ✅ Sistema aprende com feedback - **ATENDIDO**
- ⏳ Melhoria mensurável após 3-5 sessões - **EM VALIDAÇÃO**
- ⏳ Taxa de sugestões irrelevantes reduz 50%+ - **EM VALIDAÇÃO**

**Controle de Custos**:
- ✅ Estimativa de custo com 90%+ precisão - **ATENDIDO**
- ✅ Exibição informativa de custos - **ATENDIDO**
- ⚠️ Custo médio <$0.02 por protocolo - **DEPENDE DO MODELO**

**UX**:
- ✅ CLI funcional para ambos os modos - **ATENDIDO**
- ⏳ Onboarding <3 minutos - **PENDENTE (FASE 5)**
- ⏳ Transparência total do processo - **PENDENTE (FASE 5)**

**Auto-Apply**:
- ✅ Reconstrução básica funcional - **ATENDIDO (FASE 4)**
- ⏳ Taxa de sucesso >95% - **EM VALIDAÇÃO**
- ⏳ Zero protocolos quebrados - **EM VALIDAÇÃO**
- ✅ Rastreabilidade completa - **ATENDIDO**

---

## 📚 Documentação Relacionada

- **Plano de Implementação Detalhado**: `docs/V3_IMPLEMENTATION_PLAN_REFINED.md`
- **Histórico de Desenvolvimento**: `docs/dev_history.md`
- **README Principal**: `README.md`

---

**Última Revisão**: 2025-12-01  
**Próxima Revisão**: Após validação das FASES 1-4 em produção
