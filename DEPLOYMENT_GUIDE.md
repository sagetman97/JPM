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

### Get Your Qdrant Connection Details
Once deployed, note down:
- **Qdrant URL**: `https://your-qdrant-url.railway.app`
- **Port**: `6333` (default)
- **Collection Name**: `robo_advisor_rag` (we'll create this)

## Phase 2: Deploy Backend Services to Render

### Important Notes Before Starting
- **Docker Required**: Both services use Docker, so select "Docker" as the language
- **Health Check**: Both services have `/health` endpoints for monitoring
- **Environment Variables**: You'll need API keys for OpenAI (Tavily optional)
- **CORS**: Update `ALLOWED_ORIGINS` after getting your Vercel URL

### Render Form Field Reference
When creating services, you'll see these fields in the Render form:
- **Name**: Unique service name (e.g., `portfolio-tools`)
- **Project**: Optional - can create new project or leave empty
- **Language**: Select `Docker` (not Python)
- **Branch**: `main`
- **Region**: `Oregon (US West)` (or your preferred region)
- **Root Directory**: `backend` or `chatbot`
- **Instance Type**: `Free` for testing, `Starter ($7/month)` for production
- **Docker Build Context Directory**: `backend/` or `chatbot/`
- **Dockerfile Path**: `backend/Dockerfile` or `chatbot/Dockerfile`
- **Health Check Path**: `/health`
- **Environment Variables**: Add each variable individually

### Deploy Portfolio Tools (Port 8000)
1. Go to [Render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository (`sagetman97/JPM`)
5. Configure the service:
   - **Name**: `portfolio-tools`
   - **Language**: `Docker` (since we have Dockerfile)
   - **Branch**: `main`
   - **Region**: `Oregon (US West)` (or your preferred region)
   - **Root Directory**: `backend`
   - **Instance Type**: `Starter ($7/month)` or `Free` for testing
   - **Docker Build Context Directory**: `backend/`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Health Check Path**: `/health` (matches our endpoint)
   - **Auto-Deploy**: `On Commit` (enabled)
6. **Environment Variables** (click "Add Environment Variable" for each):
   - `API_HOST`: `0.0.0.0`
   - `ALLOWED_ORIGINS`: `https://your-vercel-app.vercel.app` (update with actual Vercel URL later)
   - `OPENAI_API_KEY`: `your-openai-key-here`
   - `SECRET_KEY`: `your-secret-key-here` (generate a random string)
   - **Note**: `PORT` is automatically provided by Render - don't set it manually
7. Click "Deploy web service"
8. Wait for deployment (5-10 minutes)
9. Copy the service URL (e.g., `https://portfolio-tools.onrender.com`)

### Deploy Chatbot Service (Port 8001)
1. In Render, click "New" → "Web Service"
2. Connect your GitHub repository (`sagetman97/JPM`)
3. Configure the service:
   - **Name**: `chatbot-service`
   - **Language**: `Docker` (since we have Dockerfile)
   - **Branch**: `main`
   - **Region**: `Oregon (US West)` (same region as portfolio-tools)
   - **Root Directory**: `chatbot`
   - **Instance Type**: `Starter ($7/month)` or `Free` for testing
   - **Docker Build Context Directory**: `chatbot/`
   - **Dockerfile Path**: `chatbot/Dockerfile`
   - **Health Check Path**: `/health` (matches our endpoint)
   - **Auto-Deploy**: `On Commit` (enabled)
4. **Environment Variables** (click "Add Environment Variable" for each):
   - `OPENAI_API_KEY`: `your-openai-key-here`
   - `QDRANT_HOST`: `your-qdrant-url.railway.app` (from Phase 1)
   - `QDRANT_PORT`: `6333`
   - `QDRANT_COLLECTION_NAME`: `robo_advisor_rag`
   - `TAVILY_API_KEY`: `your-tavily-key-here` (optional - for external search)
   - `LANGSMITH_API_KEY`: `your-langsmith-key-here` (optional - for monitoring)
   - `LANGSMITH_PROJECT`: `robo-advisor-chatbot` (optional)
5. Click "Deploy web service"
6. Wait for deployment (10-15 minutes)
7. Copy the service URL (e.g., `https://chatbot-service.onrender.com`)

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
     - `NEXT_PUBLIC_CHATBOT_URL`: `https://chatbot-service-14zf.onrender.com`
     - `NEXT_PUBLIC_CHATBOT_WS_URL`: `wss://chatbot-service-14zf.onrender.com`
6. Click "Deploy"
7. Wait for deployment (2-3 minutes)
8. Copy your Vercel URL (e.g., `https://your-app.vercel.app`)

## Phase 4: Update CORS URLs

### Update Backend CORS
Once you have your Vercel URL, update the CORS settings:

1. **Portfolio Tools** - Update environment variable in Render dashboard:
   - Go to your `portfolio-tools` service
   - Click "Environment" tab
   - Update `ALLOWED_ORIGINS` to: `https://your-actual-vercel-url.vercel.app`
   - Click "Save Changes"

2. **Chatbot Service** - Update environment variable in Render dashboard:
   - Go to your `chatbot-service` service  
   - Click "Environment" tab
   - Add new environment variable:
     - **Key**: `ALLOWED_ORIGINS`
     - **Value**: `https://your-actual-vercel-url.vercel.app`
   - Click "Save Changes"

3. **Redeploy both services** - Render will automatically redeploy when you save environment changes

## Phase 5: Test Production

### Test Checklist
- [ ] Frontend loads at Vercel URL
- [ ] Portfolio assessment form works
- [ ] Chatbot WebSocket connects
- [ ] File upload works
- [ ] PDF generation works
- [ ] All API endpoints respond

### Troubleshooting

#### Render Deployment Issues
- **Build Fails**: Check Docker logs in Render dashboard
- **Service Won't Start**: Verify all environment variables are set
- **Health Check Fails**: Ensure `/health` endpoint is accessible
- **CORS Errors**: Update `ALLOWED_ORIGINS` with correct Vercel URL
- **Memory Issues**: Upgrade to paid instance if using Free tier

#### Common Render Configuration Mistakes
- ❌ **Wrong Language**: Must select "Docker" not "Python"
- ❌ **Wrong Root Directory**: Must be `backend` or `chatbot`
- ❌ **Missing Environment Variables**: All required vars must be set
- ❌ **Wrong Health Check Path**: Must be `/health` not `/healthz`

#### Vercel Issues
- Check Vercel function logs for frontend issues
- Verify environment variables are set correctly
- Test WebSocket connection in browser dev tools

#### Testing Commands
```bash
# Test portfolio tools
curl https://portfolio-tools.onrender.com/health

# Test chatbot service  
curl https://chatbot-service.onrender.com/health

# Test WebSocket (in browser console)
const ws = new WebSocket('wss://chatbot-service.onrender.com/ws/chat/test');
```

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
