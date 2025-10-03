# Generator Module Structure

Struktur generator telah dipecah menjadi beberapa folder dan modul untuk memudahkan maintenance dan pengembangan:

## Struktur Folder

```
app/services/generator/
├── __init__.py                 # Main exports
├── core/                       # Core functionality
│   ├── __init__.py
│   ├── main_generator.py       # Main generation logic
│   └── schema_normalizer.py    # Schema normalization
├── types/                      # Type-specific generators
│   ├── __init__.py
│   ├── string_generator.py     # String generation
│   ├── number_generator.py     # Number generation
│   ├── boolean_generator.py    # Boolean generation
│   ├── array_generator.py      # Array generation
│   ├── object_generator.py     # Object generation
│   └── reference_generator.py  # Reference generation
└── utils/                      # Utility functions
    ├── __init__.py
    ├── cache_manager.py         # Cache management
    ├── pattern_generator.py     # Pattern and primary key generation
    └── dependency_resolver.py   # Dependency resolution
```

## Module Descriptions

### Core (`core/`)
- **main_generator.py**: Contains the main `generate_sample()` and `generate_data()` functions
- **schema_normalizer.py**: Handles schema normalization from introspector format

### Types (`types/`)
Each file handles generation for specific data types:
- **string_generator.py**: String generation with format support (email, UUID, date, etc.)
- **number_generator.py**: Integer and float generation with constraints
- **boolean_generator.py**: Boolean value generation
- **array_generator.py**: Array generation with item constraints
- **object_generator.py**: Object generation from properties
- **reference_generator.py**: Foreign key reference generation
- **primary_generator.py**: Primary key generation (both integer and string types)

### Utils (`utils/`)
- **cache_manager.py**: Manages reference and unique value caches
- **pattern_generator.py**: Pattern matching and primary key generation
- **dependency_resolver.py**: Resolves table generation order based on dependencies

## Usage

The main API remains the same:

```python
from app.services.generator import generate_data, generate_sample, clear_caches

# Generate data for multiple tables
result = generate_data(schemas, counts)

# Generate single sample
sample = generate_sample(schema, model_name, field_name)

# Clear caches
clear_caches()
```

## Benefits

1. **Modularity**: Each type has its own generator module
2. **Maintainability**: Easier to find and modify specific functionality
3. **Extensibility**: Easy to add new data types or generators
4. **Testing**: Each module can be tested independently
5. **Clarity**: Code organization reflects functionality
6. **Performance**: Smaller imports and better caching

## Backward Compatibility

The old `generator.py` file still works as a compatibility layer that imports from the new structure.