/**
 * ChatInput Component
 * 
 * The text input area at the bottom of the chat.
 * Features:
 * - Auto-expanding textarea
 * - Enter to send, Shift+Enter for newline
 * - Disabled while generating
 * - Send button with icon
 */

import { useState, useRef } from "react";
import { Send, Loader, Paperclip } from "lucide-react";

function ChatInput({ onSend, onFileUpload, isLoading, isUploading }) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Don't send empty messages or while loading
    if (!message.trim() || isLoading) return;
    
    onSend(message.trim());
    setMessage("");  // Clear input after sending
  };

  const handleKeyDown = (e) => {
    // Enter without Shift = send
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();  // Prevent newline
      handleSubmit(e);
    }
  };

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && onFileUpload) {
      onFileUpload(file);
    }
    e.target.value = "";  // Reset input
  };

  return (
    <form onSubmit={handleSubmit} className="px-4 pb-4">
      <div className="glass flex items-end gap-3 px-5 py-3.5 rounded-[26px] border border-purple/15 bg-slate-950/40 focus-within:border-purple/35 focus-within:shadow-[0_0_20px_rgba(124,58,237,0.12)] transition-all duration-300 relative z-10">
        
        {/* Attachment Button */}
        {onFileUpload && (
          <div className="relative">
            <button
              type="button"
              onClick={handleAttachmentClick}
              disabled={isLoading || isUploading}
              className="p-2 rounded-full text-light-gray hover:text-white hover:bg-purple/10 border border-transparent hover:border-purple/15 transition-all duration-200 disabled:opacity-50"
              title="Upload document core (.pdf, .docx, .txt, .md)"
            >
              {isUploading ? (
                <Loader className="w-5 h-5 animate-spin text-purple-light" />
              ) : (
                <Paperclip className="w-5 h-5" />
              )}
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
            />
          </div>
        )}
 
        {/* Textarea (auto-expands with content) */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isLoading ? "Generating cognitive response..." : "Ask the Neural Core about your documents..."}
          disabled={isLoading}
          rows={1}
          className="flex-1 bg-transparent text-white placeholder-muted 
                     resize-none outline-none text-sm leading-relaxed
                     max-h-36 overflow-y-auto disabled:opacity-50 font-sans pr-2"
          style={{
            height: "auto",
            minHeight: "24px",
          }}
          onInput={(e) => {
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
          }}
        />
        
        {/* Send Button */}
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className={`p-2.5 rounded-full transition-all duration-300 flex items-center justify-center shrink-0
            ${message.trim() && !isLoading
              ? "bg-gradient-to-r from-purple to-purple-light text-white shadow-[0_0_15px_rgba(124,58,237,0.3)] hover:scale-105"
              : "bg-white/5 text-muted cursor-not-allowed"
            }
          `}
          title="Transmit Query"
        >
          {isLoading ? (
            <Loader className="w-4.5 h-4.5 animate-spin" />
          ) : (
            <Send className="w-4.5 h-4.5" />
          )}
        </button>
      </div>
      
      <p className="text-muted text-[10px] font-mono text-center mt-2 opacity-80 uppercase tracking-widest">
        ENTER TO TRANSMIT · SHIFT+ENTER FOR NEWLINE
      </p>
    </form>
  );
}

export default ChatInput;
