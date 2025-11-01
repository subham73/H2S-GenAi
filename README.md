Branch : 
-> resource 
    / meeting -> meeting notes and agenda
    / worksheet.xlsx -> work distribution 

->  

docker build -t h2s-genai-app .
docker run -p 8000:8000 h2s-genai-app

docker run -v C:\Users\Subham\OneDrive\Desktop\H2S-GenAi\erudite-realm-472100-k9-5d79b1c4d9bb.json:/app/servicekey.json -e GOOGLE_APPLICATION_CREDENTIALS=/app/servicekey.json -p 8080:8080 h2s-genai-app