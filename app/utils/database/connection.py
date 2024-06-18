from langchain_community.graphs import Neo4jGraph

from app.settings.config import settings


class Neo4jConnection:
    def __init__(self):
        self.__uri = settings.get("NEO4J_URI")
        self.__username = settings.get("NEO4J_USER")
        self.__password = settings.get("NEO4J_PASSWORD")
        self.__database = settings.get("NEO4J_DATABASE")
        self.graph = self.create_connection()

    def create_connection(self):
        graph = Neo4jGraph(
            url=self.__uri,
            database=self.__database,
            username=self.__username,
            password=self.__password,
            sanitize=True,
            refresh_schema=True,
        )
        return graph

    def close_connection(self):
        if not self.graph._driver._closed:
            self.graph._driver.close()

    def execute_query(self, query, parameters=None):
        assert self.__driver is not None, "Driver not initialized!"
        response = None
        try:
            response = list(self.__driver.query(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if self.__driver is not None:
                self.close_connection()
        return response
