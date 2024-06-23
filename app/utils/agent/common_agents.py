from typing import List

from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import Field
from langchain_core.tools import tool
from pydantic import BaseModel

from app.core.controllers.neo4j_graph_controller import Neo4JAsk
from app.utils.agent.common_states import CypherTeamState

load_dotenv()


@tool
def search_urls(question: str) -> list[str]:
    """this tool takes in user query in string format and returns the urls for the website in which it was able to
    find the results"""
    search_result = TavilySearchResults(max_results=2).invoke(question)
    urls = [result.get("url") for result in search_result]

    return urls


@tool
def scrape_webpages(urls: List[str]) -> str:
    """Use requests and bs4 to scrape the provided web pages for detailed information."""
    loader = WebBaseLoader(urls)
    docs = loader.load()
    return "\n\n".join(
        [
            f'<Document name="{doc.metadata.get("title", "")}">\n{doc.page_content}\n</Document>'
            for doc in docs
        ]
    )


class Grade(BaseModel):
    """Binary score for relevance check."""

    binary_score: str = Field(description="Relevance score 'yes' or 'no'")


class CypherAgentWrapper:
    """**cypher_team**: Choose this team if information needs to be retrieved from neo4j database using cypher query (it generally comprise of people and their violation and ticket data) related to a person of thing that you might not know and cannot be searched by ResearchTeam. This team is connected to a neo4j database and can resolve queries by referencing stored data, making it ideal for handling unknown names or specific queries that may already have relevant information in the database.
    -Examples of queries that can be answered by CypherTeam
        example1- What are the violations for a ticket number
        example1- What is the name associated with ticket number
        example2- any random code or number that could be given like (102.33 or 34567892)
    """

    def __init__(self, llm):
        self.llm = llm

    def retriever_node(self):

        def node(state: CypherTeamState) -> CypherTeamState:
            print("---RETRIEVE---")
            response = Neo4JAsk().ask_question(state.get("question"))
            return CypherTeamState(**{"documents": response})

        return node

    def rewrite_node(self):

        def node(state: CypherTeamState) -> CypherTeamState:
            print("---TRANSFORM QUERY---")
            question = state["question"]
            msg = [
                HumanMessage(
                    content=f""" \n 
                   Look at the input and try to reason about the underlying semantic intent / meaning. \n 
                   Here is the initial question:
                   \n ------- \n
                   {question} 
                   \n ------- \n
                   Formulate an improved question: """,
                )
            ]
            # Grader
            result = self.llm.invoke(msg)
            print(result)
            return CypherTeamState(**{"question": result.content})

        return node

    def graph_node(self):
        def node(state: CypherTeamState) -> CypherTeamState:
            print("------GRAPH------")
            return state

        return node

    def entry_node(self):
        def node(state: CypherTeamState) -> CypherTeamState:
            print("inside rag team supervisor")
            print(state)
            return state

        return node

    def grade_cypher_answer(self):

        def node(state: CypherTeamState) -> str:
            """
            Determines whether the retrieved answer from cypher query is relevant to the question.

            Args:
                state (messages): The current state

            Returns:
                str: A decision for whether the documents are relevant or not
            """

            print("---CHECK RELEVANCE---")

            prompt = PromptTemplate(
                template="""You are a grader assessing relevance of a retrieved answer to a user question. \n 
                Here is the retrieved answer: \n\n {context} \n\n
                Here is the user question: {question} \n
                If the answer contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
                Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
                input_variables=["context", "question"],
            )
            model = self.llm
            llm_with_tool = model.with_structured_output(Grade)
            chain = prompt | llm_with_tool
            docs = state["documents"]
            question = state["question"]
            scored_result = chain.invoke({"question": question, "context": docs})
            score = scored_result.get("binary_score")

            if score == "yes":
                print("---DECISION: DOCS RELEVANT---")
                return "graph"

            else:
                print("---DECISION: DOCS NOT RELEVANT---")
                return "rewrite"

        return node
