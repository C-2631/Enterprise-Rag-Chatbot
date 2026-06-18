/**
 * Landing Page
 * 
 * The first thing users see. Makes a strong visual impression with:
 * - Gradient heading
 * - Health status indicator (proves frontend↔backend connection)
 * - 3D constellation animation
 * - Liquid staggering transitions
 */

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { MessageSquare, Upload, Sparkles, ArrowRight, CheckCircle, XCircle, Loader } from "lucide-react";
import { checkHealth } from "../services/api";
import InteractiveHero from "../components/landing/InteractiveHero";
import GlassCard from "../components/ui/GlassCard";
import NeoButton from "../components/ui/NeoButton";

function LandingPage() {
  // Health status: "loading" | "connected" | "error"
  const [healthStatus, setHealthStatus] = useState("loading");
  const [healthData, setHealthData] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealthData(data);
        setHealthStatus("connected");
      } catch (error) {
        console.error("Backend health check failed:", error);
        setHealthStatus("error");
      }
    };
    fetchHealth();
  }, []);

  const features = [
    {
      icon: Upload,
      title: "Upload Documents",
      description: "Drag and drop PDFs, DOCX, TXT, or Markdown files. We handle the rest.",
    },
    {
      icon: Sparkles,
      title: "AI-Powered Search",
      description: "Semantic search finds answers by meaning, not just keywords.",
    },
    {
      icon: MessageSquare,
      title: "Chat Interface",
      description: "Ask questions in natural language. Get cited answers instantly.",
    },
  ];

  // Motion variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: "spring", stiffness: 80, damping: 15 }
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-transparent">
      
      {/* ── Hero Content ── */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 pt-28 pb-12 z-10 relative">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center max-w-4xl"
        >
          {/* Health Status Badge */}
          <motion.div 
            variants={itemVariants}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-full mb-8
              text-sm font-medium transition-colors duration-300
              ${healthStatus === "connected" 
                ? "bg-success/10 text-success border border-success/20 glow-accent" 
                : healthStatus === "error"
                ? "bg-danger/10 text-danger border border-danger/20"
                : "bg-accent/10 text-accent border border-accent/20"
              }
            `}
          >
            {healthStatus === "connected" && (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Backend Connected — v{healthData?.version}</span>
              </>
            )}
            {healthStatus === "error" && (
              <>
                <XCircle className="w-4 h-4" />
                <span>Backend Offline — Start the server</span>
              </>
            )}
            {healthStatus === "loading" && (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                <span>Connecting to backend...</span>
              </>
            )}
          </motion.div>

          {/* Main Heading */}
          <motion.h1 
            variants={itemVariants}
            className="text-5xl md:text-7xl font-extrabold text-center mb-6 tracking-tight leading-tight"
          >
            <span className="gradient-text">Enterprise RAG</span>
            <br />
            <span className="text-white drop-shadow-md">Chatbot</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p 
            variants={itemVariants}
            className="text-lg md:text-xl text-light-gray text-center max-w-2xl mb-10 leading-relaxed"
          >
            Upload your documents. Ask questions in plain English.
            Get accurate, cited answers powered by Google Gemini AI.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row gap-4"
          >
            <Link to="/chat" className="gradient-button flex items-center gap-2 shadow-glow">
              <MessageSquare className="w-5 h-5" />
              Start Chatting
              <ArrowRight className="w-4 h-4" />
            </Link>
            
            <Link to="/chat">
              <NeoButton className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload & Chat
              </NeoButton>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* ── Features Grid Section ── */}
      <section className="px-4 pb-20 z-10 relative">
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.6 }}
          className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            
            return (
              <GlassCard
                key={index}
                className="hover:scale-[1.03] duration-300 hover:shadow-glow group flex flex-col justify-between"
              >
                <div>
                  {/* Icon Wrapper */}
                  <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                    <IconComponent className="w-6 h-6 text-accent" />
                  </div>
                  
                  {/* Title */}
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {feature.title}
                  </h3>
                  
                  {/* Description */}
                  <p className="text-light-gray text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </GlassCard>
            );
          })}
        </motion.div>
      </section>
    </div>
  );
}

export default LandingPage;