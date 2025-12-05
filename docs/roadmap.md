# 🗺️ Roadmap - Agente Daktus | QA

**Última Atualização**: 2025-12-05  
**Status Atual**: ✅ FASES 1-4 Completas | Sistema de Aprendizado Funcional

---

## 🎯 Visão do Produto

**Missão**: Validação e correção automatizadas de protocolos clínicos contra playbooks baseados em evidências.

**Transformação**: De **auditoria passiva** (identifica problemas) para **correção ativa** (resolve automaticamente).

---

## ✅ Funcionalidades Implementadas

### FASE 1: Análise Expandida ✅
- 20-50 sugestões por análise (vs 5-15 anterior)
- Scores de impacto (Segurança, Economia, Eficiência)
- Rastreabilidade completa (sugestão → evidência do playbook)
- Estimativa de custo por sugestão

### FASE 2: Sistema de Feedback ✅
- Coleta interativa de feedback (3 opções: S/N/Q)
- Detecção automática de padrões de rejeição
- Aprendizado contínuo via `memory_qa.md`
- Filtros ativos baseados em feedback histórico
- Segregação de sugestões rejeitadas com audit trail

### FASE 3: Controle de Custos ✅
- Estimativa pré-execução com 90%+ precisão
- Exibição informativa de custos
- Tabela de preços atualizada para todos os modelos

### FASE 4: Reconstrução de Protocolo ✅
- Usa apenas sugestões aprovadas pelo usuário
- Versionamento semântico (MAJOR.MINOR.PATCH)
- Changelog em cada nó modificado
- Timestamp padronizado (DD-MM-YYYY-HHMM)

### Correções Críticas (2025-12-04/05) ✅
- **Playbook Constraints**: Previne hallucinations, 95%+ verificabilidade
- **Reconstruction Fixes**: Respeita feedback, versioning correto
- **Learning System**: Threshold=1 para ativação imediata de padrões
- **Irrelevant Handling**: Sugestões irrelevantes removidas da reconstrução

---

## 📊 Métricas Alcançadas

| Métrica | Antes | Depois |
|---------|-------|--------|
| Sugestões por análise | 5-15 | 20-50 |
| Verificabilidade playbook | 50-60% | 95%+ |
| Feedback respeitado | 0% | 100% |
| TXT update reliability | ~80% | 99%+ |
| Pattern activation | 3 ocorrências | 1 ocorrência |

---

## ⏳ Próximas Fases (Pendentes)

### FASE 5: CLI Interativa Avançada
- Onboarding interativo guiado
- Thinking visível (o que o agente está fazendo)
- Progress bars e spinners
- Formatação rica com `rich` library

### FASE 6: Auto-Apply Completo
- Aplicação incremental com validação a cada sugestão
- Rollback automático em caso de erro
- Rastreamento de custo real vs estimado

### FASE 7: Validação Avançada
- Validação estrutural completa do JSON
- Validação de schema
- Zero protocolos quebrados salvos

### FASE 8: Diff Visual
- Diff side-by-side de mudanças
- Formatação HTML/texto
- Rastreabilidade 100%

### FASE 9-11: Integração e Deploy
- Pipeline completo integrado
- Testes intensivos (15-20 protocolos)
- Documentação final e deploy

---

## 🎯 Próximos Passos Recomendados

1. **Validar sistema atual** com múltiplos protocolos
2. **Monitorar métricas** de rejeição em `memory_qa.md`
3. **Priorizar FASE 5** (CLI Avançada) para melhorar UX
4. **Implementar FASE 6** (Auto-Apply Completo) para rollback

---

## 📚 Referências

- **README principal**: `README.md`
- **Histórico de desenvolvimento**: `docs/dev_history.md`
- **Memória do agente**: `memory_qa.md`

---

**Próxima Revisão**: Após validação com 5+ protocolos em produção
