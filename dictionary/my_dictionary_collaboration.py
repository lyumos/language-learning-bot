from dictionary.free_dictionary_api import FreeDictionaryAPI
from dictionary.google_translate_extended_api import GoogleTranslateExtendedAPI


class LanguageProcessing:

    def __init__(self, word):
        self.word = word
        self.gtea_version = GoogleTranslateExtendedAPI(word)
        self.fda_version = FreeDictionaryAPI(word)

    def check_definitions(self):
        if self.fda_version.meanings and self.gtea_version.definition_categories:
            return True
        else:
            return None

    def get_word_categories(self) -> list:
        fda_categories = self.fda_version.categories
        gtea_categories = self.gtea_version.definition_categories
        if set(fda_categories) == set(gtea_categories):
            if len(list(set(fda_categories))) > 1:
                return list(set(fda_categories)) + ['All']
            else:
                return list(set(fda_categories))
        else:
            categories = list(set(fda_categories + gtea_categories))
            if len(categories) > 1:
                return categories + ['All']
            else:
                return categories

    def get_word_definitions(self, category_choice):
        if category_choice.title() != 'Expression':
            fda_definitions = self.fda_version.get_word_definitions(category_choice.title())
            gtea_definitions = self.gtea_version.get_word_definitions(category_choice.title())
            if category_choice.title() != 'All':
                if fda_definitions and gtea_definitions:
                    return gtea_definitions + fda_definitions  #list
                elif fda_definitions and not gtea_definitions:
                    return fda_definitions  #list
                elif gtea_definitions and not fda_definitions:
                    return gtea_definitions  #list
            else:
                if fda_definitions and gtea_definitions:
                    word_definitions = fda_definitions.copy()
                    for key, value in gtea_definitions.items():
                        if key in word_definitions:
                            word_definitions[key].extend(value)
                        else:
                            word_definitions[key] = value
                    return word_definitions  #dict
                elif fda_definitions and not gtea_definitions:
                    return fda_definitions  #dict
                elif gtea_definitions and not fda_definitions:
                    return gtea_definitions  #dict
        else:
            return None

    def get_word_translations(self, category_choice):
        translation = self.gtea_version.get_translations(category_choice.title())
        if translation:
            return translation
        else:
            return None

    def get_word_examples(self, category_choice):
        fda_examples = self.fda_version.get_examples(category_choice.title())
        gtea_examples = self.gtea_version.get_examples()
        if fda_examples or gtea_examples:
            if category_choice.title() != 'All':
                if fda_examples and gtea_examples:
                    return fda_examples + gtea_examples
                if fda_examples and not gtea_examples:
                    return fda_examples
                if gtea_examples and not fda_examples:
                    return gtea_examples
            else:
                if fda_examples and gtea_examples:
                    fda_examples['All'] = gtea_examples
                    return fda_examples
                if fda_examples and not gtea_examples:
                    return fda_examples
                if not fda_examples and gtea_examples:
                    return gtea_examples
        else:
            return None

    def get_relations(self, category_choice):
        return self.fda_version.get_relations(category_choice)

    def get_audio(self):
        return self.fda_version.get_audio_link()


if __name__ == '__main__':
    word = LanguageProcessing('try')
    # print(word.get_word_categories())
    # print(word.get_word_translations('Noun'))
    # print(word.get_word_definitions('All'))
    print(word.get_word_examples('Noun'))
    # print(word.get_relations('All'))
    # print(word.get_audio())
