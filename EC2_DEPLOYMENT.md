# 🚀 RoboAdvisor EC2 Deployment Guide

This guide walks you through deploying the RoboAdvisor application on AWS EC2 using Docker Compose.

## 📋 Prerequisites

- AWS EC2 instance running Ubuntu 24.04 LTS
- SSH access to your EC2 instance
- Docker and Docker Compose installed
- Your API keys (OpenAI, Tavily, etc.)

## 🏗️ Architecture

The EC2 deployment runs all services on a single instance:

```
┌─────────────────────────────────────┐
│           EC2 Instance               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ Qdrant  │ │ Backend │ │Chatbot  │ │
│  │ :6333   │ │ :8000   │ │ :8001   │ │
│  └─────────┘ └─────────┘ └─────────┘ │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/sagetman97/JPM.git
cd JPM
```

### 2. Set Up Environment Variables
```bash
cp env.example .env
nano .env  # Edit with your actual values
```

### 3. Deploy Application
```bash
./deploy.sh
```

## 🔧 Manual Deployment

### 1. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit with your values
nano .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - Random secret for backend
- `FRONTEND_URL` - Your frontend URL (update with EC2 IP)

### 2. Start Services
```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Deployment
```bash
# Check Qdrant
curl http://localhost:6333/health

# Check Backend
curl http://localhost:8000/health

# Check Chatbot
curl http://localhost:8001/health
```

## 🌐 Accessing Services

Once deployed, your services will be available at:

- **Qdrant**: `http://YOUR_EC2_IP:6333`
- **Backend**: `http://YOUR_EC2_IP:8000`
- **Chatbot**: `http://YOUR_EC2_IP:8001`

## 🔧 Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chatbot
docker-compose logs -f backend
docker-compose logs -f qdrant
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart chatbot
```

### Stop Services
```bash
docker-compose down
```

### Update Application
```bash
git pull
docker-compose up -d --build
```

## 🗄️ Data Persistence

- **Qdrant Data**: Stored in Docker volume `qdrant_data`
- **RAG Documents**: Loaded from `chatbot/RAG Documents/`
- **Session Data**: Stored in Qdrant collections

## 🔒 Security Considerations

- Update security group to restrict access to specific IPs
- Use HTTPS with reverse proxy (Nginx) for production
- Regularly update system packages
- Monitor logs for suspicious activity

## 🚨 Troubleshooting

### Services Not Starting
```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker-compose logs

# Check disk space
df -h
```

### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8001
sudo netstat -tlnp | grep :6333
```

### Memory Issues
```bash
# Check memory usage
free -h
docker stats
```

## 📊 Monitoring

### Health Checks
All services include health check endpoints:
- Qdrant: `/health`
- Backend: `/health`
- Chatbot: `/health`

### Resource Usage
```bash
# Container resource usage
docker stats

# System resource usage
htop
```

## 🔄 Updates and Maintenance

### Regular Updates
1. Pull latest code: `git pull`
2. Rebuild containers: `docker-compose up -d --build`
3. Check logs: `docker-compose logs -f`

### Backup Qdrant Data
```bash
# Create backup
docker run --rm -v roboadvisor_qdrant_data:/data -v $(pwd):/backup ubuntu tar czf /backup/qdrant-backup.tar.gz -C /data .

# Restore backup
docker run --rm -v roboadvisor_qdrant_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/qdrant-backup.tar.gz -C /data
```

## 💰 Cost Optimization

- Use `t3.medium` or `t3.large` instances
- Enable EBS optimization
- Use Spot instances for development
- Monitor usage with CloudWatch

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `cat .env`
3. Check service health: `curl http://localhost:PORT/health`
4. Review this documentation
