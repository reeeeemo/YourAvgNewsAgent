from typing import Tuple
import json
import logging
from datetime import datetime
import pandas as pd
from src.tool import Tool
from groq import Groq
import os
from colorama import Fore
import re
from transformers import AutoTokenizer

TOOL_SYSTEM_PROMPT = """
You are a function calling AI model. You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug
into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.
For each function call return a json object with function name and arguments within <tool_call></tool_call>
XML tags as follows:

<tool_call>
{"name": <function-name>,"arguments": <args-dict>,  "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools:

<tools>
%s
</tools>
"""

# logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')



class ToolAgent():
    '''
        Agent that interacts with an LLM and use tools given to assist with user queries
        Args:
            tools (Tool | list[Tool]): list of tools available to the agent
            model (str): model type to be used for generating tool calls and responses
            tools_dict (dict) dictionary mapping tool names to callable objects
            client (Groq): client to query message from LLM
            tokenizer: tokenizer to truncuate messages in case they are too long
    '''
    def __init__(self, tools: Tool | list[Tool]):
        self.model = os.getenv('MODEL')
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Llama-70B")

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

            #print(Fore.CYAN + f'\nTool Result: {result}')

            observations[val_tool_call['id']] = result
        return observations
    
    def extract_tag_content(self, txt: str, tag: str) -> list:
        '''
            Extracts all tags from LLM response
            Args:
                txt (str): input string containing potential tags
                tag (str): name of the tag to extract
            Returns:
                list: content between specified tags
        '''
        pattern = rf"<{tag}>(.*?)</{tag}>"
        matched_contents = re.findall(pattern, txt, re.DOTALL)
        return [content.strip() for content in matched_contents]

    def chat(self, messages: list, max_total_tokens: int = 12000, max_response_tokens: int = 8192) -> str:
        '''
            Sends a request to Groq to interact with the LLM
            Args:
                messages (list[dict]): list of message objects containing chat history
            Returns:
                str: content of the model's response
        '''
        prompt = messages[0]
        usr_messages = messages[1:]

        total_tokens = len(self.tokenizer.encode(prompt['content']))
        trimmed = [prompt]

        for msg in reversed(usr_messages):
            msg_tokens = len(self.tokenizer.encode(msg['content']))
            if total_tokens + msg_tokens > max_total_tokens:
                break
            trimmed.append(msg)
            total_tokens += msg_tokens

        res = self.client.chat.completions.create(messages=trimmed, model=self.model, max_tokens=max_response_tokens)
        return str(res.choices[0].message.content)

    def run(self, usr_msg: str) -> str:
        '''
            Interacts with LLM and executes tools based on user input
            Args:
                usr_msg (str): user prompt for the agent to act upon
            Returns:
                str: final output response
        '''
        usr_prompt = {"role": "user", "content": usr_msg}
        sys_prompt = {"role": "system", "content": TOOL_SYSTEM_PROMPT % self.get_tool_signatures()}        

        tool_call_response = self.chat([sys_prompt, usr_prompt])
        tool_calls = self.extract_tag_content(str(tool_call_response), "tool_call")

        if tool_calls:
            observations = self.process_tool_calls(tool_calls)

            observation_msg = {
                "role": "user",
                "content": f"Observation: {json.dumps(observations, indent=2)}"
            }

            return self.chat([usr_prompt, observation_msg])
        return tool_call_response # if no tools are needed