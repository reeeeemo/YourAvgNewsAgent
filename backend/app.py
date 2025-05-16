from flask import Flask, request
from src.agent import ToolAgent
from dotenv import load_dotenv
from src.tools import news_search
from flask_cors import CORS

load_dotenv()

agent = ToolAgent(tools=[news_search])
app = Flask(__name__)
CORS(app)


@app.route('/query', methods=['POST'])
def query():
    data = request.json
    usr_query = data.get('query', 'Error fetching query')
    chat_history = data.get('chat_history', [])

    agent = ToolAgent(tools=[news_search])
    agent.chat_history = chat_history

    response = agent.run(usr_query)
    return response

if __name__ == '__main__':
    app.run(port=5000)