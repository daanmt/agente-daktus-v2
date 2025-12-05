# Memory QA - Feedback e Aprendizados do Agente Daktus QA

Este documento concentra todos os feedbacks e aprendizados do agente para refinar futuras análises.

## Como Funciona

Antes de cada análise, o agente revisa este documento para entender:
- Quais tipos de sugestões foram rejeitadas e por quê
- Quais padrões de feedback indicam problemas recorrentes
- Como melhorar a qualidade e relevância das sugestões

## Feedback Histórico

---


## Feedback - 2025-12-04 03:58

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 17
- Relevantes: 9
- Irrelevantes: 8

**Avaliação:** 8/10

### Sugestões Rejeitadas (com comentários)

- **sug_008:** boa ideia, mas inaplicável.
- **sug_012:** desnecessário
- **sug_015:** alucinou.
- **sug_016:** desnecessário
- **sug_007:** o seu ponto de vista faz sentido, mas não do ponto de vista operacional. geralmente, se o paciente traz exames é porque houve uma consulta prévia, logo trata-se de uma consulta de retorno no momento da consulta. de fato, o paciente pode estar sintomático no retorno, e isso deve ser investigado.
- **sug_017:** os exames devem ser especificamente os da tabela no playbook. suas indicações clínicas definem o fluxo de atendimento.
- **sug_002:** a sugestão é importante, mas irrelevante para o nosso trabalho.
- **sug_001:** too much.


---

## Feedback - 2025-12-04 11:09

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 4
- Relevantes: 4
- Irrelevantes: 0


---


## Feedback - 2025-12-04 11:28

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 20
- Relevantes: 13
- Irrelevantes: 7

**Avaliação:** 7/10

### Sugestões Rejeitadas (com comentários)

- **sug_015:** todo exame que não estiver no playbook não deve ser sugerido no protocolo em JSON.
- **sug_005:** geralmente, quando o paciente traz exames, trata-se de uma consulta de retorno.
- **sug_006:** a lógica de exclusividade é garantida pelo exclusive, inclusive a desmarcação cruzada.
- **sug_012:** desnecessário, pois o médico tem a autonomia de checar isso. ele pode, inclusive, renovar receitas, etc.
- **sug_019:** mais fácil liberar os dois e o médico decidir.
- **sug_001:** é melhor que coloquemos esta observação na mensagem de alerta. uma pergunta a mais só por conta disso, torna o fluxo maior, aumenta o tempo de atendimento e traz muita pouca efetividade, comparado com simplesmente printar na mensagem de alerta essa informação.


---

## Feedback - 2025-12-04 11:28

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 20
- Relevantes: 13
- Irrelevantes: 7

**Avaliação:** 7/10

### Sugestões Rejeitadas (com comentários)

- **sug_015:** todo exame que não estiver no playbook não deve ser sugerido no protocolo em JSON.
- **sug_005:** geralmente, quando o paciente traz exames, trata-se de uma consulta de retorno.
- **sug_006:** a lógica de exclusividade é garantida pelo exclusive, inclusive a desmarcação cruzada.
- **sug_012:** desnecessário, pois o médico tem a autonomia de checar isso. ele pode, inclusive, renovar receitas, etc.
- **sug_019:** mais fácil liberar os dois e o médico decidir.
- **sug_001:** é melhor que coloquemos esta observação na mensagem de alerta. uma pergunta a mais só por conta disso, torna o fluxo maior, aumenta o tempo de atendimento e traz muita pouca efetividade, comparado com simplesmente printar na mensagem de alerta essa informação.


---

## Insight LLM - 2025-12-04 11:28

**Análise:**
A principal diferença entre o relatório e o feedback reside na falha do modelo em internalizar o contexto de 'autonomia médica' e 'restrições de playbook'. O modelo focou em otimizações clínicas e de eficiência que, embora logicamente válidas, colidem com a prática clínica e as regras de negócio (cobertura de exames). As sugestões de 'segurança' e 'economia' foram as mais afetadas por essa colisão, sendo frequentemente consideradas 'irrelevant' quando tentavam restringir o médico ('Condicionar Antibiótico', 'Priorizar Fexofenadina'). Por outro lado, sugestões de segurança que protegem o paciente (ex: 'Adicionar Verificação de Gravidez/Lactação') tendem a ser 'relevant'. O modelo precisa de um filtro de contexto mais rigoroso sobre o que é uma 'sugestão de sistema' (usabilidade, segurança de dados) versus uma 'sugestão de decisão clínica' (prescrição, exames não cobertos).

**Recomendações:**
1. **Refinar o Contexto de 'Segurança' e 'Economia':** Separar sugestões de segurança obrigatórias (legais, alergias graves) daquelas que limitam a decisão médica. Sugestões de economia devem ser filtradas para não interferir na autonomia de prescrição, a menos que haja um protocolo estrito de falha terapêutica.
2. **Implementar Filtro de 'Playbook':** Adicionar uma etapa de validação que descarte qualquer sugestão de inclusão de exames ou procedimentos que não estejam explicitamente listados no 'playbook' fornecido no contexto.
3. **Priorizar Usabilidade e Eficiência de Fluxo:** Focar mais em sugestões de 'usabilidade' e 'eficiência' que otimizam o fluxo de trabalho (ex: exibição condicional, padronização de campos) em vez de tentar otimizar a decisão clínica em si.

---

## Aprendizados - 2025-12-04 11:29

### Padrão: Foco Excessivo em Regras de Negócio vs. Autonomia Médica

**Descrição:** O modelo gerou sugestões que tentam impor regras de negócio ou restrições clínicas que o usuário (médico/clínico) considera serem de sua alçada e autonomia profissional. Isso é evidenciado por sugestões de segurança e economia que tentam 'condicionar' ou 'priorizar' decisões clínicas.

