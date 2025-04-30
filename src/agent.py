from typing import Tuple
from database import ChromaDB
import json
import ollama
import requests
import re
import logging
from datetime import datetime

PROMPT = (
    "Todays date (IMPORTANT): {date}. Make sure to APPLY this to every TIME-BASED problem. \n"
    "You are an autonomous news reporter. Use your best judgement based on the given context.\n"
    "If the context contains relevant info, answer. Only search if the context contains no relevant information.\n"
    "If you do not know the answer, or if your context is outdated, search the internet."
    "Here is the context:\n\n"
    "{context}\n\n"
    "Here is the old conversation history:\n\n"
    "{conv_history}\n\n"
    "If the information you want is already in the context, ANSWER IMMEDIATELY.\n"
    "You MUST always answer in STRICT JSON format. NEVER add any explanation, commentary, or extra text outside the JSON.\n"
    "Format your answer exactly like:\n"
    '{{"action": "search" or "answer", "freshness": "oneDay" or "oneWeek" or "oneMonth" or "oneYear or "noLimit", "query": "text to search or your final answer"}}\n\n'
    "Rules:\n"
    '- "action" MUST BE "search" (search again) OR "answer" (MARKDOWN of your ANSWER)\n'
    '- "action" CANNOT be both "search" and "answer" at the same time\n'
    '- "freshness" is the time range for the search results. If the user asks for current news, set it to "oneYear" or "oneMonth" or "oneWeek" or "oneDay".\n'
    '- "query" is either the search query (if searching) or the final answer (if answering)\n'
)
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class Agent():
    def __init__(self, config_path: str = 'config.json'):
        '''
            Initialize the agent with the configuration file and start database
        '''
        self.config = self.get_config(config_path)
        self.db = ChromaDB(name='rag_db', model=self.config['embedding_model'])
        self.db.add_documents(self.config['rag_path'])
        # self.conversation_db = ChromaDB(name='conversation_db', model=self.config['embedding_model'])
        self.memory = []

    def get_config(self, path: str) -> dict:
        '''
            Load configuration from config.json
        '''
        with open(path, 'r') as f:
            config_data = json.load(f)
        return config_data
    def web_search(self, query: str, freshness: str) -> str:
        '''
            Perform a web search using the query and return the result
        '''
        payload = json.dumps({
            "query": query,
            "freshness": freshness,
            "summary": True,
            "count": 10
        })
        headers = {
            'Authorization': self.config['web_search']['api_key'],
            'Content-Type': 'application/json'
        }
        print(f'Performing web search with query {query}...')
        response = requests.request("POST", self.config['web_search']['url'], headers=headers, data=payload)
        return response.text
    
    def chat(self, input_query: str) -> str:
        '''
            Sends query through LLM, checks if web search, parses info, and returns response
        '''
        search_again = True
        knowledge = self.db.retrieve(input_query)['documents']
        plan = '\n'.join(text for doc in knowledge for text in doc) + '\n\n' 
        final_response = ''

        memory_ctx = '\n'.join(f"{item['role']}: {item['content']}" for item in self.memory)
        
        while search_again: # while agent still wants to get info
            try:
                stream = ollama.chat(model=self.config['language_model'], messages=[
                    {'role': 'system', 'content': PROMPT.format(date=datetime.now().strftime("%B %d, %y"), 
                                                                context=plan, 
                                                                conv_history=memory_ctx)},
                    {'role': 'user', 'content': input_query}
                ], stream=True)
                response = ''.join(chunk['message']['content'] for chunk in stream)
                plan, search_again = self.decide(response)

                if not search_again:
                    final_response = plan
                    # limit conversation history + add new history
                    self.memory.append({'role': 'user', 'content': input_query})
                    self.memory.append({'role': 'assistant', 'content': final_response})
                    if len(self.memory) > int(self.config['max_conversation_history']):
                        self.memory = self.memory[-int(self.config['max_conversation_history']):]
            
            except Exception as e:
                logging.error(f'Error during chat: {e}')
                logging.error(f'Error response: {response}')
                return "An error occurred while processing your request. Please try again."

        return final_response

    def decide(self, response: str) -> Tuple[str, bool]:
        '''
            Act on the response from LLM, and return the answer and whether to search again
        '''
        try:
            # {'action': 'search', 'query': 'cats'}
            plan = self.parse_response(response)

            if plan['action'] == 'search': # do a web search for the information
                if plan['query'] != 'RETRY':
                    fresh = plan['freshness'] if plan['freshness'] else 'noLimit'
                    results = self.web_search(plan['query'], plan['freshness'])
                    return f'Web search results:\n{results}\n\n', True
                else:
                    return 'No relevant information found. Please try again.', True
            elif plan['action'] == 'answer':
                return plan['query'], False
            else:
                return 'Invalid action. Please try again.', False
        except Exception as e:
            logging.error(f'Error during parsing: {e}')
            return 'An error occurred while processing your request. Please try again.', False
        return plan['query'], False


    def parse_response(self, response: str) -> str:
        '''
            Parse the response from the LLM and return the final answer
        '''
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'\{(?:[^{}]|\\.)*?\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    logging.error(f'Error parsing JSON: {response}')
                    return {"action": "search", "query": "RETRY"}
            logging.info(f'Non JSON response detected: {response}')
            return {"action": "answer", "query": response.strip()}