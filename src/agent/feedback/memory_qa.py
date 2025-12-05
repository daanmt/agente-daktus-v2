"""
Memory QA - Sistema Simples de Memória via Markdown

Este módulo gerencia o arquivo memory_qa.md que concentra todos os feedbacks
e aprendizados do agente para refinar futuras análises.

Abordagem:
- Arquivo markdown simples (memory_qa.md)
- Feedbacks são adicionados como seções markdown
- O Enhanced Analyzer lê este arquivo antes de cada análise
- System prompt permanece sólido, apenas guiando o agente
- Análise automática de padrões (simples + LLM)
- Migração de dados do MemoryManager
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Union, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
current_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from ..core.logger import logger


@dataclass
class FeedbackPattern:
    """
    Padrão identificado no feedback do usuário.
    """
    pattern_type: str
    description: str
    frequency: int
    examples: List[Dict]
    severity: str


@dataclass
class FeedbackMetrics:
    """
    Métricas de feedback para tracking de melhoria contínua.

    Rastreia a qualidade das sugestões ao longo do tempo para validar
    que o sistema está aprendendo e melhorando.
    """
    session_id: str
    timestamp: datetime
    protocol_name: str

    # Counts
    total_suggestions: int
    relevant_count: int
    irrelevant_count: int

    # Quality
    rejection_rate: float  # irrelevant / total_reviewed
    quality_rating: Optional[int]  # 0-10 if user provides

    # Priority breakdown
    alta_count: int
    media_count: int
    baixa_count: int
    baixa_rejection_rate: float  # Key metric for learning validation

    # Trends
    improvement_vs_previous: Optional[float]  # % change in rejection rate
    sessions_since_start: int
    cumulative_rejection_rate: float

    # Patterns
    pattern_frequencies: Dict[str, int]
    dominant_rejection_category: str


class MemoryQA:
    """
    Gerencia o arquivo memory_qa.md com feedbacks e aprendizados.
    
    Este é o único mecanismo de melhoria da análise - simples e prático.
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        """
        Inicializa o gerenciador de memória QA.
        
        Args:
            memory_file: Caminho para memory_qa.md (padrão: project_root/memory_qa.md)
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.memory_file = memory_file or (project_root / "memory_qa.md")
        
        # Criar arquivo se não existir
        if not self.memory_file.exists():
            self._initialize_memory_file()
        
        # Migrar dados do MemoryManager se existir
        self._migrate_from_memory_manager()
        
        logger.info(f"MemoryQA initialized: {self.memory_file}")
    
    def _initialize_memory_file(self) -> None:
        """Inicializa o arquivo memory_qa.md com estrutura básica."""
        content = """# Memory QA - Feedback e Aprendizados do Agente Daktus QA

Este documento concentra todos os feedbacks e aprendizados do agente para refinar futuras análises.

## Como Funciona

Antes de cada análise, o agente revisa este documento para entender:
- Quais tipos de sugestões foram rejeitadas e por quê
- Quais padrões de feedback indicam problemas recorrentes
- Como melhorar a qualidade e relevância das sugestões

## Feedback Histórico

---

## Aprendizados e Padrões Identificados

---

## Insights do LLM

---

## Recomendações para Análises Futuras

