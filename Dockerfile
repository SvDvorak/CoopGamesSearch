FROM node:20-slim AS frontend-builder

WORKDIR /app/Frontend

COPY Src/Frontend/package*.json ./
RUN npm ci

COPY Src/Frontend/ ./

RUN npm run build-only

FROM python:3.11-slim

WORKDIR /app/Backend

# Install requirements first for better caching
COPY Src/Backend/Requirements.txt .

RUN pip install --no-cache-dir -r Requirements.txt

WORKDIR /app
COPY Src/Backend/ ./Backend/
COPY Src/Countries.json ./

COPY --from=frontend-builder /app/Frontend/dist ./Frontend/dist
COPY --from=frontend-builder /app/Frontend/Resources ./Frontend/Resources

WORKDIR /app/Backend
CMD ["uvicorn", "Service:app", "--host", "0.0.0.0", "--port", "80"]