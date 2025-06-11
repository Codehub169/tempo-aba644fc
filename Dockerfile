# Choose an appropriate Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (like ffmpeg for yt-dlp)
# Using apt-get for Debian-based images (like python:3.9-slim)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files (app.py and startup.sh)
COPY app.py ./
COPY startup.sh ./

# Make the startup script executable
RUN chmod +x /app/startup.sh

# Expose the port the app runs on (default 8501, as per startup.sh)
EXPOSE 8501

# Set the entrypoint to run the startup script
ENTRYPOINT ["/app/startup.sh"]
