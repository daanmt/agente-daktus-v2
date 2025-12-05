"""
Prompt Refiner - Refinamento Automático de Prompts

[DEPRECATED] Este componente foi substituído por MemoryQA (memory_qa.py).
Mantido apenas para referência. Não usar no fluxo principal.

A funcionalidade de análise de padrões foi integrada ao MemoryQA,
que usa um arquivo markdown simples (memory_qa.md) em vez de modificar
o system prompt automaticamente.

Fase de Implementação: FASE 2 (5-7 dias)
Status: ✅ Implementado → DEPRECATED (substituído por MemoryQA)
"""

import sys
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from ..core.logger import logger
from .feedback_storage import FeedbackStorage
from .memory_manager import MemoryManager


@dataclass
class FeedbackPattern:
    """
    Padrão identificado no feedback do usuário.

    Attributes:
        pattern_type: Tipo de padrão (ex: "redundant_suggestions", "missing_context")
        description: Descrição do padrão
        frequency: Frequência de ocorrência
        examples: Exemplos de casos
        severity: Severidade (alta, média, baixa)
    """
    pattern_type: str
    description: str
    frequency: int
    examples: List[Dict]
    severity: str


@dataclass
class PromptAdjustment:
    """
    Ajuste a ser aplicado em um prompt.

    Attributes:
        adjustment_id: ID único do ajuste
        target_prompt: Prompt alvo (ex: "analysis_prompt")
        adjustment_type: Tipo de ajuste (add_restriction, modify_instruction, etc.)
        before: Versão anterior do trecho
        after: Versão ajustada do trecho
        rationale: Justificativa do ajuste
        timestamp: Data/hora do ajuste
    """
    adjustment_id: str
    target_prompt: str
    adjustment_type: str
    before: str
    after: str
    rationale: str
    timestamp: datetime


class PromptRefiner:
    """
    Refina system prompts baseado em feedback do usuário.

    Este componente analisa padrões de feedback e gera ajustes automáticos
    nos prompts para melhorar a qualidade das análises futuras.

    Fluxo de Refinamento:
    1. Analisar sessões de feedback
    2. Identificar padrões de erro
    3. Gerar ajustes de prompt
    4. Aplicar ajustes incrementalmente
    5. Versionar prompts

    Example:
        >>> refiner = PromptRefiner()
        >>> patterns = refiner.analyze_feedback_patterns(feedback_sessions)
        >>> adjustments = refiner.generate_prompt_adjustments(patterns)
        >>> refiner.apply_adjustments(adjustments)
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Inicializa o refinador de prompts.

        Args:
            prompts_dir: Diretório onde prompts são armazenados
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.prompts_dir = prompts_dir or (project_root / "src" / "config" / "prompts")
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Diretório para versões de prompts
        self.versions_dir = self.prompts_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # Diretório para changelog
        self.changelog_dir = self.prompts_dir / "changelogs"
        self.changelog_dir.mkdir(exist_ok=True)
        
        self.storage = FeedbackStorage()
        self.memory = MemoryManager()
        logger.info(f"PromptRefiner initialized: {self.prompts_dir}")

    def analyze_feedback_patterns(
        self,
        feedback_sessions: Optional[List[Dict]] = None,
        analysis_report: Optional[Dict] = None
    ) -> List[FeedbackPattern]:
        """
        Identifica padrões no feedback coletado usando análise profunda com LLM.

        Este método compara o feedback do usuário com o relatório gerado,
        identifica nuances e gera insights para melhorar os prompts.

        Padrões detectados:
        - Categorias de sugestões frequentemente rejeitadas
        - Tipos de erro recorrentes
        - Áreas onde prompts precisam melhorar
        - Discrepâncias entre relatório e feedback do usuário

        Args:
            feedback_sessions: Lista de sessões de feedback (None = carregar todas)
            analysis_report: Relatório da análise original (para comparação profunda)

        Returns:
            Lista de padrões identificados
        """
        if feedback_sessions is None:
            feedback_sessions = self.storage.load_feedback_sessions()
        
        if not feedback_sessions:
            logger.warning("No feedback sessions to analyze")
            return []
        
        patterns = []
        
        # Análise básica (padrões simples)
        redundant_pattern = self._detect_redundant_suggestions(feedback_sessions)
        if redundant_pattern:
            patterns.append(redundant_pattern)
        
        missing_context_pattern = self._detect_missing_context(feedback_sessions)
        if missing_context_pattern:
            patterns.append(missing_context_pattern)
        
        category_patterns = self._detect_category_rejection_patterns(feedback_sessions)
        patterns.extend(category_patterns)
        
        # Detectar rejeição de sugestões de baixa prioridade
        low_priority_pattern = self._detect_low_priority_rejection(feedback_sessions, analysis_report)
        if low_priority_pattern:
            patterns.append(low_priority_pattern)
        
        # Análise profunda com LLM (se relatório disponível)
        if analysis_report:
            deep_patterns = self._analyze_feedback_with_llm(feedback_sessions, analysis_report)
            patterns.extend(deep_patterns)
        
        logger.info(f"Identified {len(patterns)} feedback patterns")
        return patterns

    def _analyze_feedback_with_llm(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Dict
    ) -> List[FeedbackPattern]:
        """
        Análise profunda de feedback usando LLM para entender nuances.

        Compara feedback do usuário com relatório gerado e identifica:
        - O que o relatório disse vs o que o usuário esperava
        - Nuances e contexto que faltaram
        - Como melhorar o system prompt baseado nessa comparação

        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original da análise

        Returns:
            Lista de padrões identificados via LLM
        """
        try:
            from ..core.llm_client import LLMClient
            
            # Preparar dados para análise
            feedback_summary = self._prepare_feedback_summary(feedback_sessions)
            report_summary = self._prepare_report_summary(analysis_report)
            
            # Prompt para análise profunda
            analysis_prompt = f"""Você é um especialista em análise de feedback e melhoria de prompts para sistemas de análise clínica.

