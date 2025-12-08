# 🔍 Agente Daktus | QA

> Sistema de validação e correção automatizada de protocolos clínicos usando IA

**Versão Atual**: 3.1.0  
**Status**: Waves 1, 2, 3 Complete - Production Ready  
**Última Atualização**: 2025-12-07

---

## 🎯 O Que Faz

Valida protocolos clínicos (JSON) contra playbooks médicos (texto/PDF) para garantir:

- ✅ Consistência da lógica clínica
- ✅ Cobertura completa de sintomas
- ✅ Caminhos diagnósticos apropriados
- ✅ Recomendações baseadas em evidências
- ✅ Identificação de gaps e oportunidades de melhoria
- ✅ **Correção automatizada** com feedback loop

**Entrada**: Protocolo clínico (JSON) + Playbook médico (Markdown/PDF)  
**Saída**: Relatório de validação + Sugestões priorizadas + Protocolo corrigido (opcional)

---

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar OpenRouter

Crie um arquivo `.env` na raiz:

```env
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

**Obter chave**: https://openrouter.ai/keys

### 3. Executar

```bash
# CLI Interativa (recomendado)
python run_agent.py

# Ajuda
python run_agent.py --help
```

---

## ⚙️ Funcionalidades Principais

### 📊 Análise Expandida
- **20-50 sugestões** por análise (vs 5-15 anteriormente)
- Cada sugestão com **scores de impacto** (Segurança 0-10, Economia L/M/A)
- **Rastreabilidade completa**: cada sugestão linkada à evidência do playbook
- **Estimativa de custo** para aplicar cada sugestão

### 🔄 Human-in-the-Loop
- Usuário revisa cada sugestão: Relevante | Irrelevante | Sair
- Sistema **detecta padrões** de erro e acerto
- **Aprendizado contínuo** via `memory_qa.md`
- Sugestões irrelevantes são filtradas em análises futuras

### 🛡️ Restrição ao Playbook
- **Playbook como única fonte de verdade**
- Validação multi-camada contra hallucinations
- 95%+ das sugestões verificáveis no playbook

### 🛡️ Wave 1: Clinical Safety Foundations
- **Pydantic Schema Validation**: Estrutura de protocolo validada em tempo de reconstrução
- **AST-Based Logic Validation**: Validação segura de expressões condicionais (sem regex frágil)
- **LLM Contract Validation**: Detecção de model drift com schemas Pydantic
- **Zero Invalid Protocols**: 100% dos protocolos inválidos bloqueados antes de salvar

### 🧠 Wave 2: Memory & Learning
- **Hard Rules Engine**: Bloqueio automático de sugestões inválidas
- **Reference Validator**: Verificação rigorosa de evidências do playbook
- **Change Verifier**: Validação pós-reconstrução de mudanças aplicadas
- **Feedback Learner**: Aprendizado automático com padrões de rejeição
- **Spider/Daktus Knowledge**: Regras específicas para protocolos clínicos

### 💰 Wave 3: Observability & Cost Control
- **Real-Time Cost Tracking**: Token counter ao vivo durante análise
- **Accurate Cost Reporting**: Custos reais vs estimados, por sessão
- **Reconstruction Auditing**: Relatórios _AUDIT.txt detalhados para compliance
- **Implementation Path**: Sugestões estruturadas com JSON path exato
- **Spider-Aware Reconstruction**: LLM entende estrutura de protocolos Daktus

### 🔧 Reconstrução Inteligente
- Aplica **apenas sugestões aprovadas** pelo usuário
- Versionamento semântico automático (MAJOR.MINOR.PATCH)
- Changelog documentado em cada nó modificado

---

## 📁 Estrutura do Projeto

```
AgenteV2/
├── run_agent.py            # Entry point unificado
├── src/
│   └── agent/              # Módulo principal unificado
│       ├── analysis/       # Análise expandida
│       ├── feedback/       # Sistema de aprendizado
│       ├── applicator/     # Reconstrução de protocolos
│       ├── cost_control/   # Controle de custos
│       ├── cli/            # CLI interativa
│       └── core/           # LLM client, logger, loaders
├── models_json/            # Protocolos e playbooks
├── reports/                # Relatórios gerados
├── memory_qa.md            # Memória de aprendizado
└── docs/                   # Documentação
```

---

## 🤖 Modelos Suportados

**Recomendados:**
- `x-ai/grok-4.1-fast:free` ⭐ (gratuito, contexto 2M tokens)
- `google/gemini-2.5-flash-preview-09-2025` (baixo custo)
- `anthropic/claude-sonnet-4.5` (alta qualidade)

**Outros:**
- `x-ai/grok-4.1-fast` ($0.20/$0.50 por MTok, contexto 2M)
- `google/gemini-2.5-flash`, `google/gemini-2.5-pro`
- `anthropic/claude-opus-4.5`

---

## 📊 Performance

| Métrica | Valor |
|---------|-------|
| Sugestões por análise | 20-50 |
| Latência típica | 30-90s |
| Custo por análise | $0.00-$0.50 |
| Taxa de sucesso | >95% |
| Verificabilidade playbook | >95% |

---

## 🔧 Solução de Problemas

### "API key não configurada"
```bash
# Verifique o .env
cat .env
# Deve conter: OPENROUTER_API_KEY=sk-or-v1-...
```

### "Nenhum arquivo de protocolo encontrado"
Adicione arquivos JSON em `models_json/`

### "Playbook muito grande"
Use modelos com contexto grande (Grok 4.1, Gemini 2.5)

---

## 📚 Documentação

| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Este arquivo - visão geral e uso |
| `docs/roadmap.md` | Roadmap de desenvolvimento |
| `docs/dev_history.md` | Histórico de mudanças |
| `memory_qa.md` | Memória de aprendizado do agente |

---

## 🎯 Fluxo de Trabalho Típico

```
1. Selecionar protocolo JSON
       ↓
2. Selecionar playbook (opcional)
       ↓
3. Executar análise expandida
       ↓
4. Revisar sugestões (feedback)
       ↓
5. Agente aprende com feedback
       ↓
6. Reconstruir protocolo (opcional)
       ↓
7. Protocolo corrigido versionado
```

---

## 🔗 Links Úteis

- **OpenRouter**: https://openrouter.ai
- **Chaves de API**: https://openrouter.ai/keys
- **Catálogo de Modelos**: https://openrouter.ai/models

---

**Para o roadmap detalhado, veja [`docs/roadmap.md`](docs/roadmap.md)**  
**Para o histórico de desenvolvimento, veja [`docs/dev_history.md`](docs/dev_history.md)**
