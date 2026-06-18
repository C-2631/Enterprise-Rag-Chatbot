/**
 * MessageBubble Component
 * 
 * Displays a single chat message (user or assistant).
 * - User messages: right-aligned, glowing purple/indigo gradient
 * - Bot messages: left-aligned, frosted glass effect, math equations rendered using KaTeX,
 *   markdown formatting, and interactive source citation cards.
 */

import ReactMarkdown from "react-markdown";
import { User, Bot } from "lucide-react";
import katex from "katex";
import CitationCard from "./CitationCard";

function MessageBubble({ message, isStreaming = false }) {
  const isUser = message.role === "user";

  // ── KaTeX LaTeX / Math Formula Parser ──────────────────────
  const renderContentWithMath = (text) => {
    if (!text) return null;

    // Split content by LaTeX block math ($$...$$ or \[...\]) and inline math ($...$ or \(...\))
    const regex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\$[\s\S]*?\$|\\\([\s\S]*?\\\))/g;
    const parts = text.split(regex);

    return parts.map((part, index) => {
      // 1. Block Math Delimiters
      if ((part.startsWith("$$") && part.endsWith("$$")) || (part.startsWith("\\[") && part.endsWith("\\]"))) {
        const isBracketStyle = part.startsWith("\\[");
        const formula = isBracketStyle ? part.slice(2, -2) : part.slice(2, -2);
        try {
          const html = katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false });
          return (
            <div 
              key={index} 
              className="math-block my-3 overflow-x-auto shadow-inner bg-slate-950/50 border border-white/5 p-4 rounded-xl"
              dangerouslySetInnerHTML={{ __html: html }} 
            />
          );
        } catch (err) {
          return <div key={index} className="math-block text-danger font-mono">{formula}</div>;
        }
      }
      
      // 2. Inline Math Delimiters
      else if ((part.startsWith("$") && part.endsWith("$")) || (part.startsWith("\\(") && part.endsWith("\\)"))) {
        const isParenStyle = part.startsWith("\\(");
        const formula = isParenStyle ? part.slice(2, -2) : part.slice(1, -1);
        try {
          const html = katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false });
          return (
            <span 
              key={index} 
              className="math-inline mx-1 px-1.5 py-0.5 rounded-lg bg-purple/10 text-purple-light border border-purple/20 font-mono"
              dangerouslySetInnerHTML={{ __html: html }} 
            />
          );
        } catch (err) {
          return <span key={index} className="math-inline text-danger font-mono">{formula}</span>;
        }
      }
      
      // 3. Regular Markdown Content
      else {
        if (!part) return null;
        return (
          <ReactMarkdown 
            key={index}
            components={{
              // Inline paragraph override to maintain spacing
              p: ({ children }) => <span className="inline-block mb-2 last:mb-0 leading-relaxed">{children}</span>,
              // Preformatted code formatting
              pre: ({ children }) => <pre className="bg-slate-950/60 border border-white/5 rounded-xl p-4 my-2 overflow-x-auto font-mono text-xs text-accent">{children}</pre>,
              code: ({ children }) => <code className="bg-slate-950/40 text-accent font-mono text-xs px-1.5 py-0.5 rounded-md border border-white/5">{children}</code>
            }}
          >
            {part}
          </ReactMarkdown>
        );
      }
    });
  };

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} animate-slide-up`}>
      
      {/* Avatar Node */}
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border relative
        ${isUser 
          ? "bg-purple/15 border-purple/35 shadow-[0_0_10px_rgba(124,58,237,0.15)]" 
          : "bg-purple/15 border-purple/20 shadow-[0_0_10px_rgba(124,58,237,0.08)]"
        }
      `}>
        {isUser ? (
          <User className="w-4.5 h-4.5 text-purple-light" />
        ) : (
          <>
            <Bot className="w-4.5 h-4.5 text-accent animate-pulse" />
            <span className="w-1.5 h-1.5 rounded-full bg-accent absolute top-1 right-1" />
          </>
        )}
      </div>
      
      {/* Message Content Container */}
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        
        {/* Core bubble wrapper */}
        <div className={`rounded-2xl px-5 py-3.5 border relative overflow-hidden transition-all duration-300 ${
          isUser 
            ? "bg-gradient-to-r from-purple/80 to-purple-light/80 border-purple/30 text-white shadow-[0_4px_20px_rgba(124,58,237,0.2)]"
            : "glass border-purple/15 text-white shadow-[0_4px_15px_rgba(124,58,237,0.08)] bg-slate-900/50"
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none
                            prose-headings:text-accent prose-strong:text-white
                            prose-a:text-accent">
              {renderContentWithMath(message.content)}
              {isStreaming && <span className="chat-cursor ml-1" />}
            </div>
          )}
        </div>
        
        {/* Source Citations */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-1.5 animate-fade-in pl-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
              <p className="text-[10px] tracking-wider font-bold text-muted uppercase">Intelligence Citations:</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
              {message.sources.map((source, i) => (
                <CitationCard key={i} source={source} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;

