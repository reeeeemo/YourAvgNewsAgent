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

from src.agent import Agent

@pytest.fixture
def agent(config):
    '''
        Create ChromaDB instance called `test_db`
    '''
    return Agent(config_path='config.json')

def test_agent_web_search(agent):
    '''
        Test agent initialization
    '''
    result = agent.web_search('What is a cat?', 'noLimit')

    assert (result) # do we get a response from the web search

def test_agent_chat(agent):
    response = agent.chat('What is a cat?')

    assert(len(agent.memory) > 0) # conversation history saved
    assert(response)
    assert(response != 'An error occurred while processing your request. Please try again.')

def test_agent_decision(agent):
    decision = "{'action': 'search', 'freshness': 'noLimit', 'query': 'what is a cat?'}"
    search, didSearch = agent.decide(decision)

    assert(search)
    assert(didSearch) # no errors

def test_agent_parse(agent):
    decision = '{"action": "search", "freshness": "noLimit", "query": "what is a cat?"}'
    false_decision = "Cats are pretty funky creatures!"
    response = agent.parse_response(decision)
    false_response = agent.parse_response(false_decision)
    assert(response['query'] != 'RETRY')
    assert(false_response['query'] != 'RETRY')
    assert(false_response['action'] == 'answer')
    assert(response['action'] == 'search')