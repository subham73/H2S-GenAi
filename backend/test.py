from datetime import datetime, timezone
from typing import List
import requests
from pydantic import BaseModel
from backend.core.data_models import ComplianceResult, QAState, sample_test_compliance, TestCase
import json 
from backend.bigQuery import client
import uuid


class RequirementRequest(BaseModel):
    requirement: str
    regulatory_requirements: List[str]


threshold_compliance_score = 0.7  # Example threshold

def insert_requirement(req: RequirementRequest): # Insert requirement into BigQuery and return its UiniqueReqID
    print(f"Inserting requirement: {req.requirement} with regulations: {req.regulatory_requirements}")
     # Define your BigQuery table schema and insert the requirement
    table_id = "erudite-realm-472100-k9.qa_dataset.Requirement"
    requirement_id = str(uuid.uuid4())
    rows_to_insert = [
        {
            "req_id": requirement_id,  # use generated ID
            "req": req.requirement,
            "regulations": req.regulatory_requirements,
            "ts": datetime.now(timezone.utc).isoformat()           # timestamp
        }
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
    print("✅ Inserted row into BigQuery")
    return requirement_id


def insert_test_cases(req_id: str, test_cases: list[TestCase]):
    """
    Validate and insert test cases into BigQuery.
    Each test case gets:
      - stable unique test_id
      - req_id foreign key
      - sequence (order within the requirement)
      - full JSON payload
      - insert timestamp
    """
    print(f"Inserting {len(test_cases)} test cases for requirement {req_id}")
    table_id = "erudite-realm-472100-k9.qa_dataset.TestCase"

    rows_to_insert = []
    for idx, tc in enumerate(test_cases, start=1):
        # ✅ Validate and normalize via Pydantic
        print(type(tc))
        rows_to_insert.append({
            "test_id": str(uuid.uuid4()),           # stable unique ID
            "req_id": req_id,                       # link to requirement
            "sequence": idx,                        # sequential order
            "testcase_details": json.dumps(tc.model_dump()),       # native JSON column
            "ts": datetime.now(timezone.utc).isoformat()           # timestamp
        })

    errors = client.insert_rows_json(table_id, rows_to_insert)

    if errors:
        raise RuntimeError(f"❌ BigQuery insert failed: {errors}")

    print(f"✅ Inserted {len(rows_to_insert)} validated test cases into BigQuery")

def run_rag_compliance(testcase: dict, regulatory_tag: str) -> dict:
    """
    Call external RAG compliance API with one testcase wrapped in a list.
    """
    rag_url = "https://compliance-checking-api-ycau7ebspa-uk.a.run.app/check-compliance"

    payload = {
        "test_cases": [testcase]  # wrap single testcase in list
    }

    try:
        response = requests.post(rag_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
 
        # If the API returns a list of results, pick the first one
        results = data.get("results") or []
        if not results:
            # fallback empty result
            return {
                "test_case_id": testcase.get("test_id", ""),
                "compliance_score": None,
                "compliance_status": None,
                "recommendations": [],
                "violations": [],
                "regulatory_citations": []
            } # unwrap nested result

        print(results[0])
        return results[0]

    except requests.RequestException as e:
        raise RuntimeError(f"Compliance API call failed: {e}")

def process_compliance_for_requirement(req_id: str, regulatory_tags: list[str]):
    """
    For a given requirement, fetch all test cases, send each to RAG agent per regulatory tag,
    and store the compliance result in BigQuery.
    """
    table_id = "erudite-realm-472100-k9.qa_dataset.TestCase"
    compliance_table_id = "erudite-realm-472100-k9.qa_dataset.Compliance"

    print(f"Processing compliance for requirement {req_id} with tags {regulatory_tags}")

    # 1️⃣ Fetch test cases from DB
    query = f"""
    SELECT test_id, testcase_details
    FROM `{table_id}`
    WHERE req_id = @req_id
    ORDER BY sequence
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("req_id", "STRING", req_id)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    test_cases = list(query_job.result())

    print(f"Fetched {len(test_cases)} test cases for requirement {req_id}")

    # 2️⃣ Iterate over regulatory tags and test cases
    issue_rows = []
    rows_to_insert = []

    for tag in regulatory_tags[0]: #TODO: cz we have only one RAG engine
        tag = "fda"
        for row in test_cases:
            test_id = row["test_id"]
            testcase = row["testcase_details"]
            if isinstance(testcase, str):
                testcase = json.loads(testcase)  # convert JSON string to dict

            # ✅ Send to RAG agent
            raw_compliance_result = run_rag_compliance(testcase, tag)
            # compliance_result = compliance_result.get("result", [{}])[0]  # unwrap nested result
            print(raw_compliance_result)

            if raw_compliance_result.get("compliance_score") is None:
                print(f"⚠️ RAG returned None score for test_id={test_id}, tag={tag}")
            
            raw_compliance_result.pop("test_case_id", None)

            compliance_obj = ComplianceResult(
                test_case_id=test_id,
                regulation=tag,
                **raw_compliance_result
            )  #     validate and normalize
            compliance_result = compliance_obj.model_dump()
            print(compliance_result)
            

            # 3️⃣ Prepare row to insert into ComplianceResult table
            rows_to_insert.append({
                "test_id": test_id,
                "req_id": req_id,
                "regulatory_tag": tag,
                "compliance_result": json.dumps(compliance_result),
                "ts": datetime.now(timezone.utc).isoformat()
            })
            compliance_score = compliance_result.get("compliance_score", 0)
            if compliance_score < threshold_compliance_score:
                print(f"creating a issue ")
                issue_rows.append({
                    "issue_id": str(uuid.uuid4()),
                    "test_id": test_id,
                    "req_id": req_id,
                    "regulatory_tag": tag,
                    "compliance_score": compliance_score,
                    "compliance_result": json.dumps(compliance_result),
                })
        break  # TODO: remove after testing single tag

    # 4️⃣ Insert results into BigQuery
    if rows_to_insert:
        errors = client.insert_rows_json(compliance_table_id, rows_to_insert)
        if errors:
            raise RuntimeError(f"BigQuery insert failed: {errors}")
        
    if issue_rows:
        make_issue_after_compliance(issue_rows)

    print(f"✅ Processed compliance for {len(rows_to_insert)} test case-tag combinations")


def make_issue_after_compliance(issue_rows: list[dict]):
    """
    Create issues in BigQuery Issue table.
    Generates a summary note from recommendations and violations.
    """
    if not issue_rows:
        return
    ISSUE_TABLE = "erudite-realm-472100-k9.qa_dataset.Issue"

    # Prepare rows for BigQuery
    rows_to_insert = []
    for row in issue_rows:
        compliance_result = row["compliance_result"]
        if isinstance(compliance_result, str):
            compliance_result = json.loads(compliance_result)

        recommendations = compliance_result.get("recommendations", [])
        violations = compliance_result.get("violations", [])

        note = "Recommendations:\n- " + "\n- ".join(recommendations) + "\nViolations:\n- " + "\n- ".join(violations) #TODO inteligent summery . 

        rows_to_insert.append({
            "issue_id": str(uuid.uuid4()),
            "test_id": row["test_id"],
            "req_id": row["req_id"],
            "regulatory_tag": row["regulatory_tag"],
            "compliance_score": row["compliance_score"],
            "notes": note,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    errors = client.insert_rows_json(ISSUE_TABLE, rows_to_insert)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    print(f"✅ Created {len(rows_to_insert)} issues in Issue table")
    