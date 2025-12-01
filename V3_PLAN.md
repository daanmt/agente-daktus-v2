# 🚀 Plano de Execução V3 - MVP em 2 Semanas

**Data de Início**: 2025-12-01
**Data de Conclusão**: 2025-12-14
**Status**: 🔥 PRONTO PARA COMEÇAR

---

## 🎯 Objetivo do MVP

Transformar Agente Daktus QA de **auditoria passiva** (v2) para **correção ativa** (v3):
- Aplicar melhorias automaticamente no JSON do protocolo
- Suportar protocolos JSON massivos (3k-5k+ linhas)
- Reduzir tempo de implementação: dias → minutos (-90%)
- Reduzir custo de tokens em 50% via cache agressivo

---

## 📅 Cronograma Detalhado

### **DIA 1 (2025-12-01) - VALIDAÇÃO CRÍTICA** ⚡

**Objetivo**: Provar que auto-apply funciona antes de implementar

#### Tarefas
1. **Setup do Ambiente V3**
   - [ ] Criar branch `v3-mvp` no repo atual
   - [ ] Copiar estrutura v2 como base
   - [ ] Criar pasta `src/agent_v3/` vazia
   - [ ] Atualizar .gitignore se necessário

2. **Experimento Auto-Apply (CRÍTICO)**
   - [ ] Pegar 5 protocolos reais (variados em tamanho/especialidade)
   - [ ] Rodar v2 → gerar relatórios com sugestões
   - [ ] Criar script experimental: `validate_auto_apply.py`
   - [ ] Prompt para Sonnet 4.5: "Aplique estas sugestões no JSON"
   - [ ] Revisar manualmente cada resultado:
     - JSON válido? (testar com `json.loads()`)
     - Lógica clínica preservada?
     - Mudanças corretas aplicadas?
     - Rastreabilidade mantida?

3. **Métricas de Validação**
   - [ ] % de sucesso (meta: >80%)
   - [ ] Tipos de erro encontrados
   - [ ] Tempo economizado vs implementação manual
   - [ ] Custo de tokens por protocolo

**Decisão GO/NO-GO**:
- ✅ **Se >80% sucesso** → Implementar Fase 5 (ImprovementApplicator) nos dias 5-7
- ⚠️ **Se 60-80% sucesso** → Refinar prompt, iterar 1-2 vezes
- ❌ **Se <60% sucesso** → Reavaliar abordagem (talvez assistido, não automático)

**Entregável**: Relatório de validação em `reports/auto_apply_validation.md`

---

### **DIAS 2-4 (2025-12-02 a 04) - Compactação de Protocolos JSON** 🗜️

**Objetivo**: Resolver gargalo de protocolos grandes (>3k linhas)

#### DIA 2 - Análise e Design
- [ ] Analisar 10+ protocolos reais (medir linhas, tokens, estrutura)
- [ ] Identificar redundâncias: metadados desnecessários, campos duplicados
- [ ] Definir schema "essencial clínico" (o que DEVE manter)
- [ ] Projetar arquitetura JSONCompactor
- [ ] Documentar em `src/agent_v3/json_compactor/README.md`

#### DIA 3 - Implementação JSONCompactor
- [ ] Criar `src/agent_v3/json_compactor/compactor.py`
- [ ] Função: `compact_protocol(protocol_json) -> compacted_json`
- [ ] Remoção de metadados desnecessários
- [ ] Preservar: estrutura clínica, fluxos, variáveis, lógica de decisão
- [ ] Criar função reversa: `reconstruct_protocol(compacted, original) -> full_json`
- [ ] Unit tests: testar com 5 protocolos diferentes

#### DIA 4 - SmartChunking (se necessário)
- [ ] Avaliar: compactação resolve o problema?
- [ ] Se não resolver: implementar SmartChunking
  - [ ] Dividir JSON por seções lógicas (síndromes, fluxos)
  - [ ] Criar `src/agent_v3/chunking/smart_chunker.py`
  - [ ] Função: `chunk_protocol(protocol_json) -> chunks[]`
  - [ ] Função: `merge_chunks(chunks[], improvements[]) -> full_protocol`
