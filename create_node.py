
from connect import Neo4jConnection

conn = Neo4jConnection()

conn.query('CREATE CONSTRAINT papers IF NOT EXISTS ON (p:Paper)     ASSERT p.id IS UNIQUE')
conn.query('CREATE CONSTRAINT authors IF NOT EXISTS ON (a:Author) ASSERT a.name IS UNIQUE')
conn.query('CREATE CONSTRAINT categories IF NOT EXISTS ON (c:Category) ASSERT c.category IS UNIQUE')