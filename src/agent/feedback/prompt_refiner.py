"""
Prompt Refiner - Refinamento Automático de Prompts

Responsabilidades:
- Analisar feedback coletado e identificar padrões de erro
- Gerar ajustes automáticos nos system prompts
- Aplicar ajustes de forma incremental e rastreável
- Versionar prompts (v1.0.0 → v1.0.1)

Este componente implementa o aprendizado contínuo do sistema.

Fase de Implementação: FASE 2 (5-7 dias)
Status: ✅ Implementado
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
        logger.info(f"PromptRefiner initialized: {self.prompts_dir}")

    def analyze_feedback_patterns(
        self,
        feedback_sessions: Optional[List[Dict]] = None
    ) -> List[FeedbackPattern]:
        """
        Identifica padrões no feedback coletado.

        Padrões detectados:
        - Categorias de sugestões frequentemente rejeitadas
        - Tipos de erro recorrentes
        - Áreas onde prompts precisam melhorar

        Args:
            feedback_sessions: Lista de sessões de feedback (None = carregar todas)

        Returns:
            Lista de padrões identificados
        """
        if feedback_sessions is None:
            feedback_sessions = self.storage.load_feedback_sessions()
        
        if not feedback_sessions:
            logger.warning("No feedback sessions to analyze")
            return []
        
        patterns = []
        
        # Padrão 1: Sugestões redundantes
        redundant_pattern = self._detect_redundant_suggestions(feedback_sessions)
        if redundant_pattern:
            patterns.append(redundant_pattern)
        
        # Padrão 2: Falta de contexto
        missing_context_pattern = self._detect_missing_context(feedback_sessions)
        if missing_context_pattern:
            patterns.append(missing_context_pattern)
        
        # Padrão 3: Categorias frequentemente rejeitadas
        category_patterns = self._detect_category_rejection_patterns(feedback_sessions)
        patterns.extend(category_patterns)
        
        logger.info(f"Identified {len(patterns)} feedback patterns")
        return patterns

    def generate_prompt_adjustments(
        self,
        patterns: List[FeedbackPattern]
    ) -> List[PromptAdjustment]:
        """
        Gera ajustes de prompt baseado em padrões.

        Tipos de Ajuste:
        - Adicionar restrições (ex: "Evite sugerir X se Y já existe")
        - Melhorar instruções de categorização
        - Ajustar thresholds de relevância
        - Adicionar exemplos de boas práticas

        Args:
            patterns: Padrões identificados

        Returns:
            Lista de ajustes a serem aplicados
        """
        adjustments = []
        
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
        
        logger.info(f"Generated {len(adjustments)} prompt adjustments")
        return adjustments

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
                    comment = sug_fb.get("user_comment", "").lower()
                    # Palavras-chave que indicam redundância
                    redundant_keywords = [
                        "já existe", "redundante", "duplicado", "repetido",
                        "já contemplado", "já implementado", "similar"
                    ]
                    
                    if any(keyword in comment for keyword in redundant_keywords):
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
                    comment = sug_fb.get("user_comment", "").lower()
                    # Palavras-chave que indicam falta de contexto
                    context_keywords = [
                        "falta contexto", "não entendo", "confuso", "vago",
                        "precisa mais informação", "incompleto"
                    ]
                    
                    if any(keyword in comment for keyword in context_keywords):
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
                    comment = sug_fb.get("user_comment", "").lower()
                    # Categorias comuns
                    if "segurança" in comment or "safety" in comment:
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
