# Agent V3 - Correção Automatizada

**Versão**: 3.0.0-alpha
**Status**: 🚧 Em Desenvolvimento (MVP 2 semanas)

---

## 🎯 Visão Geral

Transformação de **auditoria passiva** (v2) para **correção ativa** (v3):
- V2 identifica problemas → V3 resolve automaticamente
- Tempo de implementação: dias → minutos (-90%)
- Custo de tokens: -50-70% (cache agressivo)
- Suporte a protocolos JSON ilimitados

---

## 📁 Estrutura de Módulos

### Core Modules

#### `pipeline.py`
Orquestrador principal do Agent V3. Integra v2 (análise) + v3 (correção).

**Função principal**:
```python
analyze_and_fix(
    protocol_path: str,
    playbook_path: str,
    model: str = "x-ai/grok-4.1-fast:free",
    auto_apply: bool = True,
    confidence_threshold: float = 0.90
) -> dict
```

#### `json_compactor/`
**Fase 4**: Compactação de Protocolos JSON

Reduz protocolos grandes (3k-5k linhas) ao essencial clínico.
- Remove redundâncias e metadados desnecessários
- Preserva estrutura clínica, fluxos, lógica de decisão
- Permite reconstrução completa posterior

**Módulos**:
- `compactor.py` - Compactação e reconstrução
- `analyzer.py` - Análise de redundâncias

#### `chunking/`
**Fase 4** (se necessário): Smart Chunking

Divide protocolos muito grandes em chunks semânticos.
- Processa incrementalmente
- Mantém contexto entre chunks (MemoryManager)
- Reconstrói protocolo completo no final

**Módulos**:
- `smart_chunker.py` - Divisão em chunks lógicos
- `memory_manager.py` - Contexto entre chunks

#### `applicator/`
**Fase 5**: Auto-Apply de Melhorias

Core engine de aplicação automática de correções.
- Recebe sugestões da v2 + protocolo original
- Gera protocolo corrigido via LLM (Sonnet 4.5)
- Mantém rastreabilidade completa

**Módulos**:
- `improvement_applicator.py` - Motor principal de aplicação
- `llm_client.py` - Cliente LLM especializado para auto-apply

#### `validator/`
**Fase 5**: Validação Estrutural

Garante que protocolo corrigido é válido e não quebrou.
- Validação de sintaxe JSON
- Validação de schema (estrutura preservada)
- Validação de integridade de dados

**Módulos**:
- `structural_validator.py` - Validações obrigatórias
- `schema_validator.py` - Validação de schema

#### `scoring/`
**Fase 5 & 7**: Confidence e Impact Scoring

Atribui scores de confiança e impacto para cada mudança.
- Confidence: 0-100% (quão segura é a mudança)
- Impact: Segurança (0-10), Economia (L/M/A), Esforço (L/M/A)

**Módulos**:
- `confidence_scorer.py` - Score de confiança
- `impact_scorer.py` - Score de impacto

#### `diff/`
**Fase 5**: Geração de Diff

Mostra exatamente o que mudou no protocolo.
- Formato legível (antes/depois)
- Rastreabilidade clínica completa
- Justificativa por mudança

**Módulos**:
- `diff_generator.py` - Geração de diff estruturado
- `formatter.py` - Formatação legível

#### `monitoring/`
**Fase 6**: Monitoramento de Performance

Rastreia métricas de custo, cache, e eficiência.
- Cache hit/miss rate
- Economia de tokens
- Alertas de anomalias

**Módulos**:
- `cache_monitor.py` - Monitoramento de cache
- `cost_tracker.py` - Rastreamento de custos

#### `output/`
Formatação de saída e relatórios v3.
- Protocolo corrigido (JSON)
- Diff de mudanças
- Relatórios de impacto

---

## 🚀 Roadmap de Implementação

