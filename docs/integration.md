# 🔗 Integration Vision - Agente Daktus QA

**Versão**: 1.0 (Draft para Discussão)  
**Data**: 2025-12-13  
**Status**: PROPOSTA INICIAL  
**Autores**: Dan Martins (conceito inicial), a refinar com Time TI

---

## 🎯 Contexto e Motivação

### Situação Atual

O Agente QA opera como ferramenta standalone (CLI), demonstrando valor técnico significativo em validação e correção de protocolos clínicos:

- ✅ 20-50 sugestões por análise (vs 5-15 em versões anteriores)
- ✅ >95% verificabilidade contra playbooks
- ✅ Sistema de aprendizado contínuo funcionando
- ✅ Zero bugs conhecidos em produção

### Oportunidade Identificada

**Integração ao Daktus Studio pode amplificar impacto**, reduzindo fricção de adoção e criando loop de feedback mais curto com usuários.

**Benefícios potenciais**:
- Validação no fluxo de trabalho (sem sair do editor)
- Adoção massiva (vs uso pontual atual)
- Feedback em tempo real
- Aprendizado mais rápido do sistema

### Propósito deste Documento

Esta proposta visa:
- Alinhar visão de integração com stakeholders
- Definir fronteiras e responsabilidades de forma clara
- Estabelecer roadmap colaborativo
- Identificar decisões técnicas pendentes

**Este é um documento vivo**, sujeito a ajustes baseados em feedback do time.

---

## 🧩 O Que É / Não É

### ✅ O Agente É (Core Competency):

- **Motor de análise clínica**: Valida protocolos contra playbooks baseados em evidências
- **Sistema de aprendizado**: Aprende com feedback do usuário via regras e padrões
- **Gerador de sugestões estruturadas**: Outputs prontos para aplicação (JSON path, diffs)
- **Validador de evidências**: Garante rastreabilidade playbook ↔ protocolo

### ❌ O Agente NÃO É (Fora de Escopo):

- **Editor de protocolos** → Expertise do Daktus Studio
- **Sistema de versionamento** → Responsabilidade do Studio
- **Interface web** → Daktus Studio já possui
- **Sistema de autenticação/permissões** → Já implementado no ecossistema Daktus
- **Substituição de processos existentes** → Complementa, não substitui

**Princípio Fundamental**: 

> O agente **complementa** a infraestrutura existente do Daktus Studio, aproveitando expertise já estabelecida em UI/UX, versionamento, e gestão de usuários.

---

## 🏗️ Arquitetura de Integração (Proposta)

### Nota Importante

Esta é uma **proposta inicial** para discussão. A arquitetura final será definida em conjunto com o time TI, considerando:

- Padrões arquiteturais existentes no Daktus
- Infraestrutura disponível
- Trade-offs de performance vs manutenibilidade
- Experiência do time com tecnologias específicas

### Modelo Proposto: Agente como "Serviço Especialista"

```
┌─────────────────────────────────────────────┐
│         DAKTUS STUDIO (Frontend)            │
│  ┌──────────────────────────────────────┐   │
│  │  Editor de Protocolos                │   │
│  │  [Trigger: Validar com IA]           │   │
│  └──────────────┬───────────────────────┘   │
│                 │ Invoca quando necessário   │
└─────────────────┼───────────────────────────┘
                  │
         ┌────────▼────────────┐
         │  DAKTUS STUDIO      │ (Backend)
         │  ┌──────────────┐   │
         │  │ API Layer    │   │
         │  └──────┬───────┘   │
         └─────────┼───────────┘
                   │ Chama serviço
         ┌─────────▼──────────┐
         │  AGENTE QA         │ (Serviço Especializado)
         │  ┌──────────────┐  │
         │  │  Analyze     │  │
         │  │  Suggest     │  │
         │  │  Apply       │  │
         │  └──────────────┘  │
         └────────────────────┘
```

### Justificativa do Modelo Proposto

**Vantagens**:
- **Desacoplamento**: Agente evolui independentemente do Studio
- **Testabilidade**: Cada camada pode ser testada isoladamente
- **Reutilização**: Outros produtos (ex: MedFlow) poderiam usar o mesmo padrão
- **Manutenibilidade**: Separação clara de responsabilidades

**Desvantagens**:
- Overhead de comunicação entre serviços
- Maior complexidade de deployment
- Necessidade de gerenciar mais um serviço

### Alternativas a Considerar (Com Expertise TI)

**Opção 1: Biblioteca Python Integrada**
- Menor overhead
- Maior acoplamento
- Deployment simplificado

**Opção 2: Message Queue (Async)**
- Maior resiliência
- Melhor para workloads pesados
- Maior complexidade

