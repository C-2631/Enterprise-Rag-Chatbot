/**
 * Documents Page
 * 
 * Features:
 * - Drag-and-drop upload zone
 * - File type validation with visual feedback
 * - Upload progress indication
 * - Document list with status badges
 * - Delete functionality
 * - Framer Motion page entry and list animations
 */

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, FileText, Trash2, CheckCircle, XCircle, 
  Loader, File, RefreshCw 
} from "lucide-react";
import toast from "react-hot-toast";
import { uploadDocument, getDocuments, deleteDocument } from "../services/api";
import GlassCard from "../components/ui/GlassCard";
import NeoButton from "../components/ui/NeoButton";

// Allowed file types and their display info
const FILE_TYPES = {
  pdf: { label: "PDF", color: "text-red-400", bg: "bg-red-400/10" },
  docx: { label: "DOCX", color: "text-blue-400", bg: "bg-blue-400/10" },
  txt: { label: "TXT", color: "text-green-400", bg: "bg-green-400/10" },
  md: { label: "MD", color: "text-purple-400", bg: "bg-purple-400/10" },
};

// Status badge styling
const STATUS_STYLES = {
  completed: { color: "text-success", bg: "bg-success/10", icon: CheckCircle },
  processing: { color: "text-accent", bg: "bg-accent/10", icon: Loader },
  failed: { color: "text-danger", bg: "bg-danger/10", icon: XCircle },
  uploaded: { color: "text-light-gray", bg: "bg-white/5", icon: File },
};

