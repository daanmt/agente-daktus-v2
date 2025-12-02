"""
Test Script for Cost Control V3

Testa a estimativa de custos e autorização antes da análise.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from agent_v3.cost_control import CostEstimator, AuthorizationManager, UserLimits
from agent_v2.protocol_loader import load_protocol, load_playbook

def main():
    """Test Cost Control"""
    
    print("\n" + "=" * 60)
    print("COST CONTROL TEST")
    print("=" * 60 + "\n")
    
    # Load test protocol and playbook
    project_root = Path(__file__).parent
    protocol_path = project_root / "models_json" / "amil_ficha_orl_v1.0.0_FIXED_20251201_073725.json"
    playbook_path = project_root / "models_json" / "Sobre a ficha de atendimento em Otorrinolaringolog 29d6587d2ef5800ba358f9c1b2236875.md"
    
    if not protocol_path.exists():
        print(f"❌ Protocol not found: {protocol_path}")
        return
    
    print("Loading protocol and playbook...")
    protocol_json = load_protocol(str(protocol_path))
    playbook_content = load_playbook(str(playbook_path)) if playbook_path.exists() else ""
    
    protocol_size = len(str(protocol_json))
    playbook_size = len(playbook_content)
    
    print(f"✓ Protocol size: {protocol_size:,} chars")
    print(f"✓ Playbook size: {playbook_size:,} chars\n")
    
    # Test Cost Estimator
    print("=" * 60)
    print("TEST 1: Cost Estimation")
    print("=" * 60 + "\n")
    
    estimator = CostEstimator()
    model = "google/gemini-2.5-flash-preview-09-2025"
    
    cost_estimate = estimator.estimate_analysis_cost(
        protocol_size=protocol_size,
        playbook_size=playbook_size,
        model=model
    )
    
    print(f"Model: {model}")
    print(f"Estimated Input Tokens: {cost_estimate.estimated_tokens['input']:,}")
    print(f"Estimated Output Tokens: {cost_estimate.estimated_tokens['output']:,}")
    print(f"Estimated Total Tokens: {cost_estimate.estimated_tokens['total']:,}")
    print(f"\nEstimated Costs:")
    print(f"  Input:  ${cost_estimate.estimated_cost_usd['input']:.4f}")
    print(f"  Output: ${cost_estimate.estimated_cost_usd['output']:.4f}")
    print(f"  Total:  ${cost_estimate.estimated_cost_usd['total']:.4f}")
    print(f"\nConfidence: {cost_estimate.confidence.upper()}\n")
    
    # Test Authorization Manager
    print("=" * 60)
    print("TEST 2: Authorization (with default limits)")
    print("=" * 60 + "\n")
    
    auth_manager = AuthorizationManager()
    
    print("Default limits:")
    print(f"  Max per operation: ${auth_manager.user_limits.max_cost_per_operation:.2f}")
    print(f"  Max daily: ${auth_manager.user_limits.max_daily_cost:.2f}")
    print(f"  Auto-approval threshold: ${auth_manager.user_limits.require_approval_above:.2f}\n")
    
    print("Requesting authorization...")
    print("(This will prompt for user input if cost > $0.50)\n")
    
    auth_decision = auth_manager.request_authorization(
        cost_estimate=cost_estimate,
        operation_description="Enhanced Analysis Test"
    )
    
    print(f"\nAuthorization Decision:")
    print(f"  Authorized: {auth_decision.authorized}")
    print(f"  Decision: {auth_decision.user_decision}")
    print(f"  Timestamp: {auth_decision.timestamp}\n")
    
    if not auth_decision.authorized:
        print("❌ Operation not authorized. Test stopped.")
        return
    
    print("✅ Cost Control test completed successfully!\n")

if __name__ == "__main__":
    main()

