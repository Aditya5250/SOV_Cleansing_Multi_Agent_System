# -------------------------------------------------------------
# Stage 1: Build the React 19 Frontend
# -------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Python 3.11 Runtime for FastAPI & Multi-Agent Backend
# -------------------------------------------------------------
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers with user ID 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PORT=7860 \
    HOST=0.0.0.0

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, sample data, docs, and compiled frontend assets
COPY backend ./backend
COPY sample_data ./sample_data
COPY docs ./docs
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set directory permissions for user 1000
RUN mkdir -p /app/scratch/uploads /home/user/.cache/huggingface && \
    chown -R user:user /app /home/user

USER user

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
