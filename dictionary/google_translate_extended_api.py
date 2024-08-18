import subprocess
import json
import mtranslate
from dotenv import load_dotenv
import os


class GoogleTranslateExtendedAPI:
    load_dotenv()
    project_dir = os.getenv('PROJ_DIR_PATH', './')
    script_file = project_dir + '/google-translate-extended-api.js'

    def __init__(self, word):
        self.word = word
        self.meaning = self._get_word_meanings()
        self.translation_categories = self._get_word_translation_categories()
        self.definition_categories = self._get_word_definition_categories()

    def _get_word_meanings(self):
        try:
            result = subprocess.run(
                ['node', self.script_file, self.word, "en", "ru"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            return None

    def _get_word_translation_categories(self):
        # print(self.meaning['translations'].keys())
        word_categories = [key for key in self.meaning['translations'].keys()]
        if len(word_categories) != 0:
            return word_categories
        else:
            return None

    def _get_word_definition_categories(self):
        word_categories = [key for key in self.meaning['definitions'].keys()]
        if len(word_categories) != 0:
            if 'Abbreviation' in word_categories:
                word_categories.remove('Abbreviation')
                return word_categories
            else:
                return word_categories
        else:
            return None

    def get_translations(self, category_choice):
        if category_choice.title() in self.meaning['translations'].keys() or category_choice == 'All':
            if category_choice.title() != 'All':
                translations = self.meaning['translations'][category_choice.title()]
            else:
                translations = self.meaning['translations']  #dict
            if translations:
                if isinstance(translations, list):
                    return translations  #list
                else:
                    if 'Abbreviation' in translations.keys():
                        del translations['Abbreviation']
                        if not translations:
                            return self.meaning['translation']
                    return translations  #dict
            else:
                translated = mtranslate.translate(self.word, "ru", "en")
                if translated != self.meaning['translation']:
                    return self.meaning['translation'] + ', ' + translated.lower()  # str
                else:
                    return self.meaning['translation']
        else:
            return self.meaning['translation']

    def get_word_definitions(self, category_choice):
        if category_choice in self.definition_categories or category_choice == 'All':
            if category_choice.title() != 'All':
                definitions = self.meaning['definitions'][category_choice]
                return definitions  #list
            else:
                if 'Abbreviation' in self.meaning['definitions'].keys():
                    del (self.meaning['definitions']['Abbreviation'])
                    return self.meaning['definitions']  #dict
                else:
                    return self.meaning['definitions']  #dict
        else:
            return None

    def get_examples(self):
        examples = self.meaning['examples']
        if len(examples) != 0:
            return examples
        else:
            return None


if __name__ == '__main__':
    word = GoogleTranslateExtendedAPI('undivided attention')

    # print(word.meaning)
    # print(word.get_word_definitions('All'))
    print(word.get_translations('All'))
