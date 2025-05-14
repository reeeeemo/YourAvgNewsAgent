from flask import Flask, request
from src.agent import ToolAgent
from dotenv import load_dotenv
from src.tools import news_search

load_dotenv()

agent = ToolAgent(tools=[news_search])
app = Flask(__name__)


@app.route('/query', methods=['GET'])
def query():
    response = agent.run(request.args.get('q', 'Error fetching Query'))
    return response

if __name__ == '__main__':
    app.run()