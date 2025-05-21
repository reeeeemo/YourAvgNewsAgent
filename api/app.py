from flask import Flask, request, jsonify
from .agent import ToolAgent
from dotenv import load_dotenv
from .tools import news_search
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
    agent.chat_history.extend(chat_history)

    response = agent.run(usr_query)
    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5328, debug=True)