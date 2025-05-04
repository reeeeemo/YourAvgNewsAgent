from src.agent import ToolAgent
from src.tool import tool
from dotenv import load_dotenv
from typing import Literal, List
import os
import requests
from datetime import datetime, timedelta

LANGUAGES = Literal['en', 'ar', 'de', 'es', 'fr', 'he', 'it', 'nl', 'no', 'pt', 'ru', 'sv', 'ud', 'zh']

def web_search(q: str, 
               searchIn: List[Literal['title', 'description', 'content']] | None = None,
               dateFrom: str | None = None,
               dateTo: str | None = None,
               language: LANGUAGES = 'en',
               sortBy: Literal['relevancy', 'popularity', 'publishedAt'] = 'publishedAt',
               ) -> str:
    """
        Search the web for keywords or phrases in news articles.
        Args:
            - q (str): query for keywords or phrases in the article title/body
            - searchIn (list): fields to restrict the query search to
            - dateFrom (str): Date in ISO 8601 format for the oldest article allowed
            - dateTo (str): Date in ISO 8601 format for the newest article allowed
            - language (str): 2 Letter ISO-639-1 code of language to get headlines for
            - sortBy (str): Order to sort the articles in
        Returns:
            result (str): JSON schema of all the articles
    """
    if dateFrom is None:
        dateFrom = (datetime.now() - timedelta(days=1)).isoformat(timespec='seconds') + 'Z'
    if dateTo is None:
        dateTo = datetime.now().isoformat(timespec='seconds') + 'Z'
    
    new_url = os.getenv('WEB_SEARCH_URL')
    params = {k: v for k, v in locals().items() if v is not None}

    for header, value in params.items():
        new_url += f'{header}={value}&'
    new_url += f'apiKey={os.getenv("WEB_SEARCH_API_KEY")}'
    
    response = requests.request('GET', new_url)
    print(response.text)

    return ""

load_dotenv()

web_search('ai')

# ag = ToolAgent(tools=[tool(web_search)])