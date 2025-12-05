"""
Memory Manager - Gerenciador de Memória Persistente

[DEPRECATED] Este componente foi substituído por MemoryQA (memory_qa.py).
Mantido apenas para referência. Não usar no fluxo principal.

A funcionalidade foi migrada para MemoryQA, que usa um arquivo markdown
simples (memory_qa.md) na raiz do projeto em vez de arquivos JSON e MD
separados em src/config/prompts/.

Estrutura:
- AGENT_MEMORY.md: Documento principal de memória (similar ao CLAUDE.md)
- Atualização incremental baseada em feedback e ajustes
- Versionamento e histórico de mudanças
Status: DEPRECATED (substituído por MemoryQA)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..core.logger import logger


@dataclass
class MemoryEntry:
    """Entrada na memória do agente."""
    timestamp: str
    entry_type: str  # "pattern", "adjustment", "insight", "best_practice"
    content: str
    source: str  # "feedback", "llm_analysis", "user_feedback"
    metadata: Optional[Dict] = None


class MemoryManager:
    """
    Gerencia memória persistente do agente.
    
    Este componente mantém um documento de memória (AGENT_MEMORY.md) que
    acumula aprendizados, padrões e ajustes para otimizar o workflow da LLM.
    
    Example:
        >>> manager = MemoryManager()
        >>> manager.add_pattern("low_priority_rejection", "Focus on high-priority suggestions")
        >>> memory_content = manager.get_memory_content()
        >>> print(memory_content[:100])
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        """
        Inicializa o gerenciador de memória.
        
        Args:
            memory_file: Caminho para o arquivo de memória (padrão: src/config/prompts/AGENT_MEMORY.md)
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.memory_file = memory_file or (project_root / "src" / "config" / "prompts" / "AGENT_MEMORY.md")
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Arquivo JSON para dados estruturados
        self.memory_data_file = self.memory_file.parent / "AGENT_MEMORY.json"
        
        # Carregar memória existente
        self.memory_entries: List[MemoryEntry] = []
        self._load_memory()
        
        logger.info(f"MemoryManager initialized: {self.memory_file}")
    
    def _load_memory(self) -> None:
        """Carrega memória existente do arquivo JSON."""
        if self.memory_data_file.exists():
            try:
                with open(self.memory_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_entries = [
                        MemoryEntry(**entry) for entry in data.get("entries", [])
                    ]
                logger.info(f"Loaded {len(self.memory_entries)} memory entries")
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                self.memory_entries = []
        else:
            self.memory_entries = []
    
    def _save_memory(self) -> None:
        """Salva memória em arquivo JSON."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "entries": [asdict(entry) for entry in self.memory_entries]
            }
            with open(self.memory_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Também atualizar o arquivo Markdown
            self._update_markdown_memory()
            
            logger.info(f"Memory saved: {len(self.memory_entries)} entries")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def _update_markdown_memory(self) -> None:
        """Atualiza o arquivo Markdown de memória."""
        try:
            content = self._generate_markdown_content()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error updating markdown memory: {e}")
    
    def _generate_markdown_content(self) -> str:
        """Gera conteúdo Markdown formatado da memória."""
        lines = [
            "# AGENT MEMORY - Memória Persistente do Agente Daktus QA",
            "",
            f"**Última atualização:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total de entradas:** {len(self.memory_entries)}",
            "",
            "---",
            "",
            "## 📚 Visão Geral",
            "",
            "Este documento contém a memória acumulada do Agente Daktus QA, incluindo:",
            "- Padrões aprendidos do feedback do usuário",
            "- Ajustes aplicados no system prompt",
            "- Insights e recomendações identificados",
            "- Melhores práticas para análise de protocolos",
            "",
            "**Objetivo:** Otimizar o workflow da LLM fornecendo contexto acumulado que melhora continuamente a qualidade das análises.",
            "",
            "---",
            "",
        ]
        
        # Agrupar por tipo
        patterns = [e for e in self.memory_entries if e.entry_type == "pattern"]
        adjustments = [e for e in self.memory_entries if e.entry_type == "adjustment"]
        insights = [e for e in self.memory_entries if e.entry_type == "insight"]
        best_practices = [e for e in self.memory_entries if e.entry_type == "best_practice"]
        
        # Padrões aprendidos
        if patterns:
            lines.extend([
                "## 🔍 Padrões Aprendidos",
                "",
                "Padrões identificados através do feedback do usuário:",
                "",
            ])
            for entry in patterns[-10:]:  # Últimos 10
                lines.extend([
                    f"### {entry.metadata.get('pattern_type', 'Padrão') if entry.metadata else 'Padrão'}",
                    f"*{entry.timestamp}*",
                    "",
                    entry.content,
                    "",
                    "---",
                    "",
                ])
        
        # Ajustes aplicados
        if adjustments:
            lines.extend([
                "## ⚙️ Ajustes Aplicados no System Prompt",
                "",
                "Ajustes que foram aplicados no system prompt baseados em feedback:",
                "",
            ])
            for entry in adjustments[-10:]:  # Últimos 10
                lines.extend([
                    f"### {entry.metadata.get('adjustment_id', 'Ajuste') if entry.metadata else 'Ajuste'}",
                    f"*{entry.timestamp}*",
                    "",
                    f"**Tipo:** {entry.metadata.get('adjustment_type', 'N/A') if entry.metadata else 'N/A'}",
                    f"**Justificativa:** {entry.metadata.get('rationale', 'N/A') if entry.metadata else 'N/A'}",
                    "",
                    entry.content,
                    "",
                    "---",
                    "",
                ])
        
        # Insights
        if insights:
            lines.extend([
                "## 💡 Insights e Recomendações",
                "",
                "Insights gerados através de análise profunda de feedback:",
                "",
            ])
            for entry in insights[-10:]:  # Últimos 10
                lines.extend([
                    f"*{entry.timestamp}*",
                    "",
                    entry.content,
                    "",
                    "---",
                    "",
                ])
        
        # Melhores práticas
        if best_practices:
            lines.extend([
                "## ✅ Melhores Práticas",
                "",
                "Práticas identificadas que geram sugestões mais precisas e úteis:",
                "",
            ])
            for entry in best_practices:
                lines.extend([
                    f"*{entry.timestamp}*",
                    "",
                    entry.content,
                    "",
                    "---",
                    "",
                ])
        
        # Resumo executivo
        lines.extend([
            "",
            "---",
            "",
            "## 📊 Resumo Executivo",
            "",
            f"- **Total de padrões aprendidos:** {len(patterns)}",
            f"- **Total de ajustes aplicados:** {len(adjustments)}",
            f"- **Total de insights:** {len(insights)}",
            f"- **Total de melhores práticas:** {len(best_practices)}",
            "",
            "---",
            "",
            "*Este documento é atualizado automaticamente pelo sistema de feedback e refinamento de prompts.*",
        ])
        
        return "\n".join(lines)
    
    def add_pattern(
        self,
        pattern_type: str,
        description: str,
        frequency: int,
        severity: str,
        examples: List[Dict]
    ) -> None:
        """
        Adiciona um padrão aprendido à memória.
        
        Args:
            pattern_type: Tipo do padrão (ex: "low_priority_rejection")
            description: Descrição do padrão
            frequency: Frequência de ocorrência
            severity: Severidade (alta, media, baixa)
            examples: Exemplos do padrão
        """
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="pattern",
            content=description,
            source="feedback_analysis",
            metadata={
                "pattern_type": pattern_type,
                "frequency": frequency,
                "severity": severity,
                "examples": examples[:3]  # Limitar exemplos
            }
        )
        self.memory_entries.append(entry)
        self._save_memory()
        logger.info(f"Pattern added to memory: {pattern_type}")
    
    def add_adjustment(
        self,
        adjustment_id: str,
        adjustment_type: str,
        rationale: str,
        adjustment_text: str
    ) -> None:
        """
        Adiciona um ajuste aplicado à memória.
        
        Args:
            adjustment_id: ID do ajuste
            adjustment_type: Tipo do ajuste
            rationale: Justificativa do ajuste
            adjustment_text: Texto do ajuste aplicado
        """
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="adjustment",
            content=adjustment_text,
            source="prompt_refinement",
            metadata={
                "adjustment_id": adjustment_id,
                "adjustment_type": adjustment_type,
                "rationale": rationale
            }
        )
        self.memory_entries.append(entry)
        self._save_memory()
        logger.info(f"Adjustment added to memory: {adjustment_id}")
    
    def add_insight(
        self,
        insight: str,
        recommendations: Optional[str] = None,
        source: str = "llm_analysis"
    ) -> None:
        """
        Adiciona um insight à memória.
        
        Args:
            insight: Texto do insight
            recommendations: Recomendações associadas (opcional)
            source: Fonte do insight
        """
        content = insight
        if recommendations:
            content += f"\n\n**Recomendações:**\n{recommendations}"
        
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="insight",
            content=content,
            source=source,
            metadata={}
        )
        self.memory_entries.append(entry)
        self._save_memory()
        logger.info("Insight added to memory")
    
    def add_best_practice(
        self,
        practice: str,
        context: Optional[str] = None
    ) -> None:
        """
        Adiciona uma melhor prática à memória.
        
        Args:
            practice: Descrição da melhor prática
            context: Contexto adicional (opcional)
        """
        content = practice
        if context:
            content += f"\n\n**Contexto:**\n{context}"
        
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            entry_type="best_practice",
            content=content,
            source="feedback_analysis",
            metadata={}
        )
        self.memory_entries.append(entry)
        self._save_memory()
        logger.info("Best practice added to memory")
    
    def get_memory_content(self, max_length: int = 5000) -> str:
        """
        Retorna conteúdo da memória formatado para uso no prompt.
        
        Args:
            max_length: Tamanho máximo do conteúdo (para limitar tokens)
        
        Returns:
            Conteúdo formatado da memória
        """
        if not self.memory_entries:
            return "Nenhuma memória acumulada ainda."
        
        # Priorizar entradas mais recentes e importantes
        recent_entries = sorted(
            self.memory_entries,
            key=lambda e: (
                e.entry_type in ("best_practice", "insight"),  # Priorizar práticas e insights
                e.timestamp
            ),
            reverse=True
        )[:20]  # Últimas 20 entradas mais relevantes
        
        lines = [
            "=== MEMÓRIA DO AGENTE - CONTEXTO ACUMULADO ===",
            "",
            "Este contexto contém aprendizados acumulados de análises anteriores:",
            "",
        ]
        
        # Agrupar por tipo
        best_practices = [e for e in recent_entries if e.entry_type == "best_practice"]
        insights = [e for e in recent_entries if e.entry_type == "insight"]
        patterns = [e for e in recent_entries if e.entry_type == "pattern"]
        adjustments = [e for e in recent_entries if e.entry_type == "adjustment"]
        
        if best_practices:
            lines.extend([
                "MELHORES PRÁTICAS IDENTIFICADAS:",
                "",
            ])
            for entry in best_practices[:5]:
                lines.extend([
                    f"- {entry.content[:200]}...",
                    "",
                ])
        
        if insights:
            lines.extend([
                "INSIGHTS RECENTES:",
                "",
            ])
            for entry in insights[:3]:
                lines.extend([
                    f"- {entry.content[:200]}...",
                    "",
                ])
        
        if patterns:
            lines.extend([
                "PADRÕES APRENDIDOS:",
                "",
            ])
            for entry in patterns[:5]:
                pattern_type = entry.metadata.get("pattern_type", "Padrão") if entry.metadata else "Padrão"
                lines.extend([
                    f"- {pattern_type}: {entry.content[:150]}...",
                    "",
                ])
        
        if adjustments:
            lines.extend([
                "AJUSTES APLICADOS RECENTEMENTE:",
                "",
            ])
            for entry in adjustments[:3]:
                rationale = entry.metadata.get("rationale", "") if entry.metadata else ""
                lines.extend([
                    f"- {rationale[:150]}...",
                    "",
                ])
        
        content = "\n".join(lines)
        
        # Limitar tamanho
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[... conteúdo truncado ...]"
        
        return content
    
    def clear_old_entries(self, keep_recent: int = 50) -> None:
        """
        Remove entradas antigas, mantendo apenas as mais recentes.
        
        Args:
            keep_recent: Número de entradas recentes para manter
        """
        if len(self.memory_entries) <= keep_recent:
            return
        
        # Manter melhores práticas e insights sempre
        important = [e for e in self.memory_entries if e.entry_type in ("best_practice", "insight")]
        
        # Manter entradas recentes
        recent = sorted(
            self.memory_entries,
            key=lambda e: e.timestamp,
            reverse=True
        )[:keep_recent]
        
        # Combinar e remover duplicatas
        all_keep = {id(e): e for e in important + recent}.values()
        self.memory_entries = list(all_keep)
        
        self._save_memory()
        logger.info(f"Cleaned memory: kept {len(self.memory_entries)} entries")

