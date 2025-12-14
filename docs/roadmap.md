# 🗺️ Roadmap - Agente Daktus | QA

**Última Atualização**: 2025-12-13  
**Versão Atual**: 3.1.0  
**Fase Atual**: Produto Técnico Autônomo (✅ COMPLETA)  
**Próxima Fase**: Integração ao Ecossistema Daktus

---

## 🎯 Visão do Produto

**Missão**: Validação e correção automatizadas de protocolos clínicos contra playbooks baseados em evidências.

**Transformação Alcançada**: De **auditoria passiva** (identifica problemas) para **correção ativa** (resolve automaticamente).

**Próxima Evolução**: De **ferramenta standalone** para **componente integrado** do ecossistema Daktus.

---

## 📊 Métricas de Sucesso

### Métricas Atuais (Produto Standalone)

| Métrica | Baseline | Atual | Melhoria |
|---------|----------|-------|----------|
| Sugestões por análise | 5-15 | 20-50 | **+230%** |
| Verificabilidade playbook | 50-60% | 95%+ | **+58%** |
| Feedback respeitado | 0% | 100% | **∞** |
| Pattern activation | 3 ocorrências | 1 ocorrência | **-66%** |
| Max protocolo reconstruível | ~50KB | 180KB+ | **+260%** |
| Crashes em produção | Frequentes | Zero | **-100%** |
| UI consistency | 40% Rich | 100% Rich | **+150%** |

### Métricas Futuras (Pós-Integração)

**A definir em conjunto com stakeholders:**

| Métrica | Baseline | Meta | Status |
|---------|----------|------|--------|
| Adoção (% usuários Studio) | 0% | TBD | PLANEJAMENTO |
| Tempo de validação | Manual | TBD | PLANEJAMENTO |
| Qualidade de protocolos | TBD | TBD | PLANEJAMENTO |
| NPS da feature | N/A | >70 | PLANEJAMENTO |

---

## 🏗️ ARQUITETURA DE FASES

### FASES 1-4: Produto Técnico Autônomo ✅ COMPLETA

**Período**: Nov 2025 - Dez 2025  
**Objetivo Alcançado**: 
- Agente standalone production-ready
- CLI robusta com análise + correção automatizada
- Sistema de aprendizado contínuo funcionando
- Zero bugs conhecidos em produção

---

#### Wave 1: Clinical Safety Foundations ✅

**Status**: 100% Implementada (Nov 2025)  
**Objetivo**: Garantir zero protocolos inválidos através de validação rigorosa.

**Implementado**:
- ✅ **Pydantic Schema Validation** - Estrutura de protocolo validada em tempo de reconstrução
- ✅ **AST-Based Logic Validation** - Validação segura de expressões condicionais (sem regex frágil)
- ✅ **LLM Contract Validation** - Detecção de model drift com schemas Pydantic
- ✅ **Cross-Reference Validation** - Valida UIDs, edges, conditional logic
- ✅ **Zero Invalid Protocols** - 100% dos protocolos inválidos bloqueados antes de salvar

**Arquivos Criados**:
- `src/agent/validators/protocol_validator.py` - Validação de schema
- `src/agent/validators/logic_validator.py` - Validação de lógica condicional
- `src/agent/validators/llm_contract.py` - Schemas Pydantic para LLM

**Localização**: `src/agent/validators/`

**Impacto**:
- **Safety**: Zero protocolos quebrados em produção
- **Reliability**: Validação automática em 3 camadas
- **Maintainability**: Código type-safe e testável

---

#### Wave 2: Memory & Learning ✅

**Status**: 100% Implementada (Dez 2025)  
**Objetivo**: Aprendizado contínuo com feedback do usuário.

**Implementado**:
- ✅ **Hard Rules Engine** - Bloqueio automático de sugestões inválidas
- ✅ **Reference Validator** - Verificação rigorosa de evidências do playbook
- ✅ **Change Verifier** - Validação pós-reconstrução de mudanças aplicadas
- ✅ **Feedback Learner** - Aprendizado automático com padrões de rejeição
- ✅ **Spider/Daktus Knowledge** - Regras específicas para protocolos clínicos

**Bugs Críticos Corrigidos**:
1. ✅ Reconstruction Display (N/A values)
2. ✅ Threshold=1 (ativação imediata de padrões)
3. ✅ Filtros sempre no prompt
4. ✅ Pattern-based filtering semântico
5. ✅ Uso de relatórios EDITED
6. ✅ Feedback UX simplificado (3 opções: S/N/Q)

