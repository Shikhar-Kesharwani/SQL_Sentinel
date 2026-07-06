<div align="center">
  <img src="frontend/public/logo.png" alt="SQL Sentinel Logo" width="120" />
  <h1>🛡️ SQL Sentinel</h1>
  <p><strong>The Ultimate AI-Powered SQL Dashboard & RAG Assistant</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=googlebard&logoColor=white" alt="Gemini AI" />
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  </p>
</div>

---

## 🚀 Overview

**SQL Sentinel** is an enterprise-grade, 100% open-source intelligent database assistant. It allows you to chat with your database in plain English, automatically generates robust SQL queries via LLMs (Google Gemini), securely executes them, and dynamically renders stunning visualizations.

Originally inspired by **Vanna AI**, SQL Sentinel achieves complete feature parity while delivering a vastly superior, modern UI/UX featuring glassmorphism, micro-animations, and an ultra-premium React frontend.

---

## ✨ Features

- 🧠 **Retrieval-Augmented Generation (RAG):** Train the AI context manager on custom SQL examples and database documentation to drastically improve query accuracy over time.
- 📊 **Dynamic Visualizations:** Instantly transforms query results into beautiful, interactive Bar, Line, and Pie charts using Recharts.
- 🔌 **Dynamic Database Connection:** Connect to any local SQLite database on the fly—the system instantly extracts and learns the schema.
- 💾 **Saved Dashboards:** Pin your favorite queries and charts to a persistent dashboard for quick reporting.
- ✏️ **Edit & Run Custom SQL:** Full power-user control. If the AI hallucinates, simply drop into the live code editor, tweak the SQL, and re-run the query in the same context.
- 📥 **Export Everything:** Instantly download raw data as CSV or export your high-res charts as PNG images.
- 🛡️ **Safety Guardrails:** Built-in safeguards prevent dangerous SQL execution (e.g., `DROP`, `DELETE`) before they ever touch your database.

---

## 🏗️ Architecture

```mermaid
graph TD
    A[User (React Frontend)] -->|Plain English Question| B(FastAPI Backend)
    B -->|Fetch Relevant Context| C[(ChromaDB Vector Store)]
    C -.->|Returns Training Examples| B
    B -->|Prompt (Schema + Context + Question)| D[Gemini LLM]
    D -.->|Generated SQL & Chart Config| B
    B -->|Execute Query| E[(SQLite Database)]
    E -.->|Raw Data| B
    B -->|Returns JSON & Config| A
    A -->|Render| F[Data Table & Recharts UI]
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+
- Node.js (v16+)
- Gemini API Key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file and add your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the backend
python -m uvicorn main:app --reload --port 8080
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# Start the React development server
npm start
```
*The app will automatically launch at `http://localhost:3000`*

---

## 🎨 UI/UX Showcase

Our interface was completely redesigned from the ground up to feel like a premium Silicon Valley product. 
- **Glassmorphism:** Frosted glass panels and stunning gradients.
- **Micro-interactions:** Everything from the logo to the chart containers physically lifts off the screen when hovered, guided by smooth cubic-bezier transitions.
- **Smart Formatting:** Massive pie charts are automatically grouped, and decimals are cleanly truncated to maintain visual harmony.

---

<div align="center">
  <i>Built with ❤️ for modern data analysts.</i>
</div>
