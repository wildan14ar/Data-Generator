import argparse, json
from .core import generate_data
from .exporters import export_json, export_csv, export_sql, export_parquet
from .seeder import seed_db

def main():
    parser = argparse.ArgumentParser(description="Schema-aware Data Generator")
    subparsers = parser.add_subparsers(dest="command")

    # ---- generate ----
    g = subparsers.add_parser("generate", help="Generate data dari schema")
    g.add_argument("schema", help="Path ke schema JSON")
    g.add_argument("--count", type=int, default=10, help="Jumlah data")
    g.add_argument("--model", type=str, default="Data", help="Nama model")
    g.add_argument("--out", type=str, default="data.json", help="File output")
    g.add_argument("--format", choices=["json","csv","sql","parquet"], default="json")
    g.add_argument("--table", type=str, help="Nama tabel (untuk SQL)")
    g.add_argument("--seed", type=int, help="Random seed")

    # ---- seed ----
    s = subparsers.add_parser("seed", help="Generate & seed ke database")
    s.add_argument("schema", help="Path ke schema JSON")
    s.add_argument("--count", type=int, default=10)
    s.add_argument("--model", type=str, default="Data")
    s.add_argument("--conn", required=True, help="DB connection string (SQLAlchemy style)")
    s.add_argument("--table", required=True, help="Nama tabel")
    s.add_argument("--seed", type=int)

    args = parser.parse_args()

    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    if args.command == "generate":
        data = generate_data(schema, args.count, args.model, args.seed)
        if args.format == "json": export_json(data, args.out)
        elif args.format == "csv": export_csv(data, args.out)
        elif args.format == "sql": 
            if not args.table: raise ValueError("--table wajib untuk SQL")
            export_sql(data, args.table, args.out)
        elif args.format == "parquet": export_parquet(data, args.out)
        print(f"✅ {args.count} rows generated to {args.out}")

    elif args.command == "seed":
        data = generate_data(schema, args.count, args.model, args.seed)
        seed_db(data, args.conn, args.table)

if __name__ == "__main__":
    main()
