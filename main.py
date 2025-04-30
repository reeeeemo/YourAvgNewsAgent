from src.agent import Agent

Agent = Agent(config_path='config.json')

while True:
    input_query = input('Ask me a question: ')
    response = Agent.chat(input_query)
    print(response)
    print('\n')