/**
 * ChatPage — The main chat interface.
 */

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Bot, Loader, Plus, MessageSquare, Menu, 
  ChevronLeft, ChevronRight, AlertCircle, FileText, Trash2, Upload
} from "lucide-react";
import toast from "react-hot-toast";

import ChatInput from "../components/chat/ChatInput";
import MessageBubble from "../components/chat/MessageBubble";
import { 
  uploadDocument, 
  getChatSessions, 
  getSessionMessages, 
  getDocuments, 
  deleteDocument,
  deleteChatSession
} from "../services/api";
import GlassCard from "../components/ui/GlassCard";

function ChatPage() {
  // ── State ─────────────────────────────────────────
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [streamingSources, setStreamingSources] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  
  // Session Documents
  const [sessionDocuments, setSessionDocuments] = useState([]);
  
  // Sidebar State
  const [sessions, setSessions] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSidebarLoading, setIsSidebarLoading] = useState(false);

  // Ref for auto-scrolling to bottom
  const messagesEndRef = useRef(null);

  // ── Load Chat Sessions (History) ──────────────────
  const fetchSessions = async () => {
    try {
      setIsSidebarLoading(true);
      const data = await getChatSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to load chat sessions:", error);
    } finally {
      setIsSidebarLoading(false);
    }
  };

  // Load session-scoped documents
  const fetchSessionDocuments = async (sid) => {
    const targetId = sid || sessionId;
    if (!targetId) {
      setSessionDocuments([]);
      return;
    }
    try {
      const data = await getDocuments(targetId);
      setSessionDocuments(data.documents || []);
    } catch (error) {
      console.error("Failed to fetch session documents:", error);
    }
  };

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Fetch documents when sessionId changes
  useEffect(() => {
    fetchSessionDocuments(sessionId);
  }, [sessionId]);

  // ── Auto-scroll to bottom when messages change ────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // ── Load Selected Session Messages ────────────────
  const handleSelectSession = async (sessId) => {
    if (isLoading || isUploading) return; // Block switching while busy
    setSessionId(sessId);
    setStreamingText("");
    setStreamingSources([]);
    
    try {
      setIsLoading(true);
      const data = await getSessionMessages(sessId);
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Failed to load messages:", error);
      toast.error("Failed to load conversation history");
    } finally {
      setIsLoading(false);
    }
  };

  // ── Start New Chat ────────────────────────────────
  const handleNewChat = () => {
    if (isLoading || isUploading) return;
    setMessages([]);
    setSessionId(null);
    setStreamingText("");
    setStreamingSources([]);
    setSessionDocuments([]);
  };

  // ── Send Message (Streaming) ──────────────────────
  const handleSend = async (question) => {
    // Add user message immediately
    const userMessage = { role: "user", content: question };
    setMessages(prev => [...prev, userMessage]);
    
    setIsLoading(true);
    setStreamingText("");
    setStreamingSources([]);
    
    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          session_id: sessionId,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let fullAnswer = "";
      let sources = [];
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              
              if (event.type === "session") {
                setSessionId(event.data);
                fetchSessions();
              }
              else if (event.type === "sources") {
                sources = event.data;
                setStreamingSources(event.data);
              }
              else if (event.type === "token") {
                fullAnswer += event.data;
                setStreamingText(prev => prev + event.data);
              }
              else if (event.type === "done") {
                const botMessage = {
                  role: "assistant",
                  content: fullAnswer,
                  sources: sources,
                };
                setMessages(prev => [...prev, botMessage]);
                setStreamingText("");
                setStreamingSources([]);
                fetchSessions();
              }
              else if (event.type === "error") {
                toast.error(`Error: ${event.data}`);
              }
            } catch (parseError) {
              // Ignore partial JSON
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      toast.error("Failed to get response. Is the backend running?");
      
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Please make sure the backend is running and you have documents uploaded.",
        sources: [],
      }]);
    } finally {
      setIsLoading(false);
      setStreamingText("");
    }
  };

  // ── File Upload Handler ───────────────────────────
  const handleFileUpload = async (file) => {
    const allowedExtensions = ["pdf", "docx", "txt", "md"];
    const ext = file.name.split(".").pop().toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      toast.error(`Unsupported file type: .${ext}. Use PDF, DOCX, TXT, or MD`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 50MB");
      return;
    }

    try {
      setIsUploading(true);
      toast.loading(`Uploading and indexing ${file.name}...`, { id: "chat-upload" });
      
      const data = await uploadDocument(file, sessionId);
      
      // If a new session was created by the backend auto-session logic
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
      } else {
        fetchSessionDocuments(sessionId);
      }
      
      toast.success(`${file.name} uploaded and indexed successfully!`, { id: "chat-upload" });
      
      // Reload sessions list
      fetchSessions();
    } catch (error) {
      console.error("Upload failed:", error);
      const message = error.response?.data?.detail || "Upload failed";
      toast.error(message, { id: "chat-upload" });
    } finally {
      setIsUploading(false);
    }
  };

  // ── Delete Document Handler ───────────────────────
  const handleDeleteDocument = async (docId) => {
    if (!window.confirm("Remove this document from the chat session?")) return;
    try {
      await deleteDocument(docId);
      toast.success("Document removed");
      fetchSessionDocuments(sessionId);
      fetchSessions();
    } catch (error) {
      console.error("Failed to delete document:", error);
      toast.error("Failed to remove document");
    }
  };
  // ── Delete Session Handler ────────────────────────
  const handleDeleteSession = async (sessId, e) => {
    e.stopPropagation(); // Prevent selecting the session when clicking delete
    if (!window.confirm("Are you sure you want to delete this neural thread? This will permanently delete all associated documents and vector memories.")) return;
    try {
      setIsSidebarLoading(true);
      await deleteChatSession(sessId);
      toast.success("Neural thread purged successfully");
      
      // If we deleted the active session, clear the view
      if (sessionId === sessId) {
        handleNewChat();
      } else {
        fetchSessions();
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
      toast.error("Failed to delete session");
    } finally {
      setIsSidebarLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-primary overflow-hidden pt-16 relative">
      
      {/* Hidden file input for sidebar upload */}
      <input
        type="file"
        id="sidebar-file-upload"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) handleFileUpload(file);
          e.target.value = "";
        }}
        accept=".pdf,.docx,.txt,.md"
        className="hidden"
      />

      {/* ── Collapsible Left Sidebar ── */}
      <motion.div
        animate={{ 
          width: isSidebarOpen ? 280 : 0,
          opacity: isSidebarOpen ? 1 : 0
        }}
        transition={{ type: "spring", stiffness: 200, damping: 25 }}
        className="h-[calc(100vh-64px)] border-r border-purple/15 bg-slate-950/80 flex flex-col shrink-0 overflow-hidden relative z-10"
      >
        {/* Sidebar backdrop grid */}
        <div className="absolute inset-0 cyber-grid-purple opacity-20 pointer-events-none" />

        {/* New Chat Button */}
        <div className="p-4 relative z-10">
          <button
            onClick={handleNewChat}
            disabled={isLoading || isUploading}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl 
                       bg-purple/15 hover:bg-purple/25 border border-purple/25 
                       text-purple-light font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(124,58,237,0.1)]"
          >
            <Plus className="w-5 h-5" />
            New Core Thread
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-[2] overflow-y-auto px-3 pb-2 space-y-1.5 relative z-10 min-h-0 border-b border-purple/10">
          <div className="px-1.5 mb-1.5 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-light" />
            <span className="text-[10px] font-bold tracking-wider text-muted uppercase">ACTIVE_THREADS</span>
          </div>
          
          {isSidebarLoading && sessions.length === 0 ? (
            <div className="flex items-center justify-center py-10">
              <Loader className="w-6 h-6 text-purple-light animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-10 px-4">
              <MessageSquare className="w-8 h-8 text-muted mx-auto mb-2 opacity-50" />
              <p className="text-xs text-muted">No recent neural logs</p>
            </div>
          ) : (
            sessions.map((sess) => {
              const isActive = sess.id === sessionId;
              return (
                <div key={sess.id} className="relative group">
                  <button
                    onClick={() => handleSelectSession(sess.id)}
                    disabled={isLoading || isUploading}
                    className={`w-full flex items-start gap-3 p-2.5 pr-8 rounded-xl text-left transition-all duration-200 border
                      ${isActive 
                        ? "bg-purple/15 text-white border-purple/35 shadow-[0_0_15px_rgba(124,58,237,0.15)]" 
                        : "text-light-gray hover:text-white hover:bg-white/5 border-transparent"
                      }
                    `}
                  >
                    <MessageSquare className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isActive ? "text-purple-light" : "text-light-gray"}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold truncate leading-normal">
                        {sess.title}
                      </p>
                      <p className="text-[9px] text-muted font-mono mt-0.5">
                        LOGS: {sess.message_count} ACTIONS
                      </p>
                    </div>
                  </button>
                  
                  {/* Delete Session Button */}
                  <button
                    onClick={(e) => handleDeleteSession(sess.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-muted hover:text-danger hover:bg-danger/10 opacity-0 group-hover:opacity-100 transition-all duration-200"
                    title="Purge Neural Thread"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Loaded Documents for this session */}
        {sessionId && (
          <div className="flex-1 flex flex-col min-h-0 relative z-10 mt-2 pb-4">
            <div className="px-4 mb-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                <span className="text-[10px] font-bold tracking-wider text-muted uppercase">LOADED_CONTEXT</span>
              </div>
              <span className="text-[9px] font-mono text-muted">{sessionDocuments.length} FILES</span>
            </div>
            
            <div className="flex-1 overflow-y-auto px-3 space-y-1.5 min-h-0">
              {sessionDocuments.length === 0 ? (
                <div className="text-center py-6 px-3 border border-dashed border-purple/15 rounded-xl bg-slate-900/40">
                  <p className="text-[9px] text-muted uppercase">No documents loaded</p>
                  <button
                    onClick={() => document.getElementById("sidebar-file-upload")?.click()}
                    className="text-[9px] text-purple-light hover:text-white mt-1.5 font-black uppercase tracking-wider bg-purple/10 border border-purple/20 px-2.5 py-1 rounded-lg block mx-auto transition-colors"
                  >
                    + LOAD CORE FILE
                  </button>
                </div>
              ) : (
                <div className="space-y-1">
                  {sessionDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50 border border-white/5 group hover:border-purple/25 transition-all duration-200"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="w-3.5 h-3.5 text-purple-light shrink-0" />
                        <span className="text-xs text-light-gray truncate font-medium" title={doc.filename}>
                          {doc.filename}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="p-1 rounded text-muted hover:text-danger hover:bg-danger/10 opacity-0 group-hover:opacity-100 transition-all"
                        title="Remove Core"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => document.getElementById("sidebar-file-upload")?.click()}
                    className="text-[9px] text-accent hover:text-white mt-2 font-black uppercase tracking-wider border border-accent/20 hover:border-accent/40 bg-accent/5 px-2.5 py-1 rounded-lg block text-center w-full transition-colors"
                  >
                    + LOAD ANOTHER CORE
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>

      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col relative h-[calc(100vh-64px)] bg-primary overflow-hidden">
        
        {/* Holographic backdrop patterns */}
        <div className="absolute inset-0 cyber-grid-purple pointer-events-none z-0 opacity-40 animate-[cyber-grid-drift_40s_linear_infinite]" />
        <div className="absolute inset-0 scanlines pointer-events-none z-0 opacity-5" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-purple/5 blur-[120px] pointer-events-none z-0" />
        
        {/* Sidebar Collapse Toggle Button */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="absolute top-4 left-4 z-20 p-2.5 rounded-xl bg-slate-900/90 border border-purple/15 
                     text-light-gray hover:text-white hover:border-purple/30 transition-all duration-200 shadow-[0_0_10px_rgba(124,58,237,0.1)]"
          title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isSidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Floating Neural Status Control Pill */}
        <div className="absolute top-4 right-4 z-20 hidden md:flex items-center gap-4 px-4 py-2.5 rounded-full glass border-purple/20 text-xs font-mono text-light-gray shadow-[0_0_15px_rgba(124,58,237,0.15)]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-light animate-ping absolute" />
            <span className="w-2.5 h-2.5 rounded-full bg-purple-light" />
            <span className="text-white font-black">NEURAL_CORE_ONLINE</span>
          </div>
          <span className="text-white/20">|</span>
          <span>LATENCY: 22ms</span>
          <span className="text-white/20">|</span>
          <span>MODEL: gemini-2.5-flash</span>
        </div>

        {/* Floating Warning Banner if no documents loaded for active thread */}
        {sessionId && sessionDocuments.length === 0 && (
          <div className="absolute top-16 left-4 right-4 z-20 flex items-center gap-3 px-4 py-2.5 rounded-xl border border-danger/20 bg-danger/10 text-danger text-xs font-mono shadow-[0_0_15px_rgba(233,69,96,0.1)]">
            <span className="w-2 h-2 rounded-full bg-danger animate-ping shrink-0" />
            <span className="w-2 h-2 rounded-full bg-danger absolute shrink-0" />
            <span className="font-bold ml-1.5 uppercase">ATTENTION:</span>
            <span>NO COGNITIVE CONTEXT LOADED. UPLOAD A DOCUMENT CORE TO ENABLE RESPONSES.</span>
          </div>
        )}

        {/* ── Chat Messages List ── */}
        <div className={`flex-1 overflow-y-auto px-4 pb-6 relative z-10 ${sessionId && sessionDocuments.length === 0 ? "pt-28" : "pt-20"}`}>
          <div className="max-w-3xl mx-auto space-y-6">
            
            {/* Empty State */}
            {messages.length === 0 && !streamingText && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center py-20"
              >
                <div className="w-20 h-20 rounded-2xl bg-purple/10 flex items-center justify-center mb-6 border border-purple/20 relative shadow-[0_0_20px_rgba(124,58,237,0.1)]">
                  <div className="absolute -inset-2 rounded-2xl border border-dashed border-purple/10 animate-[spin_10s_linear_infinite]" />
                  <Bot className="w-9 h-9 text-purple-light" />
                </div>
                <h2 className="text-3xl font-extrabold text-white tracking-tight text-center mb-3">
                  Establish <span className="bg-gradient-to-r from-purple-light to-[#ec4899] bg-clip-text text-transparent">Neural</span> Connection
                </h2>
                
                {sessionDocuments.length === 0 ? (
                  <>
                    <p className="text-light-gray text-center max-w-md text-sm leading-relaxed mb-6">
                      No documents are attached to this new session. Please upload a document core to start the model memory context.
                    </p>
                    <button
                      onClick={() => document.getElementById("sidebar-file-upload")?.click()}
                      className="gradient-button flex items-center gap-2 shadow-glow text-sm py-3 px-6"
                    >
                      <Upload className="w-4.5 h-4.5" />
                      Upload Document Core
                    </button>
                  </>
                ) : (
                  <>
                    <p className="text-light-gray text-center max-w-md text-sm leading-relaxed">
                      Intelligence core loaded successfully. Ask the Neural Core anything about the attached files!
                    </p>
                    <div className="flex flex-wrap gap-2 mt-8 justify-center">
                      {[
                        "Summarize the key points",
                        "What are the main findings?",
                      ].map((suggestion) => (
                        <button
                          key={suggestion}
                          onClick={() => handleSend(suggestion)}
                          className="px-4 py-2.5 rounded-xl text-sm font-medium text-light-gray
                                     bg-slate-900/40 hover:bg-purple/10 border border-white/10 hover:border-purple/35
                                     transition-all duration-200 shadow-md"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </motion.div>
            )}
            
            {/* Message Bubbles Wrapper */}
            <div className="space-y-6">
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div
                    key={msg.id || i}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ type: "spring", stiffness: 180, damping: 18 }}
                  >
                    <MessageBubble message={msg} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
            
            {/* Streaming Response (while generating) */}
            {streamingText && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <MessageBubble
                  message={{
                    role: "assistant",
                    content: streamingText,
                    sources: streamingSources,
                  }}
                  isStreaming={true}
                />
              </motion.div>
            )}
            
            {/* Typing Indicator */}
            {isLoading && !streamingText && (
              <div className="flex gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-xl bg-purple/20 flex items-center justify-center border border-purple/30">
                  <Bot className="w-4 h-4 text-purple-light" />
                </div>
                <GlassCard className="px-5 py-3 rounded-2xl border-purple/20 shadow-[0_0_15px_rgba(124,58,237,0.08)] bg-slate-900/60">
                  <div className="flex gap-1.5 items-center h-4">
                    <span className="w-2 h-2 bg-purple-light rounded-full animate-bounce" style={{animationDelay: "0ms"}} />
                    <span className="w-2 h-2 bg-purple-light rounded-full animate-bounce" style={{animationDelay: "150ms"}} />
                    <span className="w-2 h-2 bg-purple-light rounded-full animate-bounce" style={{animationDelay: "300ms"}} />
                  </div>
                </GlassCard>
              </div>
            )}
            
            {/* Auto-scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </div>
        
        {/* ── Chat Input (fixed at bottom) ── */}
        <div className="sticky bottom-0 bg-gradient-to-t from-primary via-primary to-transparent pt-6 pb-6 relative z-10">
          <div className="max-w-3xl mx-auto px-4">
            <ChatInput 
              onSend={handleSend} 
              onFileUpload={handleFileUpload} 
              isLoading={isLoading} 
              isUploading={isUploading} 
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
