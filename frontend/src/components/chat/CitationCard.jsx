/**
 * CitationCard Component
 * 
 * Displays a source reference from the retrieved chunks.
 * Shows: filename, relevance score, and preview text.
 * Expandable: click to see full chunk text.
 */

import { useState } from "react";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";

function CitationCard({ source }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Determine relevance badge color
  const getScoreColor = (score) => {
    if (score >= 0.7) return "text-success bg-success/10";
    if (score >= 0.4) return "text-yellow-400 bg-yellow-400/10";
    return "text-danger bg-danger/10";
  };

  return (
    <div 
      className="glass p-3 cursor-pointer hover:shadow-glow transition-all duration-200"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-accent shrink-0" />
          <span className="text-sm text-white truncate">{source.source}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getScoreColor(source.score)}`}>
            {(source.score * 100).toFixed(0)}%
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted shrink-0" />
        )}
      </div>
      
      {isExpanded && (
        <p className="text-xs text-light-gray mt-2 leading-relaxed border-t border-white/5 pt-2">
          {source.text}
        </p>
      )}
    </div>
  );
}

export default CitationCard;
