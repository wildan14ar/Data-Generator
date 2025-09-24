📜 `datagen/presets.py`
=======================

`USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": True},
        "name": {"type": "string", "format": "name"},
        "email": {"type": "string", "format": "email", "unique": True},
        "status": {"type": "string", "enum": ["active","inactive","pending"]}
    }
}

POST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "unique": True},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "userId": {"type": "ref", "ref": "User.id"}   # relasi ke User
    }
}

ENROLLMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "studentId": {"type": "ref", "ref": "User.id"},
        "courseId": {"type": "ref", "ref": "Course.id"}
    }
}`

* * * * *

🚀 Cara Pakai
=============

`# 1. Generate JSON
python -m datagen.cli generate examples/schema_user.json --count 5 --out users.json

# 2. Generate CSV dengan seed random
python -m datagen.cli generate examples/schema_post.json --count 10 --format csv --seed 42 --out posts.csv

# 3. Generate SQL insert
python -m datagen.cli generate examples/schema_user.json --count 5 --format sql --table users --out users.sql

# 4. Direct seed ke Postgres
python -m datagen.cli seed examples/schema_user.json --count 5\
  --conn "postgresql://user:pass@localhost/mydb"\
  --table users`

* * * * *

🔥 Dengan struktur ini kamu sudah bisa:

-   Generate data **multi-format**

-   Pakai **constraint lengkap**

-   Ada **relasi antar model**

-   Bisa langsung **seed ke database**

Mau saya bikinin juga **contoh relasi lengkap (User → Post, Post → Comment, Student ↔ Course)** dalam `examples/`?