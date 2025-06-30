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

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire project contents into the container at /app
COPY . /app/

# Install Python dependencies (both main and Streamlit requirements)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_streamlit.txt

# Create a simple startup script to run both services
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Starting VentureBots AI Coaching services..."\n\
\n\
# Start ADK API server in background from the app directory\n\
echo "📡 Starting ADK API server on port 8000..."\n\
cd /app\n\
adk api_server --port 8000 &\n\
ADK_PID=$!\n\
\n\
# Wait a moment for ADK to start\n\
sleep 5\n\
\n\
# Check if ADK is running\n\
if ! kill -0 $ADK_PID 2>/dev/null; then\n\
    echo "❌ ADK server failed to start"\n\
    exit 1\n\
fi\n\
\n\
echo "✅ ADK API server started successfully"\n\
\n\
# Start Streamlit on port 80 (foreground)\n\
echo "🎨 Starting Streamlit frontend on port 80..."\n\
exec streamlit run streamlit_chat.py --server.port 80 --server.address 0.0.0.0 --server.headless true\n\
' > /app/start_services.sh && chmod +x /app/start_services.sh

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables if needed by your application or ADK
# ENV GOOGLE_CLOUD_PROJECT="your-gcp-project"
# ENV GOOGLE_CLOUD_LOCATION="your-gcp-location"
# ENV GOOGLE_GENAI_USE_VERTEXAI="True" # If using Vertex AI

# Start the services
CMD ["/app/start_services.sh"] 