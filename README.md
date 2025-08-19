# RoboAdvisor - Life Insurance Needs Assessment Platform

A comprehensive life insurance needs assessment platform built with Next.js frontend and FastAPI backend, designed to help users calculate their life insurance needs and receive product recommendations.

## 🏗️ Project Architecture

### Frontend (Next.js 15.4.1)
- **Framework**: Next.js with TypeScript and Tailwind CSS
- **Port**: 3000 (http://localhost:3000)
- **Key Features**: Multi-step assessment form, interactive charts, real-time calculations
- **UI Components**: React components with Chart.js for visualizations

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.12
- **Port**: 8000 (http://localhost:8000)
- **Key Features**: Life insurance needs calculation, product recommendations, cash value projections
- **API**: RESTful API with Pydantic models for data validation

## 🚀 Quick Start (Ubuntu)

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd RoboAdvisor

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install fastapi uvicorn pydantic python-dotenv
```

### 2. Backend Setup
```bash
# Ensure you're in the project root with venv activated
cd backend

# Install backend dependencies (if requirements.txt exists)
pip install -r requirements.txt

# Start the backend server
# From project root:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Or alternatively:
cd backend
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
RoboAdvisor/
├── backend/
│   ├── main.py              # FastAPI app configuration
│   ├── api.py               # API endpoints and business logic
│   └── schemas.py           # Pydantic models for data validation
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── assessment/
│   │   │   │   └── page.tsx # Main assessment page
│   │   │   ├── layout.tsx   # Root layout
│   │   │   └── globals.css  # Global styles
│   │   ├── components/
│   │   │   ├── Chatbot.tsx  # AI chatbot component
│   │   │   ├── ModeSelector.tsx
│   │   │   └── PortfolioPie.tsx
│   │   └── utils/           # Utility functions
│   ├── next.config.js       # Next.js configuration with API proxy
│   └── package.json         # Frontend dependencies
├── documentation/           # Project documentation
└── venv/                   # Python virtual environment
```

## 🔧 Configuration

### Backend Configuration
The backend uses environment variables (optional):
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `ALLOWED_ORIGINS`: CORS origins (default: http://localhost:3000)

### Frontend Configuration
- Next.js proxy configuration in `next.config.js` routes `/api/*` to backend
- Tailwind CSS for styling
- Chart.js for data visualizations

## 🎯 Current Features

### Assessment Flow
1. **Personal Details**: Age, marital status, dependents, health status
2. **Income & Expenses**: Monthly income, living expenses, inflation adjustment
3. **Debts & Obligations**: Mortgage, other debts, additional obligations
4. **Education Needs**: Children's education costs and preferences
5. **Final Expenses & Legacy**: Funeral expenses, desired legacy amount
6. **Existing Assets**: Savings, investments, current life insurance
7. **Results & Recommendations**: Coverage breakdown, product recommendations

### Key Functionality
- **Multi-step Assessment Form**: Progressive disclosure with validation
- **Real-time Calculations**: Instant coverage needs calculation
- **Product Recommendations**: JPM TermVest+ recommendations (Term vs IUL)
- **Interactive Visualizations**: 
  - Coverage breakdown pie chart
  - Cash value growth projections (for IUL)
  - Editable monthly savings field
- **Responsive Design**: Mobile-friendly interface

### API Endpoints
- `POST /api/calculate-needs-detailed`: Main assessment calculation
- `POST /api/product-faq`: Product information and FAQ
- `GET /health`: Health check endpoint

## 🧮 Calculation Logic

### Coverage Needs Calculation
1. **Income Replacement**: Monthly income × years × 75% replacement rate
2. **Debt Coverage**: Mortgage + other debts
3. **Education Funding**: Per-child education costs
4. **Final Expenses**: Funeral costs + legacy amount
5. **Gap Analysis**: Total needs - existing assets/coverage

### Product Recommendation Logic
- **Term Track**: For users who prefer lower initial costs or are price-sensitive
- **IUL Track**: For users interested in cash value growth and long-term planning
- **Duration**: Based on age, permanent coverage preference, and life events

### Cash Value Projections
- Uses industry-standard growth rates (6-8% annually)
- Accounts for premium payments and policy fees
- Shows projected cash value over 20-40 years

## 🎨 UI/UX Features

### Design System
- **Color Scheme**: Professional blue/gray palette
- **Typography**: Clean, readable fonts
- **Components**: Consistent card-based layout
- **Responsive**: Mobile-first design approach

### Interactive Elements
- **Progress Indicator**: Multi-step form progress
- **Real-time Validation**: Form field validation
- **Dynamic Charts**: Responsive Chart.js visualizations
- **Editable Fields**: Adjustable monthly savings amount

## 🔄 Development Workflow

### Backend Development
```bash
# Start backend with auto-reload
uvicorn backend.main:app --reload

# Kill existing processes on port 8000 (if needed)
fuser -k 8000/tcp || true
```

### Frontend Development
```bash
# Start frontend with Turbopack
npm run dev

# Build for production
npm run build
```

### API Testing
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🐛 Common Issues & Solutions

### Backend Issues
1. **ModuleNotFoundError**: Ensure running from project root with `uvicorn backend.main:app`
2. **Port Conflicts**: Use `fuser -k 8000/tcp` to kill existing processes
3. **Import Errors**: Check virtual environment activation

### Frontend Issues
1. **API Connection**: Verify backend is running on port 8000
2. **Build Errors**: Use `npm run dev` for development, avoid production build issues
3. **TypeScript Errors**: Check for missing type definitions

### Calculation Issues
1. **"Failed to calculate needs"**: Check backend logs for validation errors
2. **Incorrect Results**: Verify input data types and ranges
3. **Missing Fields**: Ensure all required fields are populated

## 📊 Data Models

### Frontend State Management
- React `useState` for form data
- Multi-step form with validation
- Real-time API calls for calculations

### Backend Data Validation
- Pydantic models for input validation
- Comprehensive error handling
- Type-safe API responses

## 🚀 Deployment Considerations

### Production Setup
- **Frontend**: Vercel deployment ready
- **Backend**: Docker containerization recommended
- **Database**: PostgreSQL for persistent storage (future)
- **Environment Variables**: Secure configuration management

### Security Considerations
- Input validation on both frontend and backend
- CORS configuration for production domains
- API rate limiting (future implementation)

## 🔮 Future Enhancements

### Planned Features
- User authentication and session management
- Persistent data storage
- Advanced scenario modeling
- Integration with insurance carrier APIs
- Mobile app development

### Technical Improvements
- Database integration
- Caching layer
- Advanced analytics
- A/B testing framework
- Performance optimization

## 📞 Support & Development

### For AI Assistants
When continuing development on this project:

1. **Always check the current state** of both frontend and backend before making changes
2. **Test API endpoints** using the Swagger UI at http://localhost:8000/docs
3. **Verify form validation** and error handling in the assessment flow
4. **Check for TypeScript errors** before committing changes
5. **Maintain the existing UI/UX patterns** and color scheme
6. **Update this README** when adding new features or changing architecture

### Key Files to Monitor
- `frontend/src/app/assessment/page.tsx` - Main assessment component
- `backend/api.py` - Core calculation logic
- `backend/schemas.py` - Data models and validation
- `frontend/next.config.js` - API proxy configuration

This documentation provides a comprehensive overview for anyone (human or AI) to understand, run, and continue development on the RoboAdvisor platform. 