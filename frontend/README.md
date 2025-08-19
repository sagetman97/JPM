# Everly x JPMorgan RoboAdvisor

A next-generation, AI-powered life insurance needs assessment and education platform for financial advisors and clients.

## Features
- **Needs Assessment Calculator:** Simple, guided form for calculating life insurance needs (term/IUL) with instant recommendations.
- **Conversational AI Chatbot:** Ask questions about products, coverage, and concepts with suggested questions and multi-turn support.
- **Scenario Planning:** Visualize how changes in income, dependents, or coverage affect recommendations, with interactive charts.
- **Portfolio Integration:** See how insurance fits into a sample portfolio with dynamic pie charts.
- **Advisor Mode:** File upload (CSV/XLSX) for bulk data entry, shareable links, and export to CSV/PDF for compliance and collaboration.
- **Client Mode:** Save/load progress, revisit recommendations, and export results.
- **Accessibility & Mobile-First Design:** WCAG 2.1 AA compliant, fully responsive, and cross-browser tested.

## Getting Started

### Prerequisites
- Node.js (v18+ recommended)
- Python 3.8+ (for backend, FastAPI)
- (Optional) Vercel CLI for deployment

### Local Development
1. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd RoboAdvisor
   ```
2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```
3. **Install backend dependencies:**
   ```bash
   cd ../
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install fastapi uvicorn python-dotenv
   ```
4. **Set up environment variables:**
   - Create `.env` in the project root:
     ```
     API_HOST=0.0.0.0
     API_PORT=8000
     ALLOWED_ORIGINS=http://localhost:3000
     SECRET_KEY=your_secret_key_here
     ```
   - Create `frontend/.env.local`:
     ```
     NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
     ```
5. **Run the backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```
6. **Run the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
7. **Open in browser:**
   - Go to [http://localhost:3000](http://localhost:3000)

### Deployment (Vercel)
- The frontend is ready for Vercel. Set `NEXT_PUBLIC_API_BASE_URL` to your backend URL in Vercel project settings.
- Backend can be deployed to any cloud (Azure, AWS, GCP, etc.) or as a Vercel serverless function (with minor adaptation).

## Documentation
- See the `/documentation` folder for project vision, UX, technical architecture, and roadmap.

## Demo Flows
- **Advisor:** Switch to Advisor Mode, upload a file, run scenarios, export/share results.
- **Client:** Enter info, run calculator, save/load progress, ask chatbot, export results.

## Contact
- For questions or feedback, contact the Everly or JPMorgan project leads.
