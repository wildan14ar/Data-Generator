# 🎯 Datagen API - Schema-Aware Data Generator

REST API untuk generate data dummy berkualitas tinggi berdasarkan JSON Schema. Mendukung berbagai format output dan seeding langsung ke database.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/wildan14ar/Datagen.git
cd Datagen

# Buat virtual environment
python -m venv .venv

# Aktivasi virtual environment
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
# Start server
python app/server.py
```

API akan tersedia di:
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Statistics**: http://localhost:8000/api/v1/stats

## 🏗️ Arsitektur Baru - REST API Only

### Struktur Project

```
datagen/
├── app/                          # Main application package
│   ├── api/                     # API layer
│   │   └── v1/                  # API version 1
│   │       ├── generate.py      # Data generation endpoints
│   │       ├── seed.py          # Database seeding endpoints
│   │       ├── files.py         # File download endpoints
│   │       ├── schemas.py       # Schema validation endpoints
│   │       ├── system.py        # System endpoints (health, stats)
│   │       └── router.py        # Main API router
│   ├── core/                    # Core application components
│   │   ├── config.py           # Configuration settings
│   │   └── exceptions.py       # Exception handlers
│   ├── models/                  # Pydantic models
│   │   └── schemas.py          # Request/response models
│   ├── services/                # Business logic layer
│   │   ├── generator.py        # Data generation service
│   │   ├── exporter.py         # Data export service
│   │   └── seeder.py           # Database seeding service
│   ├── utils/                   # Utility functions
│   │   └── validators.py       # Schema validation utilities
│   ├── main.py                 # FastAPI app factory
│   └── server.py               # API server startup script
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

### Clean Architecture Benefits

- **API Layer** (`app/api/`): FastAPI routers dan HTTP handling
- **Services Layer** (`app/services/`): Business logic dan core functionality
- **Models Layer** (`app/models/`): Pydantic schemas untuk validation
- **Utils Layer** (`app/utils/`): Helper functions dan utilities
- **Core Layer** (`app/core/`): Configuration dan framework setup

## 🛠 API Endpoints

### Data Generation

#### Generate Data (In-Memory)
```http
POST /api/v1/data/generate
```

Generate data dan return langsung di response.

**Request Body:**
```json
{
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "format": "name"},
            "email": {"type": "string", "format": "email", "unique": true},
            "age": {"type": "integer", "minimum": 18, "maximum": 80}
        }
    },
    "count": 10,
    "format": "json",
    "seed": 42
}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 25
        }
    ],
    "count": 10,
    "format": "json"
}
```

#### Generate Data to File
```http
POST /api/v1/data/generate/file
```

Generate data dan save ke downloadable file.

**Request Body:**
```json
{
    "schema": {...},
    "count": 1000,
    "format": "csv",
    "filename": "users",
    "seed": 42
}
```

**Response:**
```json
{
    "success": true,
    "file_id": "uuid-here",
    "filename": "uuid_users.csv",
    "download_url": "/api/v1/files/download/uuid_users.csv",
    "count": 1000,
    "format": "csv",
    "expires_in": "1 hour"
}
```

**Supported Formats:** `json`, `csv`, `sql`, `parquet`

### Database Seeding

#### Seed Database
```http
POST /api/v1/database/seed
```

Generate data dan insert langsung ke database.

**Request Body:**
```json
{
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "format": "name"},
            "email": {"type": "string", "format": "email", "unique": true}
        }
    },
    "count": 1000,
    "connection_string": "postgresql://user:pass@localhost/dbname",
    "table_name": "users",
    "batch_size": 500
}
```

### Schema Validation

#### Validate Schema
```http
POST /api/v1/schemas/validate
```

Validate JSON schema sebelum generation.

**Request Body:**
```json
{
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "format": "name"}
        }
    }
}
```

**Response:**
```json
{
    "success": true,
    "valid": true,
    "errors": [],
    "warnings": [],
    "schema_type": "object",
    "supported_features": ["string_formats"]
}
```

### System Endpoints

#### Health Check
```http
GET /api/v1/health
```

Check API health dan uptime.

#### Statistics
```http
GET /api/v1/stats
```

Get usage statistics dan metrics.

### File Management

#### Download File
```http
GET /api/v1/files/download/{filename}
```

Download generated file.

## 📊 Schema Features

### Supported Types