TAREFA: Analise o feedback do usuário comparado com o relatório gerado e identifique padrões profundos que indiquem como melhorar o system prompt.

RELATÓRIO GERADO:
{report_summary}

FEEDBACK DO USUÁRIO:
{feedback_summary}

INSTRUÇÕES:
1. Compare o que o relatório disse com o que o usuário esperava/comentou
2. Identifique nuances e contexto que faltaram no relatório
3. Identifique padrões de erro recorrentes
4. Sugira melhorias específicas para o system prompt que geraria relatórios melhores

Responda em JSON com este formato:
{{
    "patterns": [
        {{
            "pattern_type": "tipo_do_padrão",
            "description": "Descrição detalhada do padrão identificado",
            "frequency": número_de_ocorrências,
            "severity": "alta|media|baixa",
            "examples": ["exemplo1", "exemplo2"],
            "prompt_improvement": "Sugestão específica de como melhorar o prompt"
        }}
    ],
    "insights": "Análise geral das diferenças entre relatório e feedback",
    "recommendations": "Recomendações específicas para melhorar o system prompt"
}}"""

            # Tentar usar modelo gratuito, com fallback para Gemini
            models_to_try = [
                "x-ai/grok-4.1-fast:free",
                "google/gemini-2.5-flash-lite"
            ]
            
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
                import json
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
                
                # Salvar padrão na memória
                self.memory.add_pattern(
                    pattern_type=pattern.pattern_type,
                    description=pattern.description,
                    frequency=pattern.frequency,
                    severity=pattern.severity,
                    examples=pattern.examples
                )
            
            # Armazenar insights e recomendações para uso posterior
            if "insights" in llm_result or "recommendations" in llm_result:
                self._store_llm_insights(llm_result)
                # Também salvar na memória
                if "insights" in llm_result:
                    self.memory.add_insight(
                        insight=llm_result.get("insights", ""),
                        recommendations=llm_result.get("recommendations"),
                        source="llm_analysis"
                    )
            
            logger.info(f"LLM analysis identified {len(patterns)} deep patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in LLM feedback analysis: {e}", exc_info=True)
            return []  # Retornar vazio em caso de erro, mas não quebrar o fluxo

    def _prepare_feedback_summary(self, feedback_sessions: List[Dict]) -> str:
        """Prepara resumo do feedback para análise LLM."""
        summary_parts = []
        
        for session in feedback_sessions:
            session_summary = f"Sessão: {session.get('protocol_name', 'N/A')}\n"
            session_summary += f"Modelo: {session.get('model_used', 'N/A')}\n"
            
            # Feedback geral
            if session.get('general_feedback'):
                session_summary += f"Feedback Geral: {session.get('general_feedback')}\n"
            if session.get('quality_rating'):
                session_summary += f"Avaliação: {session.get('quality_rating')}/10\n"
            
            # Feedback por sugestão
            suggestions_fb = session.get('suggestions_feedback', [])
            relevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'relevant')
            irrelevant_count = sum(1 for sf in suggestions_fb if sf.get('user_verdict') == 'irrelevant')
            
            session_summary += f"Sugestões Relevantes: {relevant_count}\n"
            session_summary += f"Sugestões Irrelevantes: {irrelevant_count}\n"
            
            # Comentários importantes
            important_comments = [
                sf.get('user_comment', '')
                for sf in suggestions_fb
                if sf.get('user_comment') and len(sf.get('user_comment', '')) > 20
            ]
            if important_comments:
                session_summary += "Comentários Importantes:\n"
                for comment in important_comments[:5]:  # Limitar a 5
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
            # Exemplos de títulos
            for sug in sugs[:3]:
                summary += f"    - {sug.get('title', 'N/A')}\n"
        
        return summary

    def _store_llm_insights(self, llm_result: Dict) -> None:
        """Armazena insights e recomendações do LLM para referência futura."""
        insights_file = self.prompts_dir / "llm_insights.json"
        
        insights_data = {
            "timestamp": datetime.now().isoformat(),
            "insights": llm_result.get("insights", ""),
            "recommendations": llm_result.get("recommendations", "")
        }
        
        # Carregar insights existentes
        all_insights = []
        if insights_file.exists():
            try:
                with open(insights_file, 'r', encoding='utf-8') as f:
                    all_insights = json.load(f)
            except Exception:
                all_insights = []
        
        all_insights.append(insights_data)
        
        # Manter apenas últimos 10
        all_insights = all_insights[-10:]
        
        # Salvar
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump(all_insights, f, ensure_ascii=False, indent=2)
        
        logger.info(f"LLM insights stored: {insights_file}")

    def generate_prompt_adjustments(
        self,
        patterns: List[FeedbackPattern],
        use_llm: bool = True
    ) -> List[PromptAdjustment]:
        """
        Gera ajustes de prompt baseado em padrões, usando LLM para ajustes inteligentes.

        Tipos de Ajuste:
        - Adicionar restrições (ex: "Evite sugerir X se Y já existe")
        - Melhorar instruções de categorização
        - Ajustar thresholds de relevância
        - Adicionar exemplos de boas práticas

        Args:
            patterns: Padrões identificados
            use_llm: Se True, usa LLM para gerar ajustes mais inteligentes

        Returns:
            Lista de ajustes a serem aplicados
        """
        adjustments = []
        
        # Ajustes baseados em regras (padrões simples)
        for pattern in patterns:
            if pattern.pattern_type == "redundant_suggestions":
                adjustment = self._create_redundancy_adjustment(pattern)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif pattern.pattern_type == "missing_context":
                adjustment = self._create_context_adjustment(pattern)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif pattern.pattern_type.startswith("category_rejection_"):
                adjustment = self._create_category_adjustment(pattern)
                if adjustment:
                    adjustments.append(adjustment)
            
            elif pattern.pattern_type == "low_priority_rejection":
                adjustment = self._create_low_priority_adjustment(pattern)
                if adjustment:
                    adjustments.append(adjustment)
        
        # Ajustes gerados por LLM (padrões complexos)
        if use_llm:
            llm_adjustments = self._generate_llm_based_adjustments(patterns)
            adjustments.extend(llm_adjustments)
        
        logger.info(f"Generated {len(adjustments)} prompt adjustments")
        return adjustments

    def _generate_llm_based_adjustments(
        self,
        patterns: List[FeedbackPattern]
    ) -> List[PromptAdjustment]:
        """
        Gera ajustes de prompt usando LLM baseado em padrões identificados.

        Args:
            patterns: Padrões identificados (incluindo os do LLM)

        Returns:
            Lista de ajustes gerados por LLM
        """
        try:
            from ..core.llm_client import LLMClient
            
            # Filtrar apenas padrões identificados por LLM ou complexos
            llm_patterns = [
                p for p in patterns
                if p.pattern_type.startswith("llm_") or p.severity == "alta"
            ]
            
            if not llm_patterns:
                return []
            
            # Carregar insights anteriores
            insights_file = self.prompts_dir / "llm_insights.json"
            previous_insights = ""
            if insights_file.exists():
                try:
                    with open(insights_file, 'r', encoding='utf-8') as f:
                        insights_data = json.load(f)
                        if insights_data:
                            latest = insights_data[-1]
                            previous_insights = f"Insights anteriores: {latest.get('insights', '')}\nRecomendações: {latest.get('recommendations', '')}"
                except Exception:
                    pass
            
            # Preparar descrição dos padrões
            patterns_desc = "\n".join([
                f"- {p.pattern_type}: {p.description} (severidade: {p.severity}, frequência: {p.frequency})"
                for p in llm_patterns
            ])
            
            # Carregar prompt atual para contexto
            prompt_file = self.prompts_dir / "enhanced_analysis_prompt.py"
            current_prompt_snippet = ""
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                    # Pegar seção relevante (primeiras 500 linhas)
                    current_prompt_snippet = prompt_content[:2000]
            
            # Prompt para gerar ajustes
            adjustment_prompt = f"""Você é um especialista em melhorar prompts para sistemas de análise clínica.