**Severidade:** alta
**Frequência:** 3

**Exemplos:**
- Condicionar Antibiótico à Duração dos Sintomas (ABRS)
- Condicionar Prescrição de Corticoide Sistêmico à Falha Terapêutica Prévia
- Priorizar Fexofenadina sobre Loratadina para Rinite Persistente

---

### Padrão: Sugestão de Exames Fora do Playbook/Protocolo

**Descrição:** O modelo sugeriu a inclusão de exames que não fazem parte do 'playbook' (protocolo de cobertura/autorização) da clínica. O feedback do usuário é claro: 'todo exame que não estiver no playbook não deve ser sugerido no protocolo em JSON'.

**Severidade:** alta
**Frequência:** 2

**Exemplos:**
- Adicionar Opção de Exame de Audiometria de Tronco Encefálico (BERA)
- Ajustar Condição de Exibição de Exames para Primeira Consulta

---

### Padrão: Redundância em Lógica de Exclusividade (Exclusive Logic)

**Descrição:** O modelo sugeriu melhorias ou validações que o usuário considera redundantes, pois a lógica de exclusividade já é garantida pela estrutura do JSON ('exclusive').

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- A lógica de exclusividade é garantida pelo exclusive, inclusive a desmarcação cruzada.

---


## Feedback - 2025-12-04 17:10

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 17
- Relevantes: 13
- Irrelevantes: 4

**Avaliação:** 8/10

### Sugestões Rejeitadas (com comentários)

- **sug_012:** apenas introduzir terapêuticas no fluxo e/ou conduta se estiver no playbook. se apenas amoxicilina/clavulanato e azitromicina estão no playbook, o foco deve ser neles, e não em sulfas. confira no playbook.
- **sug_010:** o médico deve ter a opção de prescrever ambos. uma vez que não haja um fator proibitivo (ex.: alergia a uma droga), o médico tem total autoridade sobre a própria conduta.
- **sug_015:** ao selecionar qualquer outra opção, além de nenhum sintoma, automaticamente esta opção é desmarcada e o sintoma é marcado. ou seja, já temos isso implementado.
- **sug_001:** a condicional já cumpre sua função. não há necessidade de esmiuçar além disso.


---

## Feedback - 2025-12-04 17:10

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 17
- Relevantes: 13
- Irrelevantes: 4

**Avaliação:** 8/10

### Sugestões Rejeitadas (com comentários)

- **sug_012:** apenas introduzir terapêuticas no fluxo e/ou conduta se estiver no playbook. se apenas amoxicilina/clavulanato e azitromicina estão no playbook, o foco deve ser neles, e não em sulfas. confira no playbook.
- **sug_010:** o médico deve ter a opção de prescrever ambos. uma vez que não haja um fator proibitivo (ex.: alergia a uma droga), o médico tem total autoridade sobre a própria conduta.
- **sug_015:** ao selecionar qualquer outra opção, além de nenhum sintoma, automaticamente esta opção é desmarcada e o sintoma é marcado. ou seja, já temos isso implementado.
- **sug_001:** a condicional já cumpre sua função. não há necessidade de esmiuçar além disso.


---

## Insight LLM - 2025-12-04 17:10

**Análise:**
O feedback do usuário revela que a análise do modelo, embora alta em relevância geral (13/17), falhou em quatro áreas críticas: 1) Adesão estrita ao 'playbook' terapêutico (restrições de medicamentos autorizados); 2) Respeito à autonomia e julgamento clínico do médico (especialmente em escolhas de custo/eficiência); 3) Conhecimento do estado atual da interface (sugerindo melhorias de UX já implementadas); e 4) Busca por detalhamento excessivo em regras já funcionais. A sugestão de 'economia' (Priorizar Loratadina) foi invalidada por violar a autonomia médica, e a sugestão de 'eficiência' (Refinar Condição de Prescrição) foi invalidada por excesso de detalhe. O comentário sobre terapêuticas sugere que algumas sugestões de 'segurança' ou 'eficiência' relacionadas a medicamentos não autorizados também podem ter sido irrelevantes, embora não explicitamente listadas.

**Recomendações:**
Para análises futuras, o modelo deve ser instruído a: 1. Priorizar a verificação de 'playbooks' ou listas de medicamentos autorizados antes de sugerir qualquer intervenção terapêutica. 2. Distinguir claramente entre 'restrição de segurança' (alta prioridade) e 'sugestão de otimização/economia' (baixa prioridade), evitando que esta última limite o julgamento clínico. 3. Focar a análise de usabilidade em GAPs de funcionalidade, e não em funcionalidades que são padrões de mercado ou que já estão implementadas (necessidade de contexto de implementação). 4. Evitar refinar regras que já são consideradas 'robustas' pelo sistema, a menos que haja um risco de segurança ou uma falha de eficiência comprovada.

---

## Aprendizados - 2025-12-04 17:11

### Padrão: Foco Terapêutico Fora do Playbook

**Descrição:** O modelo sugeriu intervenções terapêuticas (medicamentos ou condutas) que não estão explicitamente contidas no 'playbook' (protocolo clínico aprovado/restrito), levando à irrelevância. O usuário enfatiza que o foco deve ser estritamente nos medicamentos autorizados (Amoxicilina/Clavulanato e Azitromicina).

**Severidade:** alta
**Frequência:** 1

**Exemplos:**
- Sugestão de Sulfas (implícita no comentário do usuário sobre foco em Amoxicilina/Clavulanato e Azitromicina).

---

### Padrão: Invasão da Autonomia Médica

