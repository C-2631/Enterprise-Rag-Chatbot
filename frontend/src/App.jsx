/**
 * App Component — The Root of the Application
 * 
 * This is the top-level component that:
 * 1. Sets up client-side routing (BrowserRouter)
 * 2. Renders the Navbar on every page
 * 3. Defines which page component renders for each URL
 * 4. Adds the toast notification container
 * 
 * ROUTING:
 * - "/"           → LandingPage
 * - "/chat"       → ChatPage (coming in Phase 4)
 * - "/documents"  → DocumentsPage (coming in Phase 2)
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";

// Layout components
import Navbar from "./components/layout/Navbar";

// Page components
import LandingPage from "./pages/LandingPage";
import ChatPage from "./pages/ChatPage";
import InteractiveHero from "./components/landing/InteractiveHero";

function App() {
  return (
    // BrowserRouter enables client-side routing
    // (URL changes without full page reload)
    <BrowserRouter>
      {/* 
        Toast notifications container
        position: top-right corner
        Styled to match our dark theme
      */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#1a1a2e",
            color: "#ffffff",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          },
          success: {
            iconTheme: { primary: "#0cce6b", secondary: "#ffffff" },
          },
          error: {
            iconTheme: { primary: "#e94560", secondary: "#ffffff" },
          },
        }}
      />

      {/* Global 3D Interactive Background */}
      <div className="fixed inset-0 z-[-1]">
        <InteractiveHero />
      </div>

      {/* Navbar appears on every page */}
      <Navbar />

      {/* Route definitions — which component to show for which URL */}
      <main className="relative z-0">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          
          {/* 
            Placeholder routes — these pages will be built in later phases
            For now, they show simple placeholder text
          */}
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;