CONTEXTO:
Você precisa melhorar um system prompt baseado em padrões identificados no feedback do usuário.

PADRÕES IDENTIFICADOS:
{patterns_desc}

{previous_insights}

PROMPT ATUAL (trecho):
{current_prompt_snippet[:1000]}

TAREFA:
Gere ajustes específicos e acionáveis para melhorar o prompt. Cada ajuste deve:
1. Ser específico e claro
2. Endereçar diretamente os padrões identificados
3. Incluir o texto exato a ser adicionado/modificado no prompt
4. Ter justificativa clara

Responda em JSON com este formato:
{{
    "adjustments": [
        {{
            "adjustment_id": "adj_001",
            "target_prompt": "enhanced_analysis_prompt.py",
            "adjustment_type": "add_restriction|modify_instruction|add_example",
            "location": "Descrição de onde aplicar (ex: 'Após linha sobre categorização')",
            "before": "Texto exato a ser substituído (ou vazio se for adição)",
            "after": "Texto exato a ser adicionado/substituído",
            "rationale": "Justificativa do ajuste"
        }}
    ]
}}"""

            # Tentar usar modelo gratuito, com fallback para Gemini
            models_to_try = [
                "x-ai/grok-4.1-fast:free",
                "google/gemini-2.5-flash-lite"
            ]
            
            response = None
            last_error = None
            
            for model in models_to_try:
                try:
                    llm_client = LLMClient(model=model)
                    response = llm_client.analyze(adjustment_prompt)
                    logger.info(f"LLM adjustment generation successful with model: {model}")
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
                import json
                llm_result = json.loads(response)
            
            # Converter para PromptAdjustment
            adjustments = []
            for adj_data in llm_result.get("adjustments", []):
                adjustments.append(PromptAdjustment(
                    adjustment_id=adj_data.get("adjustment_id", f"llm_adj_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    target_prompt=adj_data.get("target_prompt", "enhanced_analysis_prompt.py"),
                    adjustment_type=adj_data.get("adjustment_type", "modify_instruction"),
                    before=adj_data.get("before", ""),
                    after=adj_data.get("after", ""),
                    rationale=adj_data.get("rationale", "Ajuste gerado por LLM baseado em padrões de feedback"),
                    timestamp=datetime.now()
                ))
            
            logger.info(f"LLM generated {len(adjustments)} intelligent adjustments")
            return adjustments
            
        except Exception as e:
            logger.error(f"Error generating LLM-based adjustments: {e}", exc_info=True)
            return []

    def apply_adjustments(
        self,
        adjustments: List[PromptAdjustment],
        prompt_file: str = "enhanced_analysis_prompt.py"
    ) -> bool:
        """
        Aplica ajustes de forma incremental e rastreável.

        Fluxo:
        1. Versionar prompts (v1.0.0 → v1.0.1)
        2. Aplicar ajustes
        3. Registrar mudanças em changelog
        4. Salvar nova versão
        5. Permitir rollback se necessário

        Args:
            adjustments: Lista de ajustes a aplicar
            prompt_file: Nome do arquivo de prompt a ajustar

        Returns:
            True se ajustes foram aplicados com sucesso
        """
        if not adjustments:
            logger.warning("No adjustments to apply")
            return False
        
        prompt_path = self.prompts_dir / prompt_file
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            return False
        
        # Ler prompt atual
        with open(prompt_path, 'r', encoding='utf-8') as f:
            current_prompt = f.read()
        
        # Detectar versão atual
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', current_prompt)
        current_version = version_match.group(1) if version_match else "1.0.0"
        new_version = self.version_prompt(current_version)
        
        # Criar backup
        backup_path = self.versions_dir / f"{prompt_file}.v{current_version}"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_prompt)
        logger.info(f"Backup created: {backup_path}")
        
        # Aplicar ajustes
        modified_prompt = current_prompt
        changelog_entries = []
        
        for adjustment in adjustments:
            # Aplicar ajuste no prompt
            if adjustment.before in modified_prompt:
                modified_prompt = modified_prompt.replace(adjustment.before, adjustment.after)
                changelog_entries.append({
                    "adjustment_id": adjustment.adjustment_id,
                    "type": adjustment.adjustment_type,
                    "rationale": adjustment.rationale,
                    "timestamp": adjustment.timestamp.isoformat()
                })
                logger.info(f"Applied adjustment: {adjustment.adjustment_id}")
                
                # Salvar ajuste na memória
                self.memory.add_adjustment(
                    adjustment_id=adjustment.adjustment_id,
                    adjustment_type=adjustment.adjustment_type,
                    rationale=adjustment.rationale,
                    adjustment_text=adjustment.after[:500]  # Limitar tamanho
                )
            else:
                logger.warning(f"Could not find adjustment target in prompt: {adjustment.adjustment_id}")
        
        # Atualizar versão no prompt
        modified_prompt = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            modified_prompt
        )
        
        # Salvar prompt modificado
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(modified_prompt)
        
        # Salvar changelog
        changelog_path = self.changelog_dir / f"{prompt_file}.changelog.json"
        changelog = []
        if changelog_path.exists():
            with open(changelog_path, 'r', encoding='utf-8') as f:
                changelog = json.load(f)
        
        changelog.append({
            "version": new_version,
            "previous_version": current_version,
            "timestamp": datetime.now().isoformat(),
            "adjustments": changelog_entries
        })
        
        with open(changelog_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Prompt updated: {current_version} → {new_version}")
        logger.info(f"Changelog saved: {changelog_path}")
        
        return True

    def _detect_redundant_suggestions(
        self,
        feedback_sessions: List[Dict]
    ) -> Optional[FeedbackPattern]:
        """
        Detecta padrão de sugestões redundantes.

        Args:
            feedback_sessions: Sessões de feedback

        Returns:
            Padrão identificado ou None
        """
        redundant_count = 0
        examples = []
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    comment = (sug_fb.get("user_comment") or "").lower()
                    # Palavras-chave que indicam redundância
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
        
        if redundant_count >= 3:  # Threshold mínimo
            severity = "alta" if redundant_count >= 10 else "media"
            return FeedbackPattern(
                pattern_type="redundant_suggestions",
                description=f"{redundant_count} sugestões rejeitadas por redundância",
                frequency=redundant_count,
                examples=examples[:5],  # Limitar exemplos
                severity=severity
            )
        
        return None

    def _detect_missing_context(
        self,
        feedback_sessions: List[Dict]
    ) -> Optional[FeedbackPattern]:
        """
        Detecta padrão de falta de contexto nas sugestões.

        Args:
            feedback_sessions: Sessões de feedback

        Returns:
            Padrão identificado ou None
        """
        missing_context_count = 0
        examples = []
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    comment = (sug_fb.get("user_comment") or "").lower()
                    # Palavras-chave que indicam falta de contexto
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

    def _detect_category_rejection_patterns(
        self,
        feedback_sessions: List[Dict]
    ) -> List[FeedbackPattern]:
        """
        Detecta padrões de rejeição por categoria.

        Args:
            feedback_sessions: Sessões de feedback

        Returns:
            Lista de padrões por categoria
        """
        category_rejections = {}
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    # Tentar inferir categoria do comment ou suggestion_id
                    # Por enquanto, agrupar por comentários similares
                    comment = (sug_fb.get("user_comment") or "").lower()
                    # Categorias comuns
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

    def _detect_low_priority_rejection(
        self,
        feedback_sessions: List[Dict],
        analysis_report: Optional[Dict] = None
    ) -> Optional[FeedbackPattern]:
        """
        Detecta padrão de rejeição de sugestões de baixa prioridade.
        
        Baseado no feedback: "a maioria das sugestões de baixo impacto são irrelevantes.
        é melhor gastar poder computacional com as critical/high suggestions."
        
        Args:
            feedback_sessions: Sessões de feedback
            analysis_report: Relatório original (para verificar prioridades)
        
        Returns:
            Padrão identificado ou None
        """
        if not analysis_report:
            return None
        
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
        
        logger.info(f"Analyzing {len(feedback_sessions)} feedback sessions with {len(suggestions_by_id)} suggestions in report")
        
        for session in feedback_sessions:
            for sug_fb in session.get("suggestions_feedback", []):
                if sug_fb.get("user_verdict") == "irrelevant":
                    suggestion_id = sug_fb.get("suggestion_id")
                    suggestion = suggestions_by_id.get(suggestion_id)
                    
                    if suggestion:
                        priority = suggestion.get("priority", "").lower()
                        logger.debug(f"Suggestion {suggestion_id}: priority='{priority}'")
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
                    else:
                        logger.warning(f"Suggestion {suggestion_id} not found in analysis report")
        
        logger.info(f"Rejections by priority: low={low_priority_rejections}, medium={medium_priority_rejections}, high={high_priority_rejections}")
        
        # Verificar se há padrão claro: muitas rejeições de baixa prioridade
        total_rejections = low_priority_rejections + medium_priority_rejections + high_priority_rejections
        if total_rejections == 0:
            return None
        
        # Se mais de 40% das rejeições são de baixa prioridade, há um padrão
        # (ajustado para capturar o feedback: "a maioria das sugestões de baixo impacto são irrelevantes")
        low_priority_ratio = low_priority_rejections / total_rejections if total_rejections > 0 else 0
        
        if low_priority_rejections >= 3 and low_priority_ratio >= 0.4:
            severity = "alta" if low_priority_rejections >= 8 else "media"
            description = (
                f"{low_priority_rejections} sugestões de baixa prioridade foram rejeitadas "
                f"({low_priority_ratio*100:.0f}% das rejeições). "
                f"Feedback indica que é melhor focar em sugestões critical/high priority."
            )
            
            pattern = FeedbackPattern(
                pattern_type="low_priority_rejection",
                description=description,
                frequency=low_priority_rejections,
                examples=examples[:5],
                severity=severity
            )
            
            # Salvar padrão na memória
            self.memory.add_pattern(
                pattern_type=pattern.pattern_type,
                description=pattern.description,
                frequency=pattern.frequency,
                severity=pattern.severity,
                examples=pattern.examples
            )
            
            return pattern
        
        return None

    def _create_redundancy_adjustment(
        self,
        pattern: FeedbackPattern
    ) -> Optional[PromptAdjustment]:
        """Cria ajuste para reduzir sugestões redundantes."""
        adjustment_text = """
