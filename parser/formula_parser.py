"""
Formula Parser Module.

This module handles the tokenization, parsing, and evaluation of logical formulas
in a Many-Logics Modal Logic (MLML) context. It supports standard operators (~, &, |, ->, <->)
and modal operators ([], <>), with dynamic evaluation based on up/down interpretations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Set, Any, Tuple
from services.logging_service import get_logger

logger = get_logger("FormulaParser")


# ==========================================
#                  LEXER
# ==========================================

class Lexer:
    """
    Tokenizer for the logic formula string.
    Converts raw text into a stream of tokens (e.g., 'ATOM', 'BOX', 'AND').
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char: Optional[str] = self.text[0] if self.text else None

    def advance(self) -> None:
        """Moves the pointer to the next character in the text."""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self) -> None:
        """Skips over any whitespace characters."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def get_atom(self) -> Tuple[str, str]:
        """Reads an alphanumeric identifier or constant."""
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return ('ATOM', result)

    def get_next_token(self) -> Tuple[str, Optional[str]]:
        """
        Scans the input and returns the next valid token.
        """
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isalnum():
                return self.get_atom()
            
            if self.current_char == '~':
                self.advance()
                return ('NOT', '~')
            
            if self.current_char == '[':
                self.advance()
                action = ""
                while self.current_char is not None and self.current_char != ']':
                    action += self.current_char
                    self.advance()
                if self.current_char == ']':
                    self.advance()
                    return ('BOX', action.strip() if action.strip() else None)
                raise ValueError("Expected ']' after action identifier")
            
            if self.current_char == '<':
                self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('DIAMOND', None)
                if self.current_char == '-':
                    self.advance()
                    if self.current_char == '>':
                        self.advance()
                        return ('IFF', '<->')
                    raise ValueError("Expected '>' after '<-'")
                
                action = ""
                while self.current_char is not None and self.current_char != '>':
                    action += self.current_char
                    self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('DIAMOND', action.strip() if action.strip() else None)
                raise ValueError("Expected '>' to close diamond operator")
            
            if self.current_char == '-':
                self.advance()
                if self.current_char == '>':
                    self.advance()
                    return ('IMPLIES', '->')
                raise ValueError("Expected '>' after '-'")
            
            if self.current_char == '&':
                self.advance()
                return ('AND', '&')
            
            if self.current_char == '|':
                self.advance()
                return ('OR', '|')
            
            if self.current_char == '(':
                self.advance()
                return ('LPAREN', '(')
            
            if self.current_char == ')':
                self.advance()
                return ('RPAREN', ')')
            
            raise ValueError(f"Unknown character: {self.current_char}")
        
        return ('EOF', None)


# ==========================================
#                 AST NODES
# ==========================================

class ASTNode(ABC):
    """Abstract Base Class for Abstract Syntax Tree nodes."""

    @abstractmethod
    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        """Evaluates the formula in the given model at the given world."""
        pass

    @abstractmethod
    def get_atoms(self) -> Set[str]:
        """Retrieves all atomic propositions used in this formula."""
        pass


class Atom(ASTNode):
    """Represents an atomic proposition or truth constant (e.g., 'p', '1', '0')."""

    def __init__(self, name: str):
        self.name = name

    def get_atoms(self) -> Set[str]:
        if self.name.upper() in ('TOP', 'BOT', '1', '0'):
            return set()
        return {self.name}

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)

        name_upper = self.name.upper()
        if name_upper in ('BOT', '0'):
            return world_lat.bottom
        if name_upper in ('TOP', '1'):
            return world_lat.top
        
        val = model.get_assignment(world, self.name)
        if val is not None:
            if val in world_lat.elements:
                return val
            if interpretation == "up":
                return model.many_lattice.up_interpretation(world_lat, val)
            else:
                return model.many_lattice.down_interpretation(world_lat, val)
            
        logger.error(f"Proposition '{self.name}' is not defined in world '{world.name_long}'.")
        raise ValueError(f"Proposition '{self.name}' is not defined in world '{world.name_long}'.")


class Not(ASTNode):
    """Represents logical negation (~A)."""

    def __init__(self, child: ASTNode):
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        val = self.child.evaluate(model, world, interpretation)
        
        # 1. Check local sublattice negation first if defined
        if hasattr(world_lat, 'negation') and callable(world_lat.negation):
            res = world_lat.negation(val)
            if res is not None:
                return res

        # 2. Fall back to base ManyLattice negation and relativize
        base_neg_map = model.many_lattice.negation_map
        if val in base_neg_map:
            negated_base = base_neg_map[val]
            if interpretation == "up":
                return model.many_lattice.up_interpretation(world_lat, negated_base)
            else:
                return model.many_lattice.down_interpretation(world_lat, negated_base)

        logger.error(f"Negation not defined for value '{val}' in world '{world.name_short}' or ManyLattice.")
        raise ValueError(f"Negation not defined for '{val}'.")


class And(ASTNode):
    """Represents logical conjunction (A & B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)
        return world_lat.meet(val_a, val_b)


