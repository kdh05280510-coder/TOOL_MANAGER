from database.db import get_connection, init_db

init_db()
conn = get_connection()
rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print([r[0] for r in rows])