**Opção 3: Serverless Function**
- Auto-scaling
- Pay-per-use
- Cold start latency

**Decisão pendente**: A definir em conjunto com time TI baseado em:
- Infraestrutura atual do Daktus
- Volume esperado de uso
- SLAs de latência aceitáveis

---

## 📋 Divisão de Responsabilidades

### 🟢 DAN (SOLO)

**Foco**: Preparar agente para ser integrável

#### Responsabilidades:
- Estabilizar contratos de entrada/saída (schemas)
- Implementar testes automatizados (unit, integration)
- Documentar API boundaries e comportamentos esperados
- Congelar breaking changes no core do agente
- Criar guias de integração técnica

#### Critério de "Integration-Ready":
- [ ] Contratos de API documentados e estáveis
- [ ] Test coverage >80%
- [ ] Zero breaking changes por período definido
- [ ] Error handling robusto
- [ ] Logging estruturado

#### Validação Necessária:
- **Time TI valida** contratos propostos antes de prosseguir
- **Gabriel/Miguel aprovam** alinhamento com visão de produto

---

### 🟡 DAN + TI (COLABORATIVO)

**Foco**: Conectar agente ao ecossistema Daktus Studio

#### Responsabilidades Compartilhadas:

**Dan**:
- Propor contratos de API (schemas Pydantic/OpenAPI)
- Implementar lado do agente (server/endpoints)
- Fornecer exemplos de uso e casos extremos
- Documentar outputs e formatos de resposta

**Time TI**:
- Validar viabilidade arquitetural das propostas
- Implementar lado do Daktus Studio (client)
- Definir estratégias de deployment
- Estabelecer padrões de error handling

**Ambos (em conjunto)**:
- Testes de integração end-to-end
- Definição de timeouts, retries, circuit breakers
- Monitoramento e observabilidade
- Troubleshooting de issues

#### Critério de Sucesso:
- [ ] Daktus Studio consegue invocar agente com sucesso
- [ ] Error handling testado em cenários reais
- [ ] Latência dentro de limites aceitáveis
- [ ] Métricas de success rate estabelecidas

#### Pontos de Alinhamento Contínuo:
- Syncs regulares sobre progresso
- Code reviews cruzados
- Decisões arquiteturais documentadas
- Retrospectivas de aprendizado

---

### 🔴 TI-LED

**Foco**: Experiência do usuário final no Daktus Studio

#### Responsabilidades:

**Time TI**:
- Design de UX/UI da feature no Studio
- Implementação de componentes frontend
- Integração com fluxo de edição existente
- Deploy em produção
- Monitoramento de métricas de uso
- Suporte a usuários

**Dan (Suporte)**:
- Consultoria técnica sobre outputs do agente
- Validação de qualidade clínica das sugestões
- Suporte a bugs relacionados ao agente
- Ajustes baseados em feedback de produção

#### Critério de Sucesso:
- [ ] Feature live em produção
- [ ] Documentação de usuário publicada
- [ ] Métricas de adoção ativas
- [ ] NPS positivo
- [ ] Zero critical bugs por período definido

---

## 🗓️ Fases de Integração

### Nota sobre Timeline

**Datas são estimativas iniciais** para planejamento, não comprometimentos. 

Timeline final será definido considerando:
- Capacidade real do time
- Outras prioridades em paralelo
- Learnings durante execução
- Complexidade descoberta na implementação

---

### Fase 1: Preparação (DAN SOLO)

**Objetivo**: Tornar agente "integration-ready"

**Duração estimada**: A definir (sugestão: 2-3 semanas)

**Entregas**:
- Contratos de API estáveis
- Test suite completo
- Documentação de integração
- Zero breaking changes

**Validação**: Time TI aprova contratos antes de Fase 2

---

### Fase 2: Conexão (DAN + TI)

**Objetivo**: Estabelecer comunicação Daktus Studio ↔ Agente

**Duração estimada**: A definir (sugestão: 3-4 semanas)

**Entregas**:
- API implementada (ambos os lados)
- Testes de integração passando
- Error handling validado
- Métricas de performance coletadas

**Validação**: Comunicação bidirecional funcionando de forma confiável

---

### Fase 3: Experiência (TI-LED)

**Objetivo**: Feature "Validar com IA" disponível para usuários

**Duração estimada**: A definir (sugestão: 4-6 semanas)

**Entregas**:
- UI/UX no Daktus Studio
- Feature em produção
- Documentação de usuário
- Métricas de adoção

**Validação**: Usuários adotando, feedback positivo, zero critical bugs

---

## 🔑 Decisões Técnicas Pendentes

**Estas decisões DEVEM ser tomadas em conjunto com Time TI:**

### 1. Protocolo de Comunicação

