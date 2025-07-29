cd Src/Frontend
npm run build

cd ../Backend
pip install -r requirements.txt
uvicorn Service:app --host 0.0.0.0 --port 80 &

cd ../Frontend
npm run build:watch