**Arquivos Criados**:
- `src/agent/learning/rules_engine.py` - Motor de regras
- `src/agent/learning/feedback_learner.py` - Sistema de aprendizado
- `src/agent/validators/reference_validator.py` - Validador de referências
- `src/agent/applicator/change_verifier.py` - Verificador de mudanças

**Localização**: `src/agent/learning/`, `src/agent/validators/`

**Impacto**:
- **Quality**: 95%+ sugestões baseadas em evidências
- **Learning**: Feedback automático gera novas regras (threshold=1)
- **Reliability**: Mudanças verificadas após reconstrução

---

#### Wave 3: Observability & Cost Control ✅

**Status**: 100% Implementada (Dez 2025)  
**Objetivo**: Rastreamento de custos reais e audit trail para compliance.

**Implementado**:
- ✅ **Real-Time Cost Tracking** - Token counter ao vivo: `📢 Tokens: 71,098 (4 calls) | 💵 $0.0708`
- ✅ **Accurate Cost Reporting** - Custos reais vs estimados, resumo por sessão
- ✅ **Reconstruction Auditing** - Relatórios `_AUDIT.txt` detalhados
- ✅ **Implementation Path** - Sugestões com `json_path`, `modification_type`, `proposed_value`
- ✅ **Studio-Aware Reconstruction** - LLM entende estrutura de protocolos Daktus
- ✅ **UI Polish** - Caminhos clicáveis, progresso de chamadas

**Arquivos Criados**:
- `src/agent/cost_control/cost_tracker.py` - Rastreamento de custos
- `src/agent/cost_control/cost_estimator.py` - Estimativas precisas
- `src/agent/applicator/audit_reporter.py` - Relatórios de auditoria

**Localização**: `src/agent/cost_control/`, `src/agent/applicator/`

**Impacto**:
- **Visibility**: Custos reais visíveis em tempo real
- **Compliance**: Audit trail completo de mudanças
- **Implementation**: Sugestões prontas para aplicação direta

---

#### Wave 4.1: Agent Intelligence ✅

**Status**: 100% Implementada (Dez 2025)  
**Objetivo**: Reduzir taxa de rejeição de alertas genéricos de 71.4% para <30%.

**Problema Resolvido**:
- Antipadrão #1: Alertas genéricos sem especificação ("adicionar alerta visual")
- 71.4% das rejeições eram por sugestões mal estruturadas

**Implementado**:
- ✅ **Alert Rules Module** - Regras de implementação de alertas com templates
- ✅ **Suggestion Validator** - Filtragem de antipadrões e duplicatas
- ✅ **Protocol Analyzer** - Ferramentas de análise estrutural
- ✅ **Good Alert Examples** - Exemplos para few-shot learning
- ✅ **Enhanced Prompt Rules** - Regras de alertas integradas no prompt

**Arquivos Criados**:
- `src/agent/analysis/alert_rules.py` - Regras e templates
- `src/agent/validators/suggestion_validator.py` - Validador
- `src/agent/core/protocol_analyzer.py` - Analisador
- `src/agent/analysis/examples/good_alert_examples.json` - Exemplos

**Localização**: `src/agent/analysis/`, `src/agent/validators/`

**Impacto**:
- **Quality**: >70% taxa de aceitação (vs 41.2% anterior)
- **Specificity**: 100% das sugestões com JSON pronto
- **Duplicates**: <5% de duplicatas

---

#### Wave 4.2: Bug Fixes & Polish ✅

**Status**: 100% Implementada (Dez 2025)  
**Objetivo**: Estabilidade em produção, robustez contra edge cases, UI/UX profissional.

**Problemas Resolvidos**:
- 7 bugs críticos bloqueando análise/reconstrução
- UI inconsistente (mix de print() e Rich Panels)
- LLM gerando IDs incorretos na reconstrução
- Erros transientes sem retry

**Implementado**:
- ✅ **Template String Escaping** - Fix erro `' node_id, field, path '` em prompts
- ✅ **NoneType Handling** - Tratamento robusto de None em questions/options
- ✅ **JSON Parsing Robusto** - Estratégia para escaped single quotes (`\'`)
- ✅ **Transient Error Retry** - Retry automático para "Response ended prematurely"
- ✅ **UI Consistency** - Rich Panels amarelos/verdes em todas estimativas de custo
- ✅ **Node ID Preservation** - Prompt reforçado para LLM preservar IDs exatos
- ✅ **ImpactScores Robustness** - Uso de ImpactScorer.calculate_impact_scores()

