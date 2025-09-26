"""
Datagen - Schema-Aware Data Generator

A Python package for generating realistic test data based on JSON Schema.
Supports multiple output formats and direct database seeding.

Author: Wildan Ahmad R
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Wildan Ahmad R"
__email__ = "wildan14ar@example.com"
__license__ = "MIT"

from .core import generate_data, generate_sample
from .exporters import export_json, export_csv, export_sql, export_parquet
from .seeder import seed_db

__all__ = [
    'generate_data',
    'generate_sample', 
    'export_json',
    'export_csv',
    'export_sql',
    'export_parquet',
    'seed_db',
]