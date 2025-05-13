from src.agent import ToolAgent
from dotenv import load_dotenv
from src.tools import news_search

load_dotenv()

ag = ToolAgent(tools=[news_search])

while True:
    print(ag.run(input('Query here: ')))