# GapX AI - Skill Gap Intelligence Platform

GapX AI is an AI-driven Career Readiness & Skill Gap Analysis platform designed to help students transition from college-level fundamentals to placement readiness in tier-1 tech firms.

## Project Features

1. **Dashboard & Analytics**: Premium dark theme dashboards styled with custom glassmorphism. Evaluates metrics such as placement probability matching, resume ATS metrics, LeetCode question counts, and XP levels.
2. **AI Resume scoring**: Interactive analyzer which extracts details from PDF files or forms to calculate ATS rating, listing technical strengths/weaknesses and missing keywords.
3. **Dynamic Roadmap tree**: Personalized 8-stage preparation paths that check-off completed topics and update your readiness metrics dynamically.
4. **AI study notes**: Instantly compiles academic study sheets containing diagrams, definitions, code blocks, and FAQs into beautifully formatted PDF notes.
5. **Coding Workspace (LeetCode Clone)**: Live IDE console supporting Java, C++, JS, and Python execution with syntax validation, test verification, and real-time AI tutor hint debugging.
6. **Mock Interview & Behavior Mesh**: Web-cam video analyzer simulator which checks smile indexes, stress coordinates, attention metrics, and feeds conversational queries question-by-question.
7. **AI Career mentor bot**: Empathetic placement counselor bot responding to negotiation tips, technical guidelines, or project suggestions.

---

## 🛠️ Tech Stack

* **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, Recharts, Lucide Icons.
* **Backend**: FastAPI, SQLAlchemy, SQLite (Default, Postgres compatible), Pydantic Settings, JWT Auth.
* **AI Engine**: Google Gemini Pro API / OpenAI GPT-4 API (with fully responsive local backup mocks).
* **Code Verification**: Judge0 CE API / Local subprocess execution sandbox.
* **PDF Compiler**: ReportLab PDF generator engines.

---

## 🚀 Step-by-Step Setup Guide

### 1. Backend Server Setup
Ensure you have Python 3.8+ installed on your system.

```bash
# Navigate to the backend directory
cd backend

# Create a python virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install necessary python modules
pip install -r requirements.txt
```

#### Setup Environment Variables (Optional)
Copy `backend/.env.example` to `backend/.env`. Key settings: `ADMIN_EMAILS` (who is admin), `GOOGLE_CLIENT_ID` (real Google sign-in), `GEMINI_API_KEY` / `OPENAI_API_KEY` (AI), `JUDGE0_API_KEY` (sandboxed code execution, required in production). The frontend reads `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).

Older minimal example:
Create a `.env` file in the `backend/` folder:
```env
# Optional: Add Google Gemini or OpenAI Key for real AI generation (otherwise robust fallback mock is used)
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key

# Optional: RapidAPI Judge0 endpoint keys (otherwise local subprocess engine runs Python code)
JUDGE0_API_KEY=your-judge0-key
```

#### Start FastAPI Server
```bash
# Run server using uvicorn
uvicorn app.main:app --reload --port 8000
```
* Interactive API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

#### Run the tests
```bash
pip install -r requirements-dev.txt
pytest
```
The suite runs a reference solution for every coding problem through the real runner, and covers auth, interviews, roadmaps, resumes and XP rules.

### 2. Frontend client Setup
Ensure you have Node.js 18+ installed on your system.

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Run the development server
npm run dev
```
* Launch the web application: [http://localhost:3000](http://localhost:3000)

---

## 🎮 Gamification Rules
* **Onboarding**: Complete profile onboarding to gain `+100 XP`.
* **Resume analysis**: Upload or questionnaire compilation awards `+150 XP`.
* **Roadmap study**: Checking off topics inside Stages awards `+50 XP`.
* **Coding Practice**: Solve LeetCode problems (Easy: `+30 XP`, Medium: `+50 XP`, Hard: `+100 XP`).
* **Level Up**: Every `500 XP` increases your Placement level and unlocks new badges!
* **Mock Interviews**: Completing a full 5-question mock session awards `+300 XP`.
