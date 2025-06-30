# Fix Remote Deployment Configuration

## Issue Identified
- Frontend (Streamlit) is accessible at https://venturebots.ncsa.ai
- Backend (ADK API) is NOT accessible externally
- Frontend can't connect to backend, causing "no text response" error

## Solution 1: Expose Backend Port (Recommended)

### Update docker-compose.yml for remote deployment:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"  # Expose backend externally
    env_file:
      - .env
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    environment:
      # Use public URL for remote deployment
      - ADK_BACKEND_URL=https://venturebots.ncsa.ai:8000
    depends_on:
      - backend
    restart: unless-stopped
```

### If using cloud deployment (Heroku, AWS, etc.):

1. **Deploy backend as separate service** on port 8000
2. **Update frontend environment variable** to point to backend URL
3. **Ensure both services can communicate**

## Solution 2: Reverse Proxy Configuration

If you prefer not to expose port 8000 publicly, configure nginx/reverse proxy:

```nginx
server {
    listen 80;
    server_name venturebots.ncsa.ai;

    # Frontend (Streamlit)
    location / {
        proxy_pass http://frontend:80;
    }

    # Backend (ADK API)
    location /api/ {
        proxy_pass http://backend:8000/;
    }
}
```

Then update frontend environment:
```yaml
environment:
  - ADK_BACKEND_URL=https://venturebots.ncsa.ai/api
```

## Solution 3: Single Container Deployment

Use the main Dockerfile that runs both services:

```bash
# Build and deploy single container
docker build -t venturebots .
docker run -p 80:80 --env-file .env venturebots
```

This runs both frontend and backend in same container.

## Testing the Fix

After implementing any solution, test with:

```bash
# Test backend accessibility
curl https://venturebots.ncsa.ai:8000/docs

# Or if using reverse proxy:
curl https://venturebots.ncsa.ai/api/docs

# Test session creation
curl -X POST https://venturebots.ncsa.ai:8000/apps/manager/users/test/sessions/test \
  -H "Content-Type: application/json" \
  -d '{"state": {"test": true}}'
```

## Recommended Implementation

1. **Expose port 8000** in your deployment platform
2. **Update ADK_BACKEND_URL** to use public URL
3. **Redeploy both services**
4. **Test backend accessibility**

The "no text response" error will be fixed once the frontend can properly connect to the backend API.