- **string**: Text data dengan formats (email, uuid, date, name) dan patterns
- **integer**: Whole numbers dengan min/max constraints
- **number**: Decimal numbers dengan min/max constraints  
- **boolean**: True/false values
- **array**: Lists dengan configurable item counts
- **object**: Nested structures dengan properties
- **ref**: References ke other generated models
- **enum**: Fixed set of possible values

### String Formats

- `email`: Generates valid email addresses
- `uuid`: Generates UUID v4 strings
- `date`: Generates date strings (YYYY-MM-DD)
- `name`: Generates person names
- Custom regex patterns supported

### Schema Examples

#### Simple User Schema
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "name": {"type": "string", "format": "name"},
        "email": {"type": "string", "format": "email", "unique": true},
        "age": {"type": "integer", "minimum": 18, "maximum": 80},
        "status": {"enum": ["active", "inactive", "pending"]},
        "created_at": {"type": "string", "format": "date"}
    }
}
```

#### Complex Schema dengan Relations
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": true},
        "title": {"type": "string", "maxLength": 100},
        "salary": {"type": "number", "minimum": 30000, "maximum": 200000},
        "department": {"enum": ["IT", "HR", "Finance", "Marketing"]},
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "zipcode": {"type": "string", "pattern": "[0-9]{5}"}
            }
        },
        "managerId": {"type": "ref", "ref": "User.id"}
    }
}
```

#### Custom Patterns
```json
{
    "type": "object",
    "properties": {
        "product_code": {"type": "string", "pattern": "[A-Z]{2}-[0-9]{4}-[A-Z]{1}"},
        "phone": {"type": "string", "pattern": "\\+62[0-9]{9,12}"}
    }
}
```

## 🗄️ Database Support

Supported databases via SQLAlchemy:
- **PostgreSQL** - Recommended untuk production
- **MySQL/MariaDB** - Popular choice
- **SQLite** - Good untuk development
- **SQL Server** - Enterprise usage

### Connection String Examples
```bash
# PostgreSQL
postgresql://username:password@localhost:5432/database

# MySQL
mysql://username:password@localhost:3306/database

# SQLite
sqlite:///path/to/database.db

# SQL Server
mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server
```

## ⚙️ Configuration

### Environment Variables (.env file)

```env
# API Settings
PROJECT_NAME="Datagen API"
VERSION="1.0.0"
DEBUG=true
API_V1_STR="/api/v1"

# Server Settings
HOST=0.0.0.0
PORT=8000
RELOAD=true

# CORS Settings  
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=

# File Settings
MAX_FILE_SIZE=104857600  # 100MB
FILE_CLEANUP_HOURS=1

# Generation Limits
MAX_RECORDS_PER_REQUEST=100000
MAX_BATCH_SIZE=10000

# Logging
LOG_LEVEL=INFO
```

## 🧪 Development & Testing

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run dengan coverage
pytest --cov=app tests/
```

### Testing the API

```bash
# Test health check
curl http://localhost:8000/api/v1/health

# Test data generation
curl -X POST "http://localhost:8000/api/v1/data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "format": "name"},
        "email": {"type": "string", "format": "email"}
      }
    },
    "count": 5
  }'
```

## 🎯 Advanced Usage Examples

### 1. E-Commerce Data

#### Products Schema
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": true},
        "name": {"type": "string", "maxLength": 100},
        "price": {"type": "number", "minimum": 10000, "maximum": 5000000},
        "category": {"enum": ["Electronics", "Clothing", "Books", "Sports"]},
        "sku": {"type": "string", "pattern": "[A-Z]{3}-[0-9]{6}"},
        "in_stock": {"type": "boolean"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3
        }
    }
}
```

#### Orders Schema
```json
{
    "type": "object", 
    "properties": {
        "id": {"type": "integer", "unique": true},
        "customer_id": {"type": "ref", "ref": "Customer.id"},
        "product_id": {"type": "ref", "ref": "Product.id"},
        "quantity": {"type": "integer", "minimum": 1, "maximum": 10},
        "total": {"type": "number", "minimum": 10000, "maximum": 10000000},
        "status": {"enum": ["pending", "processing", "shipped", "delivered"]},
        "order_date": {"type": "string", "format": "date"}
    }
}
```

### 2. Blog System Data

