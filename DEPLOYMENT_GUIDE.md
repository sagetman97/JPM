# 🚀 RoboAdvisor Deployment Guide

## Phase 1: Deploy Qdrant to Railway

### Option A: One-Click Deploy (Recommended)
1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "Deploy from Template"
4. Search for "Qdrant"
5. Click "Deploy"
6. Wait for deployment to complete
7. Go to the service dashboard
8. Copy the connection URL (it will look like: `https://your-qdrant-url.railway.app`)

### Option B: Manual Deploy
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Empty Project"
4. Click "Add Service" → "Database" → "Qdrant"
5. Wait for deployment
6. Copy the connection URL

### Update Environment Variables
Once you have the Qdrant URL, update your `.env` file:
```bash
QDRANT_HOST=your-qdrant-url.railway.app
QDRANT_PORT=6333
```

## Phase 2: Deploy Backend Services to Render

### Deploy Portfolio Tools (Port 8000)
1. Go to [Render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `portfolio-tools`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `API_HOST`: `0.0.0.0`
     - `API_PORT`: `$PORT`
     - `ALLOWED_ORIGINS`: `https://your-vercel-app.vercel.app`
     - `OPENAI_API_KEY`: `your-openai-key`
     - `SECRET_KEY`: `your-secret-key`
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Copy the service URL (e.g., `https://portfolio-tools.onrender.com`)

### Deploy Chatbot Service (Port 8001)
1. In Render, click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `chatbot-service`
   - **Root Directory**: `chatbot`
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `OPENAI_API_KEY`: `your-openai-key`
     - `TAVILY_API_KEY`: `your-tavily-key`
     - `LANGSMITH_API_KEY`: `your-langsmith-key`
     - `LANGSMITH_PROJECT`: `financial-advisor-assistant`
     - `QDRANT_HOST`: `your-qdrant-url.railway.app`
     - `QDRANT_PORT`: `6333`
4. Click "Create Web Service"
5. Wait for deployment (10-15 minutes)
6. Copy the service URL (e.g., `https://chatbot-service.onrender.com`)

## Phase 3: Deploy Frontend to Vercel

### Deploy to Vercel
1. Go to [Vercel.com](https://vercel.com)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Import your GitHub repository
5. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_BASE_URL`: `https://portfolio-tools.onrender.com`
     - `NEXT_PUBLIC_CHATBOT_URL`: `https://chatbot-service.onrender.com`
     - `NEXT_PUBLIC_CHATBOT_WS_URL`: `wss://chatbot-service.onrender.com`
6. Click "Deploy"
7. Wait for deployment (2-3 minutes)
8. Copy your Vercel URL (e.g., `https://your-app.vercel.app`)

## Phase 4: Update CORS URLs

### Update Backend CORS
Once you have your Vercel URL, update the CORS settings:

1. **Portfolio Tools** (`backend/main.py` line 13):
   ```python
   ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://your-actual-vercel-url.vercel.app').split(',')
   ```

2. **Chatbot Service** (`chatbot/main.py` line 38):
   ```python
   allow_origins=["https://your-actual-vercel-url.vercel.app"],
   ```

3. **Redeploy both services** on Render after making these changes

## Phase 5: Test Production

### Test Checklist
- [ ] Frontend loads at Vercel URL
- [ ] Portfolio assessment form works
- [ ] Chatbot WebSocket connects
- [ ] File upload works
- [ ] PDF generation works
- [ ] All API endpoints respond

### Troubleshooting
- Check Render logs for backend issues
- Check Vercel function logs for frontend issues
- Verify environment variables are set correctly
- Test WebSocket connection in browser dev tools

## Cost Summary
- **Vercel**: $0 (Hobby plan)
- **Render**: $14/month (2 services × $7)
- **Railway**: $5/month (Qdrant)
- **Total**: ~$19/month

## Next Steps
1. Set up custom domains (optional)
2. Configure monitoring and alerts
3. Set up automated backups
4. Implement CI/CD pipeline
