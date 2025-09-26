# 🎯 Datagen - Schema-Aware Data Generator

Sebuah tool Python untuk generate data dummy berkualitas tinggi berdasarkan JSON Schema. Mendukung berbagai format output dan seeding langsung ke database.

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Fitur Utama

- **Schema-driven**: Generate data berdasarkan JSON Schema dengan constraint lengkap
- **Multi-format export**: JSON, CSV, SQL, dan Parquet
- **Database seeding**: Langsung insert ke database (PostgreSQL, MySQL, SQLite)
- **Relasi antar model**: Mendukung foreign key references
- **Realistic data**: Menggunakan Faker untuk data yang realistis
- **Reproducible**: Seed control untuk konsistensi data
- **CLI interface**: Command line yang mudah digunakan

## 📦 Instalasi

```bash
# Clone repository
git clone https://github.com/wildan14ar/Datagen.git
cd Datagen

# Buat virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### 1. Buat Schema File

Buat file `user_schema.json`:
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "integer", "unique": true},
    "name": {"type": "string", "format": "name"},
    "email": {"type": "string", "format": "email", "unique": true},
    "age": {"type": "integer", "minimum": 18, "maximum": 65},
    "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
    "created_at": {"type": "string", "format": "date"}
  }
}
```

### 2. Generate Data

```bash
# Generate 10 users ke JSON
python -m src.cli generate user_schema.json --count 10 --out users.json

# Generate ke CSV dengan seed untuk reproducible results
python -m src.cli generate user_schema.json --count 50 --format csv --seed 42 --out users.csv

# Generate SQL INSERT statements
python -m src.cli generate user_schema.json --count 20 --format sql --table users --out users.sql
```

### 3. Database Seeding

```bash
# Langsung insert ke PostgreSQL
python -m src.cli seed user_schema.json --count 100 \
  --conn "postgresql://user:password@localhost/mydb" \
  --table users

# SQLite
python -m src.cli seed user_schema.json --count 50 \
  --conn "sqlite:///mydata.db" \
  --table users
```

## 📋 Dokumentasi Schema

### Tipe Data yang Didukung

#### String Types
```json
{
  "type": "string",
  "format": "email|name|uuid|date",
  "minLength": 5,
  "maxLength": 50,
  "pattern": "[A-Z]{3}-[0-9]{4}",
  "unique": true
}
```

#### Numeric Types
```json
{
  "type": "integer|number",
  "minimum": 1,
  "maximum": 1000
}
```

#### Enum Values
```json
{
  "type": "string",
  "enum": ["active", "inactive", "pending"]
}
```

#### Array Types
```json
{
  "type": "array",
  "items": {"type": "string"},
  "minItems": 1,
  "maxItems": 5
}
```

#### Object Types
```json
{
  "type": "object",
  "properties": {
    "address": {"type": "string"},
    "city": {"type": "string"}
  }
}
```

#### References (Foreign Keys)
```json
{
  "type": "ref",
  "ref": "User.id"
}
```

## 🔗 Contoh Schema dengan Relasi

### User Schema (`user.json`)
```json
{
  "type": "object", 
  "properties": {
    "id": {"type": "integer", "unique": true},
    "name": {"type": "string", "format": "name"},
    "email": {"type": "string", "format": "email", "unique": true},
    "status": {"type": "string", "enum": ["active", "inactive"]}
  }
}
```

### Post Schema (`post.json`)
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "integer", "unique": true},
    "title": {"type": "string", "maxLength": 100},
    "body": {"type": "string", "maxLength": 500},
    "userId": {"type": "ref", "ref": "User.id"},
    "published": {"type": "boolean"}
  }
}
```

Untuk menggunakan relasi:
```bash
# Generate users terlebih dahulu
python -m src.cli generate user.json --count 10 --model User --out users.json

# Kemudian generate posts yang reference ke users
python -m src.cli generate post.json --count 50 --model Post --out posts.json
```

## 🛠 CLI Commands

### Generate Command
```bash
python -m src.cli generate <schema_file> [options]

Options:
  --count INT       Jumlah data yang akan digenerate (default: 10)
  --model STR       Nama model untuk referencing (default: "Data")
  --out STR         File output (default: "data.json")
  --format STR      Format output: json|csv|sql|parquet (default: "json")
  --table STR       Nama tabel untuk SQL format
  --seed INT        Random seed untuk reproducible results
```

### Seed Command
```bash
python -m src.cli seed <schema_file> [options]

