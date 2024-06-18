CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:
# what is the name of the violator for ticket number TN-00007": 
MATCH p=(t:ticket_number {{ticket_number: "TN-00007"}})-[:NAMES_FOUND]->() RETURN p
The question is:
{question}"""
