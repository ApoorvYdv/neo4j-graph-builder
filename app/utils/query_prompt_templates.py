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
      "question": "What are the total number of companies?",
      "query": "MATCH (c:Company) RETURN count(c)",
   },
   {
      "question":"How many emails are associated with Salman Comar?",
      "query":"MATCH (p:Person {{id: 'Salman Comar'}})-[:HAS_EMAIL]->(e:Email) RETURN count(e)"
   },
   {
      "question":"How many social media groups is salman comar associated with?",
      "query":"MATCH (p:Person {{id: 'Salman Comar'}})-[:ASSOCIATED_WITH]->(smg:Social_media_group) RETURN count(smg)"
   },
   {
      "question":"How many people are associated with company Inshallah Co?",
      "query":"MATCH (c:Company {{id: 'Inshallah Co'}})-[:HAS_ENTITY]->(p:Person) RETURN count(p)"
   },
   {
      "question":"How many person are associated with social media group IndiaWithPFI?",
      "query":"MATCH (p:Person)-[:ASSOCIATED_WITH]->(smg:Social_media_group {{id: 'PFIActivism'}}) RETURN count(p)"
   },
   {
      "question":"How many person have postal code 600001?",
      "query":"MATCH (p:Person)-[:HAS_POSTAL_CODE]->(pc:Postal_code {{id: '600001'}}) RETURN count(p)"
   }, 
]

