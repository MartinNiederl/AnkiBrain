from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, TypedDict

from langchain.schema import Document


def extract_json_array(s):
    start = s.find('[')
    end = s.rfind(']') + 1  # +1 to include the bracket itself
    if start != -1 and end != -1:
        return s[start:end]
    else:
        return None


class BadOutputGenerateCardsException(Exception):
    def __init__(self, data):
        super().__init__()
        self.data = data


class ChatInterface(ABC):

    @abstractmethod
    def clear_memory(self):
        pass

    @abstractmethod
    def human_message(self, query: str) -> Tuple[str, Optional[List[Document]]]:
        pass

    def single_query_resets_memory(self, query: str):
        self.clear_memory()
        response, _ = self.human_message(query)
        self.clear_memory()

        return response

    class ExplainTopicOptions(TypedDict):
        level_of_detail: str
        level_of_expertise: str

    def explain_topic(self, topic: str, options: ExplainTopicOptions = None) -> str:
        if options is None:
            options = {'custom_prompt': '', 'level_of_detail': 'EXTREME', 'level_of_expertise': 'EXPERT', 'language': 'English'}

        custom_prompt = options['custom_prompt']
        level_of_detail = options['level_of_detail']
        level_of_expertise = options['level_of_expertise']
        language = options['language']
        query = f'''
                    Explain X using the following parameters: 
                    X = {topic}
                    LEVEL OF DETAIL = {level_of_detail}
                    LEVEL OF EXPERTISE = {level_of_expertise}
                    LANGUAGE = {language}
                    
                    {'When finished, make sure your response is in ' +
                     language + ' only.' if language is not 'English' else ''}
                     
                     {custom_prompt}
                    '''

        explanation = self.single_query_resets_memory(query)
        return explanation

    class GenerateCardsOptions(TypedDict):
        type: str

    def generate_cards(self, text: str, options: GenerateCardsOptions = None) -> str:
        if options is None:
            options = {'type': 'basic', 'language': 'English'}

        custom_prompt = options['custom_prompt']
        card_type = options['type']
        language = options['language']

        query = ''
        if card_type == 'basic':
            query = f'''
            Please read the {language} text below in quotes:
            
            "{text}"
            
            From the text above, I want you to create flash cards in {language}. Output in JSON format, using the following as a strict template for the format. 
            
            "[
            {{
              "front": "This is an example of the front of a card generated by ChatGPT to query the material. You can be creative about the best way to ask a question.", 
              "back": "This is the back of the card that is the answer to the front." 
            }}, 
            {{
              "front": "This is the front of another card.",
              "back": "This is the back of another card."
            }}
            ]"
            
            {"The example given above is in English, but remember to translate the final cards into " +
             language + ". The front text and the back text should be in " + language +
             "!. The names of the JSON fields themselves ('front' and 'back') should remain in English."
            if language is not 'English' else ''
            }

            Make each card relatively small - that means your "text" field should not be more than one or two sentences.
            
            {custom_prompt}
            
            Do not output any other text besides JSON. Begin output now as the template above.
            '''
        elif card_type == 'cloze':
            query = f'''
            Please read the {language} text below in quotes.
            
            "{text}"
            
            From the text above, I want you to create flash cards in ${language}. 
            These are special cards where you omit key words or phrases. 
            You can use asterisks *like this* to indicate that a word or phrase 
            should be hidden for whoever is studying the card. 
            You can create multiple omissions per card. 
            Please decide to hide key words or phrases depending on how important they are to the context. 
            If a word or phrase is very important, you should definitely hide it using *this notation*!
            
            Output in JSON format, using the following as a strict template for your response format:
            "[ 
            {{
              "text": "This is an example of a *flash card* made by you." 
            }}, 
            {{
              "text": "This is the *second* flash *card*, this time containing *three deletions*." 
            }},
            {{
              "text": "Please omit key *words* or *an entire phrase* using asterisks."
            }}
            ]"
            
            Make each card relatively small - that means your "text" field should not be more than one sentence.
            
            {'The example given above is in English, but remember to translate the final cards into ' +
             language + "! The name of the JSON field itself ('text') should remain in English."
            if language is not 'English' else ''
            }
            
            {custom_prompt}
            
            Do not output any other text besides JSON. Begin output now following the template above.
            '''
        else:
            raise Exception('Invalid card type')
        


        cards_raw_str = self.single_query_resets_memory(query)
        cards_raw_str = cards_raw_str.strip()
        cards_raw_str = extract_json_array(cards_raw_str)  # ???
        return cards_raw_str
        # try:
        #     cards = json.loads(cards_json_str)
        #     for card in cards:
        #         card['tags'] = []
        #         card['type'] = card_type
        #     return cards
        # except Exception as e:
        #     raise BadOutputGenerateCardsException({'message': 'Malformed JSON output', 'json': cards_json_str})
