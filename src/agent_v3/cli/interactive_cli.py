"""
Interactive CLI - Motor Principal da CLI

Responsabilidades:
- Gerenciar estado da sessão (onboarding → análise → feedback → auto-apply)
- Renderizar UI rica no terminal (progress bars, spinners, formatação)
- Exibir "thinking" do sistema (o que está sendo feito e por quê)
- Gerenciar tasks visíveis ao usuário (similar ao Claude Code)
- Capturar input do usuário de forma amigável

INSPIRAÇÃO: Claude Code CLI - Transparência total, thinking visível, tasks organizadas

Bibliotecas necessárias:
- rich: UI rica (progress bars, tables, syntax highlighting)
- prompt_toolkit: Input interativo avançado
- questionary: Prompts amigáveis

Fase de Implementação: FASE 4 (5-7 dias)
Status: 🚧 Skeleton - Aguardando implementação
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SessionStage(Enum):
    """Estágios da sessão."""
    ONBOARDING = "onboarding"
    ANALYSIS = "analysis"
    FEEDBACK = "feedback"
    AUTHORIZATION = "authorization"
    AUTO_APPLY = "auto_apply"
    COMPLETE = "complete"


@dataclass
class SessionState:
    """Estado atual da sessão."""
    stage: SessionStage
    protocol_path: Optional[str] = None
    playbook_path: Optional[str] = None
    model: Optional[str] = None
    cost_limit: Optional[float] = None
    analysis_result: Optional[Dict] = None
    feedback_session: Optional[Dict] = None


class InteractiveCLI:
    """
    CLI interativa inspirada no Claude Code.

    Características:
    - Onboarding amigável e guiado
    - Thinking visível (usuário vê o que está acontecendo)
    - Tasks atualizadas em tempo real
    - Formatação rica (cores, tabelas, syntax highlighting)
    - Transparência total do processo

    Example:
        >>> cli = InteractiveCLI()
        >>> cli.run()
    """

    def __init__(self):
        """Inicializa a CLI interativa."""
        self.session_state = SessionState(stage=SessionStage.ONBOARDING)
        # TODO: Inicializar TaskManager
        # TODO: Inicializar DisplayManager

    def run(self) -> None:
        """
        Executa o fluxo completo da CLI.

        Fluxo:
        1. Onboarding
        2. Análise expandida
        3. Feedback loop
        4. Autorização de custo
        5. Auto-apply
        6. Finalização

        TODO: Implementar orquestração completa
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def run_onboarding(self) -> None:
        """
        Onboarding amigável do usuário.

        Etapas:
        1. Apresentação do Agent V3
        2. Seleção de protocolo (com preview)
        3. Seleção de playbook (opcional)
        4. Configuração de modelo LLM
        5. Configuração de limites de custo
        6. Resumo da configuração

        TODO:
            - Criar apresentação visual
            - Implementar seleção interativa
            - Validar configurações
            - Atualizar session_state
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def show_thinking(
        self,
        thought: str,
        duration_estimate: Optional[str] = None
    ) -> None:
        """
        Exibe o 'pensamento' do sistema ao usuário.

        Exemplo:
        💭 Pensando: Carregando protocolo JSON...
        💭 Pensando: Estimando custo da análise... (~30s)

        Args:
            thought: Descrição do que está sendo feito
            duration_estimate: Estimativa de duração (opcional)

        TODO:
            - Formatar thinking com ícone
            - Exibir duração se fornecida
            - Limpar linha anterior
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def update_task_status(
        self,
        task_id: str,
        status: str
    ) -> None:
        """
        Atualiza status de task visível.

        Example:
        ✓ Carregar protocolo JSON
        ⚙ Gerar análise expandida (30s estimado)
        ⏳ Aguardando feedback do usuário

        Args:
            task_id: ID da task
            status: Novo status (pending, in_progress, completed)

        TODO:
            - Delegar para TaskManager
            - Re-renderizar lista de tasks
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def show_progress(
        self,
        step: str,
        progress: float
    ) -> None:
        """
        Exibe barra de progresso com descrição.

        Args:
            step: Descrição da etapa
            progress: Progresso 0.0-1.0

        TODO:
            - Usar rich.Progress
            - Formatar barra de progresso
            - Atualizar em tempo real
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def present_analysis_results(
        self,
        analysis_result: Dict
    ) -> None:
        """
        Apresenta resultados da análise formatados.

        Args:
            analysis_result: Resultado da análise expandida

        TODO:
            - Formatar com rich.Table
            - Agrupar sugestões por categoria
            - Destacar prioridades altas
            - Mostrar scores de impacto
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def _display_welcome_message(self) -> None:
        """
        Exibe mensagem de boas-vindas.

        TODO:
            - Criar banner visual
            - Listar funcionalidades
            - Mostrar instruções básicas
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def _select_protocol_interactive(self) -> str:
        """
        Seleção interativa de protocolo.

        TODO:
            - Listar protocolos disponíveis
            - Mostrar preview (tamanho, versão)
            - Capturar seleção com questionary
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def _select_playbook_interactive(self) -> Optional[str]:
        """
        Seleção interativa de playbook.

        TODO:
            - Listar playbooks disponíveis
            - Permitir pular (opcional)
            - Mostrar preview
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def _select_model_interactive(self) -> str:
        """
        Seleção interativa de modelo LLM.

        TODO:
            - Listar modelos com descrições
            - Mostrar custo relativo
            - Destacar recomendação
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")

    def _configure_cost_limits(self) -> float:
        """
        Configura limites de custo.

        TODO:
            - Perguntar limite desejado
            - Validar valor
            - Mostrar explicação
        """
        raise NotImplementedError("FASE 4 - Aguardando implementação")
