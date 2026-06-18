# 🧠 Enterprise RAG Chatbot

![Project Banner](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

A full-stack, enterprise-grade AI chatbot that uses **Retrieval-Augmented Generation (RAG)** to answer complex questions based strictly on your uploaded documents. It completely eliminates AI hallucinations by forcing the LLM to cite its sources directly from the files you provide.

---

## ✨ Key Features

- **📄 Multi-Format Document Support**: Upload PDFs, DOCX, TXT, and Markdown files.
- **🔍 Semantic Search**: Uses vector embeddings to find answers by *meaning*, not just exact keyword matches.
- **⚡ Real-Time Streaming**: Tokens stream to the UI in real-time (SSE) for a ChatGPT-like typing experience.
- **🔗 Source Citations**: Every generated answer includes citation cards indicating exactly which document and chunk the information came from.
- **🧠 Zero Hallucination**: Powered by Google Gemini 1.5 Flash and LangChain, the bot is strictly instructed to only answer based on the provided context.
- **🎨 Premium UI/UX**: Built with React and TailwindCSS featuring a modern Slate/Indigo design, glassmorphism, interactive 3D particle backgrounds, and LaTeX math rendering.

---

## 🏗️ Architecture

The system follows a modern service-oriented architecture:

1. **Frontend**: React + Vite + Tailwind CSS.
2. **Backend Gateway**: FastAPI handles async routing, SSE streaming, and file management.
3. **Storage Layer**: 
   - **ChromaDB**: Vector database storing high-dimensional embeddings for fast similarity search.
   - **SQLite**: Relational database tracking chat sessions, messages, and document metadata.
4. **AI Pipeline**:
   - **Parsing & Chunking**: LangChain `RecursiveCharacterTextSplitter`.
   - **Embeddings**: Google Gemini `embedding-001` model.
   - **Generation**: Google Gemini 1.5 Flash.

---

## 🚀 Getting Started

Follow these instructions to get the project running on your local machine.

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Google Gemini API Key

### 1. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Set up your environment variables:
Create a `.env` file in the `backend` folder and add your Gemini API Key:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
The backend will run on `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install the dependencies:
```bash
npm install
```

Start the React development server:
```bash
npm run dev
```
The frontend will run on `http://localhost:5173`. 

---

## 💡 How It Works (The RAG Pipeline)

1. **Upload**: You upload a document (e.g., a 50-page PDF).
2. **Chunking**: The backend extracts the text and splits it into small overlapping chunks (e.g., 800 characters each) to preserve context.
3. **Embedding**: Each chunk is passed through the Gemini embedding model to convert the text into a 768-dimensional numerical vector.
4. **Storage**: The vectors are stored in ChromaDB.
5. **Querying**: When you ask a question, your question is also converted into a vector.
6. **Retrieval**: ChromaDB performs a "cosine similarity" search to find the top 5 chunks most relevant to your question.
7. **Generation**: The retrieved chunks + your chat history + your question are sent to the Gemini LLM to generate a highly accurate, cited response.

---

## 🛠️ Tech Stack

- **Frontend**: React, Vite, TailwindCSS, Three.js (for 3D hero animation), React Markdown (with `remark-gfm`, `rehype-katex` for LaTeX).
- **Backend**: FastAPI, Pydantic, SQLAlchemy, aiosqlite.
- **AI/ML**: LangChain, Google Gemini API, PyPDF, python-docx.
- **Databases**: ChromaDB (Vector Search), SQLite (Relational Metadata).

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! 

## 📝 License
This project is open-source and available under the MIT License.
