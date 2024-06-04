
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

# Get the name of all 42 year-olds
records, summary, keys = driver.execute_query(
    "MATCH (p:Product {productName: 'Chai'}) - [:PART_OF]->(c:Category) RETURN *;"
)

# Loop through results and do something with them
for price in records:
    print(price)

# Summary information
print("The query `{query}` returned {records_count} records in {time} ms.".format(
    query=summary.query, records_count=len(records),
    time=summary.result_available_after,
))