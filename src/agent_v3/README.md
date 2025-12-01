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
    model: str = "anthropic/claude-sonnet-4.5",
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

### ✅ Setup (DIA 1)
- [x] Estrutura de pastas criada
- [x] Pacotes Python configurados
- [ ] Validação crítica de auto-apply (GO/NO-GO)

### ⏳ Fase 4: JSONCompactor (DIAS 2-4)
- [ ] Implementar `json_compactor/compactor.py`
- [ ] Implementar `chunking/smart_chunker.py` (se necessário)
- [ ] Testar com 10+ protocolos reais

### ⏳ Fase 5: Auto-Apply Engine (DIAS 5-7)
- [ ] Implementar `applicator/improvement_applicator.py`
- [ ] Implementar `validator/structural_validator.py`
- [ ] Implementar `scoring/confidence_scorer.py`
- [ ] Implementar `diff/diff_generator.py`

### ⏳ Fase 6: Prompt Caching (DIA 8)
- [ ] Integrar cache 100% em `llm_client.py`
- [ ] Implementar `monitoring/cache_monitor.py`

### ⏳ Fase 7: Impact Scoring (DIA 9)
- [ ] Implementar `scoring/impact_scorer.py`
- [ ] Ajustar prompts para incluir scores

### ⏳ Integração (DIA 10)
- [ ] Implementar `pipeline.py` completo
- [ ] CLI para v3

### ⏳ Testes (DIAS 11-13)
- [ ] Testar com 20+ protocolos reais
- [ ] Edge cases
- [ ] Correções e refinamento

### ⏳ Apresentação (DIA 14)
- [ ] Demo ao vivo
- [ ] Métricas de sucesso
- [ ] Decisão de deployment

---

## 🎯 Métricas de Sucesso MVP

**Obrigatórias**:
- ✅ Taxa de auto-apply bem-sucedida >80%
- ✅ Suporta protocolos JSON >3k linhas
- ✅ Prompt caching >70%
- ✅ Tempo: dias → <10 minutos
- ✅ Zero JSON quebrado salvo

**Desejáveis**:
- 🎯 Sugestões com impact scores
- 🎯 Diff visual legível
- 🎯 Logs de auditoria

---

## 📚 Recursos

- **Documentação principal**: `../../README.md`
- **Roadmap completo**: `../../roadmap.md`
- **Histórico**: `../../dev_history.md`
- **Script de validação**: `../../validate_auto_apply.py`
