import chromadb
import ollama
import pathlib
from langchain_community.document_loaders import TextLoader, CSVLoader, JSONLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from tqdm import tqdm
from typing import Dict

class ChromaDB():
    '''
        Custom ChromaDB class to handle vector database operations
        Args:
            client: ChromDB client instnce
            collection: ChromaDB vector database
            model: Model to use for embedding
            text_splitter: Text splitter for chunking documents
    '''
    def __init__(self, name: str ='vector_db', model: str = ''):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=name)
        self.model = model if model else ""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )

    def add_chunk(self, chunk: str, id: str, metadata: Dict =None):
        '''
            Embeds then adds a single chunk to the vector database
            Args:
                chunk: Text chunk to add to the database
                id: Unique ID for the chunk
                metadata: Optional metadata for the chunk
            
            Returns whether it was successful
        '''
        if len(chunk.strip()) < 5:
            print(f'Chunk is too short to add to the database: {chunk}')
            return False
        
        try:
            embedding = ollama.embed(model=self.model, input=chunk)['embeddings'][0]
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[id],
                metadatas=[metadata if metadata else {}]
            )
        except Exception as e:
            print(f'Error adding chunk to database: {e}')
            return False
        return True
    
    def remove_chunk(self, id: str) -> bool:
        '''
            Removes a chunk from the vector database by ID

            Returns whether successful
        '''
        try:
            self.collection.delete(ids=[id])
        except Exception as e:
            logging.error(f'Error removing chunk from database: {e}')
            return False
        return True

    def add_documents(self, folder_path: str) -> bool:
        '''
            Given a directory, load all documents recursively (if more folders are present)
            and add them to the vector database. Supported file types are:
            - .txt
            - .json
            - .csv
            - .pdf

            Returns whether the documents were added successfully
        '''
        folder_path = pathlib.Path(folder_path)

        # check for folder existence and if directory 
        if not folder_path.exists():
            print(f'Folder does not exist: {folder_path}')
            return False
        if not folder_path.is_dir():
            print(f'Path is not a directory: {folder_path}')
            return False
        
        docs = []

        # for each file, check what kind of file (if supported) and add to vector_db
        for filename in list(folder_path.glob('**/*')):
            filepath = filename
            
            # if file is another directory, recursively add documents
            if filepath.is_dir():
                self.add_documents(filepath)
                continue
            
            loader = None
            match filename.suffix.lower().split('.')[-1]:
                case 'txt':
                    loader = TextLoader(filepath, encoding='utf-8')
                case 'json':
                    loader = JSONLoader(filepath, jq_schema=None)
                case 'csv':
                    loader = CSVLoader(filepath, encoding='utf-8')
                case 'pdf':
                    loader = PyPDFLoader(filepath)
                case 'html':
                    loader = UnstructuredHTMLLoader(filepath)
                case _:
                    print(f'Unsupported file type: {filename}. Skipping...')
                    continue

            docs.extend(loader.load())
        
        # from all docs, split into chunks and add to the vector database
        chunks = self.text_splitter.split_documents(docs)
        logging.info(f'Loaded {len(chunks)} chunks from {folder_path}')
        for i, chunk in tqdm(enumerate(chunks)):
            if not self.add_chunk(chunk.page_content, str(i), metadata=chunk.metadata):
                print(f'Failed to add chunk {i} to the database.')
                continue

        return True
    
    def retrieve(self, query, top_n=5):
        '''
            Given a query, retrieve top_n most relevant documents from the vector database
            
            Returns the relevant documents
        '''
        query_embedding = ollama.embed(model=self.model, input=query)['embeddings'][0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_n,
        )
        return results
    
    def get_all_documents(self):
        '''
            Return all documents in the database
        '''
        return self.collection.get()['documents']