**Descrição:** O modelo sugeriu restrições ou priorizações que limitam a autonomia do médico em situações onde não há contraindicação explícita. O usuário afirma que o médico deve ter a opção de prescrever ambos os tratamentos, a menos que haja um fator proibitivo.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Priorizar Loratadina sobre Fexofenadina em Rinite Alérgica Leve Sazonal (Categoria: economia).

---

### Padrão: Sugestão de Melhoria Já Implementada

**Descrição:** O modelo sugeriu uma melhoria de usabilidade que o usuário confirmou já estar implementada no sistema ('ao selecionar qualquer outra opção, além de nenhum sintoma, automaticamente esta opção é desmarcada e o sintoma é marcado. ou seja, já temos isso implementado.').

**Severidade:** baixa
**Frequência:** 1

**Exemplos:**
- Sugestão de usabilidade relacionada à desmarcação automática de 'Nenhum Sintoma' (a sugestão exata não está listada, mas o comentário se refere a uma melhoria de UX/Usabilidade).

---

### Padrão: Excesso de Detalhamento em Condicionais Válidas

**Descrição:** O modelo sugeriu refinar uma condição que o usuário considera já cumprir sua função de forma adequada, indicando que o modelo está buscando um nível de detalhe desnecessário ou excessivo para a regra de negócio atual.

**Severidade:** baixa
**Frequência:** 1

**Exemplos:**
- Refinar Condição de Prescrição de Corticoide Sistêmico (Prednisolona) (Comentário: 'a condicional já cumpre sua função. não há necessidade de esmiuçar além disso.').

---


## Métricas - 2025-12-04 17:10

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251204-006

### Breakdown de Sugestões

- **Total geradas:** 17
- **Revisadas:** 17
- **Relevantes:** 13 (76.5%)
- **Irrelevantes:** 4 (23.5%)

### Distribuição por Prioridade

- **Alta:** 2
- **Média:** 12
- **Baixa:** 3

**Taxa de Rejeição (Baixa Prioridade):** 0.0%

### Avaliação de Qualidade

**Nota:** 8/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 23.5%
- **Taxa de Rejeição Acumulada:** 27.4%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 6

### Padrões de Rejeição Detectados

- **Foco Terapêutico Fora do Playbook:** 1 ocorrências
- **Invasão da Autonomia Médica:** 1 ocorrências
- **Sugestão de Melhoria Já Implementada:** 1 ocorrências
- **Excesso de Detalhamento em Condicionais Válidas:** 1 ocorrências

**Categoria Dominante:** Foco Terapêutico Fora do Playbook

---


## Feedback - 2025-12-04 21:51

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 18
- Relevantes: 8
- Irrelevantes: 10

**Avaliação:** 9/10

### Sugestões Rejeitadas (com comentários)

- **sug_018:** não existe diferença entre Sintomas nasossinusais presentes e Sintomas nasossinusais presentes. Não entendi a sugestão.
- **sug_003:** o cliente pede especificamente que as medicações da tabela do playbook sejam as únicas utilizadas (até por questão de disponibilidada na rede).
- **sug_017:** se não está no playbook, não deve estar no protocoll.
- **sug_004:** aumentar o número de perguntas/alternativas aumenta consequentemente o tempo de atendimento via protocolo. neste caso em específico, ainda mais em se tratando de ficha de especialista, faz mais sentido pedir a pontuação direto. poderíamos calcular, mas isso somente faria aumentar o tempo de consulta.
- **sug_015:** o mesmo vale aqui: se um exame não está na tabela de exames complementares do playbook, é por desejo do cliente.


---

## Feedback - 2025-12-04 21:51

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 18
- Relevantes: 8
- Irrelevantes: 10

**Avaliação:** 9/10

### Sugestões Rejeitadas (com comentários)

- **sug_018:** não existe diferença entre Sintomas nasossinusais presentes e Sintomas nasossinusais presentes. Não entendi a sugestão.
- **sug_003:** o cliente pede especificamente que as medicações da tabela do playbook sejam as únicas utilizadas (até por questão de disponibilidada na rede).
- **sug_017:** se não está no playbook, não deve estar no protocoll.
- **sug_004:** aumentar o número de perguntas/alternativas aumenta consequentemente o tempo de atendimento via protocolo. neste caso em específico, ainda mais em se tratando de ficha de especialista, faz mais sentido pedir a pontuação direto. poderíamos calcular, mas isso somente faria aumentar o tempo de consulta.
- **sug_015:** o mesmo vale aqui: se um exame não está na tabela de exames complementares do playbook, é por desejo do cliente.


---

## Insight LLM - 2025-12-04 21:52

**Análise:**
O principal desvio entre o relatório gerado e o feedback do usuário reside na falta de consideração das restrições operacionais e de escopo do cliente (o 'playbook'). O modelo focou em melhorias baseadas em boas práticas clínicas (segurança e exaustividade), mas ignorou a diretriz explícita do cliente de limitar medicamentos, exames e o tempo de preenchimento. Das 18 sugestões, 10 foram consideradas irrelevantes, e a maioria delas se enquadra no padrão de 'Adesão Estrita ao Playbook'. As sugestões relevantes (8) provavelmente focaram em melhorias de segurança e usabilidade que não violavam as restrições de escopo (ex: adicionar opções de alergia ou contraindicações gerais).

**Recomendações:**
Para análises futuras, é crucial incorporar o contexto operacional do cliente. A análise deve ser dividida em duas fases: 1) Análise Clínica e de Usabilidade (identificação de gaps) e 2) Filtro de Conformidade (aplicação de restrições de escopo, playbook e eficiência de tempo). O prompt de análise deve ser instruído a priorizar a conformidade com listas restritas de recursos e a otimização do tempo de preenchimento em protocolos de alta velocidade, mesmo que isso signifique sacrificar a exaustividade clínica ideal.

