cd Src/Frontend
npm run build:watch &

cd ../Backend
uvicorn Service:app --host 0.0.0.0 --port 80