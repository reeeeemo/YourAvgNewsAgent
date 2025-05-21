# Your Average News Agent

![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)

An agent equipped with the ability to give you the latest (or previous) news! Equipped with a rolling chat history for real-time discussion about your news!

## Features
- Conversational news agent with chat history
- Integrates with Groq (LLama 4) for AI responses
- Utilizes NewsAPI for up-to-date news articles

> **Note:** Due to NewsAPI's restrictions with the Free tier, articles have a 24h delay. Articles up to a month old can also only be searched.

## Development
1. Clone repository `git clone https://github.com/reeeeemo/YourAvgNewsAgent.git`
2. Setup environment variables (see `.env.helper`)
3. Install dependencies
    - Frontend: `cd frontend && npm install`
    - Backend (api): `pip install -r requirements.txt`
4. Run locally
    - Frontend: `npm start`
    - Backend (api): `flask --app api.app --debug run` 

# Helpful Resources used
- **Neural Maze: Building AI Agents from Scratch**
    - [YouTube Link](https://www.youtube.com/watch?v=1OLrT3dEzhA)
    - [Substack Link](https://theneuralmaze.substack.com/)
    - [GitHub Link](https://github.com/neural-maze/agentic-patterns-course)
- [**NewsAPI docs**](https://newsapi.org/docs/endpoints/everything#sources)
