import tempfile
import time
from ast import literal_eval

import pandas as pd
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts.prompt import PromptTemplate

from app.utils.database.connection import Neo4jConnection
from app.utils.llm.factory import LLMFactory
from app.utils.query_prompt_templates import CYPHER_GENERATION_TEMPLATE


class Neo4JGraphBuilder:
    """Import CSV into Neo4J database"""

    def __init__(self):
        self.db = Neo4jConnection()

    def _create_node_constraints(self):
        self.db.query(
            "CREATE CONSTRAINT ticket_number IF NOT EXISTS ON (t:ticket_number) ASSERT t.ticket_number IS UNIQUE"
        )
        self.db.query(
            "CREATE CONSTRAINT names IF NOT EXISTS ON (n:names) ASSERT n.names IS UNIQUE"
        )
        self.db.query(
            "CREATE CONSTRAINT payment_amt IF NOT EXISTS ON (p:payment_amt) ASSERT p:payment_amt IS UNIQUE"
        )
        self.db.query(
            "CREATE CONSTRAINT violations IF NOT EXISTS ON (v:violations) ASSERT v.violations IS UNIQUE"
        )

    def _create_nodes(self, nodes, node_label, property_key, node_label_key):
        # Adds nodes to the Neo4j graph dynamically based on the node label and property key.
        query = f"""
                UNWIND $rows AS row
                MERGE ({node_label_key}:{node_label} {{{property_key}: row.{property_key}}})
                RETURN count(*) as total
                """
        return self.db.query(query, parameters={"rows": nodes.to_dict("records")})

    def _insert_data(self, query, rows, batch_size=2):
        # Function to handle the updating the Neo4j database in batch mode.

        total = 0
        batch = 0
        start = time.time()
        result = None

        while batch * batch_size < len(rows):
            res = self.db.query(
                query,
                parameters={
                    "rows": rows[batch * batch_size : (batch + 1) * batch_size].to_dict(
                        "records"
                    )
                },
            )
            total += res[0]["total"]
            batch += 1
            result = {"total": total, "batches": batch, "time": time.time() - start}
            print(result)

        return result

    def _create_relations(self, rows):
        # Adds Source nodes and (:Source)-->(:Name),
        # (:Source)-->(:Org) and (:Source)-->(:Keyword)
        #  relationships to the Neo4j graph as a batch job.

        query = """
        UNWIND $rows as row
        MERGE (t:ticket_number {id: row.ticket_number}) ON CREATE SET t.ticket_number = row.ticket_number
        
        // connect names
        WITH row, t
        UNWIND row.names as names
        MATCH (n:names {names: names})
        MERGE (t)-[:NAMES_FOUND]->(n)
        
        // connect payment_amt
        WITH distinct row, t // reduce cardinality
        UNWIND row.payment_amt AS payment_amt
        MATCH (p:payment_amt {payment_amt: payment_amt})
        MERGE (t)-[:PAYMENT_AMT_DUE]->(p)

        // connect names
        WITH distinct row, t // reduce cardinality
        UNWIND row.violations AS violations
        MATCH (v:violations {violations: violations})
        MERGE (t)-[:VIOLATIONS_FOUND]->(v)

        RETURN count(distinct t) as total
        """

        return self._insert_data(query, rows)

    def upload_to_neo4j_database(self, file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(file)
            tmp_file_path = tmp_file.name
        df = pd.read_csv(tmp_file_path, converters={"violations": literal_eval})
        # df = self._drop_columns(df)

        names = pd.DataFrame(df[["names"]])
        names = names.explode("names").drop_duplicates(subset=["names"])

        print(type(df["violations"][0]))
        violations = pd.DataFrame(df[["violations"]])
        violations = violations.explode("violations").drop_duplicates(
            subset=["violations"]
        )
        print(violations)

        payment_amt = pd.DataFrame(df[["payment_amt"]])
        payment_amt = payment_amt.explode("payment_amt").drop_duplicates(
            subset=["payment_amt"]
        )

        self._create_node_constraints()

        ## Add Organizations
        self._create_nodes(payment_amt, "payment_amt", "payment_amt", "p")

        ## Add Violations
        self._create_nodes(violations, "violations", "violations", "v")

        ## Add Names
        self._create_nodes(names, "names", "names", "n")

        ## Create nodes relations
        self._create_relations(df)

        return {"success": 200, "message": "successfully uploaded"}


class Neo4JAsk:
    def __init__(self):
        self.graph = Neo4jConnection().create_connection()
        self.llm = LLMFactory().build("gemini").get_llm()

    def ask_question(self, question):
        self.graph.refresh_schema()

        CYPHER_GENERATION_PROMPT = PromptTemplate(
            input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
        )

        cypher_chain = GraphCypherQAChain.from_llm(
            cypher_llm=self.llm,
            qa_llm=self.llm,
            graph=self.graph,
            verbose=True,
            cypher_prompt=CYPHER_GENERATION_PROMPT,
            validate_cypher=True,
        )

        result = cypher_chain.invoke({"query": question})
        return result
