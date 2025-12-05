"""
Agente Daktus | QA - CLI Interface

Unified CLI supporting both Standard and Enhanced analysis modes.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# CRITICAL: Load .env FIRST, before any other imports
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

# Calculate project root: src/cli/run_qa_cli.py -> project root
project_root = Path(__file__).resolve().parent.parent.parent
env_file = project_root / ".env"

# Load .env from project root
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    # Fallback: try current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
    else:
        load_dotenv(override=True)

# Add src to path AFTER loading .env
current_dir = project_root
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import Agent unified modules
try:
    from agent.analysis.standard import analyze as v2_analyze
    from agent.core.logger import logger
    from agent.core.protocol_loader import load_protocol, load_playbook
except ImportError as e:
    print(f"ERROR: Error importing Agent core: {e}")
    print(f"Make sure you're running from the project root")
    sys.exit(1)

# Import Agent Enhanced Analyzer (optional)
try:
    from agent.analysis.enhanced import EnhancedAnalyzer
    from agent.feedback import FeedbackCollector, PromptRefiner
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False


def print_header(version: str = "V2"):
    """Print CLI header"""
    print("\n" + "=" * 60)
    print(f"AGENT {version} - Clinical Protocol Analysis")
    print("=" * 60 + "\n")


def list_files(directory: str, extension: str) -> list[Path]:
    """List files in directory with extension (relative to project root)"""
    # Use project root as base for relative paths
    if Path(directory).is_absolute():
        path = Path(directory)
    else:
        # Relative to project root
        path = project_root / directory
    
    if not path.exists():
        return []
    return sorted(path.glob(f"*{extension}"))


def select_protocol() -> Optional[str]:
    """Select protocol file"""
    print("PROTOCOL SELECTION")
    print("-" * 60)
    
    protocols = list_files("models_json", ".json")
    
    if not protocols:
        models_path = project_root / "models_json"
        print(f"ERROR: No protocol files found in models_json/")
        print(f"  Looking in: {models_path}")
        print(f"  Directory exists: {models_path.exists()}")
        if models_path.exists():
            all_files = list(models_path.iterdir())
            print(f"  Files in directory: {len(all_files)}")
            for f in all_files[:5]:
                print(f"    - {f.name}")
        return None
    
    for i, proto in enumerate(protocols, 1):
        print(f"  {i}. {proto.name}")
    
    while True:
        try:
            choice = input("\nSelect protocol number: ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(protocols):
                selected = str(protocols[idx])
                print(f"Selected: {protocols[idx].name}\n")
                return selected
            else:
                print("ERROR: Invalid number")
        except ValueError:
            print("ERROR: Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled")
            sys.exit(0)


def select_playbook() -> Optional[str]:
    """Select playbook file"""
    print("PLAYBOOK SELECTION")
    print("-" * 60)
    
    playbooks = list_files("models_json", ".md")
    playbooks.extend(list_files("models_json", ".pdf"))
    
    if not playbooks:
        print("WARNING: No playbook files found in models_json/")
        print("   Analysis will be structural only\n")
        return None
    
    for i, pb in enumerate(playbooks, 1):
        print(f"  {i}. {pb.name}")
    print(f"  0. None (structural analysis only)")
    
    while True:
        try:
            choice = input("\nSelect playbook number (0 for none): ").strip()
            
            if choice == "0":
                print("No playbook selected - structural analysis only\n")
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(playbooks):
                selected = str(playbooks[idx])
                print(f"Selected: {playbooks[idx].name}\n")
                return selected
            else:
                print("ERROR: Invalid number")
        except ValueError:
            print("ERROR: Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled")
            sys.exit(0)


def select_version() -> str:
    """Select Agent version (V2 or V3)"""
    print("VERSION SELECTION")
    print("-" * 60)
    
    versions = [
        ("V2", "Agent V2 (5-15 suggestions, faster)"),
    ]
    
    if V3_AVAILABLE:
        versions.append(("V3", "Agent V3 Enhanced (20-50 suggestions, comprehensive)"))
    else:
        print("⚠️  Agent V3 not available (Enhanced Analyzer not found)")
    
    for i, (v, desc) in enumerate(versions, 1):
        print(f"  {i}. {desc}")
    
    while True:
        try:
            choice = input("\nSelect version number: ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(versions):
                selected = versions[idx][0]
                print(f"Selected: {versions[idx][1]}\n")
                return selected
            else:
                print("ERROR: Invalid number")
        except ValueError:
            print("ERROR: Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled")
            sys.exit(0)


def select_model() -> str:
    """Select LLM model"""
    print("MODEL SELECTION")
    print("-" * 60)
    
    # Available models
    models = [
        ("x-ai/grok-4.1-fast:free", "Grok 4.1 Fast (Free) - Default - Recommended"),
        ("x-ai/grok-4.1-fast", "Grok 4.1 Fast"),
        ("x-ai/grok-code-fast-1", "Grok Code Fast 1"),
        ("google/gemini-2.5-flash-preview-09-2025", "Gemini 2.5 Flash Preview"),
        ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
        ("google/gemini-2.5-pro", "Gemini 2.5 Pro"),
        ("anthropic/claude-sonnet-4-20250514", "Claude Sonnet 4.5"),
        ("anthropic/claude-opus-4-20250514", "Claude Opus 4.5"),
        ("openai/gpt-5-mini", "GPT-5 Mini"),
    ]
    
    for i, (model_id, description) in enumerate(models, 1):
        print(f"  {i}. {description}")
    print(f"  0. Default (Grok 4.1 Fast Free)")
    
    while True:
        try:
            choice = input("\nSelect model number (0 for default): ").strip()
            
            if choice == "0" or choice == "":
                model_id = "x-ai/grok-4.1-fast:free"
                print(f"Using default: Grok 4.1 Fast (Free)\n")
                return model_id
            
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                model_id = models[idx][0]
                print(f"Selected: {models[idx][1]}\n")
                return model_id
            else:
                print("ERROR: Invalid number")
        except ValueError:
            print("ERROR: Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled")
            sys.exit(0)


def normalize_path(path_str: str, project_root: Path) -> str:
    """
    Normaliza caminho absoluto para relativo ao projeto.
    
    Args:
        path_str: Caminho (absoluto ou relativo)
        project_root: Raiz do projeto
        
    Returns:
        Caminho relativo ao projeto ou nome do arquivo se não estiver no projeto
    """
    if not path_str:
        return path_str
    
    try:
        path = Path(path_str)
        if path.is_absolute():
            try:
                # Tenta tornar relativo ao projeto
                rel_path = path.relative_to(project_root)
                return str(rel_path).replace('\\', '/')  # Normalizar separadores
            except ValueError:
                # Se não estiver dentro do projeto, retorna apenas o nome do arquivo
                return path.name
        else:
            # Já é relativo, normalizar separadores
            return str(path).replace('\\', '/')
    except Exception:
        # Em caso de erro, retorna o nome do arquivo
        return Path(path_str).name if path_str else path_str


def save_report(result: dict, protocol_name: str, project_root: Path, version: str = "V2"):
    """Save analysis report"""
    from datetime import datetime
    import json
    from agent.applicator.version_utils import generate_daktus_timestamp
    
    # Normalizar caminhos nos metadados antes de salvar
    if "metadata" in result:
        metadata = result["metadata"]
        if "protocol_path" in metadata:
            metadata["protocol_path"] = normalize_path(metadata["protocol_path"], project_root)
        if "playbook_path" in metadata:
            metadata["playbook_path"] = normalize_path(metadata["playbook_path"], project_root) if metadata.get("playbook_path") else None
    
    # Usar formato de timestamp Daktus Studio: DD-MM-YYYY-HHMM
    timestamp = generate_daktus_timestamp()
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Save JSON - ENXUTO (sem indentação para economizar espaço/tokens)
    json_path = reports_dir / f"{protocol_name}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    
    # Save text report
    txt_path = reports_dir / f"{protocol_name}_{timestamp}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write(f"AGENT {version} - PROTOCOL ANALYSIS REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        # Metadata
        metadata = result.get("metadata", {})
        f.write("METADATA\n")
        f.write("-" * 60 + "\n")
        f.write(f"Protocol: {metadata.get('protocol_path', 'N/A')}\n")
        f.write(f"Playbook: {metadata.get('playbook_path', 'None')}\n")
        f.write(f"Model: {metadata.get('model_used', 'N/A')}\n")
        f.write(f"Timestamp: {metadata.get('timestamp', 'N/A')}\n")
        f.write(f"Processing Time: {metadata.get('processing_time_ms', 0)}ms\n\n")
        
        # Improvement Suggestions
        improvements = result.get("improvement_suggestions", [])
        f.write("IMPROVEMENT SUGGESTIONS\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total: {len(improvements)} suggestions\n\n")
        
        if improvements:
            # Group by priority (aceita tanto português quanto inglês)
            def normalize_priority(priority):
                """Normaliza prioridade para português"""
                if not priority:
                    return 'baixa'
                priority_lower = str(priority).lower()
                if priority_lower in ('alta', 'high', 'critical'):
                    return 'alta'
                elif priority_lower in ('media', 'medium', 'moderate'):
                    return 'media'
                else:
                    return 'baixa'
            
            alta = [imp for imp in improvements if normalize_priority(imp.get('priority')) == 'alta']
            media = [imp for imp in improvements if normalize_priority(imp.get('priority')) == 'media']
            baixa = [imp for imp in improvements if normalize_priority(imp.get('priority')) == 'baixa']
            
            if alta:
                f.write("ALTA PRIORIDADE:\n")
                for i, imp in enumerate(alta, 1):
                    f.write(f"  {i}. {imp.get('title', imp.get('description', 'N/A'))}\n")
                f.write("\n")
            
            if media:
                f.write("MÉDIA PRIORIDADE:\n")
                for i, imp in enumerate(media, 1):
                    f.write(f"  {i}. {imp.get('title', imp.get('description', 'N/A'))}\n")
                f.write("\n")
            
            if baixa:
                f.write("BAIXA PRIORIDADE:\n")
                for i, imp in enumerate(baixa, 1):
                    f.write(f"  {i}. {imp.get('title', imp.get('description', 'N/A'))}\n")
                f.write("\n")
        else:
            f.write("No improvement suggestions.\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("Full JSON report saved to: " + str(json_path) + "\n")
        f.write("=" * 60 + "\n")
    
    return json_path, txt_path


def main():
    """Main CLI function"""
    # Step 0: Select version
    version = select_version()
    print_header(version)
    
    try:
        # Step 1: Select protocol
        protocol_path = select_protocol()
        if not protocol_path:
            print("ERROR: Protocol selection required")
            sys.exit(1)
        
        # Step 2: Select playbook
        playbook_path = select_playbook()
        
        # Step 3: Select model
        model = select_model()
        
        # Step 4: Confirm
        print("CONFIGURATION")
        print("-" * 60)
        print(f"Version: Agent {version}")
        print(f"Protocol: {Path(protocol_path).name}")
        print(f"Playbook: {Path(playbook_path).name if playbook_path else 'None'}")
        print(f"Model: {model}")
        print(f"Log: {logger.get_log_path()}\n")
        
        # Step 5: Run analysis
        print("RUNNING ANALYSIS")
        print("-" * 60)
        if version == "V3":
            print("Using Enhanced Analyzer (20-50 suggestions expected)...")
        else:
            print("Using Standard Analyzer (5-15 suggestions expected)...")
        print("This may take a few moments...\n")
        
        enhanced_result = None  # Para uso no feedback loop e reconstrução
        protocol_json = None  # Para uso na reconstrução
        if version == "V3" and V3_AVAILABLE:
            # Use V3 Enhanced Analyzer
            protocol_json = load_protocol(protocol_path)
            playbook_content = load_playbook(playbook_path) if playbook_path else ""

            analyzer = EnhancedAnalyzer(model=model)
            enhanced_result = analyzer.analyze_comprehensive(
                protocol_json=protocol_json,
                playbook_content=playbook_content,
                protocol_path=str(protocol_path)
            )

            # Convert to dict format - ENXUTO para pipeline futuro
            # Mantém apenas o essencial para categorização e implementação
            result = {
                "improvement_suggestions": [
                    {
                        "id": s.id,
                        "category": s.category,  # Para categorização
                        "priority": s.priority,  # Para priorização
                        "title": s.title,  # Resumo curto
                        "location": s.specific_location or {},  # Onde aplicar no protocolo
                        "action": s.description[:150] if s.description else s.title  # Ação resumida (max 150 chars)
                    }
                    for s in enhanced_result.improvement_suggestions
                ],
                "metadata": {
                    "protocol_path": normalize_path(str(protocol_path), project_root),
                    "playbook_path": normalize_path(str(playbook_path), project_root) if playbook_path else None,
                    "model_used": model,
                    "timestamp": datetime.now().isoformat(),
                    "version": "V3",
                    "suggestions_count": len(enhanced_result.improvement_suggestions)
                }
            }
        else:
            # Use V2 pipeline
            result = v2_analyze(
                protocol_path=protocol_path,
                playbook_path=playbook_path,
                model=model
            )
            result["metadata"]["version"] = "V2"
        
        # Step 6: Save reports
        protocol_name = Path(protocol_path).stem
        json_path, txt_path = save_report(result, protocol_name, project_root, version)

        # Step 7: Show summary
        print("ANALYSIS COMPLETE")
        print("-" * 60)
        improvements_count = len(result.get('improvement_suggestions', []))
        print(f"Improvement Suggestions: {improvements_count}")
        if version == "V3":
            print(f"  Expected range: 20-50 suggestions")
            print(f"  Status: {'✅ PASS' if 20 <= improvements_count <= 50 else '⚠️  OUT OF RANGE'}")
        print(f"\nReports saved:")
        print(f"   JSON: {json_path}")
        print(f"   Text: {txt_path}")
        print(f"   Log:  {logger.get_log_path()}\n")
        
        # Step 8: FASE 2 - Feedback Loop (opcional, APÓS relatórios salvos)
        feedback_session = None
        if version == "V3" and V3_AVAILABLE and improvements_count > 0:
            print("=" * 60)
            print("FEEDBACK LOOP - Human-in-the-Loop")
            print("=" * 60)
            print("\nAgora que você pode revisar os relatórios salvos, deseja fornecer feedback?")
            print("O feedback ajudará a melhorar futuras análises e refinar os prompts.")
            print("\nVocê pode:")
            print("  • Revisar cada sugestão e indicar se é relevante ou não")
            print("  • Editar sugestões que precisam de ajuste")
            print("  • Adicionar comentários para contexto adicional")
            print("  • Avaliar a qualidade geral da análise")
            print("\nIsso permitirá que o sistema aprenda e melhore continuamente.")
            
            feedback_choice = input("\nDeseja fornecer feedback? (S/N): ").strip().upper()
            collect_feedback = feedback_choice in ("S", "SIM", "Y", "YES")
            
            if collect_feedback:
                try:
                    collector = FeedbackCollector()
                    # Converter sugestões para dict com contexto completo
                    if enhanced_result is not None:
                        # Usar resultado completo do Enhanced Analyzer (com todos os campos)
                        suggestions_dict = [s.to_dict() for s in enhanced_result.improvement_suggestions]
                    else:
                        # Fallback: usar sugestões do resultado (formato enxuto)
                        suggestions_dict = result.get('improvement_suggestions', [])
                    
                    feedback_session = collector.collect_feedback_interactive(
                        suggestions=suggestions_dict,
                        protocol_name=protocol_name,
                        model_used=model,
                        skip_if_empty=False
                    )
                    
                    # Se usuário saiu do feedback (None), continuar normalmente
                    if feedback_session is None:
                        print("\nℹ️  Feedback não coletado. Continuando com o pipeline...")
                    
                    # Após feedback, analisar padrões e sugerir refinamento
                    elif feedback_session:
                        print("\n" + "=" * 60)
                        print("ANÁLISE DE FEEDBACK")
                        print("=" * 60)
                        refine_choice = input("\nDeseja analisar padrões e refinar prompts? (S/N): ").strip().upper()
                        if refine_choice in ("S", "SIM", "Y", "YES"):
                            try:
                                refiner = PromptRefiner()
                                patterns = refiner.analyze_feedback_patterns([feedback_session])
                                if patterns:
                                    print(f"\n✓ Identificados {len(patterns)} padrões de feedback")
                                    for pattern in patterns:
                                        print(f"  - {pattern.pattern_type}: {pattern.description} (severidade: {pattern.severity})")
                                    
                                    apply_choice = input("\nAplicar ajustes aos prompts? (S/N): ").strip().upper()
                                    if apply_choice in ("S", "SIM", "Y", "YES"):
                                        adjustments = refiner.generate_prompt_adjustments(patterns)
                                        if adjustments:
                                            success = refiner.apply_adjustments(adjustments)
                                            if success:
                                                print("✅ Prompts refinados com sucesso!")
                                            else:
                                                print("⚠️  Erro ao aplicar ajustes")
                                        else:
                                            print("ℹ️  Nenhum ajuste gerado")
                                    else:
                                        print("ℹ️  Ajustes não aplicados")
                                else:
                                    print("ℹ️  Nenhum padrão significativo identificado ainda")
                            except Exception as e:
                                logger.error(f"Error in prompt refinement: {e}", exc_info=True)
                                print(f"⚠️  Erro ao refinar prompts: {e}")
                except Exception as e:
                    logger.error(f"Error collecting feedback: {e}", exc_info=True)
                    print(f"⚠️  Erro ao coletar feedback: {e}")
            
            # Atualizar metadata com info de feedback
            if feedback_session:
                result["metadata"]["feedback_collected"] = True
                result["metadata"]["feedback_session_id"] = feedback_session.session_id if hasattr(feedback_session, 'session_id') else None
        
        # Step 9: Reconstrução do Protocolo JSON (opcional, após feedback)
        if version == "V3" and V3_AVAILABLE and improvements_count > 0:
            print("\n" + "=" * 60)
            print("RECONSTRUÇÃO DO PROTOCOLO JSON")
            print("=" * 60)
            print("\nDeseja reconstruir o arquivo JSON do protocolo aplicando as sugestões?")
            print("O protocolo será reconstruído baseado no relatório da análise.")
            print("   O protocolo original será preservado e um novo arquivo será criado.")
            
            reconstruct_choice = input("\nDeseja reconstruir o protocolo? (S/N): ").strip().upper()
            
            if reconstruct_choice in ("S", "SIM", "Y", "YES"):
                try:
                    from agent.applicator import ProtocolReconstructor
                    
                    # Preparar sugestões para reconstrução
                    if enhanced_result is not None:
                        # Usar sugestões completas do Enhanced Analyzer
                        suggestions_for_reconstruction = [s.to_dict() for s in enhanced_result.improvement_suggestions]
                    else:
                        # Fallback: usar sugestões do resultado
                        suggestions_for_reconstruction = result.get('improvement_suggestions', [])
                    
                    if not suggestions_for_reconstruction:
                        print("⚠️  Nenhuma sugestão disponível para reconstrução")
                    elif protocol_json is None:
                        print("⚠️  Protocolo original não disponível para reconstrução")
                    else:
                        reconstructor = ProtocolReconstructor(model=model)
                        reconstruction_result = reconstructor.reconstruct_protocol(
                            original_protocol=protocol_json,
                            suggestions=suggestions_for_reconstruction,
                            analysis_result=enhanced_result
                        )
                        
                        if reconstruction_result:
                            # Salvar protocolo reconstruído com versionamento correto
                            from agent.applicator.version_utils import (
                                generate_output_filename,
                                update_protocol_version
                            )
                            
                            # Atualizar versão no protocolo reconstruído
                            reconstructed_protocol = reconstruction_result.reconstructed_protocol
                            output_filename, new_version = generate_output_filename(
                                protocol_json=reconstructed_protocol,
                                protocol_path=protocol_path,
                                suffix="RECONSTRUCTED"
                            )
                            
                            # Atualizar versão no metadata
                            reconstructed_protocol = update_protocol_version(
                                reconstructed_protocol,
                                new_version
                            )
                            
                            output_dir = project_root / "models_json"
                            output_path = output_dir / output_filename
                            
                            with open(output_path, 'w', encoding='utf-8') as f:
                                json.dump(reconstructed_protocol, f, ensure_ascii=False, indent=2)
                            
                            print("\n" + "=" * 60)
                            print("✅ PROTOCOLO RECONSTRUÍDO COM SUCESSO")
                            print("=" * 60)
                            print(f"\nArquivo salvo: {output_path}")
                            print(f"Versão: {reconstruction_result.metadata.get('original_version', 'N/A')} → {new_version}")
                            print(f"Sugestões aplicadas: {len(reconstruction_result.changes_applied)}")
                            print(f"Validação: {'✅ PASSOU' if reconstruction_result.validation_passed else '❌ FALHOU'}")
                            
                            if reconstruction_result.metadata:
                                orig_size = reconstruction_result.metadata.get("original_size", 0)
                                recon_size = reconstruction_result.metadata.get("reconstructed_size", 0)
                                print(f"Tamanho original: {orig_size:,} caracteres")
                                print(f"Tamanho reconstruído: {recon_size:,} caracteres")
                                print(f"Variação: {((recon_size - orig_size) / orig_size * 100):+.1f}%")
                        else:
                            print("\n⚠️  Reconstrução não concluída")
                
                except Exception as e:
                    logger.error(f"Error during protocol reconstruction: {e}", exc_info=True)
                    print(f"\n⚠️  Erro ao reconstruir protocolo: {e}")
                    print("O protocolo original não foi alterado.")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        print(f"Check log file: {logger.get_log_path()}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

