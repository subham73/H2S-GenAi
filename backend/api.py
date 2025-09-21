from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.core.data_models import QAState, sample_test_compliance, completeQA
from backend.core.workflow import create_qa_workflow
import uvicorn
import os
from dotenv import load_dotenv
from backend.test import RequirementRequest, insert_requirement, insert_test_cases, process_compliance_for_requirement
load_dotenv()



app = FastAPI()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # default 8080
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

class RequirementRequest(BaseModel):
    requirement: str
    regulatory_requirements: list[str]

@app.post("/run-workflow")
async def run_workflow(req: RequirementRequest):
    try:
        initial_state = QAState(
            requirement=req.requirement,
            regulatory_requirements=req.regulatory_requirements
        )
        # workflow = create_qa_workflow()
        # final_state = await workflow.ainvoke(initial_state)
        input = RequirementRequest(requirement=req.requirement, regulatory_requirements=req.regulatory_requirements)
        req_id = insert_requirement(input)
        print(f"Inserted requirement with ID: {req_id}")
        try:
            dummy_final_state = QAState(**completeQA)
        except Exception as e:
            raise RuntimeError(f"Failed to parse completeQA: {e}")
            print(completeQA)
        insert_test_cases(req_id, dummy_final_state.test_cases)
        # return dummy_final_state.model_dump()
        process_compliance_for_requirement(req_id, req.regulatory_requirements)
        return "muahh"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/generate_test_cases") # Get the req  id 
async def generate_test_cases(req: RequirementRequest):
    try:
        initial_state = QAState(
            requirement=req.requirement,
            regulatory_requirements=req.regulatory_requirements
        )
        req_id = insert_requirement(req) # get requrirement id and insert requirement to db
        
        workflow = create_qa_workflow()
        final_state = await workflow.ainvoke(initial_state)
        final_state = QAState(**final_state)
        insert_test_cases(req_id, final_state.test_cases) # insert testcases to db 

        #compilance check and add ccompliance to db
        process_compliance_for_requirement(req_id, req.regulatory_requirements)

        return req_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"message": "Welcome to the QA Automation API"}

#TODO : store the requirement specification . 


from google.cloud import bigquery
client = bigquery.Client()


@app.get("/all_requirements")
async def get_requirements():
    query = "SELECT * FROM `erudite-realm-472100-k9.qa_dataset.Requirement` ORDER BY ts DESC"
    rows = list(client.query(query).result())
    return [dict(row) for row in rows]

@app.get("/requirements/{req_id}/testcases")
async def get_test_cases(req_id: str):
    query = f"""
    SELECT test_id, sequence, testcase_details
    FROM `erudite-realm-472100-k9.qa_dataset.TestCase`
    WHERE req_id = @req_id
    ORDER BY sequence
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("req_id", "STRING", req_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return [dict(row) for row in rows]

@app.get("/requirements/{req_id}/compliance")
async def get_compliance_results(req_id: str):
    query = f"""
    SELECT *
    FROM `erudite-realm-472100-k9.qa_dataset.Compliance`
    WHERE req_id = @req_id
    ORDER BY ts DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("req_id", "STRING", req_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return [dict(row) for row in rows]

@app.get("/testcases/{test_id}/compliance")
async def get_compliance_for_testcase(test_id: str):
    query = f"""
    SELECT *
    FROM `erudite-realm-472100-k9.qa_dataset.Compliance`
    WHERE test_id = @test_id
    ORDER BY ts DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("test_id", "STRING", test_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return [dict(row) for row in rows]

@app.get("/requirements/{req_id}/issues")
async def get_issues_for_requirement(req_id: str):
    query = f"""
    SELECT *
    FROM `erudite-realm-472100-k9.qa_dataset.Issue`
    WHERE req_id = @req_id
    ORDER BY ts DESC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("req_id", "STRING", req_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return [dict(row) for row in rows]

@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str):
    query = f"""
    SELECT *
    FROM `erudite-realm-472100-k9.qa_dataset.Issue`
    WHERE issue_id = @issue_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("issue_id", "STRING", issue_id)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return [dict(row) for row in rows]

#TODO : necessary
# @app.post("/requirements/{req_id}/check_compliance")
# async def recheck_compliance(req_id: str):
#     # fetch regulatory tags from Requirement table
#     query = f"SELECT regulatory_requirements FROM `erudite-realm-472100-k9.qa_dataset.Requirement` WHERE req_id=@req_id"
#     job_config = bigquery.QueryJobConfig(
#         query_parameters=[bigquery.ScalarQueryParameter("req_id", "STRING", req_id)]
#     )
#     rows = list(client.query(query, job_config=job_config).result())
#     if not rows:
#         raise HTTPException(status_code=404, detail="Requirement not found")

#     regulatory_tags = rows[0]["regulatory_requirements"]
#     process_compliance_for_requirement(req_id, regulatory_tags)
#     return {"status": "rechecked", "req_id": req_id}
