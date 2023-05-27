from neo4j import GraphDatabase, basic_auth

# Connect to the Neo4j database
uri = 'bolt://localhost:7687'
user = 'neo4j'
password = 'Stargatesg-1!#$'
driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))

# Define the Cypher query to delete all data
query = '''
MATCH (n)
DETACH DELETE n
'''

# Execute the query
with driver.session() as session:
    session.run(query)