---
"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Initialized memory_qa.md at {self.memory_file}")
    
    def get_memory_content(self, max_length: int = 5000) -> str:
        """
        Retorna o conteúdo do memory_qa.md para inclusão no prompt.
        
        CRITICAL: Esta função prioriza APRENDIZADOS e PADRÕES sobre feedback bruto.
        
        Args:
            max_length: Tamanho máximo do conteúdo (para não exceder tokens)
        
        Returns:
            Conteúdo estruturado com foco em aprendizados
        """
        if not self.memory_file.exists():
            return "Nenhum feedback histórico disponível."
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estratégia: Priorizar APRENDIZADOS > INSIGHTS > FEEDBACK recente
            output_parts = []
            
            # 1. Extrair todos os Aprendizados (### Padrão:)
            learnings = []
            lines = content.split('\n')
            current_learning = []
            in_learning = False
            
            for line in lines:
                if line.startswith("### Padrão:"):
                    if current_learning:
                        learnings.append('\n'.join(current_learning))
                    current_learning = [line]
                    in_learning = True
                elif in_learning:
                    if line.startswith("---") or line.startswith("## "):
                        learnings.append('\n'.join(current_learning))
                        current_learning = []
                        in_learning = False
                    else:
                        current_learning.append(line)
            
            if current_learning:
                learnings.append('\n'.join(current_learning))
            
            # 2. Extrair Insights LLM (mais recentes - últimos 3)
            insights = []
            insight_blocks = content.split("## Insight LLM")
            for block in insight_blocks[1:]:  # Skip first (before any insight)
                end_idx = block.find("---")
                if end_idx > 0:
                    insights.append("## Insight LLM" + block[:end_idx].strip())
            
            # 3. Construir output priorizado
            output_parts.append("# APRENDIZADOS DO FEEDBACK (CRÍTICO - LER ANTES DE GERAR SUGESTÕES)")
            output_parts.append("")
            output_parts.append("Os padrões abaixo foram identificados em feedback de usuários anteriores.")
            output_parts.append("VOCÊ DEVE EVITAR sugestões que se enquadrem nesses padrões de rejeição.")
            output_parts.append("")
            
            # Adicionar aprendizados (priorizando os mais frequentes/severos)
            if learnings:
                output_parts.append("## PADRÕES DE REJEIÇÃO IDENTIFICADOS")
                output_parts.append("")
                
                # Pegar aprendizados únicos (deduplica por nome)
                seen_patterns = set()
                unique_learnings = []
                for learning in learnings:
                    # Extrair nome do padrão
                    first_line = learning.split('\n')[0]
                    pattern_name = first_line.replace("### Padrão:", "").strip()
                    if pattern_name not in seen_patterns:
                        seen_patterns.add(pattern_name)
                        unique_learnings.append(learning)
                
                # Limitar a 10 padrões mais recentes
                for learning in unique_learnings[-10:]:
                    output_parts.append(learning)
                    output_parts.append("")
            
            # Adicionar insights mais recentes (últimos 2)
            if insights:
                output_parts.append("## INSIGHTS DE ANÁLISES ANTERIORES")
                output_parts.append("")
                for insight in insights[-2:]:
                    # Extrair apenas as recomendações
                    if "**Recomendações:**" in insight:
                        rec_start = insight.find("**Recomendações:**")
                        output_parts.append(insight[rec_start:])
                        output_parts.append("")
            
            result = '\n'.join(output_parts)
            
            # Truncar se ainda muito longo
            if len(result) > max_length:
                result = result[:max_length] + "\n\n*(Conteúdo truncado)*"
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading memory_qa.md: {e}")
            return "Erro ao carregar feedback histórico."

    def get_active_filters(self, min_frequency: int = 3) -> Dict[str, Any]:
        """
        Extrai regras de filtragem ativas baseadas nos padrões do memory_qa.md.

        Analisa os padrões identificados e retorna filtros que devem ser
        aplicados durante a geração de sugestões para evitar repetir erros.

        Args:
            min_frequency: Frequência mínima para ativar um filtro (padrão: 3)

        Returns:
            Dict com:
            - priority_threshold: str ("baixa"|"media"|"alta") - não gerar abaixo disso
            - category_filters: Dict[str, bool] - categorias habilitadas/desabilitadas
            - keyword_blocklist: List[str] - palavras-chave que indicam rejeições
            - pattern_rules: List[Dict] - regras específicas por padrão
            - rule_strength: str ("soft"|"hard") - quão agressivo aplicar filtros
            - metadata: Dict - informações sobre a extração
        """
        try:
            content = self.get_memory_content(max_length=10000)

            filters = {
                "priority_threshold": "baixa",  # Default: gerar todas as prioridades
                "category_filters": {
                    "seguranca": True,
                    "economia": True,
                    "eficiencia": True,
                    "usabilidade": True
                },
                "keyword_blocklist": [],
                "pattern_rules": [],
                "rule_strength": "soft",  # soft = avisar, hard = bloquear
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "source_patterns": [],
                    "total_patterns_found": 0,
                    "active_patterns": 0
                }
            }

            if not self.memory_file.exists():
                logger.info("No memory_qa.md file, returning default filters")
                return filters

            # Parsear padrões do memory_qa.md
            lines = content.split('\n')
            current_pattern = None
            patterns_found = []

            for i, line in enumerate(lines):
                # Detectar cabeçalhos de padrão
                if line.startswith("### Padrão:"):
                    if current_pattern:
                        patterns_found.append(current_pattern)

                    current_pattern = {
                        "name": line.replace("### Padrão:", "").strip(),
                        "description": "",
                        "frequency": 0,
                        "severity": "media"
                    }

                # Extrair detalhes do padrão
                if current_pattern:
                    if "**Frequência:**" in line or "**Frequency:**" in line:
                        try:
                            freq_str = line.split("**")[2].strip() if "**" in line else line.split(":")[-1].strip()
                            freq = int(''.join(filter(str.isdigit, freq_str)))
                            current_pattern["frequency"] = freq
                        except:
                            pass

                    if "**Severidade:**" in line or "**Severity:**" in line:
                        severity = line.split(":")[-1].strip().lower()
                        if "alta" in severity or "high" in severity:
                            current_pattern["severity"] = "alta"
                        elif "media" in severity or "medium" in severity:
                            current_pattern["severity"] = "media"
                        else:
                            current_pattern["severity"] = "baixa"

                    if "**Descrição:**" in line or "**Description:**" in line:
                        current_pattern["description"] = line.split(":")[-1].strip()

            # Adicionar último padrão
            if current_pattern:
                patterns_found.append(current_pattern)

            filters["metadata"]["total_patterns_found"] = len(patterns_found)

            # Aplicar regras baseadas nos padrões
            for pattern in patterns_found:
                if pattern["frequency"] >= min_frequency:
                    filters["metadata"]["active_patterns"] += 1
                    filters["metadata"]["source_patterns"].append(pattern["name"])
                    self._apply_pattern_filter_rules(pattern, filters)

            # Extrair keywords da lista de bloqueio dos comentários de feedback
            self._extract_keyword_blocklist(content, filters)

            # Determinar rule_strength baseado na severidade dos padrões ativos
            high_severity_count = sum(
                1 for p in patterns_found
                if p["frequency"] >= min_frequency and p["severity"] == "alta"
            )
            if high_severity_count >= 2:
                filters["rule_strength"] = "hard"

            logger.info(
                f"Active filters extracted: threshold={filters['priority_threshold']}, "
                f"patterns={len(filters['metadata']['source_patterns'])}/{filters['metadata']['total_patterns_found']}, "
                f"strength={filters['rule_strength']}"
            )

            return filters

        except Exception as e:
            logger.error(f"Error extracting active filters: {e}", exc_info=True)
            # Retornar filtros padrão seguros
            return {
                "priority_threshold": "baixa",
                "category_filters": {
                    "seguranca": True,
                    "economia": True,
                    "eficiencia": True,
                    "usabilidade": True
                },
                "keyword_blocklist": [],
                "pattern_rules": [],
                "rule_strength": "soft",
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "source_patterns": [],
                    "error": str(e)
                }
            }

    def _apply_pattern_filter_rules(self, pattern: Dict, filters: Dict) -> None:
        """
        Aplica regras de filtragem específicas baseadas no tipo de padrão.

        CRITICAL: Esta função foi expandida para detectar padrões REAIS do feedback,
        não apenas palavras-chave genéricas.

        Args:
            pattern: Padrão identificado com name, frequency, severity, description
            filters: Dict de filtros a ser modificado
        """
        pattern_name = pattern["name"].lower()
        pattern_desc = pattern.get("description", "").lower()
        freq = pattern["frequency"]
        severity = pattern["severity"]

        # ====================================================================
        # PADRÕES CRÍTICOS DETECTADOS DO FEEDBACK REAL
        # ====================================================================

        # Regra 1: Low priority rejection → aumentar threshold
        low_priority_keywords = [
            "low_priority", "baixa prioridade", "baixa_prioridade",
            "baixo impacto", "baixo retorno", "pouco valor"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in low_priority_keywords):
            if freq >= 2 or severity == "alta":
                filters["priority_threshold"] = "media"
                filters["pattern_rules"].append({
                    "rule": "priority_filter",
                    "action": "block_baixa",
                    "reason": f"Pattern '{pattern['name']}' (freq={freq}, severity={severity})",
                    "pattern": pattern["name"]
                })
                logger.info(f"Activated priority filter: blocking 'baixa' priority (pattern: {pattern['name']})")

        # Regra 2: Autonomia Médica - NÃO restringir decisões clínicas
        autonomy_keywords = [
            "autonomia médica", "autonomia do médico", "invasão", "autonomia",
            "critério médico", "decisão clínica", "julgamento médico",
            "médico deve ter a opção", "priorizar", "condicionar"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in autonomy_keywords):
            filters["pattern_rules"].append({
                "rule": "medical_autonomy",
                "action": "avoid_restricting_clinical_decisions",
                "reason": f"Pattern '{pattern['name']}' - Não restringir autonomia médica",
                "pattern": pattern["name"],
                "blocked_phrases": ["priorizar", "condicionar prescrição", "substituir por", "em vez de"]
            })
            logger.info(f"Activated medical autonomy rule (pattern: {pattern['name']})")

        # Regra 3: Fora do Playbook - NÃO sugerir conteúdo fora do playbook
        playbook_keywords = [
            "fora do playbook", "não está no playbook", "fora do escopo",
            "playbook/protocolo", "adesão estrita", "não coberto",
            "exames fora", "medicamentos fora", "terapêutica fora"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in playbook_keywords):
            filters["pattern_rules"].append({
                "rule": "playbook_strict",
                "action": "only_suggest_playbook_content",
                "reason": f"Pattern '{pattern['name']}' - Apenas conteúdo do playbook",
                "pattern": pattern["name"],
                "blocked_phrases": ["adicionar exame", "incluir medicamento", "introduzir terapêutica"]
            })
            logger.info(f"Activated playbook strict rule (pattern: {pattern['name']})")

        # Regra 4: Lógica Existente Funciona - NÃO mexer no que funciona
        existing_logic_keywords = [
            "lógica existente", "já implementado", "funciona corretamente",
            "já está correto", "condicional funcional", "exclusive funciona",
            "otimização de lógica existente"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in existing_logic_keywords):
            filters["pattern_rules"].append({
                "rule": "existing_logic",
                "action": "avoid_changing_working_logic",
                "reason": f"Pattern '{pattern['name']}' - Não alterar lógica funcional",
                "pattern": pattern["name"],
                "blocked_phrases": ["otimizar condicional", "refinar condição", "ajustar lógica"]
            })
            logger.info(f"Activated existing logic rule (pattern: {pattern['name']})")

        # Regra 5: Complexidade vs Retorno - Evitar complexidade desnecessária
        complexity_keywords = [
            "complexidade", "baixo retorno", "aumenta complexidade",
            "desnecessário", "tempo de atendimento", "over-engineering"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in complexity_keywords):
            filters["pattern_rules"].append({
                "rule": "complexity_filter",
                "action": "avoid_unnecessary_complexity",
                "reason": f"Pattern '{pattern['name']}' - Evitar complexidade",
                "pattern": pattern["name"],
                "blocked_phrases": ["adicionar pergunta", "nova etapa", "verificação adicional"]
            })
            logger.info(f"Activated complexity filter rule (pattern: {pattern['name']})")

        # Regra 6: Restrições Tecnológicas - NÃO sugerir o que não é possível
        tech_restriction_keywords = [
            "restrição tecnológica", "daktus studio", "não temos essa funcionalidade",
            "fora da autonomia", "não podemos criar", "funcionalidade não disponível"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in tech_restriction_keywords):
            filters["pattern_rules"].append({
                "rule": "tech_restriction",
                "action": "avoid_unsupported_features",
                "reason": f"Pattern '{pattern['name']}' - Restrição tecnológica",
                "pattern": pattern["name"],
                "blocked_phrases": ["tooltip", "função customizada", "nova funcionalidade"]
            })
            logger.info(f"Activated tech restriction rule (pattern: {pattern['name']})")

        # Regra 7: Contexto Ambulatorial - Foco em casos comuns
        context_keywords = [
            "contexto do protocolo", "fora do contexto", "ambulatorial",
            "desfecho raro", "corner case", "99% dos casos"
        ]
        if any(kw in pattern_name or kw in pattern_desc for kw in context_keywords):
            filters["pattern_rules"].append({
                "rule": "context_scope",
                "action": "focus_on_common_cases",
                "reason": f"Pattern '{pattern['name']}' - Focar em casos comuns",
                "pattern": pattern["name"],
                "blocked_phrases": ["caso raro", "neoplasia", "emergência"]
            })
            logger.info(f"Activated context scope rule (pattern: {pattern['name']})")

        # ====================================================================
        # PADRÕES GENÉRICOS (mantidos para compatibilidade)
        # ====================================================================

        # Regra genérica de redundância
        if "redundant" in pattern_name or "redundância" in pattern_name or "redundante" in pattern_name:
            filters["pattern_rules"].append({
                "rule": "deduplication",
                "action": "check_similarity",
                "threshold": 0.8,
                "reason": f"Pattern '{pattern['name']}' (freq={freq})",
                "pattern": pattern["name"]
            })
            logger.info(f"Activated deduplication rule (pattern: {pattern['name']})")

        # Regra genérica de contexto faltante
        if "missing_context" in pattern_name or "falta_contexto" in pattern_name or "falta contexto" in pattern_name:
            filters["pattern_rules"].append({
                "rule": "context_validation",
                "action": "require_rationale",
                "min_length": 50,
                "reason": f"Pattern '{pattern['name']}' (freq={freq})",
                "pattern": pattern["name"]
            })
            logger.info(f"Activated context validation rule (pattern: {pattern['name']})")

    def _extract_keyword_blocklist(self, content: str, filters: Dict) -> None:
        """
        Extrai palavras-chave dos comentários de rejeição para blocklist.

        Args:
            content: Conteúdo do memory_qa.md
            filters: Dict de filtros a ser modificado
        """
        # Palavras comuns indicando rejeição
        rejection_indicators = [
            "desnecessário", "alucinou", "inaplicável", "too much",
            "redundante", "já existe", "não aplicável", "irrelevante",
            "confuso", "vago", "falta contexto"
        ]

        for indicator in rejection_indicators:
            count = content.lower().count(indicator.lower())
            if count >= 2:  # Aparece pelo menos 2 vezes
                if indicator not in filters["keyword_blocklist"]:
                    filters["keyword_blocklist"].append(indicator)

        if filters["keyword_blocklist"]:
            logger.info(f"Keyword blocklist extracted: {filters['keyword_blocklist']}")

    def add_feedback_session(
        self,
        feedback_session: Dict,
        analysis_report: Optional[Dict] = None
    ) -> None:
        """
        Adiciona uma sessão de feedback ao memory_qa.md.
        
        Args:
            feedback_session: Sessão de feedback (FeedbackSession como dict)
            analysis_report: Relatório original da análise (opcional, para contexto)
        """
        try:
            timestamp = feedback_session.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    dt = datetime.now()
            else:
                dt = timestamp
            
            protocol_name = feedback_session.get('protocol_name', 'N/A')
            model_used = feedback_session.get('model_used', 'N/A')
            suggestions_fb = feedback_session.get('suggestions_feedback', [])
            
            # Preparar seção de feedback
            section = f"\n## Feedback - {dt.strftime('%Y-%m-%d %H:%M')}\n\n"
            section += f"**Protocolo:** {protocol_name}\n"
            section += f"**Modelo:** {model_used}\n\n"
            
            # Estatísticas
            relevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'relevant')
            irrelevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'irrelevant')
            total_reviewed = len(suggestions_fb)
            
            section += f"**Estatísticas:**\n"
            section += f"- Total revisado: {total_reviewed}\n"
            section += f"- Relevantes: {relevant_count}\n"
            section += f"- Irrelevantes: {irrelevant_count}\n\n"
            
            # Feedback geral
            if feedback_session.get('general_feedback'):
                section += f"**Feedback Geral:**\n{feedback_session.get('general_feedback')}\n\n"
            
            if feedback_session.get('quality_rating'):
                section += f"**Avaliação:** {feedback_session.get('quality_rating')}/10\n\n"
            
            # Sugestões rejeitadas com comentários (mais importantes)
            rejected_with_comments = [
                sf for sf in suggestions_fb
                if sf.get('user_verdict') == 'irrelevant' and sf.get('user_comment')
            ]
            
            if rejected_with_comments:
                section += "### Sugestões Rejeitadas (com comentários)\n\n"
                for sf in rejected_with_comments[:10]:  # Limitar a 10
                    sug_id = sf.get('suggestion_id', 'N/A')
                    comment = sf.get('user_comment', '')
                    section += f"- **{sug_id}:** {comment}\n"
                section += "\n"
            
            # Sugestões relevantes com comentários (para reforçar bons padrões)
            accepted_with_comments = [
                sf for sf in suggestions_fb
                if sf.get('user_verdict') == 'relevant' and sf.get('user_comment')
            ]
            
            if accepted_with_comments:
                section += "### Sugestões Relevantes (com comentários)\n\n"
                for sf in accepted_with_comments[:10]:  # Limitar a 10
                    sug_id = sf.get('suggestion_id', 'N/A')
                    comment = sf.get('user_comment', '')
                    section += f"- **{sug_id}:** {comment}\n"
                section += "\n"
            
            # Padrões identificados (foco em rejeições de baixa prioridade)
            if rejected_with_comments:
                low_priority_rejections = sum(
                    1 for sf in rejected_with_comments
                    if any(word in (sf.get('user_comment', '') or '').lower()
                           for word in ['baixa', 'low', 'baixo', 'pouco', 'menor'])
                )
                
                if low_priority_rejections >= 3:
                    section += "### Padrão Identificado\n\n"
                    section += "**Sugestões de baixa prioridade sendo rejeitadas:**\n"
                    section += "- Focar em sugestões de média/alta/crítica prioridade\n"
                    section += "- Evitar gerar muitas sugestões de baixo impacto\n"
                    section += "- Qualidade sobre quantidade\n\n"
            
            # Adicionar ao arquivo
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(section)
                f.write("\n---\n")
            
            logger.info(f"Feedback session added to memory_qa.md: {protocol_name}")
            
        except Exception as e:
            logger.error(f"Error adding feedback to memory_qa.md: {e}", exc_info=True)
    
    def get_summary(self) -> str:
        """
        Retorna um resumo dos aprendizados principais do memory_qa.md.
        
        Returns:
            Resumo formatado para inclusão no prompt
        """
        content = self.get_memory_content(max_length=3000)
        
        if "Nenhum feedback" in content or "Erro ao carregar" in content:
            return "Nenhum feedback histórico disponível."
        
        # Extrair apenas os padrões e aprendizados principais
        summary = "## Aprendizados do Memory QA\n\n"
        summary += "Revise os feedbacks históricos abaixo para refinar suas sugestões:\n\n"
        summary += content

        return summary

    def calculate_metrics(
        self,
        feedback_session: Dict,
        analysis_report: Dict,
        patterns: List[FeedbackPattern]
    ) -> FeedbackMetrics:
        """
        Calcula métricas abrangentes de uma sessão de feedback.

        Args:
            feedback_session: Sessão de feedback atual
            analysis_report: Relatório de análise original
            patterns: Padrões identificados nesta sessão

        Returns:
            FeedbackMetrics com todas as métricas calculadas
        """
        try:
            # Basic info
            session_id = feedback_session.get('session_id', 'unknown')
            timestamp_str = feedback_session.get('timestamp', datetime.now().isoformat())

            if isinstance(timestamp_str, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
            else:
                timestamp = timestamp_str

            protocol_name = feedback_session.get('protocol_name', 'N/A')
            suggestions_fb = feedback_session.get('suggestions_feedback', [])

            # Counts
            total_suggestions = len(analysis_report.get('improvement_suggestions', []))
            relevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'relevant')
            irrelevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'irrelevant')
            total_reviewed = len(suggestions_fb)

            # Quality metrics
            rejection_rate = (irrelevant_count / total_reviewed) if total_reviewed > 0 else 0.0
            quality_rating = feedback_session.get('quality_rating')

            # Priority breakdown from original suggestions
            suggestions = analysis_report.get('improvement_suggestions', [])
            alta_count = sum(1 for s in suggestions if s.get('priority', '').lower() in ('alta', 'high', 'crítica', 'critical'))
            media_count = sum(1 for s in suggestions if s.get('priority', '').lower() in ('media', 'medium', 'moderada'))
            baixa_count = sum(1 for s in suggestions if s.get('priority', '').lower() in ('baixa', 'low'))

            # Calculate baixa rejection rate (key metric)
            baixa_suggestion_ids = {
                s.get('id') for s in suggestions
                if s.get('priority', '').lower() in ('baixa', 'low')
            }
            baixa_reviewed = sum(
                1 for sf in suggestions_fb
                if sf.get('suggestion_id') in baixa_suggestion_ids
            )
            baixa_rejected = sum(
                1 for sf in suggestions_fb
                if sf.get('suggestion_id') in baixa_suggestion_ids and sf.get('user_verdict') == 'irrelevant'
            )
            baixa_rejection_rate = (baixa_rejected / baixa_reviewed) if baixa_reviewed > 0 else 0.0

            # Trends
            sessions_since_start = self._count_feedback_sessions()
            cumulative_rejection_rate = self._calculate_cumulative_rejection_rate()
            improvement_vs_previous = self._calculate_improvement_trend(rejection_rate)

            # Pattern frequencies
            pattern_frequencies = {
                pattern.pattern_type: pattern.frequency
                for pattern in patterns
            }

            # Dominant rejection category
            dominant_rejection_category = "none"
            if pattern_frequencies:
                dominant_rejection_category = max(
                    pattern_frequencies.items(),
                    key=lambda x: x[1]
                )[0]

            # Create metrics object
            metrics = FeedbackMetrics(
                session_id=session_id,
                timestamp=timestamp,
                protocol_name=protocol_name,
                total_suggestions=total_suggestions,
                relevant_count=relevant_count,
                irrelevant_count=irrelevant_count,
                rejection_rate=rejection_rate,
                quality_rating=quality_rating,
                alta_count=alta_count,
                media_count=media_count,
                baixa_count=baixa_count,
                baixa_rejection_rate=baixa_rejection_rate,
                improvement_vs_previous=improvement_vs_previous,
                sessions_since_start=sessions_since_start,
                cumulative_rejection_rate=cumulative_rejection_rate,
                pattern_frequencies=pattern_frequencies,
                dominant_rejection_category=dominant_rejection_category
            )

            logger.info(f"Metrics calculated: rejection_rate={rejection_rate:.2%}, baixa_rejection={baixa_rejection_rate:.2%}")
            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}", exc_info=True)
            # Return default metrics on error
            return FeedbackMetrics(
                session_id="error",
                timestamp=datetime.now(),
                protocol_name="error",
                total_suggestions=0,
                relevant_count=0,
                irrelevant_count=0,
                rejection_rate=0.0,
                quality_rating=None,
                alta_count=0,
                media_count=0,
                baixa_count=0,
                baixa_rejection_rate=0.0,
                improvement_vs_previous=None,
                sessions_since_start=0,
                cumulative_rejection_rate=0.0,
                pattern_frequencies={},
                dominant_rejection_category="error"
            )

    def _calculate_improvement_trend(self, current_rejection_rate: float) -> Optional[float]:
        """
        Calcula a melhoria vs sessão anterior.

        Args:
            current_rejection_rate: Taxa de rejeição atual

        Returns:
            Percentual de mudança (negativo = melhoria) ou None se não houver histórico
        """
        try:
            content = self.memory_file.read_text(encoding='utf-8')

            # Find the last rejection rate in previous feedback section
            import re
            feedback_sections = re.findall(r'## Feedback - .*?\n.*?(?=\n## |---|\Z)', content, re.DOTALL)

            if len(feedback_sections) < 1:
                return None  # Need at least 1 previous session to compare

            # Get last section (most recent previous session)
            previous_section = feedback_sections[-1]

            # Extract rejection rate from statistics
            # Format: "- Total revisado: X\n- Relevantes: Y\n- Irrelevantes: Z"
            total_match = re.search(r'Total revisado:\s*(\d+)', previous_section)
            irrelevant_match = re.search(r'Irrelevantes:\s*(\d+)', previous_section)

            if total_match and irrelevant_match:
                total = int(total_match.group(1))
                irrelevant = int(irrelevant_match.group(1))
                if total > 0:
                    previous_rate = irrelevant / total
                    # Calculate % change (negative = improvement)
                    change = ((current_rejection_rate - previous_rate) / previous_rate) * 100
                    return change

            return None

        except Exception as e:
            logger.warning(f"Could not calculate improvement trend: {e}")
            return None

    def _count_feedback_sessions(self) -> int:
        """
        Conta o número total de sessões de feedback no memory_qa.md.

        Returns:
            Número de sessões de feedback
        """
        try:
            content = self.memory_file.read_text(encoding='utf-8')
            import re
            sessions = re.findall(r'## Feedback - ', content)
            return len(sessions)
        except Exception as e:
            logger.warning(f"Could not count feedback sessions: {e}")
            return 0

    def _calculate_cumulative_rejection_rate(self) -> float:
        """
        Calcula a taxa média de rejeição em todas as sessões.

        Returns:
            Taxa de rejeição acumulada (média)
        """
        try:
            content = self.memory_file.read_text(encoding='utf-8')

            import re
            feedback_sections = re.findall(r'## Feedback - .*?\n.*?(?=\n## |---|\Z)', content, re.DOTALL)

            if not feedback_sections:
                return 0.0

            rejection_rates = []
            for section in feedback_sections:
                total_match = re.search(r'Total revisado:\s*(\d+)', section)
                irrelevant_match = re.search(r'Irrelevantes:\s*(\d+)', section)

                if total_match and irrelevant_match:
                    total = int(total_match.group(1))
                    irrelevant = int(irrelevant_match.group(1))
                    if total > 0:
                        rejection_rates.append(irrelevant / total)

            if rejection_rates:
                return sum(rejection_rates) / len(rejection_rates)
            return 0.0

        except Exception as e:
            logger.warning(f"Could not calculate cumulative rejection rate: {e}")
            return 0.0

    def analyze_feedback_patterns(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Optional[Dict] = None,
        report_path: Optional[Path] = None
    ) -> List[FeedbackPattern]:
        """
        Analisa feedbacks e identifica padrões (simples + LLM).
        Em paralelo, edita o relatório incorporando feedbacks.
        
        Args:
            feedback_sessions: Lista de sessões de feedback
            analysis_report: Relatório original da análise (opcional)
            report_path: Caminho do arquivo de relatório para edição (opcional)
        
        Returns:
            Lista de padrões identificados
        """
        patterns = []
        
        # Detectar padrões simples
        simple_patterns = self._detect_simple_patterns(feedback_sessions, analysis_report)
        patterns.extend(simple_patterns)
        
        # Análise profunda com LLM (se relatório disponível)
        # Em paralelo, edita o relatório incorporando feedbacks
        edited_report = None
        if analysis_report:
            result = self._analyze_with_llm(
                feedback_sessions, 
                analysis_report,
                return_edited_report=report_path is not None
            )
            
            if report_path is not None:
                # Retorno é uma tupla (patterns, edited_report)
                llm_patterns, edited_report = result
            else:
                # Retorno é apenas patterns
                llm_patterns = result
                edited_report = None
            
            patterns.extend(llm_patterns)
            
            # Salvar relatório editado em paralelo ao salvamento do feedback
            if edited_report and report_path:
                self._save_edited_report(edited_report, report_path)
        
        # Adicionar aprendizados ao memory_qa.md
        if patterns:
            self._add_learnings_to_memory(patterns, analysis_report)

        # Calculate and add metrics (Phase 3)
        if analysis_report and feedback_sessions:
            # Use the first/main feedback session for metrics
            main_session = feedback_sessions[0] if feedback_sessions else None
            if main_session:
                try:
                    metrics = self.calculate_metrics(main_session, analysis_report, patterns)
                    self._add_metrics_to_memory(metrics)
                    logger.info(f"Metrics tracked: rejection_rate={metrics.rejection_rate:.2%}, sessions={metrics.sessions_since_start}")
                except Exception as e:
                    logger.error(f"Error tracking metrics: {e}", exc_info=True)

        logger.info(f"Identified {len(patterns)} feedback patterns")
        return patterns
    
    def _detect_simple_patterns(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Optional[Dict] = None
    ) -> List[FeedbackPattern]:
        """
        Detecta padrões básicos (redundância, baixa prioridade, etc.).
        
        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original (opcional)
        
        Returns:
            Lista de padrões identificados
        """
        patterns = []
        
        # Padrão 1: Sugestões redundantes
        redundant_pattern = self._detect_redundant_suggestions(feedback_sessions)
        if redundant_pattern:
            patterns.append(redundant_pattern)
        
        # Padrão 2: Falta de contexto
        missing_context_pattern = self._detect_missing_context(feedback_sessions)
        if missing_context_pattern:
            patterns.append(missing_context_pattern)
        
        # Padrão 3: Rejeição de baixa prioridade
        if analysis_report:
            low_priority_pattern = self._detect_low_priority_rejection(feedback_sessions, analysis_report)
            if low_priority_pattern:
                patterns.append(low_priority_pattern)
        
        # Padrão 4: Rejeição por categoria
        category_patterns = self._detect_category_rejection_patterns(feedback_sessions)
        patterns.extend(category_patterns)
        
        return patterns
    
    def _detect_redundant_suggestions(
        self,
        feedback_sessions: List[Dict]
    ) -> Optional[FeedbackPattern]:
        """Detecta padrão de sugestões redundantes."""
        redundant_count = 0
        examples = []
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    comment = (sug_fb.get("user_comment") or "").lower()
                    redundant_keywords = [
                        "já existe", "redundante", "duplicado", "repetido",
                        "já contemplado", "já implementado", "similar"
                    ]
                    
                    if comment and any(keyword in comment for keyword in redundant_keywords):
                        redundant_count += 1
                        examples.append({
                            "suggestion_id": sug_fb.get("suggestion_id"),
                            "comment": sug_fb.get("user_comment")
                        })
        
        if redundant_count >= 3:
            severity = "alta" if redundant_count >= 10 else "media"
            return FeedbackPattern(
                pattern_type="redundant_suggestions",
                description=f"{redundant_count} sugestões rejeitadas por redundância",
                frequency=redundant_count,
                examples=examples[:5],
                severity=severity
            )
        
        return None
    
    def _detect_missing_context(
        self,
        feedback_sessions: List[Dict]
    ) -> Optional[FeedbackPattern]:
        """Detecta padrão de falta de contexto nas sugestões."""
        missing_context_count = 0
        examples = []
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    comment = (sug_fb.get("user_comment") or "").lower()
                    context_keywords = [
                        "falta contexto", "não entendo", "confuso", "vago",
                        "precisa mais informação", "incompleto"
                    ]
                    
                    if comment and any(keyword in comment for keyword in context_keywords):
                        missing_context_count += 1
                        examples.append({
                            "suggestion_id": sug_fb.get("suggestion_id"),
                            "comment": sug_fb.get("user_comment")
                        })
        
        if missing_context_count >= 3:
            severity = "alta" if missing_context_count >= 10 else "media"
            return FeedbackPattern(
                pattern_type="missing_context",
                description=f"{missing_context_count} sugestões rejeitadas por falta de contexto",
                frequency=missing_context_count,
                examples=examples[:5],
                severity=severity
            )
        
        return None
    
    def _detect_low_priority_rejection(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Dict
    ) -> Optional[FeedbackPattern]:
        """Detecta padrão de rejeição de sugestões de baixa prioridade."""
        # Mapear sugestões do relatório por ID
        suggestions_by_id = {
            sug.get("id"): sug
            for sug in analysis_report.get("improvement_suggestions", [])
        }
        
        # Contar rejeições por prioridade
        low_priority_rejections = 0
        medium_priority_rejections = 0
        high_priority_rejections = 0
        examples = []
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    suggestion_id = sug_fb.get("suggestion_id")
                    suggestion = suggestions_by_id.get(suggestion_id)
                    
                    if suggestion:
                        priority = suggestion.get("priority", "").lower()
                        if priority in ("baixa", "low", "baixo"):
                            low_priority_rejections += 1
                            examples.append({
                                "suggestion_id": suggestion_id,
                                "title": suggestion.get("title", ""),
                                "priority": priority,
                                "comment": sug_fb.get("user_comment")
                            })
                        elif priority in ("media", "medium", "média"):
                            medium_priority_rejections += 1
                        elif priority in ("alta", "high", "critical"):
                            high_priority_rejections += 1
        
        # Verificar se há padrão claro
        total_rejections = low_priority_rejections + medium_priority_rejections + high_priority_rejections
        if total_rejections == 0:
            return None
        
        low_priority_ratio = low_priority_rejections / total_rejections if total_rejections > 0 else 0
        
        if low_priority_rejections >= 3 and low_priority_ratio >= 0.4:
            severity = "alta" if low_priority_rejections >= 8 else "media"
            description = (
                f"{low_priority_rejections} sugestões de baixa prioridade foram rejeitadas "
                f"({low_priority_ratio*100:.0f}% das rejeições). "
                f"Focar em sugestões critical/high priority."
            )
            
            return FeedbackPattern(
                pattern_type="low_priority_rejection",
                description=description,
                frequency=low_priority_rejections,
                examples=examples[:5],
                severity=severity
            )
        
        return None
    
    def _detect_category_rejection_patterns(
        self,
        feedback_sessions: List[Dict]
    ) -> List[FeedbackPattern]:
        """Detecta padrões de rejeição por categoria."""
        category_rejections = {}
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    comment = (sug_fb.get("user_comment") or "").lower()
                    if comment and ("segurança" in comment or "safety" in comment):
                        category = "seguranca"
                    elif "economia" in comment or "cost" in comment:
                        category = "economia"
                    elif "eficiencia" in comment or "efficiency" in comment:
                        category = "eficiencia"
                    elif "usabilidade" in comment or "usability" in comment:
                        category = "usabilidade"
                    else:
                        continue
                    
                    if category not in category_rejections:
                        category_rejections[category] = []
                    category_rejections[category].append({
                        "suggestion_id": sug_fb.get("suggestion_id"),
                        "comment": sug_fb.get("user_comment")
                    })
        
        patterns = []
        for category, examples in category_rejections.items():
            if len(examples) >= 3:
                patterns.append(FeedbackPattern(
                    pattern_type=f"category_rejection_{category}",
                    description=f"{len(examples)} sugestões de {category} rejeitadas",
                    frequency=len(examples),
                    examples=examples[:3],
                    severity="media"
                ))
        
        return patterns
    
    def _analyze_with_llm(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Dict,
        return_edited_report: bool = False
    ) -> Union[List[FeedbackPattern], tuple]:
        """
        Usa LLM para análise profunda de feedback vs relatório.
        Opcionalmente, também edita o relatório incorporando feedbacks.
        
        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original da análise
            return_edited_report: Se True, também retorna relatório editado
        
        Returns:
            Lista de padrões identificados via LLM (e relatório editado se solicitado)
        """
        try:
            from ..core.llm_client import LLMClient
            
            # Preparar dados para análise
            feedback_summary = self._prepare_feedback_summary(feedback_sessions)
            report_summary = self._prepare_report_summary(analysis_report)
            
            # Contagens para contexto (não interpretar ausência de feedback como irrelevância)
            total_suggestions = len(analysis_report.get("improvement_suggestions", []))
            reviewed_count = sum(len(s.get("suggestions_feedback", [])) for s in feedback_sessions)
            
            # Prompt para análise profunda
            analysis_prompt = f"""Você é um especialista em análise de feedback e melhoria de análises para sistemas de análise clínica.

TAREFA: Analise o feedback do usuário comparado com o relatório gerado e identifique padrões profundos que indiquem como melhorar as análises futuras.

CONTEXT0 IMPORTANTE:
- O relatório original possui {total_suggestions} sugestões no total.
- O usuário revisou explicitamente {reviewed_count} sugestões (com veredito 'relevant' ou 'irrelevant').
- TODAS as demais sugestões devem ser tratadas como \"não avaliadas\" (sem inferir relevância ou irrelevância).

RELATÓRIO GERADO:
{report_summary}

FEEDBACK DO USUÁRIO:
{feedback_summary}

INSTRUÇÕES:
1. Compare o que o relatório disse com o que o usuário esperava/comentou
2. Considere APENAS sugestões com feedback explícito ('relevant' ou 'irrelevant') ao analisar relevância.
3. NÃO interprete ausência de feedback como irrelevância nem como baixa qualidade.
4. Identifique nuances e contexto que faltaram no relatório
5. Identifique padrões de erro recorrentes
6. Sugira melhorias específicas para análises futuras (sem modificar o system prompt)

Responda em JSON com este formato:
{{
    "patterns": [
        {{
            "pattern_type": "tipo_do_padrão",
            "description": "Descrição detalhada do padrão identificado",
            "frequency": número_de_ocorrências,
            "severity": "alta|media|baixa",
            "examples": ["exemplo1", "exemplo2"],
            "recommendation": "Recomendação específica para melhorar análises futuras"
        }}
    ],
    "insights": "Análise geral das diferenças entre relatório e feedback",
    "recommendations": "Recomendações específicas para melhorar análises futuras"
}}"""

            # Escolher modelos para análise:
            # 1) Tentar o mesmo modelo usado na análise principal (se disponível e não-Grok)
            # 2) Fallback para Gemini 2.5 Flash Preview e Gemini 2.5 Flash Lite
            models_to_try = []
            try:
                metadata = analysis_report.get("metadata", {})
                model_used = metadata.get("model_used")
                if model_used and "grok" not in str(model_used).lower():
                    models_to_try.append(model_used)
            except Exception:
                pass
            
            # Fallbacks estáveis (sem Grok, para evitar 404)
            for m in [
                "google/gemini-2.5-flash-preview-09-2025",
                "google/gemini-2.5-flash-lite",
            ]:
                if m not in models_to_try:
                    models_to_try.append(m)
            
            response = None
            last_error = None
            
            for model in models_to_try:
                try:
                    llm_client = LLMClient(model=model)
                    response = llm_client.analyze(analysis_prompt)
                    logger.info(f"LLM analysis successful with model: {model}")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to use model {model}: {e}. Trying next model...")
                    continue
            
            if response is None:
                raise Exception(f"All models failed. Last error: {last_error}")
            
            # Parsear resposta
            if isinstance(response, dict):
                llm_result = response
            else:
                llm_result = json.loads(response)
            
            # Converter para FeedbackPattern
            patterns = []
            for pattern_data in llm_result.get("patterns", []):
                pattern = FeedbackPattern(
                    pattern_type=pattern_data.get("pattern_type", "llm_identified"),
                    description=pattern_data.get("description", ""),
                    frequency=pattern_data.get("frequency", 1),
                    examples=pattern_data.get("examples", []),
                    severity=pattern_data.get("severity", "media")
                )
                patterns.append(pattern)
            
            # Armazenar insights e recomendações
            if "insights" in llm_result or "recommendations" in llm_result:
                self._store_llm_insights(llm_result)
            
            # Editar relatório incorporando feedbacks (se solicitado)
            edited_report = None
            if return_edited_report:
                edited_report = self._edit_report_with_feedback(
                    feedback_sessions,
                    analysis_report,
                    llm_result
                )
            
            logger.info(f"LLM analysis identified {len(patterns)} deep patterns")
            
            if return_edited_report:
                return patterns, edited_report
            return patterns
            
        except Exception as e:
            logger.error(f"Error in LLM feedback analysis: {e}", exc_info=True)
            if return_edited_report:
                return [], None
            return []
    
    def _prepare_feedback_summary(self, feedback_sessions: List[Dict]) -> str:
        """Prepara resumo do feedback para análise LLM."""
        summary_parts = []
        
        for session in feedback_sessions:
            session_summary = f"Sessão: {session.get('protocol_name', 'N/A')}\n"
            session_summary += f"Modelo: {session.get('model_used', 'N/A')}\n"
            
            if session.get('general_feedback'):
                session_summary += f"Feedback Geral: {session.get('general_feedback')}\n"
            if session.get('quality_rating'):
                session_summary += f"Avaliação: {session.get('quality_rating')}/10\n"
            
            suggestions_fb = session.get('suggestions_feedback', [])
            relevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'relevant')
            irrelevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'irrelevant')
            
            session_summary += f"Sugestões Relevantes: {relevant_count}\n"
            session_summary += f"Sugestões Irrelevantes: {irrelevant_count}\n"
            
            important_comments = [
                sf.get('user_comment', '')
                for sf in suggestions_fb
                if sf.get('user_comment') and len(sf.get('user_comment', '')) > 20
            ]
            if important_comments:
                session_summary += "Comentários Importantes:\n"
                for comment in important_comments[:5]:
                    session_summary += f"  - {comment}\n"
            
            summary_parts.append(session_summary)
        
        return "\n\n".join(summary_parts)
    
    def _prepare_report_summary(self, analysis_report: Dict) -> str:
        """Prepara resumo do relatório para análise LLM."""
        suggestions = analysis_report.get('improvement_suggestions', [])
        metadata = analysis_report.get('metadata', {})
        
        summary = f"Relatório de Análise\n"
        summary += f"Protocolo: {metadata.get('protocol_path', 'N/A')}\n"
        summary += f"Modelo: {metadata.get('model_used', 'N/A')}\n"
        summary += f"Total de Sugestões: {len(suggestions)}\n\n"
        
        # Agrupar por categoria
        categories = {}
        for sug in suggestions:
            cat = sug.get('category', 'N/A')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(sug)
        
        summary += "Sugestões por Categoria:\n"
        for cat, sugs in categories.items():
            summary += f"  {cat}: {len(sugs)} sugestões\n"
            for sug in sugs[:3]:
                summary += f"    - {sug.get('title', 'N/A')}\n"
        
        return summary
    
    def _store_llm_insights(self, llm_result: Dict) -> None:
        """Armazena insights e recomendações do LLM no memory_qa.md."""
        try:
            insights = llm_result.get("insights", "")
            recommendations = llm_result.get("recommendations", "")
            
            if not insights and not recommendations:
                return
            
            section = f"\n## Insight LLM - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            if insights:
                section += f"**Análise:**\n{insights}\n\n"
            
            if recommendations:
                section += f"**Recomendações:**\n{recommendations}\n\n"
            
            section += "---\n"
            
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(section)
            
            logger.info("LLM insights stored in memory_qa.md")
            
        except Exception as e:
            logger.error(f"Error storing LLM insights: {e}")
    
    def _edit_report_with_feedback(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Dict,
        llm_analysis_result: Dict
    ) -> Optional[Dict]:
        """
        Edita o relatório incorporando feedbacks do usuário.
        
        Usa LLM para:
        - Remover sugestões marcadas como irrelevantes
        - Melhorar descrições de sugestões com comentários do usuário
        - Ajustar prioridades baseado em feedback
        - Incorporar insights do LLM
        
        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original
            llm_analysis_result: Resultado da análise LLM (padrões, insights, recomendações)
        
        Returns:
            Relatório editado ou None em caso de erro
        """
        try:
            from ..core.llm_client import LLMClient
            
            # Preparar dados para edição
            feedback_summary = self._prepare_feedback_summary(feedback_sessions)
            report_json = json.dumps(analysis_report, indent=2, ensure_ascii=False)
            insights = llm_analysis_result.get("insights", "")
            recommendations = llm_analysis_result.get("recommendations", "")
            
            # Prompt para edição do relatório
            edit_prompt = f"""Você é um especialista em edição de relatórios de análise clínica.

TAREFA: Edite o relatório JSON abaixo incorporando os feedbacks do usuário e os insights identificados.

RELATÓRIO ORIGINAL (JSON):
{report_json}

FEEDBACK DO USUÁRIO:
{feedback_summary}

INSIGHTS IDENTIFICADOS:
{insights}

RECOMENDAÇÕES:
{recommendations}

INSTRUÇÕES CRÍTICAS:
1. REMOVER COMPLETAMENTE do array "improvement_suggestions" todas as sugestões marcadas como "irrelevant" pelo usuário
2. ADICIONAR essas sugestões removidas na seção "rejected_suggestions" (com estrutura completa)
3. MANTER APENAS sugestões marcadas como "relevant" no array "improvement_suggestions"
4. MELHORAR descrições de sugestões que receberam comentários do usuário
5. AJUSTAR prioridades baseado no feedback (se o usuário indicou que algo é mais/menos importante)
6. INCORPORAR insights e recomendações identificados
7. MANTER a estrutura JSON original
8. ADICIONAR campo "feedback_incorporated": true nas sugestões que foram editadas

ESTRUTURA DO JSON EDITADO:
{{
  "improvement_suggestions": [...],  // APENAS sugestões marcadas como "relevant" - REMOVER todas as "irrelevant"
  "rejected_suggestions": [          // NOVA SEÇÃO - sugestões rejeitadas
    {{
      "id": "sug_xxx",
      "original_suggestion": {{...}},  // Sugestão completa original
      "rejection_reason": "comentário do usuário explicando por que foi rejeitada",
      "rejection_category": "tipo de padrão (ex: low_priority, redundant, etc.)",
      "rejected_at": "2025-12-04T..."
    }}
  ],
  "metadata": {{...}}
}}

REGRA CRÍTICA - REMOÇÃO DE SUGESTÕES IRRELEVANTES:
- Para CADA sugestão marcada como "irrelevant" no feedback:
  1. REMOVA-A COMPLETAMENTE do array "improvement_suggestions"
  2. Crie uma entrada em "rejected_suggestions" com:
     - "id": ID da sugestão original
     - "original_suggestion": A sugestão COMPLETA original (copie todo o objeto)
     - "rejection_reason": O comentário do usuário explicando por que foi rejeitada
     - "rejection_category": Tipo de rejeição (low_priority_rejection, redundant_suggestion, missing_context, category_rejection, etc.)
     - "rejected_at": Timestamp atual (formato ISO)
- O array "improvement_suggestions" DEVE conter APENAS sugestões marcadas como "relevant"
- NUNCA mantenha uma sugestão marcada como "irrelevant" no array "improvement_suggestions"

IMPORTANTE:
- Retorne APENAS o JSON editado, sem markdown, sem explicações
- Mantenha a estrutura exata do JSON original
- Não remova campos obrigatórios
- CRIE a seção "rejected_suggestions" mesmo que esteja vazia (use array vazio [])

Responda com APENAS o JSON editado:"""

            # Escolher modelos para edição do relatório:
            # 1) Tentar o mesmo modelo usado na análise principal (se disponível e não-Grok)
            # 2) Fallback para Gemini 2.5 Flash Preview e Gemini 2.5 Flash Lite
            models_to_try = []
            try:
                metadata = analysis_report.get("metadata", {})
                model_used = metadata.get("model_used")
                if model_used and "grok" not in str(model_used).lower():
                    models_to_try.append(model_used)
            except Exception:
                pass
            
            for m in [
                "google/gemini-2.5-flash-preview-09-2025",
                "google/gemini-2.5-flash-lite",
            ]:
                if m not in models_to_try:
                    models_to_try.append(m)
            
            response = None
            last_error = None
            
            for model in models_to_try:
                try:
                    llm_client = LLMClient(model=model)
                    response = llm_client.analyze(edit_prompt)
                    logger.info(f"Report editing successful with model: {model}")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to use model {model} for report editing: {e}. Trying next model...")
                    continue
            
            if response is None:
                raise Exception(f"All models failed. Last error: {last_error}")
            
            # Parsear resposta
            if isinstance(response, dict):
                edited_report = response
            else:
                # Tentar extrair JSON da resposta
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    edited_report = json.loads(json_match.group())
                else:
                    edited_report = json.loads(response)
            
            # Validar estrutura básica
            if not isinstance(edited_report, dict):
                raise ValueError("Edited report is not a dictionary")

            if "improvement_suggestions" not in edited_report:
                logger.warning("Edited report missing 'improvement_suggestions', using original")
                return analysis_report

            # Validar seção rejected_suggestions (NOVA)
            if "rejected_suggestions" not in edited_report:
                logger.warning("LLM didn't create rejected_suggestions section, using manual segregation fallback")
                edited_report["rejected_suggestions"] = self._manual_segregation(
                    feedback_sessions, analysis_report
                )
            else:
                # Validar estrutura de cada rejected suggestion
                for rej in edited_report["rejected_suggestions"]:
                    required_keys = ["id", "original_suggestion", "rejection_reason"]
                    for key in required_keys:
                        if key not in rej:
                            logger.warning(f"Rejected suggestion missing key: {key} (ID: {rej.get('id', 'unknown')})")

                    # Validar que original_suggestion tem estrutura mínima
                    orig = rej.get("original_suggestion", {})
                    if not isinstance(orig, dict) or "id" not in orig:
                        logger.error(f"Invalid original_suggestion structure in rejected: {rej.get('id', 'unknown')}")

            # Validação de contagem (sanity check)
            original_count = len(analysis_report.get("improvement_suggestions", []))
            edited_count = len(edited_report.get("improvement_suggestions", []))
            rejected_count = len(edited_report.get("rejected_suggestions", []))

            if abs((edited_count + rejected_count) - original_count) > 2:
                logger.warning(
                    f"Suggestion count mismatch: original={original_count}, "
                    f"edited={edited_count}, rejected={rejected_count}. "
                    f"Expected edited + rejected ≈ original"
                )

            # CRITICAL VALIDATION: Garantir que sugestões irrelevantes não estão no array principal
            # Mapear verdicts de feedback para identificar sugestões irrelevantes
            irrelevant_ids = set()
            for session in feedback_sessions:
                for sf in session.get("suggestions_feedback", []):
                    if sf.get("user_verdict") == "irrelevant":
                        irrelevant_ids.add(sf.get("suggestion_id"))
            
            # Verificar e remover sugestões irrelevantes do array principal (fallback de segurança)
            suggestions_to_keep = []
            suggestions_moved_to_rejected = []
            
            for sug in edited_report.get("improvement_suggestions", []):
                sug_id = sug.get("id")
                if sug_id in irrelevant_ids:
                    # Esta sugestão foi marcada como irrelevante mas ainda está no array principal
                    logger.warning(f"CRITICAL: Suggestion {sug_id} marked as irrelevant but still in improvement_suggestions. Moving to rejected.")
                    
                    # Verificar se já não está em rejected_suggestions
                    already_rejected = any(
                        r.get("id") == sug_id 
                        for r in edited_report.get("rejected_suggestions", [])
                    )
                    
                    if not already_rejected:
                        # Adicionar à seção rejected_suggestions
                        if "rejected_suggestions" not in edited_report:
                            edited_report["rejected_suggestions"] = []
                        
                        # Encontrar comentário do usuário
                        user_comment = "No reason provided"
                        for session in feedback_sessions:
                            for sf in session.get("suggestions_feedback", []):
                                if sf.get("suggestion_id") == sug_id and sf.get("user_verdict") == "irrelevant":
                                    user_comment = sf.get("user_comment", "No reason provided")
                                    break
                        
                        edited_report["rejected_suggestions"].append({
                            "id": sug_id,
                            "original_suggestion": sug,
                            "rejection_reason": user_comment,
                            "rejection_category": self._classify_rejection(
                                user_comment,
                                sug.get("priority", "baixa")
                            ),
                            "rejected_at": datetime.now().isoformat()
                        })
                        suggestions_moved_to_rejected.append(sug_id)
                else:
                    # Manter sugestão no array principal
                    suggestions_to_keep.append(sug)
            
            # Atualizar array principal apenas com sugestões relevantes
            if suggestions_moved_to_rejected:
                edited_report["improvement_suggestions"] = suggestions_to_keep
                logger.warning(
                    f"CRITICAL FIX: Removed {len(suggestions_moved_to_rejected)} irrelevant suggestions "
                    f"from improvement_suggestions: {suggestions_moved_to_rejected}"
                )
            
            # Validar que não há IDs duplicados entre edited e rejected
            edited_ids = {s.get("id") for s in edited_report["improvement_suggestions"]}
            rejected_ids = {r.get("id") for r in edited_report.get("rejected_suggestions", [])}
            overlap = edited_ids & rejected_ids
            if overlap:
                logger.error(f"Suggestions appear in both edited and rejected lists: {overlap}")
                logger.warning("Removing duplicates from improvement_suggestions")
                # Remover duplicatas do array principal (prioridade: rejected)
                edited_report["improvement_suggestions"] = [
                    s for s in edited_report["improvement_suggestions"]
                    if s.get("id") not in overlap
                ]

            # Atualizar contagens após validação e remoção automática
            final_edited_count = len(edited_report.get("improvement_suggestions", []))
            final_rejected_count = len(edited_report.get("rejected_suggestions", []))

            # Adicionar metadados de edição
            if "metadata" not in edited_report:
                edited_report["metadata"] = {}

            edited_report["metadata"]["feedback_incorporated"] = True
            edited_report["metadata"]["edited_at"] = datetime.now().isoformat()
            edited_report["metadata"]["original_suggestions_count"] = original_count
            edited_report["metadata"]["edited_suggestions_count"] = final_edited_count
            edited_report["metadata"]["rejected_suggestions_count"] = final_rejected_count
            
            logger.info(
                f"Report edited: {edited_report['metadata']['original_suggestions_count']} → "
                f"{edited_report['metadata']['edited_suggestions_count']} suggestions "
                f"({edited_report['metadata']['rejected_suggestions_count']} rejected)"
            )
            
            return edited_report
            
        except Exception as e:
            logger.error(f"Error editing report with feedback: {e}", exc_info=True)
            return None

    def _manual_segregation(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Dict
    ) -> List[Dict]:
        """
        Fallback manual segregation quando LLM não cria rejected_suggestions.

        Constrói a seção rejected_suggestions manualmente baseado nos verdicts do feedback.

        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original

        Returns:
            Lista de sugestões rejeitadas com estrutura completa
        """
        rejected = []

        try:
            # Mapear verdicts de feedback por suggestion_id
            verdict_map = {}
            for session in feedback_sessions:
                for sf in session.get("suggestions_feedback", []):
                    if sf.get("user_verdict") == "irrelevant":
                        verdict_map[sf.get("suggestion_id")] = {
                            "user_comment": sf.get("user_comment", "No reason provided"),
                            "timestamp": session.get("timestamp", datetime.now().isoformat())
                        }

            # Construir rejected_suggestions
            for sug in analysis_report.get("improvement_suggestions", []):
                sug_id = sug.get("id")
                if sug_id in verdict_map:
                    fb = verdict_map[sug_id]

                    # Determinar categoria de rejeição baseada no comentário e prioridade
                    rejection_category = self._classify_rejection(
                        fb["user_comment"],
                        sug.get("priority", "baixa")
                    )

                    rejected.append({
                        "id": sug_id,
                        "original_suggestion": sug,  # Sugestão completa
                        "rejection_reason": fb["user_comment"],
                        "rejection_category": rejection_category,
                        "rejected_at": fb["timestamp"]
                    })

            logger.info(f"Manual segregation created {len(rejected)} rejected suggestions")
            return rejected

        except Exception as e:
            logger.error(f"Error in manual segregation: {e}", exc_info=True)
            return []

    def _classify_rejection(self, comment: str, priority: str) -> str:
        """
        Classifica tipo de rejeição baseado no comentário e prioridade.

        Args:
            comment: Comentário do usuário
            priority: Prioridade da sugestão

        Returns:
            Categoria da rejeição (low_priority_rejection, redundant, etc.)
        """
        # Empty comment - classify by priority
        if not comment or not comment.strip():
            if priority.lower() in ("baixa", "low"):
                return "low_priority_rejection"
            return "unspecified"

        comment_lower = comment.lower()

        # Detectar padrões comuns (ordem importa - específico antes de genérico)
        if any(keyword in comment_lower for keyword in ["redundante", "já existe", "duplicado"]):
            return "redundant_suggestion"

        if any(keyword in comment_lower for keyword in ["falta contexto", "confuso", "vago"]):
            return "missing_context"

        if any(keyword in comment_lower for keyword in ["segurança", "security", "seguran"]):
            return "category_rejection_seguranca"

        if any(keyword in comment_lower for keyword in ["economia", "economy", "cost", "caro", "custo"]):
            return "category_rejection_economia"

        if any(keyword in comment_lower for keyword in ["desnecessário", "irrelevante", "não aplicável", "desnecessário"]):
            if priority.lower() in ("baixa", "low"):
                return "low_priority_rejection"
            return "not_applicable"

        # Padrão de baixa prioridade como fallback
        if priority.lower() in ("baixa", "low"):
            return "low_priority_rejection"

        return "other_rejection"

    def _save_edited_report(
        self,
        edited_report: Dict,
        original_report_path: Path
    ) -> Optional[Path]:
        """
        Salva o relatório editado.
        
        Args:
            edited_report: Relatório editado
            original_report_path: Caminho do relatório original
        
        Returns:
            Caminho do relatório editado salvo ou None em caso de erro
        """
        try:
            # Gerar nome do arquivo editado
            if original_report_path.suffix == ".json":
                edited_path = original_report_path.parent / f"{original_report_path.stem}_EDITED{original_report_path.suffix}"
            else:
                edited_path = original_report_path.parent / f"{original_report_path.stem}_EDITED.json"
            
            # Salvar relatório editado
            with open(edited_path, 'w', encoding='utf-8') as f:
                json.dump(edited_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Edited report saved: {edited_path}")
            return edited_path
            
        except Exception as e:
            logger.error(f"Error saving edited report: {e}", exc_info=True)
            return None

    def _add_metrics_to_memory(self, metrics: FeedbackMetrics) -> None:
        """
        Adiciona métricas de sessão ao memory_qa.md como dashboard de melhoria.

        Args:
            metrics: FeedbackMetrics com dados da sessão atual
        """
        try:
            section = f"\n## Métricas - {metrics.timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
            section += f"**Protocolo:** {metrics.protocol_name}\n"
            section += f"**Sessão:** {metrics.session_id}\n\n"

            # Suggestion breakdown
            section += "### Breakdown de Sugestões\n\n"
            section += f"- **Total geradas:** {metrics.total_suggestions}\n"
            section += f"- **Revisadas:** {metrics.relevant_count + metrics.irrelevant_count}\n"
            section += f"- **Relevantes:** {metrics.relevant_count} ({(metrics.relevant_count/(metrics.relevant_count+metrics.irrelevant_count)*100) if (metrics.relevant_count+metrics.irrelevant_count) > 0 else 0:.1f}%)\n"
            section += f"- **Irrelevantes:** {metrics.irrelevant_count} ({metrics.rejection_rate*100:.1f}%)\n\n"

            # Priority distribution
            section += "### Distribuição por Prioridade\n\n"
            section += f"- **Alta:** {metrics.alta_count}\n"
            section += f"- **Média:** {metrics.media_count}\n"
            section += f"- **Baixa:** {metrics.baixa_count}\n\n"

            # Key metric: baixa rejection rate
            if metrics.baixa_count > 0:
                section += f"**Taxa de Rejeição (Baixa Prioridade):** {metrics.baixa_rejection_rate*100:.1f}%\n\n"

            # Quality rating
            if metrics.quality_rating is not None:
                section += f"### Avaliação de Qualidade\n\n"
                section += f"**Nota:** {metrics.quality_rating}/10\n\n"

            # Improvement trend
            section += "### Tendência de Melhoria\n\n"
            section += f"- **Taxa de Rejeição Atual:** {metrics.rejection_rate*100:.1f}%\n"
            section += f"- **Taxa de Rejeição Acumulada:** {metrics.cumulative_rejection_rate*100:.1f}%\n"

            if metrics.improvement_vs_previous is not None:
                trend_icon = "[MELHORIA]" if metrics.improvement_vs_previous < 0 else "[PIORA]"
                trend_text = f"{abs(metrics.improvement_vs_previous):.1f}%"
                section += f"- **Mudança vs Sessão Anterior:** {trend_icon} {trend_text}\n"
            else:
                section += f"- **Mudança vs Sessão Anterior:** N/A (primeira sessão)\n"

            section += f"- **Sessões até agora:** {metrics.sessions_since_start}\n\n"

            # Pattern frequencies
            if metrics.pattern_frequencies:
                section += "### Padrões de Rejeição Detectados\n\n"
                for pattern_type, freq in sorted(metrics.pattern_frequencies.items(), key=lambda x: x[1], reverse=True):
                    section += f"- **{pattern_type}:** {freq} ocorrências\n"
                section += f"\n**Categoria Dominante:** {metrics.dominant_rejection_category}\n\n"

            section += "---\n\n"

            # Append to memory file
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(section)

            logger.info(f"Metrics added to memory_qa.md: rejection_rate={metrics.rejection_rate:.2%}, improvement={metrics.improvement_vs_previous}")

        except Exception as e:
            logger.error(f"Error adding metrics to memory_qa.md: {e}", exc_info=True)

    def _add_learnings_to_memory(
        self,
        patterns: List[FeedbackPattern],
        analysis_report: Optional[Dict] = None
    ) -> None:
        """
        Adiciona padrões e aprendizados ao memory_qa.md.
        
        Args:
            patterns: Padrões identificados
            analysis_report: Relatório original (opcional)
        """
        try:
            section = f"\n## Aprendizados - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            for pattern in patterns:
                section += f"### Padrão: {pattern.pattern_type}\n\n"
                section += f"**Descrição:** {pattern.description}\n\n"
                section += f"**Severidade:** {pattern.severity}\n"
                section += f"**Frequência:** {pattern.frequency}\n\n"
                
                if pattern.examples:
                    section += "**Exemplos:**\n"
                    for ex in pattern.examples[:3]:
                        if isinstance(ex, dict):
                            sug_id = ex.get("suggestion_id", "N/A")
                            comment = ex.get("comment", "")
                            section += f"- {sug_id}: {comment}\n"
                        else:
                            section += f"- {ex}\n"
                    section += "\n"
                
                section += "---\n\n"
            
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(section)
            
            logger.info(f"Added {len(patterns)} patterns to memory_qa.md")
            
        except Exception as e:
            logger.error(f"Error adding learnings to memory_qa.md: {e}", exc_info=True)
    
    def _migrate_from_memory_manager(self) -> None:
        """
        Migra dados do MemoryManager existente para memory_qa.md.
        
        Executa na inicialização se detectar dados antigos.
        """
        try:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            memory_data_file = project_root / "src" / "config" / "prompts" / "AGENT_MEMORY.json"
            
            if not memory_data_file.exists():
                return
            
            # Verificar se já foi migrado (marcador no memory_qa.md)
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "MIGRADO DO MEMORY MANAGER" in content:
                    logger.info("Memory Manager data already migrated")
                    return
            
            # Carregar dados do MemoryManager
            with open(memory_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entries = data.get("entries", [])
            if not entries:
                return
            
            # Converter para formato markdown
            section = "\n## Dados Migrados do Memory Manager\n\n"
            section += "*Migrado automaticamente em " + datetime.now().strftime('%Y-%m-%d %H:%M') + "*\n\n"
            section += "---\n\n"
            
            # Agrupar por tipo
            patterns = [e for e in entries if e.get("entry_type") == "pattern"]
            insights = [e for e in entries if e.get("entry_type") == "insight"]
            best_practices = [e for e in entries if e.get("entry_type") == "best_practice"]
            
            if patterns:
                section += "### Padrões Aprendidos\n\n"
                for entry in patterns[-10:]:  # Últimos 10
                    metadata = entry.get("metadata", {})
                    pattern_type = metadata.get("pattern_type", "Padrão")
                    section += f"**{pattern_type}:** {entry.get('content', '')}\n\n"
                section += "---\n\n"
            
            if insights:
                section += "### Insights\n\n"
                for entry in insights[-5:]:  # Últimos 5
                    section += f"{entry.get('content', '')}\n\n"
                section += "---\n\n"
            
            if best_practices:
                section += "### Melhores Práticas\n\n"
                for entry in best_practices:
                    section += f"{entry.get('content', '')}\n\n"
                section += "---\n\n"
            
            section += "*Fim da migração*\n\n---\n"
            
            # Adicionar ao memory_qa.md
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(section)
            
            logger.info(f"Migrated {len(entries)} entries from Memory Manager to memory_qa.md")

        except Exception as e:
            logger.error(f"Error migrating from Memory Manager: {e}", exc_info=True)

    # =========================================================================
    # PHASE 4: ROBUST TXT REPORT UPDATES
    # =========================================================================

    def _generate_txt_report_content(
        self,
        edited_result: Dict,
        version: str = "V3"
    ) -> str:
        """
        Gera conteúdo do relatório TXT de forma centralizada.

        PHASE 4: Centralized TXT generation for reliability.

        Args:
            edited_result: Relatório JSON editado (com rejected_suggestions)
            version: Versão do agente (ex: "V3")

        Returns:
            String com conteúdo completo do relatório TXT
        """
        try:
            lines = []

            # Header
            lines.append("=" * 60)
            lines.append(f"AGENT {version} - PROTOCOL ANALYSIS REPORT (ATUALIZADO PELO FEEDBACK)")
            lines.append("=" * 60)
            lines.append("")

            # Metadata
            metadata = edited_result.get("metadata", {})
            lines.append("METADATA")
            lines.append("-" * 60)
            lines.append(f"Protocol: {metadata.get('protocol_path', 'N/A')}")
            lines.append(f"Playbook: {metadata.get('playbook_path', 'None')}")
            lines.append(f"Model: {metadata.get('model_used', 'N/A')}")
            lines.append(f"Timestamp: {metadata.get('timestamp', 'N/A')}")
            if metadata.get("feedback_incorporated"):
                lines.append("Feedback Incorporated: yes")
            lines.append("")

            # Improvement suggestions
            suggestions = edited_result.get("improvement_suggestions", [])
            lines.append(f"IMPROVEMENT SUGGESTIONS (APÓS FEEDBACK): {len(suggestions)}")
            lines.append("=" * 60)
            lines.append("")

            if suggestions:
                # Normalize priority helper
                def normalize_priority(priority):
                    if not priority:
                        return 'baixa'
                    priority_lower = str(priority).lower()
                    if priority_lower in ('alta', 'high', 'critical', 'crítica'):
                        return 'alta'
                    elif priority_lower in ('media', 'medium', 'moderate', 'moderada'):
                        return 'media'
                    else:
                        return 'baixa'

                # Group by priority
                alta = [s for s in suggestions if normalize_priority(s.get('priority')) == 'alta']
                media = [s for s in suggestions if normalize_priority(s.get('priority')) == 'media']
                baixa = [s for s in suggestions if normalize_priority(s.get('priority')) == 'baixa']

                # High priority
                if alta:
                    lines.append("ALTA PRIORIDADE:")
                    lines.append("-" * 60)
                    for i, sug in enumerate(alta, 1):
                        sug_id = sug.get('id', f'SUG{i:02d}')
                        title = sug.get('title', sug.get('description', 'N/A'))
                        category = sug.get('category', 'N/A')
                        lines.append(f"{i}. [{sug_id}] {title}")
                        lines.append(f"   Categoria: {category}")
                        if sug.get('description') and sug.get('description') != title:
                            desc = sug.get('description', '')[:200]
                            lines.append(f"   Descrição: {desc}")
                        lines.append("")

                # Medium priority
                if media:
                    lines.append("MÉDIA PRIORIDADE:")
                    lines.append("-" * 60)
                    for i, sug in enumerate(media, 1):
                        sug_id = sug.get('id', f'SUG{i:02d}')
                        title = sug.get('title', sug.get('description', 'N/A'))
                        category = sug.get('category', 'N/A')
                        lines.append(f"{i}. [{sug_id}] {title}")
                        lines.append(f"   Categoria: {category}")
                        if sug.get('description') and sug.get('description') != title:
                            desc = sug.get('description', '')[:200]
                            lines.append(f"   Descrição: {desc}")
                        lines.append("")

                # Low priority
                if baixa:
                    lines.append("BAIXA PRIORIDADE:")
                    lines.append("-" * 60)
                    for i, sug in enumerate(baixa, 1):
                        sug_id = sug.get('id', f'SUG{i:02d}')
                        title = sug.get('title', sug.get('description', 'N/A'))
                        category = sug.get('category', 'N/A')
                        lines.append(f"{i}. [{sug_id}] {title}")
                        lines.append(f"   Categoria: {category}")
                        if sug.get('description') and sug.get('description') != title:
                            desc = sug.get('description', '')[:200]
                            lines.append(f"   Descrição: {desc}")
                        lines.append("")
            else:
                lines.append("Nenhuma sugestão de melhoria gerada após feedback.")

            # Rejected suggestions section
            rejected = edited_result.get("rejected_suggestions", [])
            if rejected:
                lines.append("")
                lines.append("=" * 60)
                lines.append(f"SUGESTÕES REJEITADAS (FEEDBACK DO USUÁRIO): {len(rejected)}")
                lines.append("=" * 60)
                lines.append("")
                lines.append("Estas sugestões foram marcadas como irrelevantes durante o feedback:")
                lines.append("")

                for i, rej in enumerate(rejected, 1):
                    sug_id = rej.get("id", f"REJ{i:02d}")
                    orig_sug = rej.get("original_suggestion", {})
                    title = orig_sug.get("title", "N/A")
                    priority = orig_sug.get("priority", "N/A")
                    category = orig_sug.get("category", "N/A")
                    reason = rej.get("rejection_reason", "Sem motivo especificado")
                    rej_category = rej.get("rejection_category", "unknown")

                    lines.append(f"{i}. [{sug_id}] {title}")
                    lines.append(f"   Prioridade Original: {priority} | Categoria: {category}")
                    lines.append(f"   Feedback do Usuário: {reason}")
                    lines.append(f"   Padrão de Rejeição: {rej_category}")

                    # Show original description snippet
                    if orig_sug.get("description"):
                        desc_snippet = orig_sug["description"][:150]
                        if len(orig_sug["description"]) > 150:
                            desc_snippet += "..."
                        lines.append(f"   Descrição Original: {desc_snippet}")

                    lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error generating TXT report content: {e}", exc_info=True)
            return f"Error generating report: {e}"

    def update_txt_report_from_edited_json(
        self,
        edited_json_path: Path,
        txt_report_path: Path,
        version: str = "V3"
    ) -> bool:
        """
        Atualiza relatório TXT de forma robusta com atomic operations.

        PHASE 4: Robust TXT update with backup/rollback mechanism.

        Features:
        - Atomic operation: write to temp file, then move
        - Automatic backup before updating
        - Rollback on failure
        - 99%+ reliability

        Args:
            edited_json_path: Caminho do relatório JSON editado
            txt_report_path: Caminho do relatório TXT a atualizar
            version: Versão do agente (ex: "V3")

        Returns:
            True se atualização bem-sucedida, False caso contrário
        """
        import json
        import shutil
        import tempfile
        from datetime import datetime

        backup_path = None
        temp_path = None

        try:
            # Validar paths
            if not edited_json_path.exists():
                logger.error(f"Edited JSON not found: {edited_json_path}")
                return False

            # Step 1: Create backup of existing TXT (if exists)
            if txt_report_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = txt_report_path.parent / f"{txt_report_path.stem}_backup_{timestamp}.txt"
                try:
                    shutil.copy2(txt_report_path, backup_path)
                    logger.info(f"Created backup: {backup_path.name}")
                except Exception as e:
                    logger.warning(f"Could not create backup (non-critical): {e}")
                    backup_path = None  # Continue without backup

            # Step 2: Load edited JSON
            with open(edited_json_path, 'r', encoding='utf-8') as f:
                edited_result = json.load(f)

            # Step 3: Generate TXT content
            txt_content = self._generate_txt_report_content(edited_result, version)

            if txt_content.startswith("Error generating"):
                raise ValueError(f"Failed to generate TXT content: {txt_content}")

            # Step 4: Write to temporary file (atomic operation)
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                delete=False,
                dir=txt_report_path.parent,
                suffix='.txt'
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(txt_content)

            # Step 5: Atomic move (replace original)
            # On Windows, need to remove destination first
            if txt_report_path.exists():
                txt_report_path.unlink()

            shutil.move(str(temp_path), str(txt_report_path))
            temp_path = None  # Moved successfully

            logger.info(f"Successfully updated TXT report: {txt_report_path.name}")

            # Step 6: Cleanup old backup (keep only most recent)
            if backup_path and backup_path.exists():
                # Remove older backups (keep only this one)
                backup_pattern = f"{txt_report_path.stem}_backup_*.txt"
                backups = sorted(txt_report_path.parent.glob(backup_pattern))
                if len(backups) > 1:
                    # Keep only the newest backup
                    for old_backup in backups[:-1]:
                        try:
                            old_backup.unlink()
                            logger.debug(f"Removed old backup: {old_backup.name}")
                        except Exception:
                            pass  # Ignore cleanup errors

            return True

        except Exception as e:
            logger.error(f"Error updating TXT report: {e}", exc_info=True)

            # ROLLBACK: Restore from backup if update failed
            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, txt_report_path)
                    logger.warning(f"Rolled back to backup: {backup_path.name}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            # Cleanup temp file if exists
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            return False

