# How to Build and Run this Dockerfile:
#
# 1. Ensure Docker is installed on your system.
# 2. Open your terminal and navigate to the root directory of this project (where this Dockerfile is located).
# 3. Build the Docker image:
#    docker build -t venturebots .
# 4. Run the Docker container (ensure your .env file is in the same directory):
#    docker run -d -p 80:80 --env-file .env --name venturebots-app venturebots
# 5. Access the application in your browser at http://<YOUR_VM_IP_ADDRESS> or http://localhost if running locally.
#    (You might need to configure your VM's firewall to allow traffic on port 80 if it's not already open).

# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the entire project contents into the container at /app
# This includes main.py, all agentlab_v* directories, root requirements.txt, .env, etc.
COPY . /app/

# Install any needed packages specified in the root requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variables if needed by your application or ADK
# For example, if your config.yaml relies on env vars, or ADK needs project/location
# ENV GOOGLE_CLOUD_PROJECT="your-gcp-project"
# ENV GOOGLE_CLOUD_LOCATION="your-gcp-location"
# ENV GOOGLE_GENAI_USE_VERTEXAI="True" # If using Vertex AI

# Run the FastAPI application using Uvicorn from the agentlab_v5 directory
CMD ["sh", "-c", "cd /app/agentlab_v5 && adk web --port 80"] 