**Opções**:
- **REST API (HTTP)** ← proposta inicial
  - Prós: Simplicidade, padrão consolidado, fácil debug
  - Contras: Overhead HTTP, sem streaming nativo
  
- **gRPC**
  - Prós: Melhor performance, streaming, type-safe
  - Contras: Maior complexidade, menos ferramentas de debug
  
- **Message Queue (RabbitMQ/Kafka)**
  - Prós: Desacoplamento total, resiliência, retry automático
  - Contras: Overhead operacional, complexidade

**Critérios de Decisão**:
- Padrões já utilizados no ecossistema Daktus
- Latência aceitável para caso de uso (< quanto?)
- Experiência do time com tecnologias
- Complexidade de manutenção

**Responsável pela decisão**: Time TI (com input do Dan)

---

### 2. Estratégia de Error Handling

**Questões Abertas**:
- Retry automático: no cliente (Studio) ou no servidor (Agente)?
- Timeout adequado: 30s? 60s? 120s? (depende de tamanho médio de protocolos)
- Fallback: o que mostrar ao usuário se agente indisponível?
- Circuit breaker: necessário? Quando abrir/fechar?

**Responsável pela decisão**: Time TI + Dan (em conjunto)

---

### 3. Modelo de Deployment

**Questões Abertas**:
- Agente roda em container Docker separado?
- Mesma instância/processo do Daktus Studio backend?
- Serverless function (Lambda, Cloud Run)?
- Quantas réplicas? Auto-scaling?

**Critérios**:
- Infraestrutura atual do Daktus
- Volume esperado de requisições
- Budget disponível

**Responsável pela decisão**: Time TI / DevOps

---

### 4. Modos de Operação

**Proposta de 3 modos** (a validar):

#### MODO 1: ANALYZE (Read-Only)
- **Input**: Protocolo JSON + Playbook
- **Output**: Lista de sugestões + scores de impacto
- **Comportamento**: Não modifica nada, apenas analisa

#### MODO 2: SUGGEST (Interativo)
- **Input**: Protocolo + Playbook + Feedback histórico
- **Output**: Sugestões filtradas pelo aprendizado
- **Comportamento**: Usa sistema de memória/regras

#### MODO 3: APPLY (Write)
- **Input**: Protocolo + Sugestões aprovadas pelo usuário
- **Output**: Protocolo modificado + Changelog
- **Comportamento**: Aplica mudanças (versionamento via Studio)

**Questões**:
- Esses modos fazem sentido para o fluxo do Studio?
- Falta algum modo essencial?
- Nomenclatura está clara?

**Responsável**: Dan propõe, TI valida alinhamento com UX

---

### 5. Formato de Sugestões

**Proposta atual** (exemplo):

```json
{
  "suggestion_id": "sugg_001",
  "json_path": "nodes[5].questions[2].text",
  "modification_type": "UPDATE",
  "current_value": "Você tem febre?",
  "proposed_value": "Você apresenta febre (temperatura axilar ≥37.8°C)?",
  "rationale": "Especificação do critério de febre conforme playbook",
  "evidence_reference": "Playbook p.15 - Definição de febre",
  "impact_scores": {
    "safety": 8,
    "cost": 3,
    "efficiency": 5
  }
}
```

**Questões**:
- Este formato atende necessidades do frontend?
- Falta alguma informação essencial?
- Como representar mudanças complexas (adicionar nó, remover edge)?

**Responsável**: Dan propõe, TI valida viabilidade de implementação no Studio

---

## 🎯 Critérios de Sucesso

### Métricas Técnicas (Propostas)

**Fase 1 (Preparação)**:
- [ ] Test coverage >80%
- [ ] API contracts estáveis (zero breaking changes)
- [ ] Documentação completa (aprovada por TI)

**Fase 2 (Conexão)**:
- [ ] Latência p95 < valor a definir (5s? 10s?)
- [ ] Error rate <1%
- [ ] Success rate >99%
- [ ] Zero memory leaks detectados

**Fase 3 (Experiência)**:
- [ ] Zero critical bugs por período definido
- [ ] Uptime >99.5%
- [ ] Latência percebida pelo usuário aceitável

### Métricas de Negócio (Propostas)

**Adoção**:
- [ ] X% usuários do Studio experimentam feature
- [ ] Y% voltam a usar após primeira tentativa
- [ ] Z análises/mês realizadas via integração

**Qualidade**:
- [ ] Taxa de aceitação de sugestões >50%
- [ ] NPS da feature >70
- [ ] Redução em tempo de validação manual (métrica a definir)

**Impacto**:
- [ ] Protocolos validados via agente têm menos erros em produção
- [ ] Redução em retrabalho de revisão de protocolos