- [ ] Testar com os 3 maiores protocolos (>3k linhas)

**Entregável**: JSONCompactor funcional, testado com 10+ protocolos

---

### **DIAS 5-7 (2025-12-05 a 07) - Auto-Apply Engine** 🔥

**Objetivo**: Implementar core engine de aplicação automática de melhorias

#### DIA 5 - ImprovementApplicator
- [ ] Criar `src/agent_v3/applicator/improvement_applicator.py`
- [ ] Função principal:
  ```python
  apply_improvements(
      protocol_json: dict,
      suggestions: list,
      model: str = "anthropic/claude-sonnet-4.5"
  ) -> dict:
      # Retorna: {
      #   "fixed_protocol": {...},
      #   "changes": [...],
      #   "confidence_scores": {...}
      # }
  ```
- [ ] Prompt engineering: instrução clara para Sonnet 4.5
  - Input: protocolo + sugestões
  - Output: protocolo corrigido + diff + justificativa por mudança
- [ ] Implementar chamada ao LLM com cache
- [ ] Testar com 3-5 protocolos reais

#### DIA 6 - StructuralValidator + ConfidenceScoring
- [ ] Criar `src/agent_v3/validator/structural_validator.py`
- [ ] Validações obrigatórias:
  - [ ] JSON válido (sintaxe)
  - [ ] Schema preservado (estrutura não quebrou)
  - [ ] Todas as chaves obrigatórias presentes
  - [ ] Tipos de dados corretos
- [ ] Criar `src/agent_v3/scoring/confidence_scorer.py`
- [ ] Implementar scoring básico:
  - Complexidade da mudança
  - Área do protocolo afetada (crítica vs não-crítica)
  - Clareza da sugestão original
  - Threshold: >90% = auto-apply, 70-90% = preview, <70% = manual
- [ ] Integrar validação + scoring no pipeline

#### DIA 7 - DiffGenerator + Testes
- [ ] Criar `src/agent_v3/diff/diff_generator.py`
- [ ] Formato de diff legível:
  ```
  MUDANÇA 1: Adicionado exame "Hemograma completo"
  Localização: node_id="sintomas_anemicos" → conditions
  Antes: [...]
  Depois: [..., "hemograma_completo"]
  Justificativa: Playbook recomenda hemograma para sintomas de anemia
  Confiança: 95%
  ```
- [ ] Testes end-to-end:
  - [ ] Rodar v2 → sugestões
  - [ ] Rodar v3 → protocolo corrigido
  - [ ] Validar estrutura + diff + rastreabilidade
  - [ ] Comparar com implementação manual (tempo/qualidade)

**Entregável**: Auto-Apply Engine funcional e testado

---

### **DIA 8 (2025-12-08) - Prompt Caching Agressivo** 💰

**Objetivo**: Reduzir custo de tokens em 50-70%

#### Tarefas
- [ ] Revisar `src/agent_v2/llm_client.py` (já tem cache ephemeral)
- [ ] Implementar estratégia 100% cache em `src/agent_v3/llm_client.py`:
  - [ ] Playbook sempre em cache (system message com cache_control)
  - [ ] Protocolo original em cache (não muda entre iterações)
  - [ ] Instruções de sistema em cache
  - [ ] Apenas output variável sem cache
- [ ] Criar `src/agent_v3/monitoring/cache_monitor.py`
  - [ ] Logar cache hit/miss rate
  - [ ] Calcular economia de tokens
  - [ ] Alertar se cache não funciona
- [ ] Testar com 10 análises consecutivas (medir economia real)

**Entregável**: Cache 100%, economia >50% validada

---

### **DIA 9 (2025-12-09) - Impact Scoring via Prompt** 🎯

**Objetivo**: Priorizar sugestões por impacto (quick win)

#### Tarefas
- [ ] Ajustar `src/config/prompts/super_prompt.py` para incluir scores:
  ```json
  {
    "priority": "critical",
    "category": "missing_red_flag",
    "description": "...",
    "impact_scores": {
      "patient_safety": 9,  // 0-10
      "financial_impact": "high",  // low/medium/high
      "implementation_effort": "low"  // low/medium/high
    }
  }
  ```