IMPORTANTE: Antes de sugerir adicionar um nó ou funcionalidade, verifique cuidadosamente se já existe um nó similar com nome ou propósito equivalente no protocolo. Liste os nós existentes relevantes antes de sugerir adição. Evite sugestões redundantes ou duplicadas."""
        
        # Buscar local apropriado no prompt (antes da seção de sugestões)
        return PromptAdjustment(
            adjustment_id=f"adj-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            target_prompt="enhanced_analysis_prompt.py",
            adjustment_type="add_restriction",
            before="YOUR EXPANDED ANALYSIS MUST GENERATE 20-50 DETAILED IMPROVEMENT SUGGESTIONS:",
            after="YOUR EXPANDED ANALYSIS MUST GENERATE 20-50 DETAILED IMPROVEMENT SUGGESTIONS:" + adjustment_text,
            rationale=f"Reduzir sugestões redundantes (detectado {pattern.frequency} casos)",
            timestamp=datetime.now()
        )

    def _create_context_adjustment(
        self,
        pattern: FeedbackPattern
    ) -> Optional[PromptAdjustment]:
        """Cria ajuste para melhorar contexto das sugestões."""
        adjustment_text = """
IMPORTANTE: Cada sugestão deve incluir contexto suficiente para ser compreendida e implementada. Sempre forneça localização específica (node_id, field, path) e evidência clara do playbook."""
        
        return PromptAdjustment(
            adjustment_id=f"adj-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            target_prompt="enhanced_analysis_prompt.py",
            adjustment_type="modify_instruction",
            before="7. SPECIFICITY: Each suggestion must be:",
            after="7. SPECIFICITY: Each suggestion must be:" + adjustment_text,
            rationale=f"Melhorar contexto das sugestões (detectado {pattern.frequency} casos)",
            timestamp=datetime.now()
        )

    def _create_category_adjustment(
        self,
        pattern: FeedbackPattern
    ) -> Optional[PromptAdjustment]:
        """Cria ajuste para categoria específica."""
        category = pattern.pattern_type.replace("category_rejection_", "")
        adjustment_text = f"""
