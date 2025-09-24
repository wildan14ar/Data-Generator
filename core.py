import random, re
from faker import Faker

fake = Faker()
_unique_cache = {}  # cache untuk uniqueness
_ref_cache = {}     # cache untuk relasi antar model

def generate_sample(schema: dict, model_name: str = None):
    """Generate satu nilai dari schema."""

    # --- ENUM ---
    if "enum" in schema:
        return random.choice(schema["enum"])

    t = schema.get("type")

    # --- String ---
    if t == "string":
        fmt = schema.get("format")
        min_len = schema.get("minLength", 3)
        max_len = schema.get("maxLength", 12)

        if fmt == "email":
            return fake.unique.email() if schema.get("unique") else fake.email()
        if fmt == "uuid":
            return fake.unique.uuid4() if schema.get("unique") else fake.uuid4()
        if fmt == "date":
            return fake.date()
        if fmt == "name":
            return fake.name()
        if "pattern" in schema:
            pat = schema["pattern"]
            # generate dummy string cocok pattern (simple only)
            return re.sub(r"\[A-Z\]", random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), pat)
        return fake.word()[:max_len]

    # --- Integer/Number ---
    if t in ["integer", "number"]:
        minimum = schema.get("minimum", 1)
        maximum = schema.get("maximum", 1000)
        return random.randint(minimum, maximum)

    # --- Boolean ---
    if t == "boolean":
        return random.choice([True, False])

    # --- Array ---
    if t == "array":
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 3)
        return [
            generate_sample(schema["items"], model_name)
            for _ in range(random.randint(min_items, max_items))
        ]

    # --- Object ---
    if t == "object":
        return {
            key: generate_sample(sub_schema, model_name)
            for key, sub_schema in schema.get("properties", {}).items()
        }

    # --- Reference ---
    if t == "ref":
        ref_str = schema["ref"]  # contoh: "User.id"
        model, field = ref_str.split(".")
        if model not in _ref_cache:
            raise ValueError(f"Model {model} belum tersedia untuk ref")
        return random.choice([row[field] for row in _ref_cache[model]])

    return None


def generate_data(schema: dict, count: int, model_name: str = None, seed: int = None):
    """Generate banyak data dari schema."""
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    data = [generate_sample(schema, model_name) for _ in range(count)]
    if model_name:
        _ref_cache[model_name] = data
    return data
