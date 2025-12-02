"""
Feedback Collector - Captura de Feedback do Usuário

Responsabilidades:
- Apresentar sugestões ao usuário para revisão interativa
- Capturar feedback: Relevante | Irrelevante | Editar | Comentar
- Armazenar feedback estruturado para análise posterior

Este é o diferencial do V3 - Sistema de aprendizado contínuo baseado em feedback humano.

Fase de Implementação: FASE 2 (5-7 dias)
Status: ✅ Implementado
"""

import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from ..core.logger import logger
from .feedback_storage import FeedbackStorage


@dataclass
class SuggestionFeedback:
    """
    Feedback do usuário sobre uma sugestão específica.

    Attributes:
        suggestion_id: ID da sugestão
        user_verdict: "relevant", "irrelevant", "edited"
        user_comment: Comentário qualitativo opcional
        edited: Se sugestão foi editada
        edited_version: Versão editada da sugestão (se aplicável)
    """
    suggestion_id: str
    user_verdict: str  # relevant, irrelevant, edited
    user_comment: Optional[str] = None
    edited: bool = False
    edited_version: Optional[Dict] = None


@dataclass
class FeedbackSession:
    """
    Sessão completa de feedback do usuário.

    Attributes:
        session_id: ID único da sessão
        timestamp: Data/hora da sessão
        protocol_name: Nome do protocolo analisado
        model_used: Modelo LLM utilizado
        suggestions_feedback: Lista de feedbacks por sugestão
        general_feedback: Feedback geral sobre a análise
        quality_rating: Avaliação geral (0-10)
    """
    session_id: str
    timestamp: datetime
    protocol_name: str
    model_used: str
    suggestions_feedback: List[SuggestionFeedback]
    general_feedback: Optional[str] = None
    quality_rating: Optional[int] = None


