from sqlalchemy import create_engine, Table, MetaData

def seed_db(data, conn_str: str, table: str):
    engine = create_engine(conn_str)
    meta = MetaData(bind=engine)
    meta.reflect()
    tbl = meta.tables[table]

    with engine.begin() as conn:
        conn.execute(tbl.insert(), data)
    print(f"✅ Seeded {len(data)} rows into {table}")
