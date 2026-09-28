"""
Evaluation Service Module.

This module handles parsing, local evaluation, and global validity/satisfaction 
checks for formulas within Many-Logics Modal structures.
"""

from parser.formula_parser import FormulaParser
from services.logging_service import get_logger
from services.json_handler import JSONHandler
from config.config import PATHS
from math_objects.structure import Model, World

logger = get_logger("EvaluationService")

class EvaluationService:
    @staticmethod
    def _check_membership(val, lattice_filter) -> bool:
        """Checks if an evaluated value strictly falls within a given filter."""
        if lattice_filter is None or val is None:
            return False
        
        try:
            filter_set = set(lattice_filter) if not isinstance(lattice_filter, set) else lattice_filter
            if not filter_set:
                return False
        except TypeError:
            return False
        
        return val in filter_set

    @staticmethod
    def evaluate(f_str: str, model: Model, world: World, interpretation: str = "down") -> str:
        """Parses and evaluates a single formula in a specific world of a model."""
        try:
            parser = FormulaParser(f_str)
            root = parser.parse()
            
            # Check missing assignments using model.get_assignment
            unknown = [
                a for a in root.get_atoms() 
                if a.upper() not in ('0', '1', 'TOP', 'BOT') and model.get_assignment(world, a) is None
            ]
            if unknown:
                msg = f"Missing assignments in world '{world.name_short}' for: {', '.join(unknown)}"
                logger.warning(msg)
                raise ValueError(msg)

            res = root.evaluate(model, world, interpretation=interpretation)
            res_str = str(res).replace("'", "")
            
            lattice_filter = getattr(model.many_lattice, 'filter', None)
            logger.debug(f"Filter: {lattice_filter}")
            if lattice_filter:
                in_filter = EvaluationService._check_membership(res, lattice_filter)
                status = "Yes" if in_filter else "No"
                return f"{res_str} | [In Filter: <b>{status}</b>]"

            return res_str
        except ValueError as ve:
            logger.error(f"Validation error for formula '{f_str}': {str(ve)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error evaluating formula '{f_str}': {str(e)}")
            raise

    @staticmethod
    def check_validity(f_str: str, model: Model, interpretation: str = "down"):
        """Checks formula satisfaction across all worlds in the model."""
        try:
            parser = FormulaParser(f_str)
            root = parser.parse()
            
            result_worlds = []
            result_for_calculation = set()
            lattice_filter = getattr(model.many_lattice, 'filter', None)
            logger.debug(f"Filter: {lattice_filter}")

            for world in sorted(model.worlds, key=lambda w: w.name_long):
                missing = [
                    a for a in root.get_atoms() 
                    if a.upper() not in ('0', '1', 'TOP', 'BOT') and model.get_assignment(world, a) is None
                ]
                if missing:
                    msg = f"World '{world.name_short}' is missing assignments for: {', '.join(missing)}"
                    logger.error(msg)
                    raise ValueError(msg)
                
                res = root.evaluate(model, world, interpretation=interpretation)
                res_str = str(res).replace("'", "")
                result_for_calculation.add(res)
                
                def format_membership(raw_res):
                    if not lattice_filter: 
                        return ""
                    in_f = EvaluationService._check_membership(raw_res, lattice_filter)
                    return f" [In Filter: <b>{'Yes' if in_f else 'No'}</b>]"

                formatted_res = res_str + format_membership(res)
                result_worlds.append((world.name_long, formatted_res))

            if result_for_calculation:
                global_res = model.many_lattice.meet_set(result_for_calculation)
            else:
                global_res = None

            global_res_str = str(global_res).replace("'", "")
            
            if lattice_filter and global_res is not None:
                in_f = EvaluationService._check_membership(global_res, lattice_filter)
                global_res_str += f" [In Filter: <b>{'Yes' if in_f else 'No'}</b>]"

            return result_worlds, global_res_str
            
        except ValueError as ve:
            logger.error(f"Validity check validation error: {str(ve)}")
            raise
        except Exception as e:
            logger.exception("Validity check failed due to unexpected error.")
            raise