# Choose an appropriate Python base image
FROM python:3.9-slim

# Set environment variables for Python for better container behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Create a non-root user and group for running the application
# This enhances security by avoiding running processes as root.
# --system flag creates a system user/group, typically without a home directory by default,
# which is suitable for service accounts.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install system dependencies (like ffmpeg for yt-dlp)
# These are installed as root before switching to the non-root user.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
# Change ownership to the appuser. Requires Docker 17.09+ and BuildKit for --chown.
COPY --chown=appuser:appgroup requirements.txt ./

# Install Python dependencies
# Running as root to install packages system-wide. 
# --no-cache-dir reduces image size by not storing the pip download cache.
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files (app.py and startup.sh)
# Change ownership to the appuser.
COPY --chown=appuser:appgroup app.py ./
COPY --chown=appuser:appgroup startup.sh ./

# Make the startup script executable
# This is done as root, ensuring the execute bit is set correctly.
RUN chmod +x /app/startup.sh

# Switch to the non-root user for running the application
USER appuser

# Expose the port the app runs on (default 8501, as per startup.sh)
# This port is > 1024, so the non-root user can bind to it.
EXPOSE 8501

# Set the entrypoint to run the startup script
# The script will be executed as the 'appuser'.
ENTRYPOINT ["/app/startup.sh"]
