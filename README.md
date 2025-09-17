Branch : 
-> resource 
    / meeting -> meeting notes and agenda
    / worksheet.xlsx -> work distribution 

->  

docker build -t h2s-genai-app .
docker run -p 8000:8000 h2s-genai-app