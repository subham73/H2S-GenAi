# import requests
# from pprint import pprint
# import json

# # Define the endpoint
# url = "https://h2s-fastapi-app-342923646426.europe-west1.run.app/run-workflow"

# # Define the headers
# headers = {
#     "accept": "application/json",
#     "Content-Type": "application/json"
# }

# # Define the payload
# payload = {
#     "requirement": "vaccine management",
#     "regulatory_requirements": ["iso", "hipaa"]
# }

# # Make the POST request
# response = requests.post(url, headers=headers, json=payload)

# # Print the response
# print("Status Code:", response.status_code)
# print(json.dumps(response.json(), indent=2))


import json
from pathlib import Path
from typing import List, Union
from pydantic import BaseModel
from backend.core.data_models import QAState, completeQA


def models_to_jsonl(models: Union[List[BaseModel], BaseModel], filepath: str):
    path = Path(filepath)
    with path.open("w", encoding="utf-8") as f:
        if isinstance(models, list):
            for model in models:
                f.write(model.model_dump_json() + "\n")
        else:
            f.write(models.model_dump_json() + "\n")

    print(f"✅ Saved {filepath}")


# -------- Example --------
class Forecast(BaseModel):
    project_id: str
    year: int
    month: int
    forecast_type: str
    value: float


# Example usage
if __name__ == "__main__":
    data = [
        QAState(**completeQA),
    ]

    models_to_jsonl(data, "first.jsonl")
