# Hybrid Deployment Guide: Vercel + Railway

## Overview
- **Frontend (Chainlit)**: Deployed to Vercel
- **Backend (ADK)**: Deployed to Railway

## Step 1: Deploy Backend to Railway

1. **Create Railway Account**: Go to [railway.app](https://railway.app) and sign up with GitHub

2. **Create New Project**: 
   - Click "New Project"
   - Select "Deploy from GitHub repo" 
   - Choose this repository
   - Railway will auto-detect the Dockerfile

3. **Configure Environment Variables**:
   - Go to your Railway project > Variables tab
   - Add all your current `.env` variables (Google API keys, etc.)
   - Railway will automatically provide `PORT` variable

4. **Deploy**: Railway will automatically build and deploy using `docker/Dockerfile.backend`

## Step 2: Deploy Frontend to Vercel

1. **Create Vercel Account**: Go to [vercel.com](https://vercel.com) and sign up with GitHub

2. **Import Project**:
   - Click "New Project"
   - Select this repository
   - Vercel will auto-detect the `vercel.json` configuration

3. **Configure Environment Variables**:
   - Go to Project Settings > Environment Variables
   - Add: `ADK_BACKEND_URL` = `https://your-railway-app.railway.app`
   - Get the Railway URL from your Railway dashboard

4. **Deploy**: Vercel will automatically deploy the Chainlit frontend

## Step 3: Test the Deployment

1. Visit your Vercel URL (e.g., `https://venturebot.vercel.app`)
2. Check that the chat interface loads
3. Send a test message to verify backend connectivity

## Automatic Deployments

Both platforms will automatically redeploy when you push to the main branch:
- **Railway**: Rebuilds backend container
- **Vercel**: Rebuilds frontend

## Environment Variables Needed

### Railway (Backend)
```
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_GENAI_API_KEY=your-key
# ... other backend env vars from your current .env
```

### Vercel (Frontend)  
```
ADK_BACKEND_URL=https://your-railway-app.railway.app
```

## Troubleshooting

- **Connection errors**: Check that `ADK_BACKEND_URL` points to your Railway app
- **Backend not starting**: Check Railway logs for ADK server errors
- **Frontend not loading**: Check Vercel function logs

## Costs
- **Railway**: Free tier includes 500 hours/month + $5 credit
- **Vercel**: Free tier includes 100GB bandwidth + 1000 function executions