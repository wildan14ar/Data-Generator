import json
import pandas as pd
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def export_json(data: List[Dict[str, Any]], outfile: str) -> None:
    """Export data to JSON file.
    
    Args:
        data: List of data records
        outfile: Output file path
        
    Raises:
        IOError: If file cannot be written
        ValueError: If data is invalid
    """
    if not data:
        logger.warning("No data to export")
        return
    
    try:
        # Ensure directory exists
        Path(outfile).parent.mkdir(parents=True, exist_ok=True)
        
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Successfully exported {len(data)} records to {outfile}")
        
    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        raise IOError(f"Cannot write to {outfile}: {e}")

def export_csv(data: List[Dict[str, Any]], outfile: str) -> None:
    """Export data to CSV file.
    
    Args:
        data: List of data records
        outfile: Output file path
        
    Raises:
        IOError: If file cannot be written
        ValueError: If data cannot be converted to DataFrame
    """
    if not data:
        logger.warning("No data to export")
        return
    
    try:
        # Ensure directory exists
        Path(outfile).parent.mkdir(parents=True, exist_ok=True)
        
        # Flatten nested objects and arrays for CSV compatibility
        flattened_data = []
        for record in data:
            flat_record = _flatten_dict(record)
            flattened_data.append(flat_record)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(outfile, index=False, encoding='utf-8')
        
        logger.info(f"Successfully exported {len(data)} records to {outfile}")
        
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise IOError(f"Cannot write to {outfile}: {e}")

def export_sql(data: List[Dict[str, Any]], table: str, outfile: str) -> None:
    """Export data as SQL INSERT statements.
    
    Args:
        data: List of data records
        table: Target table name
        outfile: Output file path
        
    Raises:
        IOError: If file cannot be written
        ValueError: If table name or data is invalid
    """
    if not data:
        logger.warning("No data to export")
        return
    
    if not table or not table.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Invalid table name")
    
    try:
        # Ensure directory exists
        Path(outfile).parent.mkdir(parents=True, exist_ok=True)
        
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(f"-- SQL INSERT statements for table: {table}\n")
            f.write(f"-- Generated {len(data)} records\n\n")
            
            for i, row in enumerate(data):
                try:
                    # Flatten nested structures
                    flat_row = _flatten_dict(row)
                    
                    keys = ", ".join(f"`{k}`" for k in flat_row.keys())
                    values = ", ".join(_sql_escape_value(v) for v in flat_row.values())
                    f.write(f"INSERT INTO `{table}` ({keys}) VALUES ({values});\n")
                    
                except Exception as e:
                    logger.warning(f"Skipping record {i+1} due to error: {e}")
                    continue
        
        logger.info(f"Successfully exported {len(data)} SQL INSERT statements to {outfile}")
        
    except Exception as e:
        logger.error(f"Failed to export SQL: {e}")
        raise IOError(f"Cannot write to {outfile}: {e}")

def export_parquet(data: List[Dict[str, Any]], outfile: str) -> None:
    """Export data to Parquet file.
    
    Args:
        data: List of data records
        outfile: Output file path
        
    Raises:
        IOError: If file cannot be written
        ImportError: If pyarrow is not installed
    """
    if not data:
        logger.warning("No data to export")
        return
    
    try:
        import pyarrow
    except ImportError:
        raise ImportError("pyarrow is required for Parquet export. Install with: pip install pyarrow")
    
    try:
        # Ensure directory exists
        Path(outfile).parent.mkdir(parents=True, exist_ok=True)
        
        # Flatten nested objects for Parquet compatibility
        flattened_data = []
        for record in data:
            flat_record = _flatten_dict(record)
            flattened_data.append(flat_record)
        
        df = pd.DataFrame(flattened_data)
        df.to_parquet(outfile, index=False, engine='pyarrow')
        
        logger.info(f"Successfully exported {len(data)} records to {outfile}")
        
    except Exception as e:
        logger.error(f"Failed to export Parquet: {e}")
        raise IOError(f"Cannot write to {outfile}: {e}")

def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionary for CSV/SQL compatibility.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert list to comma-separated string
            items.append((new_key, ','.join(str(item) for item in v)))
        else:
            items.append((new_key, v))
    
    return dict(items)

def _sql_escape_value(value: Any) -> str:
    """Escape value for SQL INSERT statement.
    
    Args:
        value: Value to escape
        
    Returns:
        SQL-escaped string representation
    """
    if value is None:
        return "NULL"
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # Escape single quotes and wrap in quotes
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"
