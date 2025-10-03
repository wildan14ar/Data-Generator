"""
Dependency resolution for table generation order
"""

import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)


def determine_generation_order(schemas: Dict[str, Dict[str, Any]]) -> List[str]:
    """Determine the order to generate tables based on foreign key dependencies.
    
    Args:
        schemas: Dictionary of table schemas
        
    Returns:
        List of table names in dependency order (parents first)
    """
    # Build dependency graph
    dependencies = {}  # table -> set of tables it depends on
    
    for table_name, schema in schemas.items():
        dependencies[table_name] = set()
        
        if schema.get("type") == "object" and "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_schema.get("type") == "ref":
                    ref_str = prop_schema.get("ref", "")
                    if "." in ref_str:
                        referenced_table = ref_str.split(".", 1)[0]
                        if referenced_table in schemas:
                            dependencies[table_name].add(referenced_table)
    
    # Topological sort
    order = []
    visited = set()
    temp_visited = set()
    
    def visit(table: str):
        if table in temp_visited:
            logger.warning(f"Circular dependency detected involving table '{table}'")
            return
        if table in visited:
            return
        
        temp_visited.add(table)
        
        for dep in dependencies.get(table, set()):
            if dep in schemas:  # Only visit if dependency is in our schema set
                visit(dep)
        
        temp_visited.remove(table)
        visited.add(table)
        order.append(table)
    
    for table in schemas.keys():
        if table not in visited:
            visit(table)
    
    return order