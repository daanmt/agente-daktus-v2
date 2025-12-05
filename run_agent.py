#!/usr/bin/env python
"""
Agente Daktus | QA - Entry Point Unificado

Uso:
    python run_agent.py              # CLI interativa (padrão)
    python run_agent.py --help       # Ajuda
    python run_agent.py --version    # Versão
"""

import os
import sys
from pathlib import Path

# Calculate project root
project_root = Path(__file__).resolve().parent

# Load .env first
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
except ImportError:
    pass  # dotenv não é obrigatório

# Add src to path
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def main():
    """Entry point principal."""
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        try:
            from agent import __version__
            print(f"Agente Daktus | QA v{__version__}")
        except ImportError:
            print("Agente Daktus | QA v3.0.0")
        return

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("""
Agente Daktus | QA - Validação e Correção de Protocolos Clínicos

Uso:
    python run_agent.py              # Executar CLI interativa
    python run_agent.py --version    # Exibir versão
    python run_agent.py --help       # Exibir esta ajuda

A CLI interativa irá guiá-lo através de:
1. Seleção de versão (V2 ou V3)
2. Seleção de protocolo JSON
3. Seleção de playbook (opcional)
4. Seleção de modelo LLM
5. Análise do protocolo
6. Feedback interativo (opcional)
7. Reconstrução do protocolo (opcional)

Para mais informações, consulte: docs/roadmap.md
""")
        return

    # Run interactive CLI
    try:
        from agent.cli.interactive_cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"ERROR: Erro ao importar CLI interativa: {e}")
        print("Certifique-se de que está executando do diretório raiz do projeto")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

