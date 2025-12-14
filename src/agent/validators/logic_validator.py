"""
Logic Validator - Validação segura de expressões condicionais Python.

Substitui regex frágil por AST parsing, garantindo:
1. Sintaxe Python válida
2. Referências a UIDs/option_ids conhecidos
3. Operadores permitidos apenas (sem eval perigoso)
"""

import ast
import re
from typing import Tuple, List, Set, Dict
from ..core.logger import logger


def sanitize_conditional_expression(expression: str) -> str:
    """
    Sanitiza expressão condicional removendo chamadas de função inválidas.
    
    LLMs frequentemente geram funções que não existem no Daktus Studio:
    - selected_only(var, value) → 'value' in var
    - contains(var, value) → 'value' in var
    - isEmpty(var) → var == None
    - getAnswer(var) → var
    
    Args:
        expression: Expressão original com possíveis funções inválidas
        
    Returns:
        Expressão sanitizada com sintaxe Daktus válida
    """
    if not expression or not isinstance(expression, str):
        return expression
    
    original = expression
    
    # Padrão 1: "not selected_only(var, 'value')" → "" (remover completamente, é redundante)
    expression = re.sub(
        r'\s*and\s+not\s+selected_only\s*\([^)]+\)',
        '',
        expression,
        flags=re.IGNORECASE
    )
    
    # Padrão 2: "selected_only(var, 'value')" → "'value' in var"
    def replace_selected_only(match):
        var = match.group(1).strip()
        value = match.group(2).strip()
        return f"{value} in {var}"
    
    expression = re.sub(
        r'selected_only\s*\(\s*(\w+)\s*,\s*([\'"][^"\']+[\'"])\s*\)',
        replace_selected_only,
        expression,
        flags=re.IGNORECASE
    )
    
    # Padrão 3: "contains(var, 'value')" → "'value' in var"
    def replace_contains(match):
        var = match.group(1).strip()
        value = match.group(2).strip()
        return f"{value} in {var}"
    
    expression = re.sub(
        r'contains\s*\(\s*(\w+)\s*,\s*([\'"][^"\']+[\'"])\s*\)',
        replace_contains,
        expression,
        flags=re.IGNORECASE
    )
    
    # Padrão 4: "isEmpty(var)" → "var == None" ou remover
    expression = re.sub(
        r'isEmpty\s*\(\s*(\w+)\s*\)',
        r'\1 == None',
        expression,
        flags=re.IGNORECASE
    )
    
    # Padrão 5: "getAnswer('var')" → "var"
    expression = re.sub(
        r'getAnswer\s*\(\s*[\'"](\w+)[\'"]\s*\)',
        r'\1',
        expression,
        flags=re.IGNORECASE
    )
    
    # Limpar "and and" ou "or or" resultantes
    expression = re.sub(r'\s+and\s+and\s+', ' and ', expression)
    expression = re.sub(r'\s+or\s+or\s+', ' or ', expression)
    
    # Limpar espaços extras
    expression = re.sub(r'\s+', ' ', expression).strip()
    
    # Remover "and" ou "or" no início/fim
    expression = re.sub(r'^(and|or)\s+', '', expression)
    expression = re.sub(r'\s+(and|or)$', '', expression)
    
    if expression != original:
        logger.debug(f"Sanitized conditional: '{original[:50]}...' → '{expression[:50]}...'")
    
    return expression

