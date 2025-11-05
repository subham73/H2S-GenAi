from google.cloud import bigquery
import os
from dotenv import load_dotenv
load_dotenv()

client = bigquery.Client(os.getenv('GCP_PROJECT_ID'))

