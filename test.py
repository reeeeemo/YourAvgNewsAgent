from src.agent import ToolAgent
from src.tool import tool
from dotenv import load_dotenv
from typing import Literal, List
import os
import requests
from datetime import datetime, timedelta
import json

LANGUAGES = Literal['en', 'ar', 'de', 'es', 'fr', 'he', 'it', 'nl', 'no', 'pt', 'ru', 'sv', 'ud', 'zh']

@tool
def news_search(q: str, 
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
    if searchIn:
        searchIn = ','.join(searchIn)
    
    new_url = os.getenv('WEB_SEARCH_URL')
    api_key = os.getenv('WEB_SEARCH_API_KEY')
    params = {k: v for k, v in locals().items() if v is not None}
    params['apiKey'] = api_key

    response = requests.get(new_url, params=params)
    response_json = response.json()

    schema = {"status": response_json.get('status', 'error'), 
              "totalResults": response_json.get('totalResults', 0), 
              "articles": []}
    for article in response_json.get('articles', []):
        schema['articles'].append({
            "title": article.get('title', 'No Title'),
            "name": article.get('source', {}).get('name', 'No Name'),
            "description": article.get('description', 'No Description'),
            "url": article.get('url', 'No Url'),
        })

    return json.dumps(schema, indent=2)

load_dotenv()

# print(news_search('ai news today', sortBy='relevancy', searchIn=['description', 'title']))

ag = ToolAgent(tools=[news_search])

while True:
    print(ag.run(input('Query here: ')))