- [ ] Atualizar `src/agent_v2/output/validator.py` para validar novos campos
- [ ] Atualizar `src/cli/run_qa_cli.py` para rankear sugestões por impacto
- [ ] Testar com 5 protocolos reais (verificar se scores fazem sentido)

**Entregável**: Sugestões ranqueadas por impacto no relatório

---

### **DIA 10 (2025-12-10) - Integração V2 + V3** 🔗

**Objetivo**: Pipeline unificado v2 (análise) + v3 (correção)

#### Tarefas
- [ ] Criar `src/agent_v3/pipeline.py` como orquestrador:
  ```python
  analyze_and_fix(
      protocol_path,
      playbook_path,
      model="anthropic/claude-sonnet-4.5",
      auto_apply=True,
      confidence_threshold=0.90
  ) -> dict
  ```
- [ ] Fluxo integrado:
  1. Rodar v2 → análise + sugestões
  2. JSONCompactor → reduzir protocolo se necessário
  3. ImprovementApplicator → aplicar melhorias
  4. StructuralValidator → validar resultado
  5. ConfidenceScoring → avaliar confiança
  6. DiffGenerator → gerar diff
  7. Retornar tudo unificado
- [ ] Criar CLI para v3: `run_qa_v3_cli.py`
- [ ] Testar pipeline completo com 3-5 protocolos

**Entregável**: Pipeline v3 funcional end-to-end

---

### **DIAS 11-13 (2025-12-11 a 13) - Testes Intensivos** 🧪

**Objetivo**: Validar v3 com casos reais de múltiplas especialidades

#### DIA 11 - Testes de Funcionalidade
- [ ] Testar com 20+ protocolos reais:
  - ORL
  - AVC
  - Reumatologia
  - Doenças Infecciosas
  - Outros
- [ ] Medir para cada protocolo:
  - [ ] Taxa de sucesso (auto-apply sem erros)
  - [ ] Tempo de execução
  - [ ] Custo de tokens
  - [ ] Cache hit rate
  - [ ] Qualidade das correções (review manual)

#### DIA 12 - Testes de Edge Cases
- [ ] Protocolos muito pequenos (<100 linhas)
- [ ] Protocolos muito grandes (>5k linhas)
- [ ] Protocolos com estrutura não-padrão
- [ ] Playbooks muito grandes (>50 páginas)
- [ ] Playbooks muito pequenos (<5 páginas)
- [ ] Casos sem playbook (usar apenas protocolo)

#### DIA 13 - Correções e Refinamento
- [ ] Corrigir bugs encontrados
- [ ] Refinar prompts que geraram outputs ruins
- [ ] Otimizar performance (se necessário)
- [ ] Documentar limitações conhecidas
- [ ] Preparar casos de sucesso para apresentação

**Entregável**: V3 testado e validado em produção

---

### **DIA 14 (2025-12-14) - Apresentação e Decisão** 📊

**Objetivo**: Apresentar MVP para stakeholders e decidir próximos passos

#### Tarefas
- [ ] Criar apresentação em `reports/v3_mvp_presentation.md`:
  - Visão geral v2 → v3
  - Demo ao vivo (1-2 protocolos)
  - Métricas de sucesso:
    - Tempo de implementação: dias → minutos
    - Taxa de sucesso: X%
    - Economia de custo: Y%
    - Qualidade das correções (exemplos)
  - Casos de uso reais
  - Limitações e próximos passos
  - Proposta de deployment
- [ ] Review com stakeholders
- [ ] Coletar feedback
- [ ] Decidir:
  - [ ] V3 vai para produção? (quando?)
  - [ ] Investir em Fases 8-11 (feedback loop, ROI robusto, API)?
  - [ ] Manter v2 + v3 paralelo? (gradual rollout)

**Entregável**: Apresentação + decisão de deployment

---

## 📊 Métricas de Sucesso do MVP

