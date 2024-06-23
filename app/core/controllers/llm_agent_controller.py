from langchain_core.runnables.base import RunnableSerializable
from langgraph.graph import END, StateGraph

from app.utils.agent.common_agents import CypherAgentWrapper
from app.utils.agent.common_states import BaseTeamState, CypherTeamState
from app.utils.llm.factory import LLMFactory


class LLMAgentController:
    supervisor = "cypher_team_supervisor"

    def __init__(self):
        self.llm = LLMFactory().build("groq").get_llm()

        team_member_nodes = CypherAgentWrapper(self.llm)
        self.workflow = StateGraph(CypherTeamState)

        self.workflow.add_node(self.supervisor, team_member_nodes.entry_node())
        self.workflow.add_node("retriever", team_member_nodes.retriever_node())
        self.workflow.add_node("rewrite", team_member_nodes.rewrite_node())
        self.workflow.add_node("graph", team_member_nodes.graph_node())

        self.workflow.set_entry_point(self.supervisor)
        self.workflow.add_edge(self.supervisor, "retriever")

        self.workflow.add_conditional_edges(
            "retriever",
            # Assess agent decision
            team_member_nodes.grade_cypher_answer(),
        )

        self.workflow.add_edge("graph", END)
        self.workflow.add_edge("rewrite", self.supervisor)

    def enter_chain(self, data: BaseTeamState) -> BaseTeamState:
        """data looks something like this
        {"question":request.question,
        "chat_history":[],
        "answer":"",
        "messages":HumanMessage(content=request.question)}
        """
        return data

    def __call__(self) -> RunnableSerializable:
        chain = self.enter_chain | self.workflow.compile()
        return chain
