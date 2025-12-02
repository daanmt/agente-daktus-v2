"""
Test Script for Agent V3 Enhanced Analyzer

This script tests the Enhanced Analyzer V3 to generate 20-50 suggestions
instead of the 5-15 from V2.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import V3 Enhanced Analyzer
from agent_v3.analysis.enhanced_analyzer import EnhancedAnalyzer
from agent_v2.protocol_loader import load_protocol, load_playbook
from agent_v2.logger import logger

def main():
    """Test Enhanced Analyzer V3 with otorrino protocol"""
    
    print("\n" + "=" * 60)
    print("AGENT V3 - Enhanced Analyzer Test")
    print("=" * 60 + "\n")
    
    # Protocol and playbook paths
    project_root = Path(__file__).parent
    protocol_path = project_root / "models_json" / "amil_ficha_orl_v1.0.0_FIXED_20251201_073725.json"
    playbook_path = project_root / "models_json" / "Sobre a ficha de atendimento em Otorrinolaringolog 29d6587d2ef5800ba358f9c1b2236875.md"
    
    # Check files exist
    if not protocol_path.exists():
        print(f"❌ ERROR: Protocol not found: {protocol_path}")
        return
    
    if not playbook_path.exists():
        print(f"⚠️  WARNING: Playbook not found: {playbook_path}")
        print("   Continuing without playbook...")
        playbook_content = ""
    else:
        print(f"✓ Protocol: {protocol_path.name}")
        print(f"✓ Playbook: {playbook_path.name}\n")
    
    # Load protocol
    print("Loading protocol...")
    try:
        protocol_json = load_protocol(str(protocol_path))
        print(f"✓ Protocol loaded: {len(protocol_json.get('nodes', []))} nodes\n")
    except Exception as e:
        print(f"❌ ERROR loading protocol: {e}")
        return
    
    # Load playbook
    if playbook_path.exists():
        print("Loading playbook...")
        try:
            playbook_content = load_playbook(str(playbook_path))
            print(f"✓ Playbook loaded: {len(playbook_content)} characters\n")
        except Exception as e:
            print(f"⚠️  WARNING loading playbook: {e}")
            playbook_content = ""
    else:
        playbook_content = ""
    
    # Initialize Enhanced Analyzer
    print("Initializing Enhanced Analyzer V3...")
    print("Model: google/gemini-2.5-flash-preview-09-2025 (fast & cheap)\n")
    
    analyzer = EnhancedAnalyzer(model="google/gemini-2.5-flash-preview-09-2025")
    
    # Run comprehensive analysis
    print("=" * 60)
    print("RUNNING ENHANCED ANALYSIS (20-50 suggestions expected)...")
    print("=" * 60 + "\n")
    
    try:
        result = analyzer.analyze_comprehensive(
            protocol_json=protocol_json,
            playbook_content=playbook_content,
            protocol_path=str(protocol_path)
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60 + "\n")
        
        suggestions = result.improvement_suggestions
        print(f"✓ Total suggestions generated: {len(suggestions)}")
        print(f"  Expected: 20-50 suggestions")
        print(f"  Status: {'✅ PASS' if 20 <= len(suggestions) <= 50 else '⚠️  OUT OF RANGE'}\n")
        
        # Count by priority
        alta = sum(1 for s in suggestions if s.priority == "alta")
        media = sum(1 for s in suggestions if s.priority == "media")
        baixa = sum(1 for s in suggestions if s.priority == "baixa")
        
        print(f"Priority distribution:")
        print(f"  Alta:   {alta}")
        print(f"  Média:  {media}")
        print(f"  Baixa:  {baixa}\n")
        
        # Count by category
        categories = {}
        for s in suggestions:
            cat = s.category
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"Category distribution:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        print()
        
        # Show aggregate impact scores
        print(f"Aggregate impact scores:")
        for key, value in result.impact_scores.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        print()
        
        # Show first 5 suggestions as examples
        print("=" * 60)
        print("SAMPLE SUGGESTIONS (first 5)")
        print("=" * 60 + "\n")
        
        for i, sug in enumerate(suggestions[:5], 1):
            print(f"{i}. [{sug.priority.upper()}] {sug.category.upper()}")
            print(f"   Title: {sug.title}")
            print(f"   Impact Scores: Segurança={sug.impact_scores.get('seguranca', 0)}, "
                  f"Economia={sug.impact_scores.get('economia', 'L')}, "
                  f"Eficiência={sug.impact_scores.get('eficiencia', 'L')}, "
                  f"Usabilidade={sug.impact_scores.get('usabilidade', 0)}")
            print(f"   Description: {sug.description[:100]}...")
            if sug.evidence.get("playbook_reference"):
                print(f"   Evidence: {sug.evidence['playbook_reference'][:80]}...")
            print()
        
        # Save results
        output_dir = project_root / "src" / "agent_v3" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"enhanced_analysis_{timestamp}.json"
        
        # Convert result to dict for JSON serialization
        result_dict = {
            "structural_analysis": result.structural_analysis,
            "clinical_extraction": result.clinical_extraction,
            "improvement_suggestions": [s.to_dict() for s in suggestions],
            "impact_scores": result.impact_scores,
            "evidence_mapping": result.evidence_mapping,
            "cost_estimation": result.cost_estimation,
            "metadata": {
                "protocol_path": str(protocol_path),
                "playbook_path": str(playbook_path) if playbook_path.exists() else None,
                "timestamp": timestamp,
                "suggestions_count": len(suggestions)
            }
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Results saved to: {output_file}\n")
        
        print("=" * 60)
        print("TEST COMPLETE")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()