### Obrigatórias (deve ter para considerar sucesso)
- ✅ Processa protocolos JSON >3k linhas sem quebrar
- ✅ Taxa de auto-apply bem-sucedida >80%
- ✅ Tempo de implementação: dias → <10 minutos
- ✅ Prompt caching >70% (economia brutal de custo)
- ✅ Zero regressões da v2 (v2 continua funcionando)
- ✅ Validação estrutural 100% (zero JSON quebrado salvo)

### Desejáveis (nice-to-have para MVP)
- 🎯 Sugestões com impact scores (segurança, economia, esforço)
- 🎯 Diff visual legível
- 🎯 Logs de auditoria completos
- 🎯 CLI amigável para v3

---

## 🛠️ Setup Inicial (Hoje - Antes do DIA 1)

### 1. Criar Branch V3
```bash
cd "C:\Users\daanm\AgenteV2"
git checkout -b v3-mvp
```

### 2. Estrutura de Pastas V3
```bash
mkdir -p src/agent_v3
mkdir -p src/agent_v3/json_compactor
mkdir -p src/agent_v3/chunking
mkdir -p src/agent_v3/applicator
mkdir -p src/agent_v3/validator
mkdir -p src/agent_v3/scoring
mkdir -p src/agent_v3/diff
mkdir -p src/agent_v3/monitoring
```

### 3. Atualizar requirements.txt (se necessário)
```txt
# V3 Additions (verificar se já tem)
jsonschema>=4.0.0  # Para validação estrutural
deepdiff>=6.0.0    # Para diff generator
```

### 4. Criar Script de Validação DIA 1
```bash
touch validate_auto_apply.py
```

---

## ⚠️ Riscos e Mitigação

### Risco 1: Auto-apply não funciona bem (<80% sucesso)
**Mitigação**:
- Validação no DIA 1 antes de implementar
- Se não funcionar → refinar prompt ou fazer assistido
- Fallback: modo preview obrigatório (não auto-apply)

### Risco 2: Protocolos JSON quebram após correção
**Mitigação**:
- StructuralValidator obrigatório antes de salvar
- Testes automáticos de schema
- Rollback automático se validação falhar

### Risco 3: Custo de tokens explode
**Mitigação**:
- Prompt caching 100% (DIA 8)
- Monitoramento contínuo via CacheMonitor
- Alertas se custo ultrapassar threshold

### Risco 4: Prazo de 2 semanas não é suficiente
**Mitigação**:
- Priorização brutal: CORE MVP vs Nice-to-Have
- Se atrasar → cortar Fase 7 (impact scoring) e fazer POST-MVP
- MVP mínimo: JSONCompactor + Auto-Apply + Validation

---

## 🎯 Definição de "Done" para MVP

**V3 MVP está completo quando:**
1. ✅ 5+ protocolos reais testados com auto-apply >80% sucesso
2. ✅ Suporta protocolos JSON >3k linhas sem quebrar
3. ✅ Pipeline completo funciona end-to-end (v2 análise + v3 correção)
4. ✅ Validação estrutural impede JSON quebrado de ser salvo
5. ✅ Prompt caching reduz custo >50%
6. ✅ Diff generator mostra mudanças de forma legível
7. ✅ Documentação básica pronta (README v3, exemplos)
8. ✅ Apresentação para stakeholders realizada
9. ✅ Decisão tomada sobre deployment

**Após atingir "Done":**
- Merge `v3-mvp` → `main` (se aprovado)
- Tag release `v3.0.0-alpha`
- Deploy gradual (v2 + v3 paralelo)
- Coletar feedback de produção
- Planejar Fases 8-11 (POST-MVP)

---

## 📞 Contato e Suporte

**Para dúvidas durante desenvolvimento:**
- Consultar `roadmap.md` para visão macro
- Consultar `REVIEW_CLAUDE.txt` para princípios de design v2
- Consultar `dev_history.md` para decisões passadas

**Após MVP:**
- Atualizar `dev_history.md` com entrada do MVP v3
- Atualizar `roadmap.md` com status das fases
- Criar `CHANGELOG.md` para v3.0.0-alpha

---

**Última Atualização**: 2025-12-01
**Próxima Revisão**: Após DIA 14 (apresentação)