class Or(ASTNode):
    """Represents logical disjunction (A | B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)
        return world_lat.join(val_a, val_b)


class Implies(ASTNode):
    """Represents logical implication (A -> B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        val_a = self.left.evaluate(model, world, interpretation)
        val_b = self.right.evaluate(model, world, interpretation)

        # 1. Local complete sublattice implication
        if hasattr(world_lat, 'implication') and callable(world_lat.implication):
            res = world_lat.implication(val_a, val_b)
            if res is not None:
                return res

        # 2. Base ManyLattice implication relativized to local sublattice
        base_imp_map = model.many_lattice.implication_map
        if (val_a, val_b) in base_imp_map:
            base_result = base_imp_map[(val_a, val_b)]
            if interpretation == "up":
                return model.many_lattice.up_interpretation(world_lat, base_result)
            else:
                return model.many_lattice.down_interpretation(world_lat, base_result)

        logger.error(f"Implication not defined for pair ('{val_a}', '{val_b}').")
        raise ValueError(f"Implication not defined for pair ('{val_a}', '{val_b}').")


class Iff(ASTNode):
    """Represents logical equivalence (A <-> B)."""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    def get_atoms(self) -> Set[str]:
        return self.left.get_atoms().union(self.right.get_atoms())

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        imp1 = Implies(self.left, self.right)
        imp2 = Implies(self.right, self.left)
        and_node = And(imp1, imp2)
        return and_node.evaluate(model, world, interpretation)


class Box(ASTNode):
    """Represents the modal Box operator [action]A."""

    def __init__(self, action: Optional[str], child: ASTNode):
        self.action = action
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        
        # Resolve action context if not explicitly provided in syntax
        act = self.action
        if act is None or act == 'default':
            if len(model.actions) == 1:
                act = next(iter(model.actions))
            else:
                raise ValueError(
                    f"Modal operator [] requires an explicit action identifier when signature contains multiple actions: {list(model.actions)}"
                )

        if act not in model.accessibility_relation:
            raise ValueError(f"Action '{act}' is not part of the model's signature.")

        accessible_worlds = model.get_accessible_worlds(world.name_short, act)
        
        if not accessible_worlds:
            return world_lat.top

        relativized_values = set()
        for u in accessible_worlds:
            raw_val = self.child.evaluate(model, u, interpretation)
            
            if interpretation == "up":
                interp_val = model.many_lattice.up_interpretation(world_lat, raw_val)
            else:
                interp_val = model.many_lattice.down_interpretation(world_lat, raw_val)
                
            relativized_values.add(interp_val)

        return world_lat.meet_set(relativized_values)


class Diamond(ASTNode):
    """Represents the modal Diamond operator <action>A."""

    def __init__(self, action: Optional[str], child: ASTNode):
        self.action = action
        self.child = child

    def get_atoms(self) -> Set[str]:
        return self.child.get_atoms()

    def evaluate(self, model: Any, world: Any, interpretation: str = "down") -> str:
        world_lat = model.get_world_lattice(world)
        
        # Resolve action context if not explicitly provided in syntax
        act = self.action
        if act is None or act == 'default':
            if len(model.actions) == 1:
                act = next(iter(model.actions))
            else:
                raise ValueError(
                    f"Modal operator <> requires an explicit action identifier when signature contains multiple actions: {list(model.actions)}"
                )

        if act not in model.accessibility_relation:
            raise ValueError(f"Action '{act}' is not part of the model's signature.")

        accessible_worlds = model.get_accessible_worlds(world.name_short, act)
        
        if not accessible_worlds:
            return world_lat.bottom

        relativized_values = set()
        for u in accessible_worlds:
            raw_val = self.child.evaluate(model, u, interpretation)
            
            if interpretation == "up":
                interp_val = model.many_lattice.up_interpretation(world_lat, raw_val)
            else:
                interp_val = model.many_lattice.down_interpretation(world_lat, raw_val)
                
            relativized_values.add(interp_val)

        return world_lat.join_set(relativized_values)


# ==========================================
#                 PARSER
# ==========================================

class FormulaParser:
    """
    Recursive Descent Parser for logic formulas.
    Constructs an AST (Abstract Syntax Tree) from a string.
    """

    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: str) -> None:
        """Consumes the current token if it matches the expected type."""
        if self.current_token[0] == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            err_msg = f"Expected {token_type}, got {self.current_token[0]}"
            logger.error(err_msg)
            raise ValueError(err_msg)

    def parse(self) -> ASTNode:
        """Parses the entire formula into an AST root node."""
        try:
            result = self.iff()
            if self.current_token[0] != 'EOF':
                raise ValueError("Unexpected characters at end of formula")
            return result
        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise

    def iff(self) -> ASTNode:
        node = self.implies()
        while self.current_token[0] == 'IFF':
            self.eat('IFF')
            node = Iff(node, self.implies())
        return node

    def implies(self) -> ASTNode:
        node = self.or_expr()
        while self.current_token[0] == 'IMPLIES':
            self.eat('IMPLIES')
            node = Implies(node, self.or_expr())
        return node

    def or_expr(self) -> ASTNode:
        node = self.and_expr()
        while self.current_token[0] == 'OR':
            self.eat('OR')
            node = Or(node, self.and_expr())
        return node

    def and_expr(self) -> ASTNode:
        node = self.unary()
        while self.current_token[0] == 'AND':
            self.eat('AND')
            node = And(node, self.unary())
        return node

    def unary(self) -> ASTNode:
        token_type, val = self.current_token
        if token_type == 'NOT':
            self.eat('NOT')
            return Not(self.unary())
        elif token_type == 'BOX':
            self.eat('BOX')
            return Box(val, self.unary())
        elif token_type == 'DIAMOND':
            self.eat('DIAMOND')
            return Diamond(val, self.unary())
        elif token_type == 'LPAREN':
            self.eat('LPAREN')
            node = self.iff()
            self.eat('RPAREN')
            return node
        elif token_type == 'ATOM':
            self.eat('ATOM')
            return Atom(val)
        else:
            err_msg = f"Unexpected syntax in formula near token: {token_type}"
            logger.error(err_msg)
            raise ValueError(err_msg)