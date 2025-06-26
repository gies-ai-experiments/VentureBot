# How to Build and Run this Dockerfile:
#
# 1. Ensure Docker is installed on your system.
# 2. Open your terminal and navigate to the root directory of this project (where this Dockerfile is located).
# 3. Build the Docker image:
#    docker build -t venturebots .
# 4. Run the Docker container (ensure your .env file is in the same directory):
#    docker run -d -p 80:80 --env-file .env --name venturebots-app venturebots
# 5. Access the application in your browser at http://<YOUR_VM_IP_ADDRESS> or http://localhost if running locally.
#    Frontend (Streamlit): http://<YOUR_VM_IP_ADDRESS>
#    Backend API: http://<YOUR_VM_IP_ADDRESS>/api

# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Install system dependencies including nginx and supervisor
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire project contents into the container at /app
COPY . /app/

# Install Python dependencies (both main and Streamlit requirements)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_streamlit.txt

# Configure nginx
RUN echo 'server {\n\
    listen 80;\n\
    server_name _;\n\
    client_max_body_size 100M;\n\
    \n\
    # Health check endpoint\n\
    location /health {\n\
        access_log off;\n\
        return 200 "healthy\\n";\n\
        add_header Content-Type text/plain;\n\
    }\n\
    \n\
    # Backend API (ADK) - must come before / location\n\
    location /api/ {\n\
        rewrite ^/api/(.*) /$1 break;\n\
        proxy_pass http://127.0.0.1:8000;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
        proxy_read_timeout 300s;\n\
        proxy_connect_timeout 75s;\n\
    }\n\
    \n\
    # Frontend (Streamlit)\n\
    location / {\n\
        proxy_pass http://127.0.0.1:8501;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
        proxy_cache_bypass $http_upgrade;\n\
        proxy_read_timeout 300s;\n\
        proxy_connect_timeout 75s;\n\
    }\n\
}\n\
' > /etc/nginx/sites-available/default

# Configure supervisor to manage both services
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
loglevel=info\n\
\n\
[program:adk_server]\n\
command=sh -c "cd /app/agentlab_v5 && adk api_server --port 8000 --host 127.0.0.1"\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/adk_error.log\n\
stdout_logfile=/var/log/adk_access.log\n\
priority=100\n\
\n\
[program:streamlit]\n\
command=streamlit run streamlit_chat.py --server.port 8501 --server.address 127.0.0.1 --server.headless true\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/streamlit_error.log\n\
stdout_logfile=/var/log/streamlit_access.log\n\
environment=STREAMLIT_SERVER_PORT="8501"\n\
priority=200\n\
\n\
[program:nginx]\n\
command=nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/nginx_error.log\n\
stdout_logfile=/var/log/nginx_access.log\n\
priority=300\n\
' > /etc/supervisor/conf.d/supervisord.conf

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables if needed by your application or ADK
# ENV GOOGLE_CLOUD_PROJECT="your-gcp-project"
# ENV GOOGLE_CLOUD_LOCATION="your-gcp-location"
# ENV GOOGLE_GENAI_USE_VERTEXAI="True" # If using Vertex AI

# Start supervisor to manage all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 