#!/usr/bin/env python
"""
Entry point para a CLI Interativa Avançada (Agent V3)

Uso:
    python run_interactive_cli.py
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

# Import and run
try:
    from agent_v3.cli.interactive_cli import main
    if __name__ == "__main__":
        main()
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
