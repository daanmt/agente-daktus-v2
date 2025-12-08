"""
DEPRECATED: Legacy CLI Entry Point

This file is deprecated. Use run_agent.py instead.

For backward compatibility, this file redirects to the main entry point.
"""

import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import and run CLI from correct consolidated location
try:
    from agent.cli.interactive_cli import main

    if __name__ == "__main__":
        print("⚠️  WARNING: run_qa_cli.py is deprecated. Use run_agent.py instead.\n")
        main()
except ImportError as e:
    print(f"❌ Error importing CLI: {e}")
    print(f"\n💡 Please use run_agent.py as the main entry point:")
    print(f"   python run_agent.py")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n\n❌ Cancelled by user")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