class ConditionalExpressionValidator:
    """
    Valida expressões condicionais usando AST (Abstract Syntax Tree).
    
    Garante segurança clínica validando que:
    - Sintaxe é Python válido
    - Variáveis referenciadas existem (UIDs conhecidos)
    - Strings literais são option_ids válidos ou valores permitidos
    """
    
    # Adicionando 'and', 'or', 'not' como keywords reservadas por segurança, 
    # embora sejam operadores em Python, o AST lida com isso.
    # UIDs como 'visivel' são comuns em metadados.
    RESERVED_KEYWORDS = {'visivel', 'invisivel', 'true', 'false', 'True', 'False'}
    
    # Operadores não precisam ser listados para ast.parse, mas verificaremos no visitor
    
    def __init__(self, valid_uids: Set[str], valid_option_ids: Set[str]):
        """
        Args:
            valid_uids: Set de UIDs de questions válidos no protocolo
            valid_option_ids: Set de option IDs válidos em todas as questions
        """
        self.valid_uids = valid_uids
        self.valid_option_ids = valid_option_ids
    
    def validate(self, expression: str, context: str = "") -> Tuple[bool, List[str]]:
        """
        Valida expressão condicional.
        
        Args:
            expression: Expressão Python a validar (ex: "idade_paciente >= 65")
            context: Contexto para logs (ex: "node-3.condicao")
        
        Returns:
            (is_valid, warnings)
            - is_valid: True se sintaxe válida, False se erro crítico
            - warnings: Lista de avisos não-críticos (possíveis falsos positivos)
        """
        if not expression or not str(expression).strip():
            return True, []
        
        warnings = []
        expression = str(expression).strip()
        
        # Etapa 1: Validar sintaxe Python
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            logger.error(f"Invalid Python syntax in {context}: {e}")
            return False, [f"Syntax error: {e}"]
        
        # Etapa 2: Validar segurança (sem eval perigoso)
        security_check = self._check_security(tree.body)
        if not security_check[0]:
            return False, security_check[1]
        
        # Etapa 3: Validar referências (UIDs, option_ids)
        self._validate_references(tree.body, warnings, context)
        
        # Warnings não são fatais (podem ser falsos positivos)
        if warnings:
            logger.warning(f"Expression in {context} has {len(warnings)} warnings: {warnings[:3]}")
        
        return True, warnings
    
    def _check_security(self, node: ast.AST) -> Tuple[bool, List[str]]:
        """Garante que expressão não contém código perigoso."""
        dangerous = []
        
        for child in ast.walk(node):
            # Bloquear chamadas de função (ex: eval(), exec())
            if isinstance(child, ast.Call):
                dangerous.append("Function calls not allowed in conditions")
            
            # Bloquear imports
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                dangerous.append("Imports not allowed in conditions")
            
            # Bloquear atribuições
            if isinstance(child, ast.Assign):
                dangerous.append("Assignments not allowed in conditions")
        
        if dangerous:
            return False, dangerous
        return True, []
    
    def _validate_references(self, node: ast.AST, warnings: List[str], context: str):
        """Valida que variáveis e strings referenciadas existem."""
        
        for child in ast.walk(node):
            # Validar variáveis (UIDs)
            if isinstance(child, ast.Name):
                uid = child.id
                # Keywords Python como True/False não são Name em Py3 (são NameConstant ou Constant), 
                # mas 'true'/'false' minúsculos podem ser interpretados como var se não definidos.
                if uid not in self.valid_uids and uid not in self.RESERVED_KEYWORDS:
                    warnings.append(f"Unknown UID: '{uid}' (context: {context})")
            
            # Validar strings literais (option_ids)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                self._validate_string_literal(child.value, warnings, context)
            # Python < 3.8 compatibility (ast.Str was removed in 3.12)
            elif hasattr(ast, 'Str') and isinstance(child, ast.Str):
                self._validate_string_literal(child.s, warnings, context)
    
    def _validate_string_literal(self, value: str, warnings: List[str], context: str):
        """Valida string literal (deve ser option_id ou valor permitido)."""
        
        # Ignorar valores reservados
        if value in self.RESERVED_KEYWORDS:
            return
        
        # Verificar se é option_id conhecido
        if value in self.valid_option_ids:
            return
        
        # Aviso: Pode ser valor custom válido (não podemos ter certeza)
        warnings.append(
            f"Unverified string literal: '{value}' (context: {context}). "
            "Ensure this is a valid option_id or custom value."
        )


def validate_protocol_conditionals(protocol_dict: Dict) -> Tuple[bool, List[str]]:
    """
    Helper function: Valida todas as expressões condicionais em um protocolo.
    
    Returns:
        (is_valid, errors) onde errors contém apenas erros críticos
    """
    # Coletar UIDs e option_ids
    valid_uids = set()
    valid_option_ids = set()
    
    # Percorrer nodes com segurança
    nodes = protocol_dict.get("nodes", [])
    if not isinstance(nodes, list):
         return True, [] 

    for node in nodes:
        data = node.get("data", {})
        if not isinstance(data, dict):
            continue
            
        questions = data.get("questions") or []
        if not isinstance(questions, list):
            continue
            
        for question in questions:
            if not isinstance(question, dict):
                continue
                
            uid = question.get("uid")
            if uid:
                valid_uids.add(uid)
            
            options = question.get("options", [])
            if isinstance(options, list):
                for option in options:
                    if isinstance(option, dict):
                        opt_id = option.get("id")
                        if opt_id:
                            valid_option_ids.add(opt_id)
    
    validator = ConditionalExpressionValidator(valid_uids, valid_option_ids)
    errors = []
    
    # Validar node conditionals
    for node in nodes:
        if not isinstance(node, dict): 
            continue
            
        node_id = node.get("id", "unknown")
        data = node.get("data", {})
        condicao = data.get("condicao")
        
        if condicao:
            is_valid, warns = validator.validate(condicao, context=f"{node_id}.condicao")
            if not is_valid:
                errors.extend([f"{node_id}: {w}" for w in warns])
    
    # Validar question expressoes
    for node in nodes:
        data = node.get("data", {})
        questions = data.get("questions") or []
        
        for question in questions:
            if not isinstance(question, dict): 
                continue
                
            q_id = question.get("id", "unknown")
            expressao = question.get("expressao")
            
            if expressao:
                is_valid, warns = validator.validate(expressao, context=f"{q_id}.expressao")
                if not is_valid:
                    errors.extend([f"{q_id}: {w}" for w in warns])
    
    return len(errors) == 0, errors
