import sys
from unittest.mock import MagicMock

# Mock 'config' as a package
config_mock = MagicMock()
config_mock.__path__ = [] # Essential to be treated as a package
sys.modules['config'] = config_mock
sys.modules['config.prompts'] = MagicMock()

# Also mock src.config just in case
src_config_mock = MagicMock()
src_config_mock.__path__ = []
sys.modules['src.config'] = src_config_mock
sys.modules['src.config.prompts'] = MagicMock()

# Mock src.agent.core to prevent import of llm_client and config
core_mock = MagicMock()
core_mock.__path__ = []
sys.modules['src.agent.core'] = core_mock
sys.modules['src.agent.core.logger'] = MagicMock()

import unittest
import json
from src.agent.models.protocol import Protocol
from src.agent.validators.logic_validator import ConditionalExpressionValidator, validate_protocol_conditionals
from src.agent.validators.llm_contract import EnhancedAnalysisResponse
from pydantic import ValidationError

class TestWave1Validators(unittest.TestCase):

    def setUp(self):
        # Sample valid protocol data
        self.valid_protocol = {
            "metadata": {
                "company": "Test Co",
                "name": "Test Protocol",
                "version": "1.0.0",
                "flow_id": "flow_123"
            },
            "nodes": [
                {
                    "id": "node_1",
                    "type": "question",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "questions": [
                            {
                                "id": "q1",
                                "uid": "symptom_x",
                                "type": "select",
                                "text": "Has symptom X?",
                                "options": [
                                    {"id": "yes", "value": "Yes", "next": "node_2"},
                                    {"id": "no", "value": "No", "next": "node_3"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "node_2",
                    "type": "treatment",
                    "position": {"x": 100, "y": 0},
                    "data": {"description": "Treat X"}
                },
                {
                    "id": "node_3",
                    "type": "disconnect",
                    "position": {"x": 100, "y": 100},
                    "data": {}
                }
            ],
            "edges": []
        }

    # --- Test 1: Protocol Pydantic Model ---
    def test_protocol_validation_valid(self):
        """Test that a valid protocol parses correctly."""
        p = Protocol.parse_obj(self.valid_protocol)
        self.assertEqual(p.metadata.version, "1.0.0")
        self.assertEqual(len(p.nodes), 3)

    def test_protocol_validation_missing_field(self):
        """Test that missing required fields raises ValidationError."""
        del self.valid_protocol["metadata"]["version"]
        with self.assertRaises(ValidationError):
            Protocol.parse_obj(self.valid_protocol)

    def test_protocol_validation_duplicate_uid(self):
        """Test that duplicate question UIDs raise ValidationError."""
        # Add another question with same UID
        self.valid_protocol["nodes"][0]["data"]["questions"].append({
            "id": "q2",
            "uid": "symptom_x", # Duplicate
            "type": "text",
            "text": "Repeat?"
        })
        with self.assertRaises(ValidationError) as cm:
            Protocol.parse_obj(self.valid_protocol)
        self.assertIn("Duplicate question UID", str(cm.exception))

    # --- Test 2: Logic Validator (AST) ---
    def test_logic_validator_safe_expression(self):
        """Test that safe expressions pass validation."""
        validator = ConditionalExpressionValidator(
            allowed_uids={"symptom_x", "age"},
            allowed_option_ids={"yes", "no"}
        )
        
        # Valid expressions
        self.assertTrue(validator.validate("'yes' in symptom_x"))
        self.assertTrue(validator.validate("age > 10"))
        self.assertTrue(validator.validate("symptom_x == 'yes' and age > 18"))

    def test_logic_validator_unknown_ref(self):
        """Test that references to unknown UIDs or Options fail."""
        validator = ConditionalExpressionValidator(
            allowed_uids={"symptom_x"},
            allowed_option_ids={"yes"}
        )
        
        # Unknown UID
        is_valid, errors = validator.validate("unknown_uid == 'yes'")
        self.assertFalse(is_valid)
        self.assertIn("unknown identifier: unknown_uid", errors[0])

    def test_logic_validator_dangerous_code(self):
        """Test that dangerous Python code is blocked."""
        validator = ConditionalExpressionValidator(allowed_uids={}, allowed_option_ids={})
        
        dangerous_inputs = [
            "__import__('os').system('ls')",
            "exec('print(1)')",
            "eval('1+1')",
            "open('/etc/passwd')"
        ]
        
        for expr in dangerous_inputs:
            is_valid, errors = validator.validate(expr)
            self.assertFalse(is_valid, f"Should block: {expr}")
            self.assertTrue(any("Call" in e or "unsafe" in e for e in errors))

    def test_validate_protocol_conditionals_integration(self):
        """Test the helper function that scans the whole protocol."""
        # Add a condition to node 2
        self.valid_protocol["nodes"][1]["data"]["condicao"] = "'yes' in symptom_x"
        
        # Should pass
        is_valid, errors = validate_protocol_conditionals(self.valid_protocol)
        self.assertTrue(is_valid, f"Errors: {errors}")

        # Add invalid condition
        self.valid_protocol["nodes"][2]["data"]["condicao"] = "unknown_var == 1"
        is_valid, errors = validate_protocol_conditionals(self.valid_protocol)
        # Assuming strict validation returns False, or warnings text
        # The function returns (bool, list)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    # --- Test 3: LLM Contract ---
    def test_llm_contract_valid(self):
        """Test that valid LLM output parses correctly."""
        llm_output = {
            "improvement_suggestions": [
                {
                    "id": "sug_1",
                    "category": "seguranca",
                    "priority": "alta",
                    "title": "Fix X",
                    "description": "Description",
                    "rationale": "Rationale",
                    "impact_scores": {"seguranca": 10},
                    "evidence": {"playbook_reference": "Page 10, Line 5..."},
                    "implementation_effort": {},
                    "auto_apply_cost_estimate": {},
                    "specific_location": {"node_id": "node_1"}
                }
            ],
            "metadata": {"analysis_version": "1.0"}
        }
        resp = EnhancedAnalysisResponse(**llm_output)
        self.assertEqual(len(resp.improvement_suggestions), 1)
        self.assertEqual(resp.improvement_suggestions[0].priority, "alta")

    def test_llm_contract_generic_reference(self):
        """Test that generic playbook references are flagged/rejected."""
        llm_output = {
            "improvement_suggestions": [
                {
                    "id": "sug_1",
                    "category": "seguranca",
                    "priority": "alta",
                    "title": "Fix X",
                    "description": "Description",
                    "rationale": "Rationale",
                    "impact_scores": {"seguranca": 10},
                    "evidence": {"playbook_reference": "Based on general medical knowledge"}, # Generic
                    "implementation_effort": {},
                    "auto_apply_cost_estimate": {},
                    "specific_location": {"node_id": "node_1"}
                }
            ],
            "metadata": {"analysis_version": "1.0"}
        }
        with self.assertRaises(ValidationError) as cm:
            EnhancedAnalysisResponse(**llm_output)
        self.assertIn("Playbook reference must be specific", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