**Arquivos Modificados**:
- `src/agent/analysis/enhanced.py`
- `src/agent/validators/logic_validator.py`
- `src/agent/core/llm_client.py`
- `src/agent/applicator/protocol_reconstructor.py`
- `src/agent/cost_control/cost_tracker.py`
- `src/agent/cost_control/authorization_manager.py`
- `src/agent/cli/interactive_cli.py`

**Impacto Real**:
- **Stability**: Zero crashes conhecidos em análise e reconstrução
- **UX**: UI profissional e consistente (100% Rich Panels)
- **Robustness**: Erros transientes recuperáveis (3 retries com backoff)
- **Scalability**: Protocolos grandes (145+ KB) analisam com sucesso

---

### FASE 5: Integração ao Ecossistema Daktus ⏳ INICIANDO

**Contexto**: 

O agente alcançou maturidade técnica como produto standalone. O próximo passo natural é integração ao fluxo principal de trabalho dos usuários no Daktus Studio.

**Estratégia**: 

Progressão colaborativa **Dan Solo → Dan + TI → TI-led**, respeitando expertise de cada área e criando checkpoints de validação entre fases.

**Objetivo**: 

Transformar o agente de ferramenta pontual em componente integrado do ecossistema Daktus, permitindo validação de protocolos sem sair do fluxo de edição.

**Documento de Referência**: 

Ver [`integration.md`](integration.md) para visão completa, decisões técnicas pendentes e divisão detalhada de responsabilidades.

---

#### Wave 5.1: Stabilization & Trust (DAN SOLO) 🟢

**Responsável**: Dan  
**Validação**: Time TI (contratos de API, viabilidade técnica)  
**Status**: PLANEJAMENTO

**Objetivo**: 

Preparar agente para ser invocado externamente de forma confiável, estabelecendo contratos estáveis e cobertura de testes adequada.

**Escopo**:
- [ ] **API Contracts**: Schemas Pydantic/OpenAPI documentando inputs/outputs
- [ ] **Test Coverage**: Unit, integration e e2e tests (>80% coverage)
- [ ] **API Stability**: Congelamento de breaking changes
- [ ] **Error Handling**: Respostas padronizadas para todos os cenários
- [ ] **Logging**: Estruturado (JSON) para observabilidade
- [ ] **Documentation**: Guia de integração técnica completo

**Deliverables**:
- Contract specification (a validar com Time TI)
- Test suite abrangente
- Integration guide (draft para discussão)
- Error catalog documentado

**Não-Escopo**:
- ❌ UI web (Wave 5.3, TI-led)
- ❌ Refatorações arquiteturais grandes
- ❌ Features novas no core do agente
- ❌ Mudanças no modelo de dados

**Checkpoints de Validação**:
1. Contratos de API aprovados por Guilherme/Time TI
2. Test coverage mínimo atingido e validado
3. Documentação revisada e aprovada
4. Demonstração de estabilidade (zero breaking changes por período definido)

**Critério de "Integration-Ready"**:
- [ ] API contracts estáveis e documentados
- [ ] Test coverage >80%
- [ ] Error handling robusto testado
- [ ] Logging estruturado implementado
- [ ] Zero breaking changes por período definido
- [ ] Aprovação do Time TI para prosseguir

---

#### Wave 5.2: Integration Readiness (DAN + TI) 🟡

**Responsável**: Dan + Guilherme/Time TI (colaborativo)  
**Status**: PLANEJAMENTO

**Objetivo**: 

Estabelecer comunicação bidirecional entre Daktus Studio e Agente QA, validando arquitetura de integração em ambiente controlado.

**Responsabilidades Compartilhadas**:

**Dan**:
- Implementar API server no agente (endpoints, serialização)
- Criar error handling específico para chamadas externas
- Implementar logging estruturado (JSON)
- Fornecer exemplos de uso e casos extremos
- Documentar outputs e comportamentos esperados

**Time TI**:
- Validar viabilidade arquitetural das propostas
- Implementar client no Daktus Studio backend
- Definir estratégias de deployment
- Estabelecer padrões de retry, timeout, circuit breaker
- Configurar infraestrutura necessária

**Ambos (em conjunto)**:
- Testes de integração end-to-end
- Troubleshooting de issues
- Definição de SLAs de latência
- Documentação de arquitetura
- Retrospectivas de aprendizado

**Deliverables**:
- Daktus Studio → Agente QA funcionando (ambiente dev/staging)
- Error handling validado em cenários reais
- Testes de integração passando
- Métricas de latência e success rate coletadas
- Documentação de deployment