class FeedbackCollector:
    """
    Coleta feedback do usuário sobre sugestões de melhoria.

    Este componente apresenta sugestões interativamente e captura
    feedback estruturado para o sistema de fine-tuning de prompts.

    Fluxo de Coleta:
    1. Apresentar sugestão formatada ao usuário
    2. Perguntar: Relevante? (S/N/Editar/Comentar)
    3. Se Editar: permite edição inline
    4. Se Comentar: captura comentário qualitativo
    5. Armazenar feedback estruturado

    Example:
        >>> collector = FeedbackCollector()
        >>> session = collector.collect_feedback_interactive(suggestions, "protocol.json", "model")
        >>> print(f"Feedback coletado: {len(session.suggestions_feedback)} sugestões")
    """

    def __init__(self, auto_save: bool = True):
        """
        Inicializa o coletor de feedback.

        Args:
            auto_save: Se True, salva automaticamente após coleta
        """
        self.storage = FeedbackStorage()
        self.auto_save = auto_save
        logger.info("FeedbackCollector initialized")

    def collect_feedback_interactive(
        self,
        suggestions: List[Dict],
        protocol_name: str,
        model_used: str,
        skip_if_empty: bool = False
    ) -> FeedbackSession:
        """
        Apresenta sugestões interativamente e coleta feedback.

        Para cada sugestão:
        1. Exibe sugestão formatada
        2. Pergunta: Relevante? (S/N/Editar/Comentar)
        3. Captura resposta e processa
        4. Armazenar feedback estruturado

        Args:
            suggestions: Lista de sugestões para revisão
            protocol_name: Nome do protocolo
            model_used: Modelo LLM utilizado
            skip_if_empty: Se True, retorna sessão vazia se não houver sugestões

        Returns:
            FeedbackSession com todos os feedbacks coletados
        """
        if not suggestions and skip_if_empty:
            logger.info("No suggestions to collect feedback for, skipping")
            return None
        
        if not suggestions:
            logger.warning("No suggestions provided for feedback collection")
            return None
        
        print("\n" + "=" * 60)
        print("FEEDBACK COLLECTION - Human-in-the-Loop")
        print("=" * 60)
        print(f"\nProtocol: {protocol_name}")
        print(f"Model: {model_used}")
        print(f"Total suggestions: {len(suggestions)}")
        print("\nVocê será solicitado a revisar cada sugestão.")
        print("Opções: S (Relevante), N (Irrelevante), E (Editar), C (Comentar)")
        print("=" * 60 + "\n")
        
        # Gerar session ID
        session_id = self.storage._generate_session_id()
        suggestions_feedback = []
        
        # Coletar feedback para cada sugestão
        for idx, suggestion in enumerate(suggestions, 1):
            print(f"\n[{idx}/{len(suggestions)}] Revisando sugestão...")
            print("(Digite 'Q' a qualquer momento para sair do feedback e retornar ao pipeline)")
            
            try:
                feedback = self.capture_user_verdict(suggestion, idx, len(suggestions))
                if feedback is None:  # Usuário saiu
                    print("\n⚠️  Feedback interrompido pelo usuário")
                    print("Retornando ao pipeline principal...")
                    logger.info(f"Feedback collection interrupted by user at suggestion {idx}/{len(suggestions)}")
                    return None  # Retornar None para indicar que feedback foi cancelado
                suggestions_feedback.append(feedback)
            except KeyboardInterrupt:
                print("\n\n⚠️  Feedback interrompido (Ctrl+C)")
                print("Retornando ao pipeline principal...")
                logger.info(f"Feedback collection interrupted by keyboard interrupt")
                return None  # Retornar None para indicar que feedback foi cancelado
        
        # Coletar feedback geral
        print("\n" + "=" * 60)
        print("FEEDBACK GERAL")
        print("=" * 60)
        general_feedback_data = self.collect_general_feedback()
        
        # Criar sessão
        session = FeedbackSession(
            session_id=session_id,
            timestamp=datetime.now(),
            protocol_name=protocol_name,
            model_used=model_used,
            suggestions_feedback=suggestions_feedback,
            general_feedback=general_feedback_data.get("general_feedback"),
            quality_rating=general_feedback_data.get("quality_rating")
        )
        
        # Salvar se auto_save
        if self.auto_save:
            self.storage.save_feedback_session(asdict(session))
            print(f"\n✅ Feedback salvo: {session_id}")
        
        logger.info(f"Feedback collection completed: {session_id}, {len(suggestions_feedback)} suggestions")
        return session

    def present_suggestion(
        self,
        suggestion: Dict,
        index: int,
        total: int
    ) -> None:
        """
        Apresenta uma sugestão formatada ao usuário com contexto ampliado.

        Args:
            suggestion: Sugestão a ser apresentada
            index: Índice da sugestão atual
            total: Total de sugestões
        """
        print("\n" + "=" * 60)
        print(f"SUGESTÃO {index}/{total}")
        print("=" * 60)
        
        # Prioridade com emoji
        priority = suggestion.get("priority", "baixa").upper()
        priority_emoji = {
            "ALTA": "🔴",
            "HIGH": "🔴",
            "MEDIA": "🟡",
            "MEDIUM": "🟡",
            "BAIXA": "🟢",
            "LOW": "🟢"
        }
        emoji = priority_emoji.get(priority, "⚪")
        
        print(f"\n{emoji} PRIORIDADE: {priority}")
        print(f"📁 CATEGORIA: {suggestion.get('category', 'N/A')}")
        print(f"🆔 ID: {suggestion.get('id', 'N/A')}")
        
        # Título
        title = suggestion.get("title", "")
        if title:
            print(f"\n📝 TÍTULO:")
            print(f"   {title}")
        
        # Descrição completa (contexto ampliado)
        description = suggestion.get("description", "")
        if description:
            print(f"\n📄 DESCRIÇÃO COMPLETA:")
            # Quebrar em linhas se muito longo
            if len(description) > 200:
                words = description.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) > 70:
                        if current_line:
                            lines.append(current_line)
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line:
                    lines.append(current_line)
                for line in lines:
                    print(f"   {line}")
            else:
                print(f"   {description}")
        
        # Rationale (justificativa clínica) - contexto adicional
        rationale = suggestion.get("rationale", "")
        if rationale:
            print(f"\n💡 JUSTIFICATIVA CLÍNICA:")
            if len(rationale) > 200:
                words = rationale.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) > 70:
                        if current_line:
                            lines.append(current_line)
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line:
                    lines.append(current_line)
                for line in lines:
                    print(f"   {line}")
            else:
                print(f"   {rationale}")
        
        # Evidence (evidência do playbook) - contexto crítico
        evidence = suggestion.get("evidence", {})
        if evidence:
            print(f"\n📚 EVIDÊNCIA DO PLAYBOOK:")
            playbook_ref = evidence.get("playbook_reference", "")
            context = evidence.get("context", "")
            if playbook_ref:
                print(f"   Referência: {playbook_ref}")
            if context:
                print(f"   Contexto: {context}")
        
        # Impact scores (se disponível)
        impact_scores = suggestion.get("impact_scores", {})
        if impact_scores:
            print(f"\n📊 SCORES DE IMPACTO:")
            if "seguranca" in impact_scores:
                seg = impact_scores["seguranca"]
                bar = "█" * seg + "░" * (10 - seg)
                print(f"   Segurança:   {bar} {seg}/10")
            if "economia" in impact_scores:
                econ = impact_scores["economia"]
                print(f"   Economia:    {econ} (L=Baixa, M=Média, A=Alta)")
            if "eficiencia" in impact_scores:
                eff = impact_scores["eficiencia"]
                print(f"   Eficiência:  {eff} (L=Baixa, M=Média, A=Alta)")
            if "usabilidade" in impact_scores:
                usab = impact_scores["usabilidade"]
                bar = "█" * usab + "░" * (10 - usab)
                print(f"   Usabilidade: {bar} {usab}/10")
        
        # Implementation effort (se disponível)
        implementation = suggestion.get("implementation_effort", {})
        if implementation:
            print(f"\n⚙️  ESFORÇO DE IMPLEMENTAÇÃO:")
            effort = implementation.get("effort", "")
            time_est = implementation.get("estimated_time", "")
            complexity = implementation.get("complexity", "")
            if effort:
                print(f"   Esforço: {effort}")
            if time_est:
                print(f"   Tempo estimado: {time_est}")
            if complexity:
                print(f"   Complexidade: {complexity}")
        
        # Location (se disponível)
        location = suggestion.get("specific_location", {})
        if location:
            print(f"\n📍 LOCALIZAÇÃO NO PROTOCOLO:")
            node_id = location.get("node_id")
            field = location.get("field")
            path = location.get("path")
            if node_id:
                print(f"   Node ID: {node_id}")
            if field:
                print(f"   Campo: {field}")
            if path:
                print(f"   Caminho: {path}")
        
        # Cost estimate (se disponível)
        cost_estimate = suggestion.get("auto_apply_cost_estimate", {})
        if cost_estimate:
            cost = cost_estimate.get("estimated_cost_usd", 0)
            if cost:
                print(f"\n💰 CUSTO ESTIMADO PARA APLICAR: ${cost:.4f} USD")
        
        print("\n" + "-" * 60)

    def capture_user_verdict(
        self,
        suggestion: Dict,
        index: int,
        total: int
    ) -> SuggestionFeedback:
        """
        Captura veredito do usuário sobre uma sugestão.

        Opções:
        - S (Sim, relevante)
        - N (Não, irrelevante)
        - E (Editar sugestão)
        - C (Adicionar comentário)

        Args:
            suggestion: Sugestão sendo avaliada
            index: Índice da sugestão
            total: Total de sugestões

        Returns:
            SuggestionFeedback com veredito e dados adicionais
        """
        # Apresentar sugestão
        self.present_suggestion(suggestion, index, total)
        
        suggestion_id = suggestion.get("id", f"sug-{index}")
        
        while True:
            try:
                print(f"\nEsta sugestão é relevante?")
                print("  S - Sim (Relevante)")
                print("  N - Não (Irrelevante)")
                print("  E - Editar sugestão")
                print("  C - Adicionar comentário")
                print("  P - Pular (marcar como relevante)")
                print("  Q - Sair do feedback (retornar ao pipeline)")
                
                response = input("\nEscolha (S/N/E/C/P/Q): ").strip().upper()
                
                if response in ("Q", "SAIR", "QUIT", "EXIT"):
                    # Usuário quer sair
                    return None
                
                if response in ("S", "SIM", "Y", "YES", "P", "PULAR"):
                    # Relevante
                    verdict = "relevant"
                    comment = None
                    
                    # Perguntar comentário opcional
                    if response == "C" or input("Adicionar comentário? (S/N): ").strip().upper() in ("S", "SIM", "Y", "YES"):
                        comment = self.capture_comment(suggestion)
                    
                    return SuggestionFeedback(
                        suggestion_id=suggestion_id,
                        user_verdict=verdict,
                        user_comment=comment,
                        edited=False
                    )
                
                elif response in ("N", "NAO", "NO"):
                    # Irrelevante
                    verdict = "irrelevant"
                    comment = input("Motivo da rejeição (opcional): ").strip()
                    if not comment:
                        comment = None
                    
                    return SuggestionFeedback(
                        suggestion_id=suggestion_id,
                        user_verdict=verdict,
                        user_comment=comment,
                        edited=False
                    )
                
                elif response in ("E", "EDITAR", "EDIT"):
                    # Editar
                    edited_version = self.allow_edit_suggestion(suggestion)
                    comment = input("Comentário sobre a edição (opcional): ").strip()
                    if not comment:
                        comment = None
                    
                    return SuggestionFeedback(
                        suggestion_id=suggestion_id,
                        user_verdict="edited",
                        user_comment=comment,
                        edited=True,
                        edited_version=edited_version
                    )
                
                elif response in ("C", "COMENTAR", "COMMENT"):
                    # Apenas comentar (mantém como relevante)
                    comment = self.capture_comment(suggestion)
                    return SuggestionFeedback(
                        suggestion_id=suggestion_id,
                        user_verdict="relevant",
                        user_comment=comment,
                        edited=False
                    )
                
                else:
                    print("❌ Opção inválida. Por favor, escolha S, N, E, C ou P.")
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Coleta de feedback cancelada pelo usuário.")
                # Marcar como relevante por padrão se cancelado
                return SuggestionFeedback(
                    suggestion_id=suggestion_id,
                    user_verdict="relevant",
                    user_comment="Feedback cancelado pelo usuário",
                    edited=False
                )

    def allow_edit_suggestion(
        self,
        suggestion: Dict
    ) -> Dict:
        """
        Permite edição inline de uma sugestão.

        Args:
            suggestion: Sugestão original

        Returns:
            Sugestão editada pelo usuário
        """
        print("\n" + "=" * 60)
        print("EDIÇÃO DE SUGESTÃO")
        print("=" * 60)
        print("\nCampos editáveis:")
        print("  1. Título")
        print("  2. Descrição")
        print("  3. Cancelar edição")
        
        edited = suggestion.copy()
        
        while True:
            try:
                choice = input("\nQual campo deseja editar? (1/2/3): ").strip()
                
                if choice == "1":
                    current_title = suggestion.get("title", "")
                    print(f"\nTítulo atual: {current_title}")
                    new_title = input("Novo título (Enter para manter): ").strip()
                    if new_title:
                        edited["title"] = new_title
                        print("✅ Título atualizado")
                
                elif choice == "2":
                    current_desc = suggestion.get("description", "")
                    print(f"\nDescrição atual: {current_desc}")
                    print("Nova descrição (Enter para manter, 'END' para finalizar):")
                    new_desc_lines = []
                    while True:
                        line = input()
                        if line.strip().upper() == "END":
                            break
                        new_desc_lines.append(line)
                    if new_desc_lines:
                        edited["description"] = "\n".join(new_desc_lines)
                        print("✅ Descrição atualizada")
                
                elif choice == "3":
                    print("❌ Edição cancelada")
                    return suggestion
                
                else:
                    print("❌ Opção inválida")
                    continue
                
                # Continuar editando?
                if input("\nEditar outro campo? (S/N): ").strip().upper() not in ("S", "SIM", "Y", "YES"):
                    break
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Edição cancelada")
                return suggestion
        
        return edited

    def capture_comment(
        self,
        suggestion: Dict
    ) -> str:
        """
        Captura comentário qualitativo do usuário.

        Args:
            suggestion: Sugestão sendo comentada

        Returns:
            Comentário do usuário
        """
        print("\n" + "-" * 60)
        print("COMENTÁRIO")
        print("-" * 60)
        print("Digite seu comentário (Enter para finalizar, 'END' em linha vazia para concluir):")
        
        comment_lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END" and not comment_lines:
                    return ""
                if line.strip().upper() == "END":
                    break
                comment_lines.append(line)
            except KeyboardInterrupt:
                print("\n⚠️  Comentário cancelado")
                return ""
        
        comment = "\n".join(comment_lines).strip()
        return comment if comment else None

    def collect_general_feedback(self) -> Dict[str, any]:
        """
        Coleta feedback geral sobre a análise completa.

        Returns:
            Dict com feedback geral e quality rating
        """
        print("\n" + "=" * 60)
        print("FEEDBACK GERAL SOBRE A ANÁLISE")
        print("=" * 60)
        
        # Quality rating
        while True:
            try:
                rating_str = input("\nAvalie a qualidade geral da análise (0-10): ").strip()
                if not rating_str:
                    rating = None
                    break
                rating = int(rating_str)
                if 0 <= rating <= 10:
                    break
                else:
                    print("❌ Por favor, digite um número entre 0 e 10")
            except ValueError:
                print("❌ Por favor, digite um número válido")
            except KeyboardInterrupt:
                rating = None
                break
        
        # General feedback
        print("\nComentários gerais sobre a análise (opcional):")
        print("(Digite 'END' em linha vazia para finalizar)")
        feedback_lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                feedback_lines.append(line)
            except KeyboardInterrupt:
                break
        
        general_feedback = "\n".join(feedback_lines).strip()
        if not general_feedback:
            general_feedback = None
        
        return {
            "quality_rating": rating,
            "general_feedback": general_feedback
        }
