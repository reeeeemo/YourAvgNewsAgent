import pytest
import json
from src.tool import tool
from src.agent import ToolAgent

@pytest.fixture
def tool_decorator():
    def greetings(name: str):
        "Greets the user"
        print(f'Greetings, {name}')
    return tool(greetings)

@pytest.fixture
def agent(tool_decorator):
    return ToolAgent(tools=[tool_decorator])


def test_tool(tool_decorator):
    '''
        Test sample tool and it's functions
    '''
    # test class vars
    assert tool_decorator.name, "Tool name should be initialized"
    assert json.dumps(tool_decorator.fn_signature), "Tool signature should be initalized"

    # test class functions 
    assert tool_decorator(name="meow") is None
    schema = f'{{"name": "{tool_decorator.name}", "arguments": {{"name": "meowie"}}, "id": "2"}}'
    assert type(tool_decorator.validate_args(json.loads(schema))['arguments']['name']) == str, "Variables should be validated"

def test_agent(agent):
    '''
        Test sample agent and it's tools / functions
    '''
    # test class vars
    assert agent.tools, "Tool list should be initialized"
    assert agent.tools_dict, "Tool dictionary should be initialized"

    # test class functions
    assert len(agent.get_tool_signatures()) > 0, "Tool should be added to the agent"
    schema = f'{{"name": "{agent.tools[0].name}", "arguments": {{"name": "meowie"}}, "id": "2"}}'
    assert len(agent.process_tool_calls([schema])) > 0, "Tool should be processed with return value"

def test_agent_responses(agent):
    '''
        Test sample agent's functions for chatting 
    '''
    assert agent.tools, "Tool list should be initialized"
    assert agent.tools_dict, "Tool dictionary should be initialized"

    assert len(agent.chat([{"role": "system", "content": "This is a test response. Output anything"}, {"role": "user", "content": "Test response"}])) > 0, "Agent should return LLM response"
    assert len(agent.run('This is a test response')) > 0, 'Agent should return full response / use tools if needed'