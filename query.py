import duckdb

con = duckdb.connect("jeopardy_seasons.duckdb", read_only=True)
con.execute("USE prod")

# con.sql("""
#     SELECT catalog_name, schema_name
#     FROM information_schema.schemata
#     ORDER BY catalog_name, schema_name
# """).show()

# con.sql("SHOW TABLES").show()

con.sql("""
    SELECT *
    FROM prod.mrt_todays_episode
""").show()

con.close()