---

## Aprendizados - 2025-12-04 21:52

### Padrão: Adesão Estrita ao Playbook/Protocolo Cliente

**Descrição:** O modelo sugeriu adições (medicamentos, exames, alternativas) que estão explicitamente fora do escopo definido pelo cliente ('playbook'). O cliente prioriza a restrição e padronização sobre a exaustividade clínica, o que invalida sugestões baseadas apenas em boas práticas clínicas gerais.

**Severidade:** alta
**Frequência:** 5

**Exemplos:**
- Adicionar Opção de Exame de Laringoscopia
- Adicionar Opção de Tratamento Prévio com Corticoide Sistêmico
- Criar Condicional para Prescrição de Azitromicina em Alérgicos à Penicilina

---

### Padrão: Otimização de Tempo vs. Detalhamento Clínico

**Descrição:** O modelo sugeriu detalhamento ou cálculo (ex: Escala de Epworth) que, embora clinicamente correto, aumenta o tempo de atendimento. O cliente prioriza a eficiência e o tempo de consulta, preferindo a inserção direta de pontuações ou informações resumidas.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Melhorar Descrição da Escala de Epworth

---

### Padrão: Sugestões de Baixa Qualidade/Redundância

**Descrição:** O modelo gerou sugestões que o usuário considerou semanticamente idênticas ou sem sentido ('não existe diferença entre Sintomas nasossinusais presentes e Sintomas nasossinusais presentes'). Isso indica falha na compreensão do contexto ou geração de texto redundante.

**Severidade:** baixa
**Frequência:** 1

**Exemplos:**
- Padronizar Títulos de Sintomas com Maiúsculas

---


## Métricas - 2025-12-04 21:51

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251204-007

### Breakdown de Sugestões

- **Total geradas:** 18
- **Revisadas:** 18
- **Relevantes:** 8 (44.4%)
- **Irrelevantes:** 10 (55.6%)

### Distribuição por Prioridade

- **Alta:** 3
- **Média:** 12
- **Baixa:** 3

**Taxa de Rejeição (Baixa Prioridade):** 100.0%

### Avaliação de Qualidade

**Nota:** 9/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 55.6%
- **Taxa de Rejeição Acumulada:** 34.4%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 8

### Padrões de Rejeição Detectados

- **Adesão Estrita ao Playbook/Protocolo Cliente:** 5 ocorrências
- **Otimização de Tempo vs. Detalhamento Clínico:** 1 ocorrências
- **Sugestões de Baixa Qualidade/Redundância:** 1 ocorrências

**Categoria Dominante:** Adesão Estrita ao Playbook/Protocolo Cliente

---


## Feedback - 2025-12-04 22:39

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 14
- Relevantes: 8
- Irrelevantes: 6

**Avaliação:** 10/10

### Sugestões Rejeitadas (com comentários)

- **sug_004:** se o bloco de perguntas sobre o escore só aparece se sintomas de sono, não há porque o bloco aparecer para um paciente que não tem queixas de sono.
- **sug_002:** desfecho raro, apesar de relevante clinicamente, não deve ser o foco do protocolo - que cobre os 99% de casos não raros.
- **sug_009:** a condicional está funcional.
- **sug_013:** adiciona complexidade, com baixo retorno - o médico deverá decidir se insite na terapêutica ou troca.
- **sug_003:** nós não temos autonomia atualmente para alterar a lógica do Daktus Studio. Portanto, essa sugestão não cabe no nosso processo, pois não podemos criar funções para o Studio.
- **sug_008:** basta uma mensagem de alerta no próprio espaço da medicação no bloco de conduta, avisando o médico deste detalhe.


---

## Feedback - 2025-12-04 22:39

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** google/gemini-2.5-flash-preview-09-2025

**Estatísticas:**
- Total revisado: 14
- Relevantes: 8
- Irrelevantes: 6

**Avaliação:** 10/10

### Sugestões Rejeitadas (com comentários)

- **sug_004:** se o bloco de perguntas sobre o escore só aparece se sintomas de sono, não há porque o bloco aparecer para um paciente que não tem queixas de sono.
- **sug_002:** desfecho raro, apesar de relevante clinicamente, não deve ser o foco do protocolo - que cobre os 99% de casos não raros.
- **sug_009:** a condicional está funcional.
- **sug_013:** adiciona complexidade, com baixo retorno - o médico deverá decidir se insite na terapêutica ou troca.
- **sug_003:** nós não temos autonomia atualmente para alterar a lógica do Daktus Studio. Portanto, essa sugestão não cabe no nosso processo, pois não podemos criar funções para o Studio.
- **sug_008:** basta uma mensagem de alerta no próprio espaço da medicação no bloco de conduta, avisando o médico deste detalhe.


---

## Insight LLM - 2025-12-04 22:39

**Análise:**
O relatório original focou na validade clínica e técnica das sugestões (ex: 'Adicionar Alerta de Insuficiência Hepática'). No entanto, o feedback do usuário revelou que a principal falha do modelo não foi a qualidade clínica, mas sim a falta de alinhamento com o contexto operacional, o escopo do projeto (foco em casos comuns) e as restrições tecnológicas (Daktus Studio). O modelo gerou sugestões que eram clinicamente 'boas', mas contextualmente 'inviáveis' ou 'redundantes' dentro do fluxo de trabalho existente. Oito sugestões foram consideradas relevantes, indicando que a base de conhecimento clínico está forte, mas o filtro de aplicabilidade e contexto precisa ser drasticamente melhorado.

