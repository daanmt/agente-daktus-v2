"""
Interactive CLI - Motor Principal da CLI

Responsabilidades:
- Gerenciar estado da sessão (onboarding → análise → feedback → auto-apply)
- Renderizar UI rica no terminal (progress bars, spinners, formatação)
- Exibir "thinking" do sistema (o que está sendo feito e por quê)
- Gerenciar tasks visíveis ao usuário
- Capturar input do usuário de forma amigável

Status: ✅ IMPLEMENTADO (Core & Onboarding)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

# Add project root to path
current_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Load .env first
from dotenv import load_dotenv
env_file = current_dir / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)

# Import CLI components (from same package)
from .display_manager import DisplayManager
from .task_manager import TaskManager, TaskStatus

# Import questionary for interactive prompts
try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    questionary = None

# Import agent components
try:
    from ..analysis.enhanced import EnhancedAnalyzer
    from ..analysis.standard import analyze as v2_analyze
    from ..core.logger import logger
    from ..core.protocol_loader import load_protocol, load_playbook
    from ..feedback import FeedbackCollector
    from ..feedback.memory_qa import MemoryQA
    from ..applicator import ProtocolReconstructor
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False
    EnhancedAnalyzer = None
    v2_analyze = None
    logger = None
    load_protocol = None
    load_playbook = None
    FeedbackCollector = None
    MemoryQA = None
    ProtocolReconstructor = None


class SessionStage(Enum):
    """Estágios da sessão."""
    WELCOME = "welcome"
    ONBOARDING = "onboarding"
    ANALYSIS = "analysis"
    RESULTS_REVIEW = "results_review"
    FEEDBACK = "feedback"
    RECONSTRUCTION = "reconstruction"
    COMPLETE = "complete"


@dataclass
class SessionState:
    """Estado atual da sessão."""
    stage: SessionStage = SessionStage.WELCOME
    protocol_path: Optional[str] = None
    playbook_path: Optional[str] = None
    model: Optional[str] = None
    version: str = "V3"  # "V2" or "V3"
    analysis_result: Optional[Dict] = None
    enhanced_result: Optional[Any] = None  # ExpandedAnalysisResult
    feedback_session: Optional[Any] = None  # FeedbackSession
    reconstruction_result: Optional[Any] = None  # ReconstructionResult
    report_json_path: Optional[Path] = None  # Caminho do relatório JSON salvo
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent)


class InteractiveCLI:
    """
    CLI interativa para análise de protocolos clínicos.

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
        self.session_state = SessionState()
        self.display = DisplayManager()
        self.tasks = TaskManager(console=self.display.console if self.display.rich_available else None)
        self.project_root = self.session_state.project_root

    def run(self) -> None:
        """
        Executa o fluxo completo da CLI.

        Fluxo:
        1. Welcome
        2. Onboarding
        3. Análise expandida
        4. Results review
        5. Feedback loop (opcional)
        6. Reconstruction (opcional)
        7. Finalização
        """
        try:
            # 1. Welcome
            self._run_welcome()

            # 2. Onboarding
            self._run_onboarding()

            # 3. Analysis
            self._run_analysis()

            # 4. Results review
            self._run_results_review()

            # 5. Feedback (opcional)
            if self.session_state.version == "V3" and V3_AVAILABLE:
                self._run_feedback()

            # 6. Reconstruction (opcional)
            if self.session_state.version == "V3" and V3_AVAILABLE:
                self._run_reconstruction()

            # 7. Complete
            self._run_complete()

        except KeyboardInterrupt:
            self.display.show_warning("\nOperação cancelada pelo usuário.")
            sys.exit(0)
        except Exception as e:
            self.display.show_error(f"Erro inesperado: {e}")
            if logger:
                logger.error(f"CLI error: {e}", exc_info=True)
            sys.exit(1)

    def _run_welcome(self) -> None:
        """Exibe mensagem de boas-vindas."""
        self.display.show_banner(
            title="Agente Daktus | QA - Enhanced Analysis",
            subtitle="Validação e Correção Automatizada de Protocolos Clínicos"
        )
        self.display.show_info("Bem-vindo! Este assistente irá guiá-lo através da análise de protocolos clínicos.")
        print()  # Linha em branco

    def _run_onboarding(self) -> None:
        """Onboarding amigável do usuário."""
        self.session_state.stage = SessionStage.ONBOARDING

        # 1. Version selection
        self.session_state.version = self._select_version_interactive()

        # 2. Protocol selection
        self.session_state.protocol_path = self._select_protocol_interactive()
        if not self.session_state.protocol_path:
            self.display.show_error("Seleção de protocolo é obrigatória.")
            sys.exit(1)

        # 3. Playbook selection (optional)
        self.session_state.playbook_path = self._select_playbook_interactive()

        # 4. Model selection
        self.session_state.model = self._select_model_interactive()

        # 5. Configuration summary
        self._show_configuration_summary()

    def _select_version_interactive(self) -> str:
        """Seleção interativa de versão."""
        versions = [
            ("V2", "Agent V2 (Standard) - 5-15 sugestões, mais rápido"),
        ]

        if V3_AVAILABLE:
            versions.append(("V3", "Agent V3 (Enhanced) - 5-50 sugestões, análise completa (prioriza média/alta/crítica)"))
        else:
            self.display.show_warning("Agent V3 não disponível (Enhanced Analyzer não encontrado)")

        if QUESTIONARY_AVAILABLE:
            choices = [f"{v[0]}: {v[1]}" for v in versions]
            answer = questionary.select(
                "Selecione a versão do Agent:",
                choices=choices,
                default=choices[-1] if V3_AVAILABLE else choices[0]
            ).ask()
            selected = answer.split(":")[0]
        else:
            # Fallback simples
            print("\nSELEÇÃO DE VERSÃO")
            print("-" * 60)
            for i, (v, desc) in enumerate(versions, 1):
                print(f"  {i}. {desc}")
            while True:
                try:
                    choice = input("\nSelecione o número: ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(versions):
                        selected = versions[idx][0]
                        break
                    else:
                        print("Número inválido")
                except (ValueError, KeyboardInterrupt):
                    print("Entrada inválida")
                    sys.exit(0)

        self.display.show_success(f"Versão selecionada: Agent {selected}")
        return selected

    def _select_protocol_interactive(self) -> Optional[str]:
        """Seleção interativa de protocolo."""
        protocols = self._list_files("models_json", ".json")

        if not protocols:
            self.display.show_error("Nenhum arquivo de protocolo encontrado em models_json/")
            return None

        if QUESTIONARY_AVAILABLE:
            choices = [f"{p.name} ({self._format_file_size(p)})" for p in protocols]
            answer = questionary.select(
                "Selecione o protocolo para análise:",
                choices=choices
            ).ask()
            selected_name = answer.split(" (")[0]
            selected = next((str(p) for p in protocols if p.name == selected_name), None)
        else:
            # Fallback simples
            print("\nSELEÇÃO DE PROTOCOLO")
            print("-" * 60)
            for i, proto in enumerate(protocols, 1):
                size = self._format_file_size(proto)
                print(f"  {i}. {proto.name} ({size})")
            while True:
                try:
                    choice = input("\nSelecione o número: ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(protocols):
                        selected = str(protocols[idx])
                        break
                    else:
                        print("Número inválido")
                except (ValueError, KeyboardInterrupt):
                    print("Entrada inválida")
                    sys.exit(0)

        if selected:
            self.display.show_success(f"Protocolo selecionado: {Path(selected).name}")
        return selected

    def _select_playbook_interactive(self) -> Optional[str]:
        """Seleção interativa de playbook."""
        playbooks = self._list_files("models_json", ".md")
        playbooks.extend(self._list_files("models_json", ".pdf"))

        if not playbooks:
            self.display.show_info("Nenhum playbook encontrado - análise será apenas estrutural")
            return None

        if QUESTIONARY_AVAILABLE:
            choices = ["Nenhum (análise estrutural apenas)"]
            choices.extend([f"{p.name} ({self._format_file_size(p)})" for p in playbooks])
            answer = questionary.select(
                "Selecione o playbook (opcional):",
                choices=choices,
                default=choices[0]
            ).ask()

            if answer.startswith("Nenhum"):
                return None

            selected_name = answer.split(" (")[0]
            selected = next((str(p) for p in playbooks if p.name == selected_name), None)
        else:
            # Fallback simples
            print("\nSELEÇÃO DE PLAYBOOK")
            print("-" * 60)
            print("  0. Nenhum (análise estrutural apenas)")
            for i, pb in enumerate(playbooks, 1):
                size = self._format_file_size(pb)
                print(f"  {i}. {pb.name} ({size})")
            while True:
                try:
                    choice = input("\nSelecione o número (0 para nenhum): ").strip()
                    if choice == "0":
                        selected = None
                        break
                    idx = int(choice) - 1
                    if 0 <= idx < len(playbooks):
                        selected = str(playbooks[idx])
                        break
                    else:
                        print("Número inválido")
                except (ValueError, KeyboardInterrupt):
                    print("Entrada inválida")
                    sys.exit(0)

        if selected:
            self.display.show_success(f"Playbook selecionado: {Path(selected).name}")
        else:
            self.display.show_info("Análise será apenas estrutural (sem playbook)")
        return selected

    def _select_model_interactive(self) -> str:
        """Seleção interativa de modelo LLM."""
        models = [
            ("x-ai/grok-4.1-fast:free", "Grok 4.1 Fast (Free) - Recomendado", "$0.00"),
            ("x-ai/grok-4.1-fast", "Grok 4.1 Fast", "$0.20/$0.50 por MTok"),
            ("x-ai/grok-code-fast-1", "Grok Code Fast 1", "$0.20/$1.50 por MTok"),
            ("google/gemini-2.5-flash-preview-09-2025", "Gemini 2.5 Flash Preview", "$0.30/$2.50 por MTok"),
            ("google/gemini-2.5-flash", "Gemini 2.5 Flash", "$0.30/$2.50 por MTok"),
            ("google/gemini-2.5-pro", "Gemini 2.5 Pro", "$1.25/$10.00 por MTok"),
            ("anthropic/claude-sonnet-4-20250514", "Claude Sonnet 4.5", "$3.00/$15.00 por MTok"),
            ("anthropic/claude-opus-4-20250514", "Claude Opus 4.5", "$5.00/$25.00 por MTok"),
        ]

        if QUESTIONARY_AVAILABLE:
            choices = [f"{desc} - {cost}" for _, desc, cost in models]
            answer = questionary.select(
                "Selecione o modelo LLM:",
                choices=choices,
                default=choices[0]  # Grok Free como padrão
            ).ask()
            selected_desc = answer.split(" - ")[0]
            selected = next((model_id for model_id, desc, _ in models if desc == selected_desc), models[0][0])
        else:
            # Fallback simples
            print("\nSELEÇÃO DE MODELO")
            print("-" * 60)
            for i, (model_id, desc, cost) in enumerate(models, 1):
                marker = " (Padrão)" if i == 1 else ""
                print(f"  {i}. {desc} - {cost}{marker}")
            print("  0. Padrão (Grok 4.1 Fast Free)")
            while True:
                try:
                    choice = input("\nSelecione o número (0 para padrão): ").strip()
                    if choice == "0" or choice == "":
                        selected = models[0][0]
                        break
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        selected = models[idx][0]
                        break
                    else:
                        print("Número inválido")
                except (ValueError, KeyboardInterrupt):
                    print("Entrada inválida")
                    sys.exit(0)

        self.display.show_success(f"Modelo selecionado: {selected}")
        return selected

    def _show_configuration_summary(self) -> None:
        """Exibe resumo da configuração."""
        summary = {
            "Versão": f"Agent {self.session_state.version}",
            "Protocolo": Path(self.session_state.protocol_path).name if self.session_state.protocol_path else "N/A",
            "Playbook": Path(self.session_state.playbook_path).name if self.session_state.playbook_path else "Nenhum",
            "Modelo": self.session_state.model or "N/A",
        }

        if self.session_state.version == "V3":
            summary["Esperado"] = "5-50 sugestões (prioriza média/alta/crítica)"

        self.display.show_summary_panel("Resumo da Configuração", summary)

        # Confirmação
        if QUESTIONARY_AVAILABLE:
            proceed = questionary.confirm("Prosseguir com a análise?", default=True).ask()
        else:
            proceed = input("\nProsseguir com a análise? (S/n): ").strip().upper() in ("S", "SIM", "Y", "YES", "")

        if not proceed:
            self.display.show_info("Análise cancelada pelo usuário.")
            sys.exit(0)

    def _list_files(self, directory: str, extension: str) -> List[Path]:
        """Lista arquivos em um diretório com extensão específica."""
        path = self.project_root / directory
        if not path.exists():
            return []
        return sorted(path.glob(f"*{extension}"))

    def _format_file_size(self, file_path: Path) -> str:
        """Formata tamanho de arquivo de forma legível."""
        try:
            size = file_path.stat().st_size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except Exception:
            return "N/A"

    def _run_analysis(self) -> None:
        """Executa análise com task tracking e progress display."""
        self.session_state.stage = SessionStage.ANALYSIS

        # Criar tasks
        self.tasks.add_task("load_protocol", "Carregar protocolo JSON", "5s")
        self.tasks.add_task("load_playbook", "Carregar playbook", "10s")
        if self.session_state.version == "V3":
            self.tasks.add_task("analyze", "Gerar análise expandida (5-50 sugestões, prioriza média/alta/crítica)", "60-90s")
        else:
            self.tasks.add_task("analyze", "Gerar análise padrão (5-15 sugestões)", "30-60s")

        # Renderizar tasks iniciais
        self.tasks.render_tasks(self.display)
        print()

        try:
            with self.display.create_progress_bar("Análise em andamento", total=4) as progress:
                pb_task = progress.add_task("Preparando análise", total=4)

                # Task 1: Load protocol
                self.tasks.update_status("load_protocol", TaskStatus.IN_PROGRESS)
                if not load_protocol:
                    raise ImportError("load_protocol não disponível")

                with self.display.spinner("Carregando protocolo..."):
                    protocol_path_to_load = self.session_state.protocol_path
                    edited_path = Path(str(protocol_path_to_load).replace('.json', '_EDITED.json'))
                    if edited_path.exists():
                        logger.info(f"Using EDITED protocol for analysis: {edited_path.name}")
                        protocol_path_to_load = edited_path
                    protocol_json = load_protocol(protocol_path_to_load)

                progress.update(pb_task, advance=1)
                self.tasks.mark_completed("load_protocol")
                self.tasks.render_tasks(self.display)
                print()

                # Task 2: Load playbook (se fornecido)
                playbook_content = ""
                self.tasks.update_status("load_playbook", TaskStatus.IN_PROGRESS)
                if self.session_state.playbook_path:
                    if not load_playbook:
                        raise ImportError("load_playbook não disponível")
                    with self.display.spinner("Carregando playbook..."):
                        playbook_content = load_playbook(self.session_state.playbook_path)
                    self.tasks.mark_completed("load_playbook")
                else:
                    self.tasks.mark_completed("load_playbook")  # Skip
                progress.update(pb_task, advance=1)
                self.tasks.render_tasks(self.display)
                print()

                # Task 3: Run analysis
                self.tasks.update_status("analyze", TaskStatus.IN_PROGRESS)
                self.display.show_thinking("Executando análise expandida, isso pode levar até 90s...")
                with self.display.spinner("Executando análise LLM..."):
                    if self.session_state.version == "V3" and V3_AVAILABLE and EnhancedAnalyzer:
                        analyzer = EnhancedAnalyzer(model=self.session_state.model)
                        enhanced_result = analyzer.analyze_comprehensive(
                            protocol_json=protocol_json,
                            playbook_content=playbook_content,
                            protocol_path=str(self.session_state.protocol_path)
                        )

                        # Converter para formato dict (enxuto)
                        suggestions_dict = [
                            {
                                "id": s.id,
                                "category": s.category,
                                "priority": s.priority,
                                "title": s.title,
                                "description": s.description,
                                "impact_scores": {
                                    "seguranca": s.impact_scores.seguranca if hasattr(s.impact_scores, 'seguranca') else 0,
                                    "economia": s.impact_scores.economia if hasattr(s.impact_scores, 'economia') else "N/A",
                                    "eficiencia": s.impact_scores.eficiencia if hasattr(s.impact_scores, 'eficiencia') else "N/A",
                                    "usabilidade": s.impact_scores.usabilidade if hasattr(s.impact_scores, 'usabilidade') else 0,
                                },
                                "location": s.specific_location or {},
                                "action": s.description[:150] if s.description else s.title
                            }
                            for s in enhanced_result.improvement_suggestions
                        ]

                        result = {
                            "improvement_suggestions": suggestions_dict,
                            "metadata": {
                                "protocol_path": self._normalize_path(str(self.session_state.protocol_path)),
                                "playbook_path": self._normalize_path(str(self.session_state.playbook_path)) if self.session_state.playbook_path else None,
                                "model_used": self.session_state.model,
                                "timestamp": datetime.now().isoformat(),
                                "version": "V3",
                                "suggestions_count": len(enhanced_result.improvement_suggestions)
                            }
                        }

                        self.session_state.enhanced_result = enhanced_result
                        self.session_state.analysis_result = result

                    else:
                        # V2 Standard Analysis
                        if not v2_analyze:
                            raise ImportError("v2_analyze não disponível")
                        
                        result = v2_analyze(
                            protocol_path=self.session_state.protocol_path,
                            playbook_path=self.session_state.playbook_path,
                            model=self.session_state.model
                        )
                        result["metadata"]["version"] = "V2"
                        self.session_state.analysis_result = result

                self.tasks.mark_completed("analyze")
                progress.update(pb_task, advance=1)
                self.tasks.render_tasks(self.display)
                print()

                # Task 4: Salvar relatórios
                with self.display.spinner("Salvando relatórios..."):
                    self._save_reports(result)
                progress.update(pb_task, advance=1)

            suggestions_count = len(result.get('improvement_suggestions', []))
            self.display.show_success(f"Análise concluída! {suggestions_count} sugestões geradas.")

            if self.session_state.version == "V3":
                expected_range = "5-50"
                status = "✅ PASSOU" if 5 <= suggestions_count <= 50 else "⚠️  FORA DO ESPERADO"
                self.display.show_info(f"Esperado: {expected_range} sugestões (prioriza média/alta/crítica) | Status: {status}")

        except Exception as e:
            self.tasks.mark_failed("analyze", str(e))
            self.tasks.render_tasks(self.display)
            self.display.show_error(f"Erro durante análise: {e}")
            if logger:
                logger.error(f"Analysis error: {e}", exc_info=True)
            raise

    def _run_results_review(self) -> None:
        """Revisa resultados da análise."""
        self.session_state.stage = SessionStage.RESULTS_REVIEW

        if not self.session_state.analysis_result:
            self.display.show_warning("Nenhum resultado disponível para revisão.")
            return

        suggestions = self.session_state.analysis_result.get('improvement_suggestions', [])
        
        if not suggestions:
            self.display.show_info("Nenhuma sugestão gerada.")
            return

        # Exibir tabela de sugestões
        self.display.show_suggestions_table(suggestions, max_rows=20)

        # Exibir resumo
        alta = [s for s in suggestions if s.get('priority', '').lower() in ('alta', 'high')]
        media = [s for s in suggestions if s.get('priority', '').lower() in ('media', 'medium')]
        baixa = [s for s in suggestions if s.get('priority', '').lower() in ('baixa', 'low')]

        summary = {
            "Total": len(suggestions),
            "Alta Prioridade": len(alta),
            "Média Prioridade": len(media),
            "Baixa Prioridade": len(baixa)
        }

        self.display.show_summary_panel("Resumo da Análise", summary)

    def _run_feedback(self) -> None:
        """Executa feedback loop."""
        if not V3_AVAILABLE or not FeedbackCollector:
            return

        suggestions_count = len(self.session_state.analysis_result.get('improvement_suggestions', []))
        if suggestions_count == 0:
            return

        self.session_state.stage = SessionStage.FEEDBACK

        self.display.show_banner(
            title="Feedback Loop - Human-in-the-Loop",
            subtitle="Sua opinião ajuda a melhorar futuras análises"
        )

        self.display.show_info("Agora que você pode revisar os relatórios salvos, deseja fornecer feedback?")
        self.display.show_info("O feedback ajudará a melhorar futuras análises e refinar os prompts.")

        if QUESTIONARY_AVAILABLE:
            collect_feedback = questionary.confirm(
                "Deseja fornecer feedback?",
                default=False
            ).ask()
        else:
            choice = input("\nDeseja fornecer feedback? (S/N): ").strip().upper()
            collect_feedback = choice in ("S", "SIM", "Y", "YES")

        if not collect_feedback:
            self.display.show_info("Feedback não coletado. Continuando...")
            return

        try:
            collector = FeedbackCollector()
            
            # Preparar sugestões para feedback
            if self.session_state.enhanced_result:
                suggestions_dict = [s.to_dict() for s in self.session_state.enhanced_result.improvement_suggestions]
            else:
                suggestions_dict = self.session_state.analysis_result.get('improvement_suggestions', [])

            protocol_name = Path(self.session_state.protocol_path).stem
            feedback_session = collector.collect_feedback_interactive(
                suggestions=suggestions_dict,
                protocol_name=protocol_name,
                model_used=self.session_state.model,
                skip_if_empty=False
            )

            if feedback_session is None:
                self.display.show_info("Feedback não coletado. Continuando...")
            else:
                # feedback_session pode ser parcial (quando usuário saiu com Q)
                feedback_count = len(feedback_session.suggestions_feedback) if hasattr(feedback_session, 'suggestions_feedback') else 0
                if feedback_count > 0:
                    self.display.show_info(f"Feedback parcial coletado: {feedback_count} sugestões revisadas")
                self.session_state.feedback_session = feedback_session
                
                # Salvar feedback no memory_qa.md (garantir que foi salvo)
                self._save_feedback_to_memory_qa(feedback_session)
                
                self.display.show_success("Feedback coletado e salvo na memória!")
                
                # Análise automática de padrões e edição do relatório (em paralelo)
                if MemoryQA and self.session_state.analysis_result:
                    try:
                        memory_qa = MemoryQA()
                        
                        # Converter FeedbackSession para dict se necessário
                        if hasattr(feedback_session, '__dict__'):
                            feedback_dict = asdict(feedback_session) if hasattr(feedback_session, '__dict__') else feedback_session
                        else:
                            feedback_dict = feedback_session
                        
                        # Converter datetime para string se necessário
                        if isinstance(feedback_dict.get('timestamp'), datetime):
                            feedback_dict['timestamp'] = feedback_dict['timestamp'].isoformat()
                        
                        # Usar caminho do relatório salvo anteriormente
                        txt_report_path = getattr(self.session_state, "report_txt_path", None)

                        # Análise automática de padrões (simples + LLM) + edição do relatório
                        self.display.show_info("Analisando padrões de feedback e editando relatório...")
                        with self.display.spinner("Processando feedback e editando relatório..."):
                            patterns, edited_report = memory_qa.analyze_feedback_patterns(
                                feedback_sessions=[feedback_dict],
                                analysis_report=self.session_state.analysis_result,
                                report_path=None,
                                txt_report_path=txt_report_path
                            )

                        # Guardar relatório editado em memória para reconstrução
                        if edited_report:
                            self.session_state.edited_report = edited_report
                        
                        if patterns:
                            self.display.show_info(f"Identificados {len(patterns)} padrões de feedback")
                            for pattern in patterns:
                                severity_icon = "🔴" if pattern.severity == "alta" else "🟡" if pattern.severity == "media" else "🟢"
                                self.display.show_info(f"  {severity_icon} {pattern.pattern_type}: {pattern.description}")
                            
                            self.display.show_success("Padrões adicionados ao memory_qa.md para refinar análises futuras!")
                            
                            # Atualizar relatório TXT usando função robusta com atomic operations
                            # Atualizar TXT com dados em memória (sem _EDITED.json)
                            if edited_report and txt_report_path:
                                success = memory_qa.update_txt_report_from_edited_data(
                                    edited_report=edited_report,
                                    txt_report_path=txt_report_path,
                                    version=self.session_state.version
                                )
                                if success:
                                    self.display.show_success(f"✅ Relatório TXT atualizado com segurança: {txt_report_path.name}")
                                    self.display.show_info("   • Backup criado automaticamente")
                                    self.display.show_info("   • Operação atômica (sem corrupção de arquivo)")
                                else:
                                    self.display.show_warning("⚠️  Falha ao atualizar relatório TXT (rollback aplicado se necessário)")
                                    if logger:
                                        logger.warning("TXT update failed, check logs for details")
                            elif not txt_report_path:
                                self.display.show_warning("Caminho do relatório TXT não encontrado para edição")
                        else:
                            self.display.show_info("Nenhum padrão significativo identificado.")
                            
                    except Exception as e:
                        self.display.show_warning(f"Erro ao analisar padrões: {e}")
                        if logger:
                            logger.error(f"Pattern analysis error: {e}", exc_info=True)

        except Exception as e:
            self.display.show_error(f"Erro ao coletar feedback: {e}")
            if logger:
                logger.error(f"Feedback collection error: {e}", exc_info=True)

    def _run_reconstruction(self) -> None:
        """Executa reconstrução de protocolo."""
        if not V3_AVAILABLE or not ProtocolReconstructor:
            return

        suggestions_count = len(self.session_state.analysis_result.get('improvement_suggestions', []))
        if suggestions_count == 0:
            return

        self.session_state.stage = SessionStage.RECONSTRUCTION

        self.display.show_banner(
            title="Reconstrução do Protocolo JSON",
            subtitle="Aplicar sugestões automaticamente ao protocolo"
        )

        self.display.show_info("Deseja reconstruir o arquivo JSON do protocolo aplicando as sugestões?")
        self.display.show_info("O protocolo original será preservado e um novo arquivo será criado.")

        if QUESTIONARY_AVAILABLE:
            reconstruct = questionary.confirm(
                "Deseja reconstruir o protocolo?",
                default=False
            ).ask()
        else:
            choice = input("\nDeseja reconstruir o protocolo? (S/N): ").strip().upper()
            reconstruct = choice in ("S", "SIM", "Y", "YES")

        if not reconstruct:
            self.display.show_info("Reconstrução cancelada.")
            return

        try:
            with self.display.create_progress_bar("Reconstrução em andamento", total=4) as progress:
                pb_task = progress.add_task("Preparando reconstrução", total=4)

                # Preparar sugestões editadas em memória (pós-feedback); fallback para originais
                edited_report = getattr(self.session_state, "edited_report", None)
                if edited_report:
                    suggestions_for_reconstruction = edited_report.get("improvement_suggestions", [])
                    rejected_count = len(edited_report.get("rejected_suggestions", []))
                    if rejected_count > 0:
                        self.display.show_info(f"📝 Usando apenas sugestões aprovadas: {len(suggestions_for_reconstruction)} relevantes, {rejected_count} rejeitadas")
                else:
                    if self.session_state.enhanced_result:
                        suggestions_for_reconstruction = [s.to_dict() for s in self.session_state.enhanced_result.improvement_suggestions]
                    else:
                        suggestions_for_reconstruction = self.session_state.analysis_result.get('improvement_suggestions', [])

                progress.update(pb_task, advance=1)

                if not suggestions_for_reconstruction:
                    self.display.show_warning("Nenhuma sugestão disponível para reconstrução")
                    return

                # Carregar protocolo original
                if not load_protocol:
                    raise ImportError("load_protocol não disponível")

                protocol_path_to_load = self.session_state.protocol_path
                with self.display.spinner("Carregando protocolo para reconstrução..."):
                    protocol_json = load_protocol(protocol_path_to_load)

                progress.update(pb_task, advance=1)

                # Reconstruir
                self.display.show_thinking("Aplicando sugestões aprovadas no protocolo...")
                with self.display.spinner("Aplicando sugestões..."):
                    reconstructor = ProtocolReconstructor(model=self.session_state.model)
                    reconstruction_result = reconstructor.reconstruct_protocol(
                        original_protocol=protocol_json,
                        suggestions=suggestions_for_reconstruction,
                        analysis_result=self.session_state.enhanced_result
                    )

                progress.update(pb_task, advance=1)

                if reconstruction_result:
                    # Salvar protocolo reconstruído
                    from ..applicator.version_utils import (
                        generate_output_filename,
                        update_protocol_version
                    )

                    reconstructed_protocol = reconstruction_result.reconstructed_protocol
                    output_filename, new_version = generate_output_filename(
                        protocol_json=reconstructed_protocol,
                        protocol_path=self.session_state.protocol_path,
                        suffix="RECONSTRUCTED"
                    )

                    reconstructed_protocol = update_protocol_version(
                        reconstructed_protocol,
                        new_version
                    )

                    output_dir = self.project_root / "models_json"
                    output_path = output_dir / output_filename

                    with self.display.spinner("Gravando protocolo reconstruído..."):
                        import json
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(reconstructed_protocol, f, ensure_ascii=False, indent=2)

                    progress.update(pb_task, advance=1)

                    # Exibir resultados
                    changes = reconstruction_result.changes_applied
                    if changes:
                        self.display.show_diff(changes)

                    summary = {
                        "Arquivo": str(output_path),
                        "Versão": f"{reconstruction_result.metadata.get('original_version', 'N/A')} → {new_version}",
                        "Sugestões Aplicadas": len(changes),
                        "Validação": "✅ PASSOU" if reconstruction_result.validation_passed else "❌ FALHOU"
                    }
                    self.display.show_summary_panel("Reconstrução Concluída", summary)

                    self.session_state.reconstruction_result = reconstruction_result
                    self.display.show_success("Protocolo reconstruído com sucesso!")
                else:
                    self.display.show_warning("Reconstrução não concluída")

        except Exception as e:
            self.display.show_error(f"Erro ao reconstruir protocolo: {e}")
            if logger:
                logger.error(f"Reconstruction error: {e}", exc_info=True)

    def _save_reports(self, result: Dict) -> None:
        """Salva apenas relatório texto (JSON permanece em memória)."""
        try:
            from ..applicator.version_utils import generate_daktus_timestamp

            protocol_name = Path(self.session_state.protocol_path).stem
            timestamp = generate_daktus_timestamp()
            reports_dir = self.project_root / "reports"
            reports_dir.mkdir(exist_ok=True)

            # Salvar texto
            txt_path = reports_dir / f"{protocol_name}_{timestamp}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"AGENT {self.session_state.version} - PROTOCOL ANALYSIS REPORT\n")
                f.write("=" * 60 + "\n\n")

                metadata = result.get("metadata", {})
                f.write("METADATA\n")
                f.write("-" * 60 + "\n")
                f.write(f"Protocol: {metadata.get('protocol_path', 'N/A')}\n")
                f.write(f"Playbook: {metadata.get('playbook_path', 'None')}\n")
                f.write(f"Model: {metadata.get('model_used', 'N/A')}\n")
                f.write(f"Timestamp: {metadata.get('timestamp', 'N/A')}\n\n")

                suggestions = result.get("improvement_suggestions", [])
                f.write(f"IMPROVEMENT SUGGESTIONS: {len(suggestions)}\n")
                f.write("=" * 60 + "\n\n")

                if suggestions:
                    # Agrupar por prioridade
                    def normalize_priority(priority):
                        if not priority:
                            return 'baixa'
                        priority_lower = str(priority).lower()
                        if priority_lower in ('alta', 'high', 'critical'):
                            return 'alta'
                        elif priority_lower in ('media', 'medium', 'moderate'):
                            return 'media'
                        else:
                            return 'baixa'
                    
                    alta = [s for s in suggestions if normalize_priority(s.get('priority')) == 'alta']
                    media = [s for s in suggestions if normalize_priority(s.get('priority')) == 'media']
                    baixa = [s for s in suggestions if normalize_priority(s.get('priority')) == 'baixa']
                    
                    if alta:
                        f.write("ALTA PRIORIDADE:\n")
                        f.write("-" * 60 + "\n")
                        for i, sug in enumerate(alta, 1):
                            sug_id = sug.get('id', f'SUG{i:02d}')
                            title = sug.get('title', sug.get('description', 'N/A'))
                            category = sug.get('category', 'N/A')
                            f.write(f"{i}. [{sug_id}] {title}\n")
                            f.write(f"   Categoria: {category}\n")
                            if sug.get('description') and sug.get('description') != title:
                                desc = sug.get('description', '')[:200]
                                f.write(f"   Descrição: {desc}\n")
                            f.write("\n")
                    
                    if media:
                        f.write("MÉDIA PRIORIDADE:\n")
                        f.write("-" * 60 + "\n")
                        for i, sug in enumerate(media, 1):
                            sug_id = sug.get('id', f'SUG{i:02d}')
                            title = sug.get('title', sug.get('description', 'N/A'))
                            category = sug.get('category', 'N/A')
                            f.write(f"{i}. [{sug_id}] {title}\n")
                            f.write(f"   Categoria: {category}\n")
                            if sug.get('description') and sug.get('description') != title:
                                desc = sug.get('description', '')[:200]
                                f.write(f"   Descrição: {desc}\n")
                            f.write("\n")
                    
                    if baixa:
                        f.write("BAIXA PRIORIDADE:\n")
                        f.write("-" * 60 + "\n")
                        for i, sug in enumerate(baixa, 1):
                            sug_id = sug.get('id', f'SUG{i:02d}')
                            title = sug.get('title', sug.get('description', 'N/A'))
                            category = sug.get('category', 'N/A')
                            f.write(f"{i}. [{sug_id}] {title}\n")
                            f.write(f"   Categoria: {category}\n")
                            if sug.get('description') and sug.get('description') != title:
                                desc = sug.get('description', '')[:200]
                                f.write(f"   Descrição: {desc}\n")
                            f.write("\n")
                else:
                    f.write("Nenhuma sugestão de melhoria gerada.\n")

            # Armazenar caminho do TXT para atualizações futuras
            self.session_state.report_txt_path = txt_path

            self.display.show_info(f"Relatório salvo: {txt_path.name}")

        except Exception as e:
            self.display.show_warning(f"Erro ao salvar relatórios: {e}")

    def _save_feedback_to_memory_qa(self, feedback_session: Any) -> None:
        """Salva feedback no memory_qa.md (sistema simples de memória)."""
        try:
            from ..feedback.memory_qa import MemoryQA
            
            memory_qa = MemoryQA()
            
            # Converter FeedbackSession para dict
            if hasattr(feedback_session, '__dict__'):
                feedback_dict = asdict(feedback_session)
            else:
                feedback_dict = feedback_session
            
            # Adicionar ao memory_qa.md
            memory_qa.add_feedback_session(
                feedback_session=feedback_dict,
                analysis_report=self.session_state.analysis_result
            )
            
            self.display.show_info("Feedback adicionado ao memory_qa.md")
            
        except Exception as e:
            self.display.show_warning(f"Erro ao salvar feedback no memory_qa.md: {e}")
            if logger:
                logger.error(f"Error saving feedback to memory_qa.md: {e}", exc_info=True)

    def _normalize_path(self, path_str: str) -> str:
        """Normaliza caminho para relativo."""
        if not path_str:
            return path_str
        try:
            path = Path(path_str)
            if path.is_absolute():
                try:
                    return str(path.relative_to(self.project_root)).replace('\\', '/')
                except ValueError:
                    return path.name
            return str(path).replace('\\', '/')
        except Exception:
            return Path(path_str).name if path_str else path_str

    def _run_complete(self) -> None:
        """Finaliza a sessão."""
        self.session_state.stage = SessionStage.COMPLETE
        self.display.show_banner(
            title="Sessão Concluída",
            subtitle="Obrigado por usar o Agente Daktus | QA!"
        )


def main():
    """Entry point para a CLI interativa."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()

