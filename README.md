# 🔍 Agente Daktus | QA

> Sistema de validação e correção automatizada de protocolos clínicos usando IA

**Versão Atual**: 3.2.0  
**Status**: ✅ PRODUCTION-READY | Waves 1-4.3 Completas | Feedback Loop Completo  
**Última Atualização**: 2025-12-13

---

## 🎯 O Que Faz

Valida protocolos clínicos (JSON) contra playbooks médicos (texto/PDF) para garantir:

- ✅ Consistência da lógica clínica
- ✅ Cobertura completa de sintomas
- ✅ Caminhos diagnósticos apropriados
- ✅ Recomendações baseadas em evidências
- ✅ Identificação de gaps e oportunidades de melhoria
- ✅ **Correção automatizada** com feedback loop
- ✅ **Aprendizado contínuo** com histórico de feedback

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

### 🎯 Wave 4.1: Agent Intelligence
- **Alert Rules Module**: Regras de implementação de alertas com templates
- **Suggestion Validator**: Filtragem de antipadrões e duplicatas
- **Protocol Analyzer**: Ferramentas de análise estrutural
- **Good Alert Examples**: Few-shot learning para alertas específicos
- **Enhanced Prompts**: Redução de 71.4% → <30% em taxa de rejeição

### ✨ Wave 4.2: Bug Fixes & Polish
- **Template String Escaping**: Correção de erros em prompts complexos
- **NoneType Handling**: Tratamento robusto de edge cases
- **JSON Parsing Robusto**: Estratégias para LLM quirks
- **Transient Error Retry**: Retry automático com backoff exponencial
- **UI Consistency**: 100% Rich Panels profissionais
- **Node ID Preservation**: Reconstrução preserva IDs originais
- **Production Stability**: Zero crashes conhecidos

### 🔄 Wave 4.3: Feedback Loop & Learning (v3.2.0)
- **Verificação de Mudanças**: Mostra O QUE foi realmente modificado vs O QUE falhou  
- **Erros de Validação Claros**: Painel detalhado com erros de lógica condicional e severity  
- **Aprendizado com Falhas**: Sistema salva lições de implementações que falharam (`memory_qa.md`)  
- **Aprendizado com Validação**: Detecta erros de sintaxe e salva em memória  
- **Resumo Final Acionável**: Status claro (SUCESSO / PARCIAL / FALHAS)  
- **Sanitização de Condicionais**: Remove automaticamente funções inválidas do LLM  
- **Parser JSON Robusto**: Fix de strings multi-linha e JSON truncado  

**Arquivos principais:**
- `src/agent/cli/display_manager.py` - Novos métodos de display  
- `src/agent/learning/feedback_learner.py` - Aprendizado duplo (falhas + validação)  
- `src/agent/validators/logic_validator.py` - Sanitizador de condicionais  
- `src/agent/core/llm_client.py` - Parser JSON melhorado (Strategy 6 & 7)  

**⚠️ Problema Conhecido:** LLM ainda gera 4-5 funções inválidas apesar das instruções. Ver `docs/PROBLEMA_VALIDACAO_CONDICIONAIS.md` para análise completa e soluções.
- **Feedback Loop Completo**: Agente aprende e evita repetir mesmos erros

---

## 📁 Estrutura do Projeto

```
Agente Daktus/
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