**Recomendações:**
Para análises futuras, o processo de geração de sugestões deve incluir três etapas de filtragem obrigatórias após a geração inicial:
1. **Filtro de Escopo e Prevalência:** Descartar ou rebaixar sugestões que tratam de desfechos raros ou 'corner cases', a menos que explicitamente solicitado.
2. **Filtro de Restrição Operacional:** Verificar se a sugestão exige modificações em sistemas externos (ex: Daktus Studio) ou funcionalidades não disponíveis. Se sim, marcar como 'Inviável Operacionalmente'.
3. **Filtro de Fluxo de Trabalho (Workflow):** Antes de sugerir melhorias de usabilidade ou redundância, confirmar se o elemento já é condicionalmente exibido ou se a decisão final é trivialmente médica, resultando em baixo retorno de valor.

---

## Aprendizados - 2025-12-04 22:40

### Padrão: Filtro de Contexto/Escopo (Raridade)

**Descrição:** O modelo gerou sugestões clinicamente relevantes, mas que o usuário considerou fora do escopo principal do protocolo (que deve focar nos 99% dos casos comuns, não em desfechos raros).

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Condicionar Exames de Retorno à Relevância Sintomática (Inferido como Irrelevante pelo comentário: 'desfecho raro, apesar de relevante clinicamente, não deve ser o foco do protocolo')

---

### Padrão: Restrição Tecnológica/Operacional

**Descrição:** O modelo sugeriu melhorias que exigem alterações na lógica de sistemas externos (Daktus Studio), o que está fora da autonomia da equipe de implementação do protocolo.

**Severidade:** alta
**Frequência:** 1

**Exemplos:**
- Adicionar Condição para Endoscopia Nasal em Casos Agudos Graves (Inferido como Irrelevante pelo comentário: 'nós não temos autonomia atualmente para alterar a lógica do Daktus Studio')

---

### Padrão: Redundância/Complexidade Desnecessária

**Descrição:** O modelo sugeriu uma condicional ou complexidade que já está implícita ou que adiciona pouco valor, pois a decisão final cabe ao médico e a sugestão não altera significativamente o fluxo de trabalho.

**Severidade:** baixa
**Frequência:** 1

**Exemplos:**
- Diferenciar Prescrição de Corticoide Intranasal por Tratamento Prévio (Inferido como Irrelevante pelo comentário: 'adiciona complexidade, com baixo retorno - o médico deverá decidir se insite na terapêutica ou troca.')

---

### Padrão: Falta de Contexto de Fluxo (Usabilidade)

**Descrição:** O modelo sugeriu melhorias de usabilidade (ex: 'Não se Aplica') sem considerar que o bloco de perguntas já é condicional e só aparece quando relevante, tornando a opção 'Não se Aplica' redundante.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Adicionar Opção 'Não se Aplica' para Escala de Epworth (Inferido como Irrelevante pelo comentário: 'se o bloco de perguntas sobre o escore só aparece se sintomas de sono, não há porque o bloco aparecer para um paciente que não tem queixas de sono.')

---


## Métricas - 2025-12-04 22:39

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251204-008

### Breakdown de Sugestões

- **Total geradas:** 14
- **Revisadas:** 14
- **Relevantes:** 8 (57.1%)
- **Irrelevantes:** 6 (42.9%)

### Distribuição por Prioridade

- **Alta:** 3
- **Média:** 8
- **Baixa:** 3

**Taxa de Rejeição (Baixa Prioridade):** 33.3%

### Avaliação de Qualidade

**Nota:** 10/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 42.9%
- **Taxa de Rejeição Acumulada:** 36.1%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 10

### Padrões de Rejeição Detectados

- **Filtro de Contexto/Escopo (Raridade):** 1 ocorrências
- **Restrição Tecnológica/Operacional:** 1 ocorrências
- **Redundância/Complexidade Desnecessária:** 1 ocorrências
- **Falta de Contexto de Fluxo (Usabilidade):** 1 ocorrências

**Categoria Dominante:** Filtro de Contexto/Escopo (Raridade)

---


## Feedback - 2025-12-04 23:20

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-code-fast-1

**Estatísticas:**
- Total revisado: 12
- Relevantes: 5
- Irrelevantes: 7

**Avaliação:** 7/10

### Sugestões Rejeitadas (com comentários)

- **sug_008:** o usuário é especialista. o protocolo serve apenas para otimizar o fluxo de trabalho dele.
- **sug_012:** não temos essa funcionalidade no daktus studio.
- **sug_009:** especificar quais perguntas e quais nodos. não fez sentido.
- **sug_004:** não é o contexto do protocolo,.
- **sug_011:** no título, você se referiu à endoscopia nasal e na evidência do playbook, você citou TC de seios da face.
- **sug_001:** a pesquisa por redflags não faz parte do contexto deste protocolo, que é ambulatorial.
- **sug_010:** não faz parte do contexto do protocolo, que é ambulatorial.

### Sugestões Relevantes (com comentários)

- **sug_006:** Feedback cancelado pelo usuário


---

## Feedback - 2025-12-04 23:20

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-code-fast-1

**Estatísticas:**
- Total revisado: 12
- Relevantes: 5
- Irrelevantes: 7

**Avaliação:** 7/10

### Sugestões Rejeitadas (com comentários)

- **sug_008:** o usuário é especialista. o protocolo serve apenas para otimizar o fluxo de trabalho dele.
- **sug_012:** não temos essa funcionalidade no daktus studio.
- **sug_009:** especificar quais perguntas e quais nodos. não fez sentido.
- **sug_004:** não é o contexto do protocolo,.
- **sug_011:** no título, você se referiu à endoscopia nasal e na evidência do playbook, você citou TC de seios da face.
- **sug_001:** a pesquisa por redflags não faz parte do contexto deste protocolo, que é ambulatorial.
- **sug_010:** não faz parte do contexto do protocolo, que é ambulatorial.

