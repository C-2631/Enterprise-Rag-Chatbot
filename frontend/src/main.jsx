/**
 * Application Entry Point
 * 
 * This is the FIRST JavaScript file that runs.
 * It does one thing: mount the React app into the DOM.
 * 
 * StrictMode: A development helper that:
 * - Warns about unsafe lifecycle methods
 * - Warns about deprecated APIs
 * - Detects unexpected side effects (runs effects twice in dev)
 * - Has ZERO impact in production
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Import global styles (Tailwind + our custom CSS)
import "./index.css";

// Import the root App component
import App from "./App.jsx";

// Find the <div id="root"> in index.html and mount React into it
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);