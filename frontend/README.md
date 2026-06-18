# React + Vite
# 🚀 Frontend — Enterprise RAG Chatbot
This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=Vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
Currently, two official plugins are available:
This directory contains the **Frontend application** for the Enterprise RAG Chatbot. It is a highly optimized, modern React single-page application (SPA) built using Vite for lightning-fast development and optimized production builds.
- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)
## ✨ UI / UX Highlights
## React Compiler
- **Premium Modern Theme**: Features a sleek Slate & Indigo color palette, drawing inspiration from top-tier enterprise SaaS platforms.
- **Glassmorphism & Neomorphism**: Uses advanced Tailwind utility classes to create elegant frosted glass cards and floating, pressed UI elements.
- **Interactive 3D Background**: The landing page features a dynamic, interactive neural-network style particle matrix built using an HTML5 Canvas, which reacts smoothly to mouse movements.
- **Real-Time Streaming Interface**: The Chat UI handles Server-Sent Events (SSE) seamlessly, rendering AI tokens onto the screen exactly like ChatGPT.
- **Advanced Markdown Support**: Uses `react-markdown` along with `remark-gfm` (for tables) and `rehype-katex` (for LaTeX equations) to perfectly render complex AI outputs.
The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.
## 📁 Directory Structure
Note: This will impact Vite dev & build performances.
```text
frontend/
├── index.html           # Main HTML entry point
├── package.json         # Dependencies and scripts
├── tailwind.config.js   # Custom colors, animations, and shadows
├── src/
│   ├── main.jsx         # React DOM rendering
│   ├── App.jsx          # Application Shell and Routing
│   ├── index.css        # Global CSS, gradients, animations
│   ├── components/
│   │   ├── chat/        # Chat bubbles, input box, markdown renderer
│   │   ├── layout/      # Sidebar, headers, layout shells
│   │   └── landing/     # Interactive 3D Hero, Feature cards
│   ├── pages/           
│   │   ├── LandingPage.jsx # The welcome screen
│   │   └── ChatPage.jsx    # The main chatbot interface
│   └── services/        # API integration (fetching, deleting sessions)
```
## Expanding the ESLint configuration
## 🛠️ Getting Started
If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher recommended)
### Installation
1. Open a terminal in the `frontend` directory.
2. Install the necessary NPM packages:
```bash
npm install
```
### Running the Development Server
Start the Vite development server:
```bash
npm run dev
```
The application will automatically start and can be viewed at [http://localhost:5173](http://localhost:5173).
> **Note:** Ensure the backend FastAPI server is running simultaneously on `localhost:8000`, as the frontend relies on it for all AI and document processing endpoints.
### Building for Production
To create an optimized, minified bundle ready for deployment:
```bash
npm run build
```
This will generate a `dist/` folder containing your production-ready static files.
