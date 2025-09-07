
import os
import psycopg2

url = os.environ.get("POSTGRES_URL", "postgresql://trust:trust@localhost:5432/trust")
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("""
insert into countries (iso3, iso2, name, region, income_group) values
('SWE','SE','Sweden','Europe','High income'),
('USA','US','United States','North America','High income'),
('BRA','BR','Brazil','Latin America','Upper middle income'),
('NGA','NG','Nigeria','Africa','Lower middle income'),
('IND','IN','India','South Asia','Lower middle income')
on conflict (iso3) do nothing;
""")
conn.commit()
cur.close()
conn.close()
print("Seeded countries.")
