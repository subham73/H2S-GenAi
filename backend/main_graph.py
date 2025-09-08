import asyncio
from core.data_models import QAState
from core.workflow import create_qa_workflow, export_test_cases_to_json, generate_traceability_matrix


async def main():
    specification = """
    Healthcare Patient Management System:
    The system shall provide secure patient data management capabilities including:
    - Patient registration and demographic data storage
    - Medical history tracking with audit trails
    - Integration with external laboratory systems
    - HIPAA-compliant data encryption and access controls
    - Role-based authentication for healthcare providers
    - Automated report generation for regulatory compliance
    - Data backup and disaster recovery procedures
    The system must comply with HIPAA, FDA 510(k) requirements for medical devices,
    and implement IEC 62304 software lifecycle processes.
    """
    initial_state = QAState(
        specification=specification,
        regulatory_requirements=["HIPAA", "FDA_510K", "IEC_62304"] # from the frontend it should change
    )
    workflow = create_qa_workflow()
    print("Starting Healthcare QA Automation Workflow...")
    try:
        final_state = await workflow.ainvoke(initial_state)
        print(f"\nWorkflow completed successfully!")
        print(type(final_state))
        final_state = QAState(**final_state)

        print(f"Generated {len(final_state.test_cases)} test cases")
        # print(f"Performed {len(final_state.compliance_results)} compliance checks")
        # print("\nSample Test Cases:")
        # for i, tc in enumerate(final_state.test_cases[:3]):
        #     print(f"\n{i+1}. {tc.title}")
        #     print(f"   Priority: {tc.priority}")
        #     print(f"   Compliance: {tc.compliance_status}")
        #     print(f"   Regulatory Tags: {', '.join(tc.regulatory_tags)}")
        # violations = [cr for cr in final_state.compliance_results if cr.violations]
        # if violations:
        #     print(f"\nCompliance Issues Found: {len(violations)}")
        #     for violation in violations[:3]:
        #         print(f"- {violation.regulation}: {', '.join(violation.violations)}")
        # traceability = generate_traceability_matrix(final_state)
        # print(f"\nTraceability Matrix: {len(traceability)} requirements traced")
        # json_export = export_test_cases_to_json(final_state)
        # print(f"\nExport completed: {len(json_export)} characters")
    except Exception as e:
        import traceback
        print(f"Workflow failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())