### ✅ Setup e Validação (DIA 1) - COMPLETO
- [x] Estrutura de pastas criada
- [x] Pacotes Python configurados
- [x] **Validação crítica de auto-apply (GO/NO-GO)** ✅
  - Taxa de sucesso: 100% (3/3 protocolos)
  - Custo: $0.0029-$0.012 por protocolo
  - Decisão: **GO - PROSSEGUIR COM IMPLEMENTAÇÃO**

### 🔄 FASE 1: ImprovementApplicator (PRÓXIMO - 3-5 dias)
- [ ] Implementar `applicator/improvement_applicator.py`
- [ ] Implementar `applicator/llm_client.py`
- [ ] Cost estimation integrado
- [ ] Version management (MAJOR.MINOR.PATCH)
- [ ] Output filename generation
- [ ] Testes unitários completos

### ⏳ FASE 2: StructuralValidator (2-3 dias)
- [ ] Implementar `validator/structural_validator.py`
- [ ] Implementar `validator/schema_validator.py`
- [ ] Validações obrigatórias (JSON, schema, integrity)
- [ ] Testes unitários

### ⏳ FASE 3: Pipeline Integration (3-5 dias)
- [ ] Implementar `pipeline.py` completo
- [ ] Integração V2 → V3
- [ ] Flags de controle (auto_apply, confidence_threshold)
- [ ] Output unificado
- [ ] Testes de integração

### ⏳ FASE 4: DiffGenerator (2-3 dias)
- [ ] Implementar `diff/diff_generator.py`
- [ ] Structural diff + field-level diff
- [ ] Rastreabilidade completa
- [ ] Formatter legível

### ⏳ FASE 5: Confidence Scoring (3-4 dias)
- [ ] Implementar `scoring/confidence_scorer.py`
- [ ] Heurísticas MVP (alta/média/baixa confiança)
- [ ] Integração com pipeline
- [ ] Decisões automáticas baseadas em threshold

### ⏳ FASE 6: CLI Unificado (1-2 dias)
- [ ] Atualizar CLI para V2+V3
- [ ] Modo de operação configurável
- [ ] Preview de mudanças
- [ ] Estimativa de custo pré-execução

### ⏳ FASE 7: Testes Intensivos (2-3 dias)
- [ ] Testar com 15-20 protocolos reais
- [ ] Múltiplas especialidades
- [ ] Edge cases e correções
- [ ] Validação de métricas

### ⏳ FASE 8: Production Deploy (1 dia)
- [ ] Documentação atualizada
- [ ] Deploy em produção
- [ ] Monitoramento inicial
- [ ] Coleta de feedback

**📋 Plano Detalhado**: Ver `../../V3_IMPLEMENTATION_PLAN.md`

---

## 🎯 Métricas de Sucesso MVP

**Validação Crítica (DIA 1)** - ✅ COMPLETO:
- ✅ Taxa de auto-apply bem-sucedida: **100%** (target: >80%)
- ✅ Custo por protocolo: **$0.0029-$0.012** (viável em escala)
- ✅ Tempo de correção: **Segundos** (vs dias manualmente)
- ✅ JSON válido: **100%**
- ✅ Estrutura preservada: **100%**

**Obrigatórias para MVP Completo**:
- ✅ Taxa de auto-apply bem-sucedida >95%
- ✅ Suporta protocolos JSON ilimitados
- ✅ Tempo: dias → <10 minutos
- ✅ Zero JSON quebrado salvo
- ✅ Rastreabilidade completa (diff + versionamento)

**Desejáveis**:
- 🎯 Custo médio <$0.02 por protocolo
- 🎯 Confidence scoring funcional
- 🎯 Diff visual legível
- 🎯 Logs de auditoria

---

## 📚 Recursos

- **Documentação principal**: `../../README.md`
- **Roadmap completo**: `../../roadmap.md`
- **Histórico**: `../../dev_history.md`
- **Plano de Implementação V3**: `../../V3_IMPLEMENTATION_PLAN.md` 🆕
- **Script de validação**: `../../test_v3_auto_apply.py` (DIA 1 - completo)
- **Script legacy**: `../../validate_auto_apply.py` (deprecated)
