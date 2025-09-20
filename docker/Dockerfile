# How to Build and Run this Dockerfile:
#
# 1. Ensure Docker is installed on your system.
# 2. Open your terminal and navigate to the root directory of this project (where this Dockerfile is located).
# 3. Build the Docker image:
#    docker build -t venturebots .
# 4. Run the Docker container (ensure your .env file is in the same directory):
#    docker run -d -p 80:80 --env-file .env --name venturebots-app venturebots
# 5. Access the application in your browser at http://<YOUR_VM_IP_ADDRESS> or http://localhost if running locally.
#    Frontend (Chainlit): http://<YOUR_VM_IP_ADDRESS>
#    Backend API: http://<YOUR_VM_IP_ADDRESS>/api

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire project contents into the container at /app
COPY . /app/

# Install Python dependencies (backend + Chainlit frontend)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-frontend.txt

# Create a simple startup script to run both services
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Starting VentureBots AI Coaching services..."\n\
\n\
cd /app\n\
echo "📡 Starting FastAPI backend on port 8000..."\n\
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
BACKEND_PID=$!\n\
sleep 3\n\
if ! kill -0 $BACKEND_PID 2>/dev/null; then\n\
    echo "❌ Backend failed to start"\n\
    exit 1\n\
fi\n\
echo "✅ Backend is running"\n\
\n\
echo "🎨 Starting Chainlit frontend on port 80..."\n\
exec chainlit run chainlit_app.py --port 80 --host 0.0.0.0 --headless\n' > /app/start_services.sh && chmod +x /app/start_services.sh

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables if needed by your application
# ENV GEMINI_API_KEY="your-gemini-key"
# ENV VENTUREBOT_API_URL="http://localhost:8000"

# Start the services
CMD ["/app/start_services.sh"] 
