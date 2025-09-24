import json
import pandas as pd

def export_json(data, outfile: str):
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_csv(data, outfile: str):
    df = pd.DataFrame(data)
    df.to_csv(outfile, index=False)

def export_sql(data, table: str, outfile: str):
    with open(outfile, "w", encoding="utf-8") as f:
        for row in data:
            keys = ", ".join(row.keys())
            values = ", ".join([f"'{str(v)}'" for v in row.values()])
            f.write(f"INSERT INTO {table} ({keys}) VALUES ({values});\n")

def export_parquet(data, outfile: str):
    df = pd.DataFrame(data)
    df.to_parquet(outfile, index=False)
