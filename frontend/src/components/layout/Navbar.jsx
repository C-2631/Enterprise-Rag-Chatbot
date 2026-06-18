/**
 * Navbar Component
 * 
 * A glassmorphic navigation bar fixed at the top of the page.
 * Uses our custom .glass class from index.css for the frosted effect.
 * 
 * DESIGN DECISIONS:
 * - Fixed position: stays visible while scrolling
 * - z-50: renders above all other content
 * - Glass effect: matches our modern dark theme
 * - Responsive: works on mobile and desktop
 */

import { Link, useLocation } from "react-router-dom";
import { MessageSquare, FileText, Home, Bot } from "lucide-react";

function Navbar() {
  // useLocation tells us which page we're on
  // We use this to highlight the active nav link
  const location = useLocation();

  // Helper: check if a path is the current page
  const isActive = (path) => location.pathname === path;

  // Define our navigation links in one place
  // Each has: path (URL), label (display text), icon (Lucide component)
  const navLinks = [
    { path: "/", label: "Home", icon: Home },
    { path: "/chat", label: "Chat", icon: MessageSquare },
  ];

  return (
    <nav className="glass fixed top-0 left-0 right-0 z-50 px-6 py-4">
      {/* 
        Flex container: logo on left, links on right
        max-w-7xl: limits width on ultra-wide screens
        mx-auto: centers the content
      */}
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* ── Logo / Brand ── */}
        <Link to="/" className="flex items-center gap-2 group">
          {/* Bot icon with accent color */}
          <Bot className="w-8 h-8 text-accent group-hover:text-purple-light transition-colors" />
          
          {/* App name with gradient */}
          <span className="text-xl font-bold gradient-text">
            RAG Chatbot
          </span>
        </Link>

        {/* ── Navigation Links ── */}
        <div className="flex items-center gap-1">
          {navLinks.map((link) => {
            // Get the icon component (e.g., Home, MessageSquare)
            const IconComponent = link.icon;
            
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  text-sm font-medium transition-all duration-200
                  ${isActive(link.path)
                    ? "bg-accent/20 text-accent"         // Active: highlighted
                    : "text-light-gray hover:text-white hover:bg-white/5"  // Inactive: subtle
                  }
                `}
              >
                <IconComponent className="w-4 h-4" />
                <span className="hidden sm:inline">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;