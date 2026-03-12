import sqlite3

conn = sqlite3.connect('data/commerce.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:", tables)

# Check if prompt_revisions exists
if 'prompt_revisions' in tables:
    print("\n✓ prompt_revisions table exists")
    cursor = conn.execute("SELECT COUNT(*) FROM prompt_revisions")
    count = cursor.fetchone()[0]
    print(f"  Rows: {count}")
else:
    print("\n✗ prompt_revisions table NOT FOUND")
    print("  Need to initialize PromptRegistry")

conn.close()
