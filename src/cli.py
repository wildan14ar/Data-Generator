#!/usr/bin/env python3
"""
Command Line Interface for Datagen - Schema-Aware Data Generator
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Handle imports for both direct execution and module import
try:
    from .core import generate_data, clear_caches
    from .exporters import export_json, export_csv, export_sql, export_parquet
    from .seeder import seed_db, test_connection
except ImportError:
    # Direct execution - use absolute imports
    from core import generate_data, clear_caches
    from exporters import export_json, export_csv, export_sql, export_parquet
    from seeder import seed_db, test_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and validate JSON schema from file.
    
    Args:
        schema_path: Path to schema JSON file
        
    Returns:
        Loaded schema dictionary
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file is invalid JSON
        ValueError: If schema is invalid
    """
    schema_file = Path(schema_path)
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    if not schema_file.suffix.lower() == '.json':
        logger.warning(f"Schema file doesn't have .json extension: {schema_path}")
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in schema file: {e}", e.doc, e.pos)
    
    # Basic schema validation
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a JSON object")
    
    if 'type' not in schema:
        raise ValueError("Schema must have a 'type' property")
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def handle_generate_command(args) -> None:
    """Handle the generate subcommand.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Load schema
        schema = load_schema(args.schema)
        
        # Clear caches for fresh start
        clear_caches()
        
        # Generate data
        logger.info(f"Generating {args.count} records...")
        data = generate_data(schema, args.count, args.model, args.seed)
        
        # Export data
        if args.format == "json":
            export_json(data, args.out)
        elif args.format == "csv":
            export_csv(data, args.out)
        elif args.format == "sql":
            if not args.table:
                raise ValueError("--table argument is required for SQL format")
            export_sql(data, args.table, args.out)
        elif args.format == "parquet":
            export_parquet(data, args.out)
        
        print(f"✅ Successfully generated {len(data)} records to {args.out}")
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_seed_command(args) -> None:
    """Handle the seed subcommand.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Load schema
        schema = load_schema(args.schema)
        
        # Test database connection
        logger.info("Testing database connection...")
        if not test_connection(args.conn):
            raise ConnectionError("Cannot connect to database")
        
        # Clear caches for fresh start  
        clear_caches()
        
        # Generate data
        logger.info(f"Generating {args.count} records...")
        data = generate_data(schema, args.count, args.model, args.seed)
        
        # Seed database
        logger.info(f"Seeding database...")
        seed_db(data, args.conn, args.table)
        
        print(f"✅ Successfully seeded {len(data)} records into table '{args.table}'")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Datagen - Schema-Aware Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate JSON data
  %(prog)s generate user_schema.json --count 100 --out users.json
  
  # Generate CSV with seed
  %(prog)s generate user_schema.json --count 50 --format csv --seed 42 --out users.csv
  
  # Generate SQL INSERT statements  
  %(prog)s generate user_schema.json --count 20 --format sql --table users --out users.sql
  
  # Seed PostgreSQL database
  %(prog)s seed user_schema.json --count 100 --conn "postgresql://user:pass@localhost/db" --table users
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="Datagen 1.0.0"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ---- Generate subcommand ----
    gen_parser = subparsers.add_parser(
        "generate", 
        help="Generate data from schema",
        description="Generate synthetic data based on JSON schema"
    )
    gen_parser.add_argument(
        "schema", 
        help="Path to JSON schema file"
    )
    gen_parser.add_argument(
        "--count", 
        type=int, 
        default=10, 
        help="Number of records to generate (default: 10)"
    )
    gen_parser.add_argument(
        "--model", 
        type=str, 
        default="Data", 
        help="Model name for referencing (default: 'Data')"
    )
    gen_parser.add_argument(
        "--out", 
        type=str, 
        default="data.json", 
        help="Output file path (default: 'data.json')"
    )
    gen_parser.add_argument(
        "--format", 
        choices=["json", "csv", "sql", "parquet"], 
        default="json",
        help="Output format (default: json)"
    )
    gen_parser.add_argument(
        "--table", 
        type=str, 
        help="Table name (required for SQL format)"
    )
    gen_parser.add_argument(
        "--seed", 
        type=int, 
        help="Random seed for reproducible results"
    )

    # ---- Seed subcommand ----
    seed_parser = subparsers.add_parser(
        "seed", 
        help="Generate data and seed database",
        description="Generate synthetic data and insert directly into database"
    )
    seed_parser.add_argument(
        "schema", 
        help="Path to JSON schema file"
    )
    seed_parser.add_argument(
        "--count", 
        type=int, 
        default=10,
        help="Number of records to generate (default: 10)"
    )
    seed_parser.add_argument(
        "--model", 
        type=str, 
        default="Data",
        help="Model name for referencing (default: 'Data')"
    )
    seed_parser.add_argument(
        "--conn", 
        required=True, 
        help="Database connection string (SQLAlchemy format)"
    )
    seed_parser.add_argument(
        "--table", 
        required=True, 
        help="Target table name"
    )
    seed_parser.add_argument(
        "--seed", 
        type=int, 
        help="Random seed for reproducible results"
    )

    # Parse arguments
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle commands
    if args.command == "generate":
        handle_generate_command(args)
    elif args.command == "seed":
        handle_seed_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