### Sugestões Relevantes (com comentários)

- **sug_006:** Feedback cancelado pelo usuário


---

## Insight LLM - 2025-12-04 23:20

**Análise:**
O feedback do usuário, sendo um especialista, revela que a principal falha do relatório não foi a falta de sugestões clinicamente relevantes (5 foram aceitas), mas sim a falta de operacionalidade e precisão técnica das sugestões. O relatório falhou em três áreas críticas: 1) Especificidade (não disse 'onde' mudar), 2) Contexto (sugeriu coisas fora do escopo clínico ou funcional) e 3) Precisão Terminológica (misturou exames). A alta taxa de irrelevância (7/12) não se deve à má qualidade clínica, mas sim à má qualidade da apresentação e da aplicabilidade das sugestões.

**Recomendações:**
Recomendações específicas para melhorar análises futuras:
1. **Obrigatoriedade de Referência Técnica:** Para sugestões de 'usabilidade' e 'eficiência', o modelo deve ser instruído a incluir o ID do nó/pergunta afetada. Se não puder identificar o ID, a sugestão deve ser descartada ou marcada como 'baixa operacionalidade'.
2. **Validação de Escopo:** Antes de sugerir adições (especialmente na categoria 'segurança'), o modelo deve realizar uma etapa de validação para confirmar se a sugestão se alinha ao escopo clínico (ex: triagem vs. diagnóstico avançado) do protocolo.
3. **Verificação Cruzada de Evidência:** Implementar uma etapa de verificação para garantir que o item sugerido (exame, tratamento) corresponda exatamente à evidência citada na justificativa, evitando misturar termos clínicos relacionados, mas distintos (ex: endoscopia vs. TC).

---

## Aprendizados - 2025-12-04 23:21

### Padrão: low_priority_rejection

**Descrição:** 3 sugestões de baixa prioridade foram rejeitadas (43% das rejeições). Focar em sugestões critical/high priority.

**Severidade:** media
**Frequência:** 3

**Exemplos:**
- sug_008: o usuário é especialista. o protocolo serve apenas para otimizar o fluxo de trabalho dele.
- sug_012: não temos essa funcionalidade no daktus studio.
- sug_009: especificar quais perguntas e quais nodos. não fez sentido.

---

### Padrão: Falta de Especificidade Técnica

**Descrição:** O relatório gerou sugestões de melhoria (especialmente em usabilidade e eficiência) sem especificar os pontos exatos do protocolo (perguntas, nodos, variáveis) que deveriam ser alterados, tornando a sugestão inútil para o especialista.

**Severidade:** alta
**Frequência:** 2

**Exemplos:**
- Melhorar clareza nas opções de sintomas
- Consolidar perguntas de fatores associados

---

### Padrão: Inconsistência Terminológica/Contextual

**Descrição:** O relatório misturou conceitos ou exames diferentes ao justificar uma sugestão, demonstrando falta de precisão clínica ou contextual. Isso ocorreu ao sugerir otimização de um procedimento (endoscopia nasal) e justificar com evidência de outro (TC de seios da face).

**Severidade:** alta
**Frequência:** 1

**Exemplos:**
- Otimizar indicação de endoscopia nasal (justificado com TC de seios da face)

---

### Padrão: Sugestões Fora do Escopo Funcional

**Descrição:** O relatório sugeriu melhorias que dependem de funcionalidades que o sistema de destino (Daktus Studio) não possui, ignorando as restrições técnicas da plataforma.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Adicionar tooltips explicativos em perguntas complexas (Comentário: 'não temos essa funcionalidade no daktus studio.')

---

### Padrão: Sugestões Fora do Contexto Clínico do Protocolo

**Descrição:** O relatório gerou sugestões que, embora clinicamente válidas, não se encaixam no objetivo ou escopo definido para o protocolo específico (ex: um protocolo de triagem não deve abordar manejo de neoplasias).

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Incluir verificação de suspeita de neoplasias (Comentário: 'não é o contexto do protocolo.')

---


## Métricas - 2025-12-04 23:20

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251204-009

### Breakdown de Sugestões

- **Total geradas:** 12
- **Revisadas:** 12
- **Relevantes:** 5 (41.7%)
- **Irrelevantes:** 7 (58.3%)

### Distribuição por Prioridade

- **Alta:** 5
- **Média:** 4
- **Baixa:** 3

**Taxa de Rejeição (Baixa Prioridade):** 100.0%

### Avaliação de Qualidade

**Nota:** 7/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 58.3%
- **Taxa de Rejeição Acumulada:** 39.8%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 12

### Padrões de Rejeição Detectados

- **low_priority_rejection:** 3 ocorrências
- **Falta de Especificidade Técnica:** 2 ocorrências
- **Inconsistência Terminológica/Contextual:** 1 ocorrências
- **Sugestões Fora do Escopo Funcional:** 1 ocorrências
- **Sugestões Fora do Contexto Clínico do Protocolo:** 1 ocorrências

**Categoria Dominante:** low_priority_rejection

---


## Feedback - 2025-12-05 00:00

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-4.1-fast

**Estatísticas:**
- Total revisado: 20
- Relevantes: 12
- Irrelevantes: 8

**Avaliação:** 9/10

### Sugestões Rejeitadas (com comentários)

