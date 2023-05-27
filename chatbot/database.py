from neo4j import GraphDatabase, basic_auth


import logging
from neo4j import GraphDatabase, basic_auth

logger = logging.getLogger(__name__)

class DatabaseQueryError(Exception):
    pass

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, **parameters):
        with self.driver.session() as session:
            try:
                result = session.run(query, **parameters)
                return result.data()
            except Exception as e:
                logger.error("An error occurred during the database operation: %s", e, exc_info=True)
                raise DatabaseQueryError(f"Error running query: {query}") from e


    def get_answer(self, question):
        query = "MATCH (q:Question)-[:ANSWER]->(a:Answer) WHERE q.text = $question RETURN a.text AS answer"
        parameters = {"question": question}
        result = self.run_query(query, **parameters)
        if result:
            return result[0]["answer"]
        else:
            return None

    def create_node(self, node_id, info):
        query = "CREATE (n:Node {id: $node_id, info: $info})"
        parameters = {"node_id": node_id, "info": info}
        self.run_query(query, **parameters)

    def create_relation(self, question, node_id):
        query = "MATCH (q:Question), (n:Node) WHERE q.text = $question AND n.id = $node_id CREATE (q)-[:HAS_INFO]->(n)"
        parameters = {"question": question, "node_id": node_id}
        self.run_query(query, **parameters)
