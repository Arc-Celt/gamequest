# Use Python 3.11 image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with CUDA support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs chroma_db embeddings /data/chroma_db /home/user/huggingface/hub /home/user/cache
RUN chmod -R 777 /data /home/user

# Create symlink from /.cache to /home/user/cache to avoid permission issues
RUN ln -sf /home/user/cache /.cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV TRANSFORMERS_CACHE=/home/user/huggingface/hub
ENV HF_HOME=/home/user/huggingface
ENV HF_HUB_CACHE=/home/user/huggingface/hub
ENV TMPDIR=/tmp
ENV XDG_CACHE_HOME=/home/user/cache

# Expose the port that Hugging Face Spaces expects
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860 || exit 1

# Start the Flask application
CMD python flask/app.py