IMPORTANTE: Ao gerar sugestões de categoria '{category}', seja especialmente cuidadoso para garantir relevância e evitar sugestões genéricas ou já implementadas."""
        
        return PromptAdjustment(
            adjustment_id=f"adj-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            target_prompt="enhanced_analysis_prompt.py",
            adjustment_type="add_category_guidance",
            before="2. CATEGORIZATION: Each suggestion MUST be categorized as ONE of:",
            after="2. CATEGORIZATION: Each suggestion MUST be categorized as ONE of:" + adjustment_text,
            rationale=f"Melhorar qualidade de sugestões de {category} (detectado {pattern.frequency} rejeições)",
            timestamp=datetime.now()
        )

    def _create_low_priority_adjustment(
        self,
        pattern: FeedbackPattern
    ) -> Optional[PromptAdjustment]:
        """Cria ajuste para focar em sugestões de alta prioridade."""
        adjustment_text = """
CRITICAL PRIORITY FOCUS: 
- PRIORIZE generating HIGH and CRITICAL priority suggestions over LOW priority ones
- LOW priority suggestions should only be included if they are truly valuable and not redundant
- Focus computational resources on suggestions that have significant impact (safety score >= 7, or high efficiency/economy impact)
- Avoid generating many low-impact suggestions just to reach the target count
- Quality over quantity: Better to generate 20 high-quality, high-priority suggestions than 50 mixed-quality suggestions"""
        
        return PromptAdjustment(
            adjustment_id=f"adj-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            target_prompt="enhanced_analysis_prompt.py",
            adjustment_type="add_priority_guidance",
            before="YOUR EXPANDED ANALYSIS MUST GENERATE 20-50 DETAILED IMPROVEMENT SUGGESTIONS:",
            after="YOUR EXPANDED ANALYSIS MUST GENERATE 20-50 DETAILED IMPROVEMENT SUGGESTIONS:" + adjustment_text,
            rationale=f"Focar em sugestões de alta prioridade (detectado {pattern.frequency} rejeições de baixa prioridade)",
            timestamp=datetime.now()
        )

    def version_prompt(
        self,
        current_version: str
    ) -> str:
        """
        Incrementa versão do prompt (semver).

        Args:
            current_version: Versão atual (ex: "1.0.0")

        Returns:
            Nova versão (ex: "1.0.1")
        """
        try:
            parts = current_version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            # Incrementar PATCH
            patch += 1
            new_version = f"{major}.{minor}.{patch}"
            
            logger.info(f"Version incremented: {current_version} → {new_version}")
            return new_version
        except Exception as e:
            logger.error(f"Error versioning prompt: {e}")
            # Fallback: adicionar timestamp
            return f"1.0.{int(datetime.now().timestamp())}"

    def rollback_to_version(
        self,
        target_version: str,
        prompt_file: str = "enhanced_analysis_prompt.py"
    ) -> bool:
        """
        Faz rollback para versão anterior do prompt.

        Args:
            target_version: Versão alvo para rollback
            prompt_file: Nome do arquivo de prompt

        Returns:
            True se rollback foi bem-sucedido
        """
        backup_path = self.versions_dir / f"{prompt_file}.v{target_version}"
        
        if not backup_path.exists():
            logger.error(f"Version backup not found: {backup_path}")
            return False
        
        prompt_path = self.prompts_dir / prompt_file
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            return False
        
        # Restaurar versão
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        logger.info(f"Rolled back to version: {target_version}")
        return True