Options:
  --count INT       Jumlah data yang akan digenerate (default: 10)
  --model STR       Nama model untuk referencing (default: "Data") 
  --conn STR        Database connection string (required)
  --table STR       Nama tabel target (required)
  --seed INT        Random seed
```

## 🏗 Arsitektur Code

### Struktur Project
```
src/
├── cli.py          # Command line interface
├── core.py         # Core data generation logic
├── exporters.py    # Export functions untuk berbagai format
└── seeder.py       # Database seeding functionality
```

### Core Components

#### 1. `core.py` - Data Generation Engine
- **`generate_sample()`**: Generate satu data point dari schema
- **`generate_data()`**: Generate multiple data points
- **Caching system**: `_unique_cache` untuk uniqueness, `_ref_cache` untuk relasi
- **Format handlers**: Email, UUID, date, pattern matching

#### 2. `exporters.py` - Multi-Format Export
- **`export_json()`**: Pretty-printed JSON dengan UTF-8 encoding
- **`export_csv()`**: CSV menggunakan pandas
- **`export_sql()`**: SQL INSERT statements
- **`export_parquet()`**: Parquet format untuk big data

#### 3. `seeder.py` - Database Integration
- **SQLAlchemy integration**: Universal database support
- **Reflection-based**: Otomatis detect table structure
- **Transaction-safe**: Menggunakan engine.begin() untuk atomicity

#### 4. `cli.py` - Command Line Interface
- **Argparse-based**: Clean command structure
- **Subcommands**: `generate` dan `seed`
- **Validation**: Required parameters dan error handling

## 🔧 Advanced Usage

### Custom Pattern Generation
```json
{
  "type": "string",
  "pattern": "[A-Z]{2}-[0-9]{4}-[A-Z]{1}"
}
```
Generates: "AB-1234-C"

### Complex Nested Objects
```json
{
  "type": "object",
  "properties": {
    "profile": {
      "type": "object", 
      "properties": {
        "bio": {"type": "string", "maxLength": 200},
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1,
          "maxItems": 5
        }
      }
    }
  }
}
```

### Database Connection Strings
```bash
# PostgreSQL
postgresql://username:password@localhost:5432/database

# MySQL
mysql://username:password@localhost:3306/database

# SQLite
sqlite:///path/to/database.db

# SQL Server
mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
```

## 🚨 Saran dan Rekomendasi

### ✅ Improvements yang Disarankan

1. **Error Handling yang Lebih Robust**
   - Validasi schema sebelum generation
   - Handle database connection errors
   - Validasi file path dan permissions

2. **Testing Framework**
   - Unit tests untuk core functions
   - Integration tests untuk database seeding
   - Schema validation tests

3. **Configuration Management**
   - Support untuk config file (.env, .toml)
   - Database connection pooling
   - Default schema templates

4. **Performance Optimizations**
   - Batch insert untuk database seeding
   - Memory-efficient generation untuk large datasets
   - Progress bars untuk long operations

5. **Extended Format Support**
   - XML export
   - YAML export  
   - Excel files (.xlsx)
   - Avro format

6. **Advanced Schema Features**
   - JSON Schema validation (Draft 7/2019-09)
   - Conditional schemas (if/then/else)
   - Schema composition (allOf, anyOf, oneOf)
   - Custom format validators

### 🔒 Security Considerations

1. **SQL Injection Prevention**
   - Parameterized queries instead of string concatenation
   - Input sanitization untuk SQL export

2. **Connection Security**
   - SSL/TLS support untuk database connections
   - Credential management best practices

### 📊 Monitoring & Logging

1. **Logging Framework**
   - Structured logging dengan levels
   - Progress tracking untuk large generations
   - Performance metrics

2. **Validation & Quality Control**
   - Data quality checks
   - Schema compliance validation
   - Uniqueness constraint verification

### 🎯 Usage Examples Repository

Buat folder `examples/` dengan schema-schema umum:
- E-commerce (products, orders, customers)
- Blog system (users, posts, comments)
- Educational (students, courses, enrollments)
- Financial (accounts, transactions, users)

### 🚀 Future Enhancements

1. **Web UI**: Simple web interface untuk non-technical users
2. **API Mode**: REST API untuk integration dengan other systems
3. **Streaming**: Support untuk infinite data streams
4. **Multi-language**: Localized fake data (names, addresses, etc.)
5. **ML Integration**: AI-powered realistic data patterns

## 📄 License

MIT License - lihat file [LICENSE](LICENSE) untuk detail lengkap.

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wildan14ar/Datagen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wildan14ar/Datagen/discussions)
- **Email**: wildan14ar@example.com