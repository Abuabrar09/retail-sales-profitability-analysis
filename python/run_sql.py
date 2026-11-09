import sys
import duckdb

# Usage: python python/run_sql.py sql/<file>.sql
con = duckdb.connect("retail.duckdb")          # local database file
sql_text = open(sys.argv[1]).read()

# drop comment lines, then run each statement separated by ;
lines = [l for l in sql_text.splitlines() if not l.strip().startswith("--")]
for stmt in "\n".join(lines).split(";"):
    if stmt.strip():
        result = con.sql(stmt)
        if result is not None:
            result.show(max_rows=50)