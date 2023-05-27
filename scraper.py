import asyncio
import logging
import random
import requests
from urllib.parse import urlparse
from urllib import robotparser
from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_fixed
from parsel import Selector
import spacy
from neo4j import GraphDatabase, basic_auth
from uuid import uuid4

import asyncio
import logging
import random
import requests
from urllib.parse import urlparse
from urllib import robotparser
from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_fixed
from parsel import Selector
import spacy
from neo4j import GraphDatabase, basic_auth
from uuid import uuid4

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, **kwargs):
        with self.driver.session() as session:
            try:
                session.run(query, **kwargs)
            except Exception as e:
                logging.error(f"Exception during database operation: {str(e)}")
                return None


class Scraper:
    def __init__(self, database, nlp, max_retries, request_delay):
        self.database = database
        self.nlp = nlp
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(REQUEST_DELAY))
    async def scrape(self, url, language):
        async with ClientSession() as session:
            if not await self.can_fetch(url):
                logging.warning(f"Blocked by robots.txt: {url}")
                return []
            html = await self.fetch_url(session, url)
            if html:
                return await self.parse_page(html, language)
            return []

    # Rest of the code...


        async def fetch_url(self, session, url):
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            try:
                async with self.semaphore, session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logging.error(f"Exception during request: {str(e)}")
                return None

        async def can_fetch(self, url):
            robots_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt"
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch('*', url)

        async def parse_page(self, html, language):
            sel = Selector(html)
            text_content = ' '.join(sel.css('p::text, h1::text, h2::text, h3::text, h4::text, h5::text, h6::text').getall())
            nlp = self.nlp.get(language)
            doc = nlp(text_content)
            qna_pairs = []
            for sentence in doc.sents:
                if sentence.ents:
                    for ent in sentence.ents:
                        qna_pairs.append({
                            'question': f"What is the {ent.label_} in the sentence '{sentence}'?",
                            'answer': ent.text
                        })
            return qna_pairs

        @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_fixed(REQUEST_DELAY))
        async def scrape_website(self, url, language):
            async with ClientSession() as session:
                if not await self.can_fetch(url):
                    logging.warning(f"Blocked by robots.txt: {url}")
                    return []
                html = await self.fetch_url(session, url)
                if html:
                    return await self.parse_page(html, language)
                return []

        async def insert_qna_pairs(self, qna_pairs, language):
            for pair in qna_pairs:
                question_text = pair['question']
                answer_text = pair['answer']

                # Check if the question already exists
                query = (
                    "MATCH (q:Question {question_text: $question_text}) "
                    "RETURN q.question_id AS question_id"
                )
                result = self.database.run_query(query, question_text=question_text)
                existing_question = None   # Added this line
                if result:
                    existing_question = result.single()

                if existing_question is not None:
                    question_id = existing_question["question_id"]
                else:
                    question_id = str(uuid4())
                    # Create a new question node
                    query = (
                        "CREATE (q:Question {question_id: $question_id, question_text: $question_text})"
                    )
                    self.database.run_query(query, question_id=question_id, question_text=question_text)

                # Check if the answer already exists
                query = (
                    "MATCH (a:Answer {answer_text: $answer_text}) "
                    "RETURN a.answer_id AS answer_id"
                )
                result = self.database.run_query(query, answer_text=answer_text)
                existing_answer = None   # Added this line
                if result:
                    existing_answer = result.single()

                if existing_answer is not None:
                    answer_id = existing_answer["answer_id"]
                else:
                    answer_id = str(uuid4())
                    # Create a new answer node
                    query = (
                        "CREATE (a:Answer {answer_id: $answer_id, answer_text: $answer_text})"
                    )
                    self.database.run_query(query, answer_id=answer_id, answer_text=answer_text)

                # Create a relationship between the question and answer
                query = (
                    "MATCH (q:Question {question_id: $question_id}), (a:Answer {answer_id: $answer_id}) "
                    "MERGE (q)-[:ANSWER]->(a)"
                )
                self.database.run_query(query, question_id=question_id, answer_id=answer_id)

        async def scrape_and_store(self, url, language):
            qna_pairs = await self.scrape_website(url, language)
            await self.insert_qna_pairs(qna_pairs, language)