**A validar**: 
- Estas métricas fazem sentido para o negócio?
- Temos baseline para comparação?
- Quais outras métricas são prioritárias?

---

## 🤝 Próximos Passos

### Imediato (Esta Semana)

1. **Validação desta proposta** (Gabriel, Miguel, Guilherme)
   - Este documento reflete a visão correta?
   - Há ajustes necessários antes de prosseguir?
   - Prioridade está alinhada com roadmap do Studio?

2. **Coleta de feedback**
   - O que está faltando?
   - O que está sobrando?
   - Onde há riscos não mapeados?

### Curto Prazo (Próximas Semanas)

3. **Kickoff técnico** (Dan + Guilherme + Time TI)
   - Alinhar decisões arquiteturais pendentes
   - Definir pontos de sincronização (daily? weekly?)
   - Estabelecer canais de comunicação (Slack? Reuniões?)

4. **Detalhamento de Fase 1**
   - Quebrar em tasks específicas
   - Definir contratos de API (draft para validação)
   - Setup de ambiente de testes

### Médio Prazo

5. **Execução incremental**
   - Fase 1 → validação → Fase 2 → validação → Fase 3
   - Retrospectivas ao final de cada fase
   - Ajustes de rota baseados em learnings

---

## 🌐 Expansão Futura: MedFlow

### Contexto

MedFlow (produto irmão do Daktus) possui fluxos similares de validação de protocolos clínicos. A integração do agente QA ao Daktus Studio pode servir como **piloto** para expansão futura.

### Oportunidades de Sinergia

**Aprendizados compartilhados**:
- Arquitetura de integração testada no Daktus pode ser replicada
- Erros e acertos documentados beneficiam ambos os produtos
- Sistema de aprendizado do agente pode ser alimentado por ambos

**Implementação**:
- **Foco inicial**: Daktus Studio (validar modelo de integração)
- **Expansão futura**: MedFlow (replicar padrão bem-sucedido)
- **Benefício mútuo**: Base de regras/padrões compartilhada

### Não-Escopo Atual

Esta integração com MedFlow **não está no escopo das Fases 1-3**. É uma oportunidade futura a ser explorada após validação bem-sucedida no Daktus Studio.

---

## 📚 Apêndices

### A. Glossário de Termos

- **Daktus Studio**: Plataforma web de edição de protocolos clínicos (anteriormente chamado Spider)
- **Agente QA**: Sistema de validação e correção automatizada de protocolos
- **Playbook**: Documento de referência clínica (Markdown ou PDF) baseado em evidências
- **Protocolo**: Arquivo JSON representando fluxo clínico estruturado
- **Sugestão**: Recomendação de mudança gerada pelo agente
- **Feedback Loop**: Sistema de aprendizado baseado em aceitação/rejeição de sugestões

### B. Por Que Estas Escolhas?

**Por que REST como proposta inicial?**
- Simplicidade de implementação e debug
- Padrão consolidado com vasta documentação
- Baixa curva de aprendizado para o time
- Permite validação rápida do modelo de integração

**Importante**: Esta é uma **proposta inicial**, não uma decisão final. Estamos abertos a alternativas que façam mais sentido arquiteturalmente.

**Por que fases incrementais?**
- Permite validação de hipóteses antes de investir pesado
- Reduz risco de retrabalho
- Gera learnings que informam fases seguintes
- Facilita alinhamento contínuo com stakeholders

**Por que divisão Solo/Colaborativo/TI-led?**
- Clareza de responsabilidades
- Aproveita expertise de cada área
- Reduz gargalos de comunicação
- Permite paralelização quando possível

### C. Premissas e Riscos

**Premissas**:
- [ ] Time TI tem capacidade para colaborar nas fases propostas
- [ ] Infraestrutura atual do Daktus suporta um serviço adicional
- [ ] Usuários têm necessidade real de validação automatizada
- [ ] Latência de análise é aceitável para caso de uso

**Riscos Identificados**:
- **Técnico**: Latência pode ser inaceitável para protocolos muito grandes
- **Produto**: Usuários podem não adotar se UX não for fluida
- **Operacional**: Manutenção de mais um serviço aumenta carga do time
- **Negócio**: ROI pode não justificar investimento

**Mitigações**:
- Validar premissas em cada fase antes de prosseguir
- Testes com usuários reais antes de produção
- Métricas de adoção e satisfação desde o início
- Opção de rollback se feature não performar

---

**Este documento é um ponto de partida para discussão, não um plano definitivo.**

Feedback e contribuições do time são essenciais para refiná-lo e torná-lo viável.

**Próxima revisão**: Após feedback de stakeholders (Gabriel, Miguel, Guilherme, Time TI)
