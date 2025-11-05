from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.core.data_models import QAState, sample_test_compliance, completeQA
from backend.core.workflow import create_qa_workflow
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.test import RequirementRequest, insert_requirement, insert_test_cases, process_compliance_for_requirement
from backend.bigQuery import client, bigquery
from backend.core.workflow import publish_message, publish_issues_notificaiton, publish_requirements_notification
load_dotenv()

def insert_requirement_analysis_placeholder(req_id: str):
    query = """
    INSERT INTO "erudite-realm-472100-k9.qa_dataset.ReqAnalysis" (requirement_id, analysis, status)
    VALUES (@req_id, '{}', 'pending')
    """
    client.query(query, [
        bigquery.ScalarQueryParameter("req_id", "STRING", req_id),
    ])

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://qa-frontend-342923646426.us-central1.run.app", "https://medtestgen.web.app"],  # Or specify ["http://localhost:5173"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        insert_requirement_analysis_placeholder(req_id) # insert placeholder for requirement analysis

        
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

@app.get("/sync_requirements/{req_id}")
async def sync_requirements(req_id: str):
    try:
        publish_requirements_notification(req_id)
        return {"Success": req_id}
    except Exception as e:
        return {"Failure": f"Failed to sync requirement: {str(e)}"}


@app.get("/sync_issues/{issue_id}")
async def sync_issues(issue_id: str):
    try:
        publish_issues_notificaiton(issue_id)
        return {"Success": issue_id}
    except Exception as e:
        return {"Failure": f"Failed to sync issue: {str(e)}"}    

# TODO - SYNC ALL ISSUES AND REQUIREMENTS AT ONCE
# @app.get("/sync_all_issues")
# async def sync_all_issues():
#     try:
#         publish_issues_notificaiton()
#         return {"Success": "Synced all issues"}
#     except Exception as e:
#         return {"Failure": f"Failed to sync issues: {str(e)}"}    

# @app.get("/sync_all_requirements")
# async def sync_all_requirements():
#     try:
#         publish_requirements_notification()
#         return {"Success": "Synced all requirements"}
#     except Exception as e:
#         return {"Failure": f"Failed to sync requirements: {str(e)}"}

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # default 8080
    uvicorn.run(app, host="0.0.0.0", port=port)