- **sug_005:** a lógica de exclusive e preselected funciona perfeitamente.
- **sug_014:** aumentam complexidade com baixo retorno em eficiência
- **sug_018:** tooltips não são necessários de serem implementados.
- **sug_004:** a condição atual está correta.
- **sug_019:** a critério médico.
- **sug_008:** resultado de exames é condicional de exames_avaliacao = True. está correta.
- **sug_001:** não há necessidade de avaliar critérios de exclusão diretamente via protocolo. partimos do ponto que, no ambulatorio de otorrino, não chegarão os critérios de exclusão e, se chegarem, o especialista conduz de forma mais eficiente.
- **sug_020:** mais uma vez, não há que investigar diretamente os critérios de exclusão.


---

## Feedback - 2025-12-05 00:00

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-4.1-fast

**Estatísticas:**
- Total revisado: 20
- Relevantes: 12
- Irrelevantes: 8

**Avaliação:** 9/10

### Sugestões Rejeitadas (com comentários)

- **sug_005:** a lógica de exclusive e preselected funciona perfeitamente.
- **sug_014:** aumentam complexidade com baixo retorno em eficiência
- **sug_018:** tooltips não são necessários de serem implementados.
- **sug_004:** a condição atual está correta.
- **sug_019:** a critério médico.
- **sug_008:** resultado de exames é condicional de exames_avaliacao = True. está correta.
- **sug_001:** não há necessidade de avaliar critérios de exclusão diretamente via protocolo. partimos do ponto que, no ambulatorio de otorrino, não chegarão os critérios de exclusão e, se chegarem, o especialista conduz de forma mais eficiente.
- **sug_020:** mais uma vez, não há que investigar diretamente os critérios de exclusão.


---

## Insight LLM - 2025-12-05 00:00

**Análise:**
O relatório gerado pelo modelo x-ai/grok-4.1-fast demonstrou uma boa cobertura de categorias (20 sugestões), mas falhou em calibrar a relevância das sugestões para o contexto clínico específico. O usuário valoriza a estabilidade e a correção da lógica existente ('a condição atual está correta') e rejeita otimizações que introduzem complexidade desnecessária. A alta taxa de relevância (12/20) em Segurança (8 sugestões) sugere que o modelo acertou ao focar em prevenção de erros e lacunas clínicas (e.g., gestação, contraindicações), mas errou ao tentar refinar processos já funcionais (Eficiência e Economia).

**Recomendações:**
Melhorias específicas para análises futuras:
1. **Priorização de Segurança:** Manter a alta prioridade em sugestões de 'Segurança', pois estas tiveram alta aceitação.
2. **Validação de Status Quo:** Adicionar uma etapa de inferência para determinar se a lógica atual é 'Correta e Estável' ou 'Incorreta/Ambígua'. Sugestões de Eficiência só devem ser geradas se a lógica for classificada como 'Incorreta/Ambígua'.
3. **Filtro de Complexidade:** Implementar um filtro que descarte sugestões de Usabilidade que não impactam diretamente a segurança ou o diagnóstico (e.g., tooltips, ícones), focando apenas em clareza de labels e inclusão de scores clínicos essenciais.

---

## Aprendizados - 2025-12-05 00:00

### Padrão: Rejeição de Otimização de Lógica Existente

**Descrição:** O modelo sugeriu otimizações ou condicionais mais restritivas (Eficiência e Economia) em áreas onde o usuário afirma que a lógica atual já está correta e funcional. Isso indica que o modelo falhou em validar a robustez da implementação existente antes de sugerir uma alternativa.

**Severidade:** alta
**Frequência:** 4

**Exemplos:**
- Otimizar condicionais para exames pediátricos
- Condicionar TC seios apenas refratários

---

### Padrão: Rejeição de Usabilidade de Baixo Impacto Clínico

**Descrição:** Sugestões focadas em melhorias visuais ou de usabilidade (tooltips, ícones) foram explicitamente rejeitadas pelo usuário, que as considerou como 'aumentam complexidade com baixo retorno'. Em um ambiente clínico, a prioridade é a clareza e a funcionalidade, não o aprimoramento estético ou de conveniência menor.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Adicionar ícones/tooltips em sintomas

---

### Padrão: Sensibilidade Extrema à Complexidade vs. Retorno

**Descrição:** O padrão mais profundo é a aversão do usuário a qualquer sugestão que aumente a complexidade de manutenção ou a carga cognitiva sem um ganho significativo em segurança ou eficiência operacional. As 8 sugestões irrelevantes provavelmente caíram neste critério, indicando que o modelo superestimou o valor de pequenas otimizações.

**Severidade:** alta
**Frequência:** 8

**Exemplos:**
- Padronizar posologias com playbook exato
- Priorizar budesonida irrigação só refratária

---


## Métricas - 2025-12-05 00:00

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251204-010

### Breakdown de Sugestões

- **Total geradas:** 20
- **Revisadas:** 20
- **Relevantes:** 12 (60.0%)
- **Irrelevantes:** 8 (40.0%)

### Distribuição por Prioridade

- **Alta:** 6
- **Média:** 10
- **Baixa:** 4

**Taxa de Rejeição (Baixa Prioridade):** 75.0%

### Avaliação de Qualidade

**Nota:** 9/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 40.0%
- **Taxa de Rejeição Acumulada:** 39.8%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 14

### Padrões de Rejeição Detectados

- **Sensibilidade Extrema à Complexidade vs. Retorno:** 8 ocorrências
- **Rejeição de Otimização de Lógica Existente:** 4 ocorrências
- **Rejeição de Usabilidade de Baixo Impacto Clínico:** 1 ocorrências

**Categoria Dominante:** Sensibilidade Extrema à Complexidade vs. Retorno

---


## Feedback - 2025-12-05 00:53

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-4.1-fast