**Decisões Técnicas Pendentes** (a definir em conjunto):
- **Protocolo de comunicação**: REST vs gRPC vs Message Queue
- **Deployment model**: Container separado vs mesma instância vs serverless
- **Retry strategy**: Client-side vs Server-side vs ambos
- **Timeout values**: Baseado em tamanho médio de protocolos
- **Observability**: Métricas a coletar, alertas a configurar

**Checkpoints de Alinhamento**:
- Syncs regulares (frequência a definir)
- Code reviews cruzados
- Sessões de pair programming quando necessário
- Decisões arquiteturais documentadas

**Critério de Sucesso**:
- [ ] Daktus Studio invoca agente com sucesso
- [ ] Error handling testado (happy path + edge cases)
- [ ] Latência dentro de limites aceitáveis (a definir)
- [ ] Success rate >99%
- [ ] Documentação de troubleshooting completa

---

#### Wave 5.3: Studio Integration (TI-LED) 🔴

**Responsável**: Guilherme/Time TI  
**Suporte**: Dan (consultoria técnica)  
**Status**: PLANEJAMENTO

**Objetivo**: 

Feature "Validar com IA" disponível para usuários finais no Daktus Studio, integrada ao fluxo de edição de protocolos.

**Escopo (Time TI executa)**:
- [ ] Design de UX/UI da feature no Studio
- [ ] Implementação de trigger (botão, menu, atalho)
- [ ] Preview de sugestões na interface de edição
- [ ] Aplicação de mudanças no protocolo (com confirmação)
- [ ] Integração com sistema de versionamento do Studio
- [ ] Deploy em ambiente de produção
- [ ] Documentação de usuário (como usar a feature)
- [ ] Monitoramento de métricas de uso e performance

**Papel do Dan (Suporte)**:
- Consultoria técnica sobre outputs do agente
- Validação de qualidade clínica das sugestões
- Suporte a bugs relacionados ao agente
- Ajustes no agente baseados em feedback de produção
- Treinamento do time TI sobre funcionamento interno

**Deliverables**:
- Feature live em produção
- Documentação de usuário publicada
- Dashboard de métricas ativo
- Runbook de troubleshooting
- Plano de rollback (se necessário)

**Critério de Sucesso**:
- [ ] Feature acessível para usuários do Studio
- [ ] Métricas de adoção sendo coletadas
- [ ] NPS da feature positivo (meta: >70)
- [ ] Zero critical bugs por período definido
- [ ] Latência percebida pelo usuário aceitável
- [ ] Documentação de suporte disponível

**Métricas de Adoção (a monitorar)**:
- % de usuários que experimentam a feature
- % de usuários que voltam a usar
- Número de análises realizadas por semana/mês
- Taxa de aceitação de sugestões
- Feedback qualitativo via NPS/entrevistas

---

## 🌐 EXPANSÃO FUTURA: MedFlow

### Contexto

MedFlow (produto irmão do Daktus) possui fluxos similares de validação de protocolos clínicos. A integração do agente QA ao Daktus Studio pode servir como **piloto** para expansão futura.

### Estratégia de Sinergia

**Aprendizados Compartilhados**:
- Arquitetura de integração testada no Daktus pode ser replicada no MedFlow
- Erros e acertos documentados beneficiam ambos os produtos
- Sistema de aprendizado do agente pode ser alimentado por ambos os produtos
- Base de regras/padrões compartilhada entre ecossistemas

**Faseamento**:
1. **Fase Atual**: Validar modelo de integração no Daktus Studio
2. **Fase Futura**: Replicar padrão bem-sucedido no MedFlow
3. **Benefício Mútuo**: Agente aprende com feedback de ambos os produtos

### Não-Escopo Atual

Esta integração com MedFlow **não está no escopo das Waves 5.1-5.3**. É uma oportunidade futura a ser explorada após validação bem-sucedida da integração no Daktus Studio.

**Gatilho para reavaliação**: Sucesso comprovado da integração no Daktus Studio (métricas de adoção, NPS, estabilidade).

---

## ⏭️ FASES FUTURAS (Pós-Integração)

### FASE 6: Performance & Scale

**Contexto**: Após integração bem-sucedida, otimizar para volume e custo.

**Objetivo**: Reduzir latência e custo operacional mantendo qualidade.

---

#### Wave 6.1: Performance Optimization

**Prioridade**: MÉDIA (após Wave 5.3)  
**Status**: BACKLOG

