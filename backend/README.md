# ⚙️ Backend — Enterprise RAG Chatbot
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
This directory contains the **Backend API** for the Enterprise RAG Chatbot. It is an asynchronous, high-performance web server built with FastAPI that orchestrates the entire Retrieval-Augmented Generation (RAG) pipeline.
## ✨ Core Technologies
- **FastAPI**: Provides robust, asynchronous REST APIs with auto-generated Swagger documentation.
- **LangChain**: Handles document chunking, prompt engineering, and LLM abstractions.
- **Google Gemini**: Uses `embedding-001` for vectorizing text and `Gemini-1.5-Flash` for fast, accurate generation.
- **ChromaDB**: The vector database used to store high-dimensional embeddings and perform rapid semantic similarity searches.
- **SQLAlchemy & aiosqlite**: Asynchronous Object-Relational Mapping (ORM) to interact with the SQLite database that tracks chat histories and uploaded documents.
## 📁 Directory Structure
```text
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # SQLite connection and session factory
│   ├── chroma_db.py         # Vector database client initialization
│   ├── models/              # SQLAlchemy database schemas (Chat & Document)
│   ├── routers/             # API Endpoints (Upload, Chat, Sessions)
│   ├── services/            # Core business logic
│   │   ├── document_service.py # Parses PDF, DOCX, TXT, MD
│   │   ├── indexing_service.py # LangChain chunking and vector storage
│   │   └── chat_service.py     # RAG context injection and LLM generation
│   └── prompts/
│       └── system_prompt.py    # Strict instructions preventing hallucination
├── chroma_db/               # (Auto-generated) Vector DB persistent storage
├── rag_chatbot.db           # (Auto-generated) SQLite persistent storage
├── requirements.txt         # Python dependencies
└── .env                     # API Keys (Not tracked in Git)
```
## 🛠️ Getting Started
### Prerequisites
- Python 3.10+
- A Google Gemini API Key
### Installation
1. Open a terminal in the `backend` directory.
2. Create and activate a Python virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
### Configuration
Create a `.env` file in the root of the `backend` directory and add your API key:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
### Running the Server
Start the FastAPI application using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The server will start running at [http://localhost:8000](http://localhost:8000).
### API Documentation
Once the server is running, you can interact with and test the API directly using FastAPI's built-in Swagger UI by navigating to:
[http://localhost:8000/docs](http://localhost:8000/docs)
