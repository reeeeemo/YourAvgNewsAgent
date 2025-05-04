from typing import Tuple
import json
import ollama
import requests
import re
import logging
from datetime import datetime
import pandas as pd
from src.tool import Tool, tool

PROMPT = (
    "TODAY'S DATE (IMPORTANT): {date}.\n"
    " You MUST use this exact date - {date} - in ALL responses, headings, and summaries, and searches."
    "Do NOT assume or use any other date.\n\n"

    "You are an AI news summarizer. Use the provided context to answer the user's request\n"
    "If the context is sufficient, answer directly. Only search if the context contains no relevant information.\n"
    "If you do not know the answer, or if your context is outdated (date: {date}), search the internet."
    "The current date is {date}. DO NOT include outdated or fabricated content. \n\n"

    "-- CONTEXT START --\n\n"
    "{context}\n\n"
    "-- CONTEXT END -- \n\n"

    "-- CONVERSATION HISTORY AS OF {date} --\n\n"
    "{conv_history}\n\n"
    "-- END CONVERSATION HISTORY -- \n\n"

    "If the information is in the context, ANSWER IMMEDIATELY.\n"

    "You MUST always answer in STRICT JSON format. NEVER add any explanation, commentary, or extra text outside the JSON.\n"
    "Format your answer exactly like:\n"
    '{{"action": "search" or "answer", "freshness": "oneDay" or "oneWeek" or "oneMonth" or "oneYear" or "noLimit", "query": "text to search or your final answer (use {date} in all headings)"}}\n\n'
    
    "RULES:\n"
    '- "action" MUST BE "search" (search again) OR "answer" (MARKDOWN of your ANSWER)\n'
    '- "action" CANNOT be both "search" and "answer" at the same time\n'
    '- "freshness" is the time range for the search results. If the user asks for current news, set it to "oneYear" or "oneMonth" or "oneWeek" or "oneDay".\n'
    '- "query" is either the search query (if searching) or the final answer (if answering)\n'
    "- Use today's date ({date}) in your headings and time references"
)

SUMMARY_PROMPT = (
    "You are to summarize this article given, in the SMALLEST amount of words possible, while keeping it INFORMATIVE\n"
    "Rules: \n"
    "- Do NOT make up any facts, do NOT fabricate content or include extra data.\n"
    "- Do NOT add ANY explanation, commentary, or extra text. ONLY sumarrize the data, NOTHING ELSE. \n"
    "- Do NOT ask any questions. JUST SUMMARIZE \n"
)
# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

import os
from colorama import Fore

class ToolAgent():
    '''
        Agent that interacts with an LLM and use tools given to assist with user queries
        Args:
            tools (Tool | list[Tool]): list of tools available to the agent
            model (str): model type to be used for generating tool calls and responses
            tools_dict (dict) dictionary mapping tool names to callable objects
    '''
    def __init__(self, tools: Tool | list[Tool]):
        self.model = os.getenv('LLAMA_MODEL')
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}

    def get_tool_signatures(self) -> str:
        '''
            Collects and concatenates all function signatures of all tools
            Returns:
                str: concatenated string of all tool function signatures in JSON format
        '''
        return "".join([tool.fn_signature for tool in self.tools])
    
    def process_tool_calls(self, tool_calls: list) -> dict:
        '''
            Processes each tool call, validates the arguments, and collects results
            Args:
                tool_calls (list): list of string, each representing a tool call in JSON format
            Returns:
                dict: dictionary where keys are tool call IDs and values are results
        '''
        observations = {}
        for tool_call_str in tool_calls:
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call['name']
            tool = self.tools_dict[tool_name]

            print(Fore.CYAN + f'\nUsing Tool: {tool.name}')

            val_tool_call = tool.validate_args(tool_call_schema=tool_call)
            result = tool(**val_tool_call['arguments'])

            print(Fore.CYAN + f'\nTool Result: {result}')

            observations[val_tool_call['id']] = result
        return observations



"""
class Agent():
    def __init__(self, config_path: str = 'config.json'):
        '''
            Initialize the agent with the configuration file and start database
        '''
        self.config = self.get_config(config_path)
        self.db = ChromaDB(name='rag_db', model=self.config['embedding_model'])
        self.db.add_documents(self.config['rag_path'])
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

        try:
            json_data = response.json()
        except Exception as e:
            print('Error parsing JSON response', e)
            return ""
        
        try:
            articles = json_data['data']['webPages']['value']
            for article in articles: 
                print(article.get('name'), "|", article.get("url"), "|", article.get("datePublished"))
            chunks = [articles[i:i+5] for i in range(0, len(articles), 5)]

            new_articles = []

            for chunk in chunks:
                df = pd.json_normalize(chunk)
                df = df.fillna({'summary': ''})
                cleaned_df = df[['name', 'url', 'summary']]
                for _, row in cleaned_df.iterrows():
                    new_summary = self.query_llm(row['summary'], SUMMARY_PROMPT)
                    date = row.get('datePublished', self.infer_date(row)) 
                    new_articles.append(f'Title: {row["name"]}\nURL: {row["url"]}\nSummary: {new_summary}\nDate Published: {date}')
                
            return '\n'.join(new_article for new_article in new_articles)
        except KeyError:
            print("KeyError missing 'data.webPages.value' in response")
            return json.dumps(json_data, indent=2)
    
    def infer_date(self, article):
        mat = re.search(r'/(\d{4})/(\d{2})/(\d{2})', article.get('url', ''))
        if mat:
            return f'{mat.group(2)}/{mat.group(3)}/{mat.group(1)}'
        
        mat = re.search(r'([A-Z][a-z]{2,8})\.?\s+(\d{1,2}),\s+(\d{4})', article.get('summary', ''))
        if mat:
            return f'{mat.group(1)} {mat.group(2)}, {mat.group(3)}'
        return 'Unknown'

    def query_llm(self, query: str, llm_prompt: str) -> str:
        stream = ollama.chat(model=self.config['language_model'], messages=[
            {'role': 'system', 'content': llm_prompt},
            {'role': 'user', 'content': query}
        ], stream=True)
        response = ''.join(chunk['message']['content'] for chunk in stream)
        return response

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
                response = self.query_llm(input_query, PROMPT.format(
                                                        date=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 
                                                        context=plan, conv_history=memory_ctx))
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
"""