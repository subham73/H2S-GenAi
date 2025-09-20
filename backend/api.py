from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.core.data_models import QAState, sample_test_compliance
from backend.core.workflow import create_qa_workflow
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()



app = FastAPI()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # default 8080
    uvicorn.run(app, host="0.0.0.0", port=port)

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
        dummy_final_state = sample_test_compliance
        # return dummy_final_state.model_dump()
        return dummy_final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/run-local-workflow")
async def run_workflow(req: RequirementRequest):
    try:
        initial_state = QAState(
            requirement=req.requirement,
            regulatory_requirements=req.regulatory_requirements
        )
        workflow = create_qa_workflow()
        final_state = await workflow.ainvoke(initial_state)
        final_state = QAState(**final_state)
        return final_state.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
async def read_root():
    return {"message": "Welcome to the QA Automation API"}

