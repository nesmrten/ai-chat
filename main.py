import os
import asyncio
import logging
from dotenv import load_dotenv
from transformers import T5ForConditionalGeneration, T5Tokenizer
from database import Neo4jDatabase
from assistant import ChatbotAssistant

load_dotenv()

logging.basicConfig(
    filename="scrape.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_chatbot_assistant():
    load_dotenv()
    db = Neo4jDatabase(os.getenv("DB_URI"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))
    model = T5ForConditionalGeneration.from_pretrained(os.getenv("T5_MODEL_PATH"))
    tokenizer = T5Tokenizer.from_pretrained(os.getenv("T5_MODEL_PATH"))
    assistant = ChatbotAssistant(db, model, tokenizer)
    while True:
        try:
            user_input = input("User: ")
            asyncio.run(assistant.handle_request(user_input))
        except Exception as e:
            logger.error("An error occurred while handling request: %s", e, exc_info=True)

if __name__ == "__main__":
    run_chatbot_assistant()
