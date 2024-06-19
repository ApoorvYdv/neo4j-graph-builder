# CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
# Instructions:
# Use only the provided relationship types and properties in the schema.
# Do not use any other relationship types or properties that are not provided.
# Schema:
# {schema}
# Note: Do not include any explanations or apologies in your responses.
# Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
# Do not include any text except the generated Cypher statement.
# Examples: Here are a few examples of generated Cypher statements for particular questions:
# # what is the name of the violator for ticket number TN-00007":
# MATCH p=(t:ticket_number {{ticket_number: "TN-00007"}})-[:NAMES_FOUND]->() RETURN p
# The question is:
# {question}"""

CYPHER_GENERATION_PROMPT_TEMPLATE = """You are a Neo4j expert. Given an input question,
create a syntactically correct Cypher statement to query a graph database.

Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

Below are a number of examples of questions and their corresponding Cypher queries.
"""


FEW_SHOT_EXAMPLES = [
    {
        "question": "What are the total number of ticket numbers?",
        "query": "MATCH (t:ticket_number) RETURN count(t)",
    },
    {
        "question": "What is the name for ticket number PS335598?",
        "query": "MATCH p=(t:ticket_number {{ticket_number: 'PS335598'}})-[:NAMES_FOUND]->() RETURN p",
    },
    {
        "question": "How many violations does ticket number TS32424 have?",
        "query": "MATCH (t:ticket_number {{ticket_number: 'TS32424'}})-[:HAS_VIOLATIONS]->(v:violations) RETURN count(v)",
    },
    {
        "question": "List all the violations for ticket number YV356152",
        "query": "MATCH p=(t:ticket_number {{ticket_number: 'YV356152'}})-[:HAS_VIOLATIONS]->(v:violations) RETURN v.violations",
    },
    {
        "question": "Which ticket number has violation as littering?",
        "query": "MATCH p=(t:ticket_number)-[:HAS_VIOLATIONS]->(v:violations {{violations: 'littering'}}) RETURN t.ticket_number",
    },
    {
        "question": "which ticket number has payment amount due greater than 300?",
        "query": "MATCH (t:ticket_number)-[:PAYMENT_AMT_DUE]->(p:payment_amt) WHERE p.payment_amt > 300 RETURN t.ticket_number",
    },
]
