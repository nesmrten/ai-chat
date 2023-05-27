import spacy
from spacy import displacy

nlp = spacy.load("en_core_web_sm")

class TextProcessor:
    def __init__(self, model='en_core_web_sm'):
        self.nlp = spacy.load(model)

    def extract_intent_entity(self, text):
        doc = self.nlp(text)
        intents = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return intents, entities