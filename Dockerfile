FROM python:3.11-slim

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# HF Spaces requires non-root user
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Copy and install Python deps first (cache layer)
COPY energy-grid-env/requirements.txt ./energy-grid-env/requirements.txt
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    "uvicorn[standard]>=0.29.0,<1.0.0" \
    "starlette>=0.37.2,<0.39.0" \
    "pydantic>=2.0.0" \
    "numpy>=1.26.0" \
    "openai>=1.50.0" \
    "python-dotenv>=1.0.0" \
    "openenv-core>=0.2.0" \
    "fastmcp>=3.0.0"

# Copy backend
COPY energy-grid-env/ ./energy-grid-env/

# Copy and build frontend
COPY frontend/package.json frontend/package-lock.json ./frontend/
WORKDIR /home/user/app/frontend
RUN npm install

COPY frontend/ ./
RUN npm run build

# Copy built frontend to static dir
RUN mkdir -p /home/user/app/energy-grid-env/static && \
    cp -r dist/* /home/user/app/energy-grid-env/static/

WORKDIR /home/user/app/energy-grid-env

# Switch to non-root user
USER user

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
