import requests
import json


class FreeDictionaryAPI:
    BASE_URL = 'https://api.dictionaryapi.dev/api/v2/entries/en/'

    def __init__(self, word):
        self.word = word
        self.meanings = self._get_word_meanings()
        self.categories = self._get_word_categories()

    def _get_word_meanings(self):
        response = requests.get(self.BASE_URL + self.word)
        text = response.text
        json_format = json.loads(text)
        try:
            meanings = json_format[0]['meanings']
            if isinstance(json_format, list):
                return meanings
            else:
                return None
        except KeyError as e:
            return None

    def _get_word_categories(self) -> list:
        if self.meanings:
            word_categories = [meaning['partOfSpeech'].title() for meaning in self.meanings]
            return word_categories
        else:
            return None

    def get_word_definitions(self, category_choice):
        if category_choice in self.categories or category_choice == 'All':
            definitions = []
            target_definitions = {}
            for meaning in self.meanings:
                if category_choice == meaning['partOfSpeech'].title():
                    for definition in meaning['definitions']:
                        if len(definitions) < 4:
                            definitions.append(definition['definition'])
                    return definitions  #list
                elif category_choice == 'All':
                    for definition in meaning['definitions']:
                        if len(definitions) < 4:
                            definitions.append(definition['definition'])
                    target_definitions[meaning['partOfSpeech'].title()] = definitions
                    definitions = []
            return target_definitions  #dict
        else:
            return None

    def get_examples(self, category_choice) -> dict:
        examples = []
        target_examples = {}
        try:
            for meaning in self.meanings:
                if category_choice == meaning['partOfSpeech'].title():
                    for definition in meaning['definitions']:
                        if 'example' in definition:
                            examples.append(definition['example'])
                    # target_examples = {meaning['partOfSpeech']: examples}
                    target_examples = examples
                elif category_choice == 'All':
                    for definition in meaning['definitions']:
                        if 'example' in definition:
                            examples.append(definition['example'])
                        if examples:
                            target_examples[meaning['partOfSpeech'].title()] = examples
                            examples = []
            if target_examples:
                return target_examples
            else:
                return None
        except TypeError:
            return None

    def get_relations(self, category_choice):
        relations = {'synonyms': [], 'antonyms': []}
        synonyms = []
        antonyms = []
        try:
            for meaning in self.meanings:
                if category_choice == meaning['partOfSpeech'].title():
                    for definition in meaning['definitions']:
                        if len(definition['synonyms']) != 0:
                            for synonym in definition['synonyms']:
                                if synonym not in synonyms:
                                    synonyms.append(synonym)
                        if len(definition['antonyms']) != 0:
                            for antonym in definition['antonyms']:
                                if antonym not in antonyms:
                                    antonyms.append(antonym)
                    relations['synonyms'] = synonyms
                    relations['antonyms'] = antonyms
                elif category_choice == 'All':
                    for definition in meaning['definitions']:
                        if len(definition['synonyms']) != 0:
                            for synonym in definition['synonyms']:
                                if synonym not in synonyms:
                                    synonyms.append(synonym)
                        if len(definition['antonyms']) != 0:
                            for antonym in definition['antonyms']:
                                if antonym not in antonyms:
                                    antonyms.append(antonym)
                    relations['synonyms'] = synonyms
                    relations['antonyms'] = antonyms
                    synonyms = []
                    antonyms = []
            if relations['synonyms'] or relations['antonyms']:
                return relations
            else:
                return None
        except TypeError:
            return None


if __name__ == '__main__':
    word = FreeDictionaryAPI('try')
    # print(word.meanings)
    print(word.get_relations('Noun'))
    # print(word.categories)
    # print(word.get_word_definitions('Interjection'))
    # print(word.get_examples('All'))
