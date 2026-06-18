// This is a placeholder for your API service.
// You can add your API-related functions here, for example using axios.

import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Adjust the baseURL to your backend
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Checks the health of the backend API.
 * @returns {Promise<object>} A promise that resolves to the health status data.
 */
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// ── Document API Functions ──────────────────────────

/**
 * Upload a document file.
 * 
 * Uses FormData because we're sending a FILE, not JSON.
 * The Content-Type is automatically set to 'multipart/form-data' by axios.
 * 
 * @param {File} file - The file object from an <input> or drag-and-drop
 * @returns {Promise<object>} Upload result with document metadata
 */
export const uploadDocument = async (file, sessionId = null) => {
  const formData = new FormData();
  formData.append("file", file);  // "file" matches the FastAPI parameter name

  const url = sessionId ? `/documents/upload?session_id=${sessionId}` : "/documents/upload";

  const response = await apiClient.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",  // Override default JSON header
    },
  });
  return response.data;
};

/**
 * Get list of all uploaded documents.
 * @param {string} sessionId - Optional chat session ID to filter documents
 * @returns {Promise<object>} { documents: [...], total: number }
 */
export const getDocuments = async (sessionId = null) => {
  const url = sessionId ? `/documents?session_id=${sessionId}` : "/documents";
  const response = await apiClient.get(url);
  return response.data;
};

/**
 * Delete a document by ID.
 * @param {string} documentId - UUID of the document to delete
 * @returns {Promise<object>} Deletion confirmation
 */
export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/documents/${documentId}`);
  return response.data;
};

/**
 * Search documents using semantic similarity.
 * 
 * @param {string} query - Natural language search query
 * @param {number} topK - Number of results (default: 5)
 * @returns {Promise<object>} Search results with scores
 */
export const searchDocuments = async (query, topK = 5) => {
  const response = await apiClient.post("/search", {
    query: query,
    top_k: topK,
  });
  return response.data;
};

/**
 * Get vector store statistics.
 * @returns {Promise<object>} Vector store stats (chunk count, status)
 */
export const getVectorStoreStats = async () => {
  const response = await apiClient.get("/search/stats");
  return response.data;
};

// ── Chat API Functions ──────────────────────────────

/**
 * Get all chat sessions.
 * @returns {Promise<object>} { sessions: [...], total: number }
 */
export const getChatSessions = async () => {
  const response = await apiClient.get("/chat/sessions");
  return response.data;
};

/**
 * Get all messages for a specific chat session.
 * @param {string} sessionId - UUID of the chat session
 * @returns {Promise<object>} { messages: [...], total: number }
 */
export const getSessionMessages = async (sessionId) => {
  const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
  return response.data;
};

/**
 * Delete a chat session and all its associated data.
 * @param {string} sessionId - UUID of the chat session
 * @returns {Promise<object>} Deletion confirmation
 */
export const deleteChatSession = async (sessionId) => {
  const response = await apiClient.delete(`/chat/sessions/${sessionId}`);
  return response.data;
};

export default apiClient;
