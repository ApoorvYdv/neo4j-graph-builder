import os
import tempfile
import time
from ast import literal_eval

import pandas as pd
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Neo4jVector
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer

from app.utils.database.connection import Neo4jConnection
from app.utils.llm.factory import LLMFactory
from app.utils.query_prompt_templates import (
    CYPHER_GENERATION_PROMPT_TEMPLATE, FEW_SHOT_EXAMPLES)


class Neo4JGraphBuilder:
    """Import CSV into Neo4J database"""

    def __init__(self):
        self.graph = Neo4jConnection().graph

    def _create_node_constraints(self):
        self.graph.query(
            "CREATE CONSTRAINT ticket_number IF NOT EXISTS FOR (t:ticket_number) REQUIRE t.ticket_number IS UNIQUE"
        )
        self.graph.query(
            "CREATE CONSTRAINT names IF NOT EXISTS FOR (n:names) REQUIRE n.names IS UNIQUE"
        )
        self.graph.query(
            "CREATE CONSTRAINT payment_amt IF NOT EXISTS FOR (p:payment_amt) REQUIRE p.payment_amt IS UNIQUE"
        )
        self.graph.query(
            "CREATE CONSTRAINT violations IF NOT EXISTS FOR (v:violations) REQUIRE v.violations IS UNIQUE"
        )

    def _create_nodes(self, nodes, node_label, property_key, node_label_key):
        # Adds nodes to the Neo4j graph dynamically based on the node label and property key.
        query = f"""
                UNWIND $rows AS row
                MERGE ({node_label_key}:{node_label} {{{property_key}: row.{property_key}}})
                RETURN count(*) as total
                """
        return self.graph.query(query, params={"rows": nodes.to_dict("records")})

    def _insert_data(self, query, rows, batch_size=2):
        # Function to handle the updating the Neo4j database in batch mode.

        total = 0
        batch = 0
        start = time.time()
        result = None

        while batch * batch_size < len(rows):
            res = self.graph.query(
                query,
                params={
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

        // connect violations
        WITH distinct row, t // reduce cardinality
        UNWIND row.violations AS violations
        MATCH (v:violations {violations: violations})
        MERGE (t)-[:HAS_VIOLATIONS]->(v)

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
        self.graph = Neo4jConnection().graph
        self.vector_store_kwargs = Neo4jConnection().vector_store_kwargs
        self.llm = LLMFactory().build("gemini").get_llm()
        self.embeddings = LLMFactory().build("gemini").load_embedding_model()

    def get_few_shot_prompt(self, example_selector):
        example_prompt = PromptTemplate.from_template(
            "User input: {question}\nCypher query: {query}"
        )
        prompt = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=example_prompt,
            prefix=CYPHER_GENERATION_PROMPT_TEMPLATE,
            suffix="User input: {question}\nCypher query: ",
            input_variables=["question", "schema"],
        )
        return prompt

    def get_dynamic_few_shot_examples(self):
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples=FEW_SHOT_EXAMPLES,
            embeddings=self.embeddings,
            vectorstore_cls=Neo4jVector,
            k=5,
            input_keys=["question"],
            **self.vector_store_kwargs,
        )
        example_selector.select_examples(
            {"question": "What are the total number of ticket numbers?"}
        )
        return example_selector

    def ask_question(self, question):
        self.graph.refresh_schema()

        example_selector = self.get_dynamic_few_shot_examples()
        cypher_prompt = self.get_few_shot_prompt(example_selector)

        cypher_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            cypher_prompt=cypher_prompt,
            validate_cypher=True,
            return_intermediate_steps=True,
        )

        result = cypher_chain.invoke(question)
        return result


class Neo4JGraphTransformer:
    def __init__(self):
        self.graph = Neo4jConnection().graph
        self.llm = LLMFactory().build("groq").get_llm()

    def generate_graph(self, file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file)
            tmp_file_path = tmp_file.name
        loader = PyPDFLoader(tmp_file_path)
        document = loader.load()

        llm_transformer = LLMGraphTransformer(llm=self.llm)
        graph_documents = llm_transformer.convert_to_graph_documents(document)
        print(graph_documents)

        self.graph.add_graph_documents(graph_documents)
        os.remove(tmp_file_path)
        return {"status_code": 200, "message": "successfully add document"}