**Estatísticas:**
- Total revisado: 10
- Relevantes: 8
- Irrelevantes: 2

**Avaliação:** 10/10

### Sugestões Rejeitadas (com comentários)

- **sug_005:** a lógica de exclusivo e preselected funciona corretamente.
- **sug_001:** não é necessário investigar critérios de exclusão presentes no palybook, pois apesar de fazer sentido clínico, não é prático aumentar o protocolo com perguntas que fogem do escopo do protocolo (o médico decidirá em qual fluxo o paciente dele entrará).


---

## Feedback - 2025-12-05 00:53

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Modelo:** x-ai/grok-4.1-fast

**Estatísticas:**
- Total revisado: 10
- Relevantes: 8
- Irrelevantes: 2

**Avaliação:** 10/10

### Sugestões Rejeitadas (com comentários)

- **sug_005:** a lógica de exclusivo e preselected funciona corretamente.
- **sug_001:** não é necessário investigar critérios de exclusão presentes no palybook, pois apesar de fazer sentido clínico, não é prático aumentar o protocolo com perguntas que fogem do escopo do protocolo (o médico decidirá em qual fluxo o paciente dele entrará).


---

## Insight LLM - 2025-12-05 00:54

**Análise:**
O feedback do usuário revela uma alta taxa de aceitação (80% de relevância), indicando que a análise do modelo foi, em grande parte, bem-sucedida. As duas sugestões irrelevantes caíram nas categorias de 'Segurança' e 'Usabilidade'. O principal ponto de divergência não foi a validade clínica das sugestões, mas sim a praticidade e o escopo do protocolo. O usuário explicitamente rejeitou a ideia de adicionar etapas que fogem do escopo do protocolo (critérios de exclusão) e confirmou que a lógica de implementação (exclusivo/preselected) já estava correta. Isso sugere que o modelo precisa refinar sua compreensão sobre o limite prático de intervenção em um protocolo já estabelecido (o 'playbook').

**Recomendações:**
Ajustar o foco da análise para priorizar a praticidade e o escopo do protocolo (playbook). Especificamente:
1. **Praticidade vs. Perfeição Clínica:** Ao sugerir melhorias de 'segurança' ou 'escopo', o modelo deve ponderar se a nova etapa adiciona complexidade que o médico já gerencia fora do sistema. Sugestões que adicionam perguntas que 'fogem do escopo' devem ser evitadas.
2. **Validação de Lógica Existente:** Evitar sugerir mudanças em lógicas de UI/UX (como 'exclusivo' ou 'preselected') a menos que haja um erro claro de usabilidade ou um conflito clínico. Assumir que a lógica de implementação do sistema está correta, a menos que o contrário seja evidente.
3. **Reforçar Otimização:** Continuar priorizando sugestões de 'eficiência' e 'economia' que garantam o uso racional de recursos, pois estas tiveram alta aceitação.

---

## Aprendizados - 2025-12-05 00:54

### Padrão: Over-engineering de Segurança/Escopo

**Descrição:** O modelo sugeriu melhorias de segurança/escopo que, embora clinicamente válidas (como verificar critérios de exclusão no início), foram consideradas impraticáveis ou fora do escopo prático do protocolo pelo usuário, adicionando complexidade desnecessária.

**Severidade:** media
**Frequência:** 1

**Exemplos:**
- Adicionar verificação de critérios de exclusão no início

---

### Padrão: Foco Excessivo em Detalhes de Implementação (Lógica)

**Descrição:** O modelo pode ter sugerido correções ou melhorias em lógicas de interface (como 'exclusivo' e 'preselected') que já estavam funcionando corretamente ou que o usuário considerou que não precisavam de intervenção.

**Severidade:** baixa
**Frequência:** 1

**Exemplos:**
- Simplificar multiChoice de sintomas nasossinusais removendo 'nenhum' exclusivo

---

### Padrão: Alta Relevância em Otimização Clínica e Econômica

**Descrição:** A maioria das sugestões de otimização clínica (eficiência) e economia foram consideradas relevantes, indicando que o modelo acertou ao focar em critérios de uso racional de medicamentos e exames.

**Severidade:** alta
**Frequência:** 3

**Exemplos:**
- Condicionar escala Epworth apenas se sintomas sono + risco
- Otimizar condutas medicamentosas para ABRS com critérios exatos
- Limitar prednisona a refratários com pólipos/anosmia confirmados

---


## Métricas - 2025-12-05 00:53

**Protocolo:** amil_ficha_orl_v1.0.0_11-11-2025-1643
**Sessão:** fb-20251205-001

### Breakdown de Sugestões

- **Total geradas:** 10
- **Revisadas:** 10
- **Relevantes:** 8 (80.0%)
- **Irrelevantes:** 2 (20.0%)

### Distribuição por Prioridade

- **Alta:** 5
- **Média:** 3
- **Baixa:** 2

**Taxa de Rejeição (Baixa Prioridade):** 0.0%

### Avaliação de Qualidade

**Nota:** 10/10

### Tendência de Melhoria

- **Taxa de Rejeição Atual:** 20.0%
- **Taxa de Rejeição Acumulada:** 37.4%
- **Mudança vs Sessão Anterior:** [PIORA] 0.0%
- **Sessões até agora:** 16

### Padrões de Rejeição Detectados

- **Alta Relevância em Otimização Clínica e Econômica:** 3 ocorrências
- **Over-engineering de Segurança/Escopo:** 1 ocorrências
- **Foco Excessivo em Detalhes de Implementação (Lógica):** 1 ocorrências

**Categoria Dominante:** Alta Relevância em Otimização Clínica e Econômica

---