#### Users Schema
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": true},
        "username": {"type": "string", "minLength": 3, "maxLength": 20},
        "email": {"type": "string", "format": "email", "unique": true},
        "full_name": {"type": "string", "format": "name"},
        "bio": {"type": "string", "maxLength": 500},
        "avatar_url": {"type": "string", "format": "uuid"},
        "role": {"enum": ["user", "author", "admin"]},
        "is_active": {"type": "boolean"},
        "joined_date": {"type": "string", "format": "date"}
    }
}
```

#### Posts Schema  
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": true},
        "title": {"type": "string", "minLength": 10, "maxLength": 200},
        "slug": {"type": "string", "pattern": "[a-z0-9-]+"},
        "content": {"type": "string", "minLength": 100, "maxLength": 5000},
        "author_id": {"type": "ref", "ref": "User.id"},
        "category": {"enum": ["tech", "lifestyle", "business", "travel"]},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "published": {"type": "boolean"},
        "views": {"type": "integer", "minimum": 0, "maximum": 100000},
        "published_date": {"type": "string", "format": "date"}
    }
}
```

### 3. Financial Data

#### Transactions Schema
```json
{
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "account_id": {"type": "ref", "ref": "Account.id"},
        "amount": {"type": "number", "minimum": -1000000000, "maximum": 1000000000},
        "type": {"enum": ["debit", "credit", "transfer", "fee"]},
        "category": {"enum": ["food", "transport", "salary", "entertainment", "bills"]},
        "description": {"type": "string", "maxLength": 200},
        "reference_number": {"type": "string", "pattern": "TXN[0-9]{10}"},
        "status": {"enum": ["pending", "completed", "failed", "cancelled"]},
        "transaction_date": {"type": "string", "format": "date"}
    }
}
```

## 🚨 Migration dari CLI ke REST API

### ❌ CLI Commands (Deprecated)

```bash
# OLD - CLI approach (tidak lagi didukung)
python -m src.cli generate user_schema.json --count 100 --out users.json
python -m src.cli seed user_schema.json --count 100 --conn "postgresql://..." --table users
```

### ✅ REST API Approach (New)

```bash
# NEW - REST API approach
curl -X POST "http://localhost:8000/api/v1/data/generate/file" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {...},
    "count": 100,
    "format": "json",
    "filename": "users"
  }'

curl -X POST "http://localhost:8000/api/v1/database/seed" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {...},
    "count": 100,
    "connection_string": "postgresql://...",
    "table_name": "users"
  }'
```

## 🔧 Error Handling

API menggunakan standardized error responses:

```json
{
    "success": false,
    "error": "Validation failed",
    "error_type": "ValidationError",
    "details": "Schema must have a 'type' property",
    "status_code": 400
}
```

### Error Types
- `ValidationError` - Request validation failed
- `GenerationError` - Data generation failed  
- `ExportError` - File export failed
- `DatabaseError` - Database operation failed
- `SchemaValidationError` - Schema validation failed
- `InternalServerError` - Unexpected server error

## 📈 Performance & Limits

### Default Limits
- Maximum records per request: **100,000**
- Maximum batch size for database: **10,000** 
- File cleanup after: **1 hour**
- Maximum file size: **100MB**

### Performance Tips

1. **Large datasets**: Gunakan file generation untuk datasets > 10k records
2. **Database seeding**: Gunakan batch_size optimal (500-2000) 
3. **Memory usage**: API secara otomatis manage memory untuk large generations
4. **Concurrent requests**: FastAPI mendukung async concurrent processing

## 📝 License

MIT License - lihat file [LICENSE](LICENSE) untuk detail lengkap.

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Create Pull Request

## 📞 Support & Community

- **GitHub Issues**: [Report bugs atau request features](https://github.com/wildan14ar/Datagen/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/wildan14ar/Datagen/discussions)
- **Documentation**: API docs tersedia di `/docs` endpoint

## 🎉 What's New in v2.0

### ✅ Completed Restructuring

1. **Removed CLI**: Pure REST API focus
2. **Clean Architecture**: Layered application structure
3. **Versioned APIs**: `/api/v1/` endpoints
4. **Better Error Handling**: Standardized error responses
5. **Auto Documentation**: Swagger/ReDoc integration
6. **Production Ready**: Proper middleware dan security
7. **Modern Dependencies**: Updated to latest versions
8. **Development Experience**: Hot reload dan testing support

### 🚀 Benefits

- **Better Maintainability**: Clear separation of concerns
- **Scalability**: Easy untuk add new endpoints dan features  
- **Testing**: Each layer dapat di-test independently
- **Documentation**: Automatic API documentation
- **Production Ready**: Proper error handling dan security
- **Developer Experience**: Easy untuk understand dan extend

Project ini sekarang menggunakan modern FastAPI best practices dan provides solid foundation untuk production-ready REST API service! 🎉