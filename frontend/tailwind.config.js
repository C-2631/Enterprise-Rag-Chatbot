/** @type {import('tailwindcss').Config} */
export default {

  // Tell Tailwind which files to scan for class names
  // It removes unused CSS in production — only the classes you actually use make it to the bundle
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {

      // ── Custom Colors ──────────────────────────────
      // These become usable as: bg-primary, text-accent, border-purple, etc.
      colors: {
        primary: "#0f172a",      // Sleek Slate 900
        secondary: "#1e293b",    // Sleek Slate 800
        tertiary: "#334155",     // Card/surface background Slate 700
        accent: "#38bdf8",       // Modern Light Blue 400
        purple: "#6366f1",       // Modern Indigo 500
        "purple-light": "#818cf8", // Modern Indigo 400
        danger: "#f43f5e",       // Rose 500
        success: "#10b981",      // Emerald 500
        muted: "#64748b",        // Slate 500
        "light-gray": "#cbd5e1", // Slate 300
      },

      // ── Custom Font ────────────────────────────────
      // Usage: font-sans (applied by default since we override 'sans')
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },

      // ── Custom Animations ──────────────────────────
      // Usage: animate-fade-in, animate-slide-up, etc.
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "pulse-glow": "pulseGlow 2s infinite",
        "float": "float 3s ease-in-out infinite",
      },

      // ── Keyframes for animations ───────────────────
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(0, 212, 255, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(0, 212, 255, 0.6)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },

      // ── Custom Backdrop Blur ───────────────────────
      // For glassmorphism: backdrop-blur-glass
      backdropBlur: {
        glass: "16px",
      },

      // ── Custom Box Shadow ──────────────────────────
      // For neomorphism and glass effects
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.3)",
        "neo-raised": "8px 8px 16px rgba(0,0,0,0.4), -8px -8px 16px rgba(255,255,255,0.05)",
        "neo-pressed": "inset 4px 4px 8px rgba(0,0,0,0.4), inset -4px -4px 8px rgba(255,255,255,0.05)",
        glow: "0 0 30px rgba(0, 212, 255, 0.3)",
        "glow-purple": "0 0 30px rgba(124, 58, 237, 0.3)",
      },
    },
  },

  plugins: [],
}