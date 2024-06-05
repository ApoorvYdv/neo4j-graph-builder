
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class Neo4jConnection:
    
    def __init__(self):
        self.__uri = os.getenv("NEO4J_URI")
        self.__user = os.getenv("NEO4J_USER")
        self.__pwd = os.getenv("NEO4J_PASSWORD")
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response