function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await getDocuments();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      toast.error("Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileUpload = async (file) => {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!FILE_TYPES[ext]) {
      toast.error(`Unsupported file type: .${ext}. Use PDF, DOCX, TXT, or MD`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 50MB");
      return;
    }

    try {
      setIsUploading(true);
      toast.loading(`Uploading ${file.name}...`, { id: "upload" });
      
      await uploadDocument(file);
      toast.success(`${file.name} uploaded successfully!`, { id: "upload" });
      await fetchDocuments();
    } catch (error) {
      const message = error.response?.data?.detail || "Upload failed";
      toast.error(message, { id: "upload" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.filename}"? This cannot be undone.`)) {
      return;
    }

    try {
      await deleteDocument(doc.id);
      toast.success(`Deleted: ${doc.filename}`);
      
      // Optimistic UI updates
      setDocuments(prev => prev.filter(d => d.id !== doc.id));
    } catch (error) {
      toast.error("Failed to delete document");
      await fetchDocuments();
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
    e.target.value = "";
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="min-h-screen pt-24 px-4 pb-16 relative overflow-hidden"
    >
      {/* ── Holographic Backdrop Layers ── */}
      <div className="absolute inset-0 cyber-grid pointer-events-none z-0 opacity-50" />
      <div className="absolute inset-0 scanlines pointer-events-none z-0 opacity-5" />
      <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-accent/10 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-10 right-10 w-80 h-80 rounded-full bg-success/5 blur-[100px] pointer-events-none z-0" />

      <div className="max-w-4xl mx-auto relative z-10">

        {/* ── Page Header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10 pb-6 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              <span className="text-[10px] tracking-[0.2em] font-bold text-accent uppercase">SYSTEM_INGESTION_MODULE</span>
            </div>
            <h1 className="text-4xl font-extrabold text-white tracking-tight">
              Data <span className="bg-gradient-to-r from-accent to-[#00e5ff] bg-clip-text text-transparent">Vault</span> Ingestion
            </h1>
            <p className="text-light-gray text-sm mt-1">
              Feed raw text intelligence cores to the vector index model.
            </p>
          </div>
          <NeoButton
            onClick={fetchDocuments}
            className="flex items-center gap-2 border border-accent/20 text-accent glow-accent/10 py-2.5"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh Core
          </NeoButton>
        </div>

        {/* ── Upload Zone (Futuristic Portal) ── */}
        <motion.div
          whileHover={{ scale: 1.005, borderColor: "rgba(0, 229, 255, 0.4)" }}
          whileTap={{ scale: 0.995 }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            glass p-12 mb-10 text-center cursor-pointer relative overflow-hidden
            transition-all duration-300 border-2 border-dashed
            ${isDragOver
              ? "border-accent bg-accent/5 shadow-[0_0_35px_rgba(0,229,255,0.2)]"
              : "border-white/10 hover:border-accent/30 bg-slate-900/40"
            }
            ${isUploading ? "opacity-60 pointer-events-none" : ""}
          `}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileInput}
          />
          
          <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
            {isUploading ? (
              <div className="relative mb-6">
                <Loader className="w-16 h-16 text-accent animate-spin" />
                <div className="absolute inset-0 w-16 h-16 rounded-full border border-accent/20 animate-ping" />
              </div>
            ) : (
              <div className="relative mb-6 group">
                {/* Cyber decoration rings */}
                <div className="absolute -inset-4 rounded-full border border-accent/10 animate-[spin_12s_linear_infinite]" />
                <div className="absolute -inset-2 rounded-full border border-dashed border-accent/20 animate-[spin_8s_linear_infinite_reverse]" />
                <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20 group-hover:bg-accent/20 transition-all duration-300">
                  <Upload className={`w-7 h-7 transition-colors ${
                    isDragOver ? "text-accent" : "text-light-gray"
                  }`} />
                </div>
              </div>
            )}
            
            <h3 className="text-xl font-bold text-white mb-2">
              {isDragOver ? "Deploy file to vault portal!" : "Drag & drop a file or click to upload"}
            </h3>
            <p className="text-xs text-light-gray max-w-sm mb-6 leading-relaxed">
              Compatible formats include PDF, DOCX, TXT, or MD. Maximum size limit is 50MB per document core.
            </p>
            
            <div className="flex items-center justify-center gap-3">
              {Object.entries(FILE_TYPES).map(([ext, info]) => (
                <span
                  key={ext}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold tracking-wider border border-white/5 shadow-inner ${info.color} ${info.bg}`}
                >
                  .{ext.toUpperCase()}
                </span>
              ))}
            </div>
          </label>
        </motion.div>

        {/* ── Document List (Data Server Blades) ── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <h2 className="text-sm font-bold tracking-wider text-muted uppercase">ACTIVE_STORAGE_CORES</h2>
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-xs font-mono text-light-gray">
              {documents.length} SYSTEMS ONLINE
            </span>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader className="w-10 h-10 text-accent animate-spin" />
            </div>
          ) : documents.length === 0 ? (
            <GlassCard className="p-12 text-center border border-white/5">
              <FileText className="w-14 h-14 text-muted mx-auto mb-4 opacity-50" />
              <p className="text-white font-medium text-lg">No active intelligence cores registered</p>
              <p className="text-muted text-sm mt-1 max-w-xs mx-auto">Upload documents above to build the system knowledge index.</p>
            </GlassCard>
          ) : (
            <motion.div layout className="space-y-3">
              <AnimatePresence mode="popLayout">
                {documents.map((doc) => {
                  const typeInfo = FILE_TYPES[doc.file_type] || { label: doc.file_type.toUpperCase(), color: "text-white", bg: "bg-white/5" };
                  const statusInfo = STATUS_STYLES[doc.status] || STATUS_STYLES.uploaded;
                  const StatusIcon = statusInfo.icon;

                  return (
                    <motion.div
                      layout
                      initial={{ opacity: 0, x: -30 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 30 }}
                      transition={{ type: "spring", stiffness: 220, damping: 22 }}
                      key={doc.id}
                    >
                      <GlassCard className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 group hover:shadow-[0_0_20px_rgba(0,229,255,0.08)] border-l-4 border-l-accent relative overflow-hidden bg-slate-950/40">
                        {/* Blade background grid pattern */}
                        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-accent/5 to-transparent pointer-events-none" />
                        
                        {/* Left: File details */}
                        <div className="flex items-center gap-4 min-w-0 flex-1 relative z-10">
                          <span className={`px-3 py-1.5 rounded-xl text-xs font-black tracking-wider shrink-0 border border-white/5 shadow-md ${typeInfo.color} ${typeInfo.bg}`}>
                            {typeInfo.label}
                          </span>
                          
                          <div className="min-w-0">
                            <p className="text-white font-bold truncate text-base hover:text-accent transition-colors duration-200" title={doc.filename}>{doc.filename}</p>
                            <p className="text-muted text-xs font-mono mt-0.5">
                              SIZE: {formatSize(doc.file_size)} | SECTIONS: {doc.chunk_count} | INGESTED: {new Date(doc.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        
                        {/* Right: Status metrics & Action blades */}
                        <div className="flex items-center justify-between md:justify-end gap-4 shrink-0 relative z-10">
                          <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold uppercase tracking-wider border border-white/5 ${statusInfo.color} ${statusInfo.bg}`}>
                            <StatusIcon className={`w-3.5 h-3.5 ${doc.status === "processing" ? "animate-spin text-accent" : ""}`} />
                            {doc.status}
                          </span>
                          
                          <button
                            onClick={() => handleDelete(doc)}
                            className="p-2 rounded-xl text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/20 transition-all duration-200 opacity-100 md:opacity-0 md:group-hover:opacity-100"
                            title="Decommission Core"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </GlassCard>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default DocumentsPage;