**Escopo**:
- Lazy loading de protocolos grandes
- Paralelização de validações
- Cache de embeddings persistente
- Otimização de prompts (redução de tokens)

**Impacto Esperado**:
- -40% tempo de análise
- -30% custo por análise
- Suporta protocolos >500KB

---

#### Wave 6.2: Cost Optimization

**Prioridade**: MÉDIA  
**Status**: BACKLOG

**Escopo**:
- Prompt caching (OpenRouter/Anthropic)
- Estratégias de fallback para modelos mais baratos
- Batch processing de análises
- Cost circuit breaker (limites de orçamento)

**Impacto Esperado**:
- -50% custo em cenários de uso intenso
- Maior previsibilidade de custos

---

### FASE 7: Advanced Features

**Contexto**: Features que ampliam capacidades além de validação básica.

**Objetivo**: Tornar agente ainda mais valioso para diferentes use cases.

---

#### Wave 7.1: Batch Processing

**Prioridade**: BAIXA  
**Status**: BACKLOG

**Escopo**:
- Análise de múltiplos protocolos simultaneamente
- Relatórios comparativos entre protocolos
- Identificação de padrões entre protocolos
- Dashboard de qualidade da base

---

#### Wave 7.2: REST API Pública

**Prioridade**: BAIXA  
**Status**: BACKLOG

**Escopo**:
- API externa para integrações third-party
- Autenticação via API keys
- Rate limiting e quotas
- Documentação OpenAPI completa

---

#### Wave 7.3: Web Dashboard

**Prioridade**: BAIXA  
**Status**: BACKLOG

**Escopo**:
- Interface web standalone (Streamlit/Flask)
- Visualização de histórico de análises
- Métricas de qualidade e aprendizado
- Gestão de feedback e regras

---

### FASE 8: Data & Analytics (Condicional)

**Contexto**: SQLite híbrido para analytics avançados.

**Status**: ADIADO (decisão de 2025-12-11)

**Justificativa do Adiamento**:
- ✅ Sistema production-ready com arquitetura de arquivos atual
- ✅ `memory_qa.md` gerenciável (225KB < 500KB limite)
- ✅ Sistema de aprendizado funcionando bem
- ❌ Sem urgência de analytics/dashboard no momento

**Gatilhos para Reavaliar**:
1. `memory_qa.md` > 500KB (degradação de performance)
2. Necessidade de dashboard/analytics de negócio
3. Volume > 50 análises/mês de forma consistente
4. ROI analytics requerido por stakeholders

**Referência**: `DATA_ARCHITECTURE_PROPOSAL.md` (se decisão mudar no futuro)

---

## 🎯 Próximos Passos Imediatos

### Esta Semana
1. [ ] Validar `integration.md` com Gabriel, Miguel, Guilherme
2. [ ] Coletar feedback sobre visão de integração
3. [ ] Ajustar proposta baseado em input do time

### Próximas 2 Semanas
1. [ ] Kickoff técnico (Dan + Guilherme + Time TI)
2. [ ] Definir decisões arquiteturais pendentes
3. [ ] Detalhar Wave 5.1 em tasks específicas

### Próximo Mês
1. [ ] Executar Wave 5.1 (Stabilization & Trust)
2. [ ] Validar contratos de API com Time TI
3. [ ] Preparar ambiente para Wave 5.2

---

## 📚 Referências

| Documento | Descrição |
|-----------|-----------|
| [`README.md`](../README.md) | Visão geral do produto, quick start |
| [`dev_history.md`](dev_history.md) | Histórico de desenvolvimento, changelog |
| [`integration.md`](integration.md) | **NOVO** - Vision doc para integração ao Daktus Studio |
| [`../memory_qa.md`](../memory_qa.md) | Memória de aprendizado do agente |

---

## 🔄 Histórico de Revisões

| Data | Versão | Mudanças |
|------|--------|----------|
| 2025-12-13 | 2.0 | Adicionada Fase 5 (Integração), criado integration.md, refatoração completa |
| 2025-12-11 | 1.2 | Decisão de adiar Wave 7 (Data Architecture) |
| 2025-12-07 | 1.1 | Wave 4.2 completa (Bug Fixes & Polish) |
| 2025-11-25 | 1.0 | Versão inicial do roadmap |

---

**Próxima Revisão**: Após validação da Fase 5 com stakeholders

**Feedback**: Este é um documento vivo. Contribuições e ajustes são bem-vindos via discussão com o time.
