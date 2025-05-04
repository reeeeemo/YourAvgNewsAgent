import pytest
from src.database import ChromaDB
import json
import pathlib


'''
    ###################
    PYTESTS FOR DATABASE
    ###################
'''

@pytest.fixture
def config():
    '''
        Load configuration from config.json
    '''
    with open('config.json', 'r') as f:
        config_data = json.load(f)
    return config_data

@pytest.fixture
def chroma_db(config):
    '''
        Create ChromaDB instance called `test_db`
    '''
    return ChromaDB(model=config['embedding_model'], name='test_db')

@pytest.fixture
def temp_txt_file(tmp_path):
    '''
        Create temporary text file with sample text
    '''
    temp_fp = tmp_path / 'temptest.txt'
    temp_fp.write_text('Cats are pretty cool!')
    return temp_fp

def test_sample_database(chroma_db):
    '''
        Tests databse initialization and connection
    '''
    assert chroma_db is not None, "Database should be initialized"
    assert chroma_db.client is not None, "ChromaDB client should be initialized"
    assert chroma_db.collection is not None, "ChromaDB collection should be initialized"


def test_add_documents_sucess(chroma_db, config):
    '''
        Test adding documents to the database
    '''
    valid_path = pathlib.Path.cwd() / config['rag_path']
    result = chroma_db.add_documents(valid_path)
    assert result, "Documents should be added successfully"


def test_add_documents_failure(chroma_db):
    '''
        Test adding documents from an invalid path
    '''
    result = chroma_db.add_documents('invalid_path')
    assert not result, "Documents should not be added from an invalid path"

def test_add_chunk(chroma_db):
    '''
        Test adding a single chunk to the database
    '''
    chunk = "Meow meow meow meow"
    id = "test_meow_1"
    metadata = {'source': 'test_source', 'file_type': 'txt'}
    chroma_db.add_chunk(chunk, id, metadata)

    assert len(chroma_db.collection.get(ids=[id])['documents']) == 1, "Chunk should be added to the database"
    assert chroma_db.collection.get(ids=[id])['documents'][0] == chunk, "Chunk content should match the added chunk"

def test_add_documents(chroma_db, temp_txt_file):
    '''
        Test adding documents from a temporary text file
    '''
    result = chroma_db.add_documents(temp_txt_file.parent)

    assert result, "Documents should be added successfully"

    stored_docs = chroma_db.collection.get()['documents']

    assert len(stored_docs) > 0, "Database should contain documents after adding"
    assert len(chroma_db.retrieve("Cats are pretty cool!")) > 0, "Should retrieve the added document"



'''
    ###################
    PYTESTS FOR AGENT
    ###################
'''

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
