import os
from dotenv import load_dotenv
import asyncio
import logging
from neo4j import GraphDatabase, basic_auth
from transformers import pipeline, T5ForConditionalGeneration, T5Tokenizer
from uuid import uuid4

load_dotenv()

# Environment Configuration
load_dotenv()  # Load .env file into environment

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
LOG_FILE = os.getenv("LOG_FILE", "scrape.log")
REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", 1))
CRAWL_DELAY = int(os.getenv("CRAWL_DELAY", 3))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
SEMAPHORE_LIMIT = int(os.getenv("SEMAPHORE_LIMIT", 5))
USER_AGENTS = [ua.strip() for ua in os.getenv("USER_AGENTS",
                  "Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36, Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36, Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0, Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36, Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0, Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A365 Safari/600.1.4").split(",")]

required_env_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'USER_AGENTS']
if not all([globals()[var] for var in required_env_vars]):
    missing = [var for var in required_env_vars if not globals()[var]]
    raise Exception(f"Missing required environment variables: {', '.join(missing)}")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, **parameters):
        with self.driver.session() as session:
            result = session.run(query, **parameters)
            return result.data()

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


class ChatbotAssistant:
    def __init__(self, database):
        self.database = database
        self.chatbot_model = T5ForConditionalGeneration.from_pretrained("t5-base")
        self.chatbot_tokenizer = T5Tokenizer.from_pretrained("t5-base")

    async def get_answer(self, question):
        # Generate answer using chatbot model
        question_generator = pipeline("text2text-generation", model=self.chatbot_model, tokenizer=self.chatbot_tokenizer)
        inputs = "question: " + question + " context: "
        answer = question_generator(inputs, max_length=100, num_return_sequences=1)[0]["generated_text"]
        return answer

    async def handle_user_feedback(self, question, correction):
        if correction.lower() == "ok":
            return  # No need to store feedback for correct answers
        
        # Store user feedback in the knowledge graph or database
        query = "MERGE (q:Question {text: $question}) MERGE (c:Correction {text: $correction}) CREATE (q)-[:HAS_CORRECTION]->(c)"
        parameters = {"question": question, "correction": correction}
        self.database.run_query(query, **parameters)


async def scrape_website(url):
    async with ClientSession() as session:
        response = await fetch(session, url)
        if response:
            return await response.text()
        else:
            return None


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return await response.read()
    except (ClientError, ServerTimeoutError, TooManyRedirects):
        logging.error(f"Request failed for URL: {url}")
    except Exception as e:
        logging.error(f"An error occurred during the request: {str(e)}")


def preprocess_input(question):
    # Implement your preprocessing logic here
    return question


def process_input(question):
    # Implement NLP techniques like tokenization, NER, etc.
    return question


def recognize_intent(processed_question):
    # Implement intent recognition and entity extraction logic
    intent = "example_intent"
    entities = ["example_entity"]
    return intent, entities


def extract_info(scraped_data):
    # Implement logic to extract relevant information from the scraped website
    extracted_info = ["info_1", "info_2"]
    return extracted_info


def generate_node_id():
    # Implement a method to generate unique IDs for nodes
    return str(uuid4())


def generate_non_programming_answer(question):
    # Generate a response for non-programming questions
    return f"Apologies, I don't have the answer for the question: {question}"


async def chat_and_learn():
    database = Neo4jDatabase(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    assistant = ChatbotAssistant(database)
    while True:
        question = input("Enter your programming question: ")
        if question.lower() == "exit":
            break

        # Preprocess user input
        preprocessed_question = preprocess_input(question)

        # Process user input using NLP techniques
        processed_question = process_input(preprocessed_question)

        # Perform intent recognition and entity extraction
        intent, entities = recognize_intent(processed_question)

        # Query the knowledge graph or database
        answer = await assistant.get_answer(question)

        if answer:
            print("Answer:", answer)
            correction = input("Enter your correction or type 'ok' if the answer is correct: ")
            await assistant.handle_user_feedback(question, correction)
        else:
            print("No answer found.")
            correction = input("I found no answer in my knowledge base. To allow my learning process to proceed automatically and provide you with the latest knowledge, please confirm my request: ")
            if correction.lower() == "ok":
                # Initiate web scraping
                duckduckgo_url = f"https://duckduckgo.com/?q={question}&t=h_&ia=web"
                scraped_data = await scrape_website(duckduckgo_url)

                if scraped_data:
                    # Extract relevant information from the scraped website
                    extracted_info = extract_info(scraped_data)

                    for info in extracted_info:
                        node_id = generate_node_id()
                        database.create_node(node_id, info)
                        database.create_relation(question, node_id)

                else:
                    answer = generate_non_programming_answer(question)
                    print("Answer:", answer)
                    correction = input("Enter your correction or type 'ok' if the answer is correct: ")
                    await assistant.handle_user_feedback(question, correction)

            else:
                await assistant.handle_user_feedback(question, correction)

    database.close()


asyncio.run(chat_and_learn())
