import uuid
import re
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from langchain_core.tools import BaseTool
from core.data_models import HEALTHCARE_REGULATIONS


class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TestCaseType(Enum):
    FUNCTIONAL = "Functional"
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    PERFORMANCE = "Performance"
    INTEGRATION = "Integration"


@dataclass
class Entity:
    """Extracted entities from specification"""
    actors: Set[str] = field(default_factory=set)
    actions: Set[str] = field(default_factory=set)
    data: Set[str] = field(default_factory=set)
    constraints: Set[str] = field(default_factory=set)
    systems: Set[str] = field(default_factory=set)


@dataclass
class FunctionalIntent:
    """Identified functional intent from specification"""
    primary_function: str
    sub_functions: List[str] = field(default_factory=list)
    business_rules: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)


@dataclass
class SecurityImplication:
    """Security implications identified"""
    risk_level: Priority
    threat_vectors: List[str] = field(default_factory=list)
    data_sensitivity: str = "MEDIUM"
    authentication_required: bool = True
    authorization_levels: List[str] = field(default_factory=list)


@dataclass
class RegulatoryMapping:
    """Mapping to regulatory standards"""
    applicable_regulations: List[str] = field(default_factory=list)
    compliance_requirements: Dict[str, List[str]] = field(default_factory=dict)
    audit_trails: List[str] = field(default_factory=list)


@dataclass
class TraceabilityMatrix:
    """Traceability matrix for requirements to test cases"""
    requirement_id: str
    specification_section: str
    functional_test_ids: List[str] = field(default_factory=list)
    security_test_ids: List[str] = field(default_factory=list)
    compliance_test_ids: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0


class SpecificationAnalyzer:
    """Advanced NLP-based specification analyzer"""
    
    def __init__(self, rag_connection: Optional[Any] = None):
        self.rag_connection = rag_connection
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for entity extraction"""
        self.actor_patterns = [
            r'\b(?:user|admin|patient|doctor|nurse|system|operator|manager|analyst)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:shall|must|will|can|may))',
            r'\b(?:the|a|an)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:shall|must|will)'
        ]
        
        self.action_patterns = [
            r'\b(?:create|read|update|delete|process|validate|authenticate|authorize|log|audit|encrypt|decrypt|backup|restore|integrate|synchronize|notify|alert|report|export|import|calculate|analyze|generate|transform|filter|search|query|monitor|track|schedule|configure|manage|maintain)\b',
            r'\b(?:shall|must|will|should)\s+([a-z]+(?:\s+[a-z]+)*)',
            r'\b(?:able\s+to|capability\s+to|function\s+to)\s+([a-z]+(?:\s+[a-z]+)*)'
        ]
        
        self.data_patterns = [
            r'\b(?:patient\s+data|medical\s+record|health\s+information|personal\s+data|clinical\s+data|diagnostic\s+data|treatment\s+data|medication\s+data|lab\s+results|imaging\s+data|vital\s+signs|demographic\s+data|insurance\s+information|billing\s+data|audit\s+log|transaction\s+log|user\s+credentials|authentication\s+token|session\s+data|configuration\s+data|system\s+logs|error\s+logs|performance\s+metrics|reports|dashboards|alerts|notifications)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:data|information|record|file|document|report)\b'
        ]
        
        self.constraint_patterns = [
            r'\b(?:within|under|over|above|below|maximum|minimum|at\s+least|no\s+more\s+than|between)\s+[\d\w\s]+',
            r'\b(?:must\s+not|shall\s+not|cannot|prohibited|restricted|limited\s+to|only\s+if|unless|except|provided\s+that)\b[^.]*',
            r'\b(?:compliant\s+with|according\s+to|as\s+per|in\s+accordance\s+with)\s+[A-Z\d\s-]+',
            r'\b(?:real-time|24/7|business\s+hours|offline|online|concurrent|sequential|parallel)\b'
        ]

    def normalize_specification(self, specification: str) -> str:
        """Normalize specification text"""
        # Remove extra whitespace and normalize line breaks
        normalized = re.sub(r'\s+', ' ', specification.strip())
        
        # Standardize terminology using RAG if available
        if self.rag_connection:
            normalized = self._enhance_with_domain_knowledge(normalized)
        
        return normalized

    def _enhance_with_domain_knowledge(self, text: str) -> str:
        """Enhance specification with domain knowledge from RAG"""
        # This is a placeholder for RAG integration
        # In practice, you'd query your RAG system for domain-specific enhancements
        return text

    def extract_entities(self, specification: str) -> Entity:
        """Extract key entities using NLP patterns"""
        entities = Entity()
        
        # Extract actors
        for pattern in self.actor_patterns:
            matches = re.finditer(pattern, specification, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    entities.actors.add(match.group(1).lower().strip())
                else:
                    entities.actors.add(match.group(0).lower().strip())
        
        # Extract actions
        for pattern in self.action_patterns:
            matches = re.finditer(pattern, specification, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    entities.actions.add(match.group(1).lower().strip())
                else:
                    entities.actions.add(match.group(0).lower().strip())
        
        # Extract data entities
        for pattern in self.data_patterns:
            matches = re.finditer(pattern, specification, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    entities.data.add(match.group(1).lower().strip())
                else:
                    entities.data.add(match.group(0).lower().strip())
        
        # Extract constraints
        for pattern in self.constraint_patterns:
            matches = re.finditer(pattern, specification, re.IGNORECASE)
            for match in matches:
                entities.constraints.add(match.group(0).strip())
        
        # Extract system references
        system_pattern = r'\b([A-Z]+(?:[A-Z][a-z]+)*(?:\s+System|\s+API|\s+Service|\s+Database|\s+Server))\b'
        system_matches = re.finditer(system_pattern, specification)
        for match in system_matches:
            entities.systems.add(match.group(1))
        
        return entities

    def identify_functional_intent(self, specification: str, entities: Entity) -> FunctionalIntent:
        """Identify functional intent using domain-specific NLP"""
        intent = FunctionalIntent(primary_function="core_system_functionality")
        
        # Determine primary function based on key actions and data
        if any(action in ['authenticate', 'login', 'authorize'] for action in entities.actions):
            intent.primary_function = "authentication_and_authorization"
        elif any(data in ['patient data', 'medical record', 'health information'] for data in entities.data):
            intent.primary_function = "healthcare_data_management"
        elif any(action in ['report', 'generate', 'analyze'] for action in entities.actions):
            intent.primary_function = "reporting_and_analytics"
        elif any(action in ['integrate', 'synchronize', 'import', 'export'] for action in entities.actions):
            intent.primary_function = "system_integration"
        
        # Extract sub-functions
        action_groups = {
            'data_management': ['create', 'read', 'update', 'delete', 'process'],
            'security': ['encrypt', 'decrypt', 'authenticate', 'authorize'],
            'monitoring': ['log', 'audit', 'monitor', 'track', 'alert'],
            'integration': ['integrate', 'synchronize', 'import', 'export'],
            'reporting': ['report', 'generate', 'analyze', 'calculate']
        }
        
        for group, actions in action_groups.items():
            if any(action in entities.actions for action in actions):
                intent.sub_functions.append(group)
        
        # Extract business rules from constraints
        intent.business_rules = list(entities.constraints)
        
        # Identify integration points
        intent.integration_points = list(entities.systems)
        
        return intent

    def detect_security_implications(self, specification: str, entities: Entity) -> SecurityImplication:
        """Detect security implications using pattern analysis"""
        implication = SecurityImplication(risk_level=Priority.MEDIUM)
        
        # Assess risk level based on data sensitivity
        high_risk_data = ['patient data', 'medical record', 'personal data', 'health information', 'clinical data']
        if any(data in entities.data for data in high_risk_data):
            implication.risk_level = Priority.CRITICAL
            implication.data_sensitivity = "HIGH"
        
        # Identify threat vectors
        if any(action in ['authenticate', 'authorize'] for action in entities.actions):
            implication.threat_vectors.extend(['credential_theft', 'session_hijacking', 'privilege_escalation'])
        
        if any(data in ['patient data', 'medical record'] for data in entities.data):
            implication.threat_vectors.extend(['data_breach', 'unauthorized_access', 'data_tampering'])
        
        if any(system in entities.systems for system in entities.systems):
            implication.threat_vectors.extend(['integration_vulnerabilities', 'api_attacks'])
        
        # Determine authorization levels
        if 'admin' in entities.actors:
            implication.authorization_levels.append('administrator')
        if any(actor in ['doctor', 'nurse', 'clinician'] for actor in entities.actors):
            implication.authorization_levels.append('healthcare_provider')
        if 'patient' in entities.actors:
            implication.authorization_levels.append('patient')
        
        return implication

    def map_regulatory_standards(self, specification: str, entities: Entity, regulations: List[str]) -> RegulatoryMapping:
        """Map specification to regulatory standards"""
        mapping = RegulatoryMapping()
        
        # Filter applicable regulations based on domain and data types
        for regulation in regulations:
            if regulation in HEALTHCARE_REGULATIONS:
                reg_keywords = HEALTHCARE_REGULATIONS[regulation].get('keywords', [])
                if any(keyword.lower() in specification.lower() for keyword in reg_keywords):
                    mapping.applicable_regulations.append(regulation)
        
        # Map compliance requirements for each regulation
        for regulation in mapping.applicable_regulations:
            requirements = []
            reg_config = HEALTHCARE_REGULATIONS.get(regulation, {})
            
            # Patient data handling requirements
            if any(data in ['patient data', 'medical record', 'health information'] for data in entities.data):
                requirements.extend(reg_config.get('data_protection', []))
            
            # Authentication requirements
            if any(action in ['authenticate', 'authorize'] for action in entities.actions):
                requirements.extend(reg_config.get('access_control', []))
            
            # Audit requirements
            if any(action in ['log', 'audit', 'monitor'] for action in entities.actions):
                requirements.extend(reg_config.get('audit_trail', []))
            
            mapping.compliance_requirements[regulation] = requirements
        
        # Determine required audit trails
        if any(data in ['patient data', 'medical record'] for data in entities.data):
            mapping.audit_trails.extend(['data_access', 'data_modification', 'user_authentication'])
        
        return mapping


class ParallelTestCaseGenerator:
    """Parallel test case generation with async processing"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def generate_all_test_cases(
        self,
        entities: Entity,
        functional_intent: FunctionalIntent,
        security_implications: SecurityImplication,
        regulatory_mapping: RegulatoryMapping
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Generate all test cases in parallel"""
        
        # Create async tasks for parallel execution
        functional_task = asyncio.create_task(
            self._generate_functional_test_cases(entities, functional_intent)
        )
        
        security_task = asyncio.create_task(
            self._generate_security_test_cases(entities, security_implications)
        )
        
        compliance_task = asyncio.create_task(
            self._generate_compliance_test_cases(entities, regulatory_mapping)
        )
        
        # Wait for all tasks to complete
        functional_tests, security_tests, compliance_tests = await asyncio.gather(
            functional_task, security_task, compliance_task
        )
        
        return functional_tests, security_tests, compliance_tests
    
    async def _generate_functional_test_cases(self, entities: Entity, intent: FunctionalIntent) -> List[Dict]:
        """Generate functional test cases based on intent"""
        test_cases = []
        
        # Main functional test case
        main_tc = self._create_functional_test_case(
            feature=intent.primary_function,
            actors=list(entities.actors),
            actions=list(entities.actions),
            data=list(entities.data),
            constraints=list(entities.constraints)
        )
        test_cases.append(main_tc)
        
        # Sub-function test cases
        for sub_function in intent.sub_functions:
            sub_tc = self._create_functional_test_case(
                feature=sub_function,
                actors=list(entities.actors),
                actions=[action for action in entities.actions if self._is_relevant_action(action, sub_function)],
                data=list(entities.data),
                constraints=list(entities.constraints)
            )
            test_cases.append(sub_tc)
        
        return test_cases
    
    async def _generate_security_test_cases(self, entities: Entity, implications: SecurityImplication) -> List[Dict]:
        """Generate security test cases based on implications"""
        test_cases = []
        
        for threat_vector in implications.threat_vectors:
            security_tc = self._create_security_test_case(
                threat_vector=threat_vector,
                risk_level=implications.risk_level,
                actors=list(entities.actors),
                data=list(entities.data),
                auth_levels=implications.authorization_levels
            )
            test_cases.append(security_tc)
        
        return test_cases
    
    async def _generate_compliance_test_cases(self, entities: Entity, mapping: RegulatoryMapping) -> List[Dict]:
        """Generate compliance test cases based on regulatory mapping"""
        test_cases = []
        
        for regulation, requirements in mapping.compliance_requirements.items():
            for requirement in requirements:
                compliance_tc = self._create_compliance_test_case(
                    regulation=regulation,
                    requirement=requirement,
                    actors=list(entities.actors),
                    data=list(entities.data),
                    audit_trails=mapping.audit_trails
                )
                test_cases.append(compliance_tc)
        
        return test_cases
    
    def _create_functional_test_case(
        self, 
        feature: str, 
        actors: List[str], 
        actions: List[str], 
        data: List[str], 
        constraints: List[str]
    ) -> Dict:
        """Create a comprehensive functional test case"""
        test_case_id = str(uuid.uuid4())
        primary_actor = actors[0] if actors else "user"
        primary_action = actions[0] if actions else "execute"
        
        return {
            "id": test_case_id,
            "type": TestCaseType.FUNCTIONAL.value,
            "title": f"Functional Test - {feature.replace('_', ' ').title()}",
            "description": f"Verify that {primary_actor} can {primary_action} {feature} functionality",
            "preconditions": [
                "System is operational and accessible",
                f"{primary_actor.title()} has appropriate permissions",
                "Required data is available",
                "Integration points are configured"
            ],
            "test_data": {
                "actors": actors,
                "target_data": data,
                "constraints": constraints
            },
            "steps": self._generate_functional_steps(feature, primary_actor, primary_action, data),
            "expected_results": [
                f"{feature.replace('_', ' ').title()} executes successfully",
                "All business rules are enforced",
                "Data integrity is maintained",
                "Appropriate responses are returned"
            ],
            "priority": Priority.HIGH.value,
            "estimated_effort": "2-4 hours",
            "automation_feasible": True,
            "traceability_id": f"FUNC-{feature.upper()}-{test_case_id[:8]}"
        }
    
    def _create_security_test_case(
        self,
        threat_vector: str,
        risk_level: Priority,
        actors: List[str],
        data: List[str],
        auth_levels: List[str]
    ) -> Dict:
        """Create a comprehensive security test case"""
        test_case_id = str(uuid.uuid4())
        
        return {
            "id": test_case_id,
            "type": TestCaseType.SECURITY.value,
            "title": f"Security Test - {threat_vector.replace('_', ' ').title()}",
            "description": f"Verify security controls against {threat_vector} threats",
            "preconditions": [
                "Security policies are configured",
                "Test environment is isolated",
                "Security monitoring is enabled",
                "Baseline security state is established"
            ],
            "test_data": {
                "threat_vector": threat_vector,
                "risk_level": risk_level.value,
                "target_data": data,
                "authorization_levels": auth_levels
            },
            "steps": self._generate_security_steps(threat_vector, actors, data),
            "expected_results": [
                "Security controls prevent unauthorized access",
                "Security events are properly logged",
                "Data confidentiality is maintained",
                "System remains stable under attack"
            ],
            "priority": risk_level.value,
            "estimated_effort": "4-8 hours",
            "automation_feasible": True,
            "requires_security_expertise": True,
            "traceability_id": f"SEC-{threat_vector.upper()}-{test_case_id[:8]}"
        }
    
    def _create_compliance_test_case(
        self,
        regulation: str,
        requirement: str,
        actors: List[str],
        data: List[str],
        audit_trails: List[str]
    ) -> Dict:
        """Create a comprehensive compliance test case"""
        test_case_id = str(uuid.uuid4())
        
        return {
            "id": test_case_id,
            "type": TestCaseType.COMPLIANCE.value,
            "title": f"{regulation} Compliance - {requirement}",
            "description": f"Verify {regulation} compliance for {requirement}",
            "preconditions": [
                f"{regulation} policies are implemented",
                "Compliance monitoring is active",
                "Audit trail capture is enabled",
                "Required documentation is available"
            ],
            "test_data": {
                "regulation": regulation,
                "requirement": requirement,
                "target_data": data,
                "audit_trails": audit_trails
            },
            "steps": self._generate_compliance_steps(regulation, requirement, actors, data),
            "expected_results": [
                f"{regulation} requirements are met",
                "Compliance evidence is generated",
                "Audit trails are complete",
                "No compliance violations detected"
            ],
            "priority": Priority.CRITICAL.value,
            "estimated_effort": "3-6 hours",
            "automation_feasible": False,
            "requires_compliance_review": True,
            "traceability_id": f"COMP-{regulation}-{test_case_id[:8]}"
        }
    
    def _generate_functional_steps(self, feature: str, actor: str, action: str, data: List[str]) -> List[Dict]:
        """Generate dynamic functional test steps"""
        steps = [
            {"step": 1, "action": f"Login as {actor} with valid credentials"},
            {"step": 2, "action": f"Navigate to {feature.replace('_', ' ')} module"},
            {"step": 3, "action": f"Prepare test data: {', '.join(data[:3]) if data else 'default test data'}"},
            {"step": 4, "action": f"Execute {action} operation"},
            {"step": 5, "action": "Verify operation results"},
            {"step": 6, "action": "Check data integrity"},
            {"step": 7, "action": "Validate business rules compliance"},
            {"step": 8, "action": "Logout and clean up test data"}
        ]
        return steps
    
    def _generate_security_steps(self, threat_vector: str, actors: List[str], data: List[str]) -> List[Dict]:
        """Generate dynamic security test steps"""
        steps = [
            {"step": 1, "action": f"Set up security test environment for {threat_vector}"},
            {"step": 2, "action": "Establish baseline security state"},
            {"step": 3, "action": f"Attempt {threat_vector} attack vector"},
            {"step": 4, "action": "Monitor security controls response"},
            {"step": 5, "action": "Verify access denial and logging"},
            {"step": 6, "action": "Check audit trail generation"},
            {"step": 7, "action": "Validate data protection measures"},
            {"step": 8, "action": "Clean up security test artifacts"}
        ]
        return steps
    
    def _generate_compliance_steps(self, regulation: str, requirement: str, actors: List[str], data: List[str]) -> List[Dict]:
        """Generate dynamic compliance test steps"""
        steps = [
            {"step": 1, "action": f"Review {regulation} requirement: {requirement}"},
            {"step": 2, "action": "Prepare compliance test scenario"},
            {"step": 3, "action": "Execute functionality under compliance review"},
            {"step": 4, "action": "Collect compliance evidence"},
            {"step": 5, "action": "Verify audit trail completeness"},
            {"step": 6, "action": "Document compliance status"},
            {"step": 7, "action": "Generate compliance report"},
            {"step": 8, "action": "Archive compliance artifacts"}
        ]
        return steps
    
    def _is_relevant_action(self, action: str, sub_function: str) -> bool:
        """Check if action is relevant to sub-function"""
        action_mapping = {
            'data_management': ['create', 'read', 'update', 'delete', 'process'],
            'security': ['encrypt', 'decrypt', 'authenticate', 'authorize'],
            'monitoring': ['log', 'audit', 'monitor', 'track', 'alert'],
            'integration': ['integrate', 'synchronize', 'import', 'export'],
            'reporting': ['report', 'generate', 'analyze', 'calculate']
        }
        return action in action_mapping.get(sub_function, [])


class TraceabilityManager:
    """Manages traceability matrix and requirements mapping"""
    
    def __init__(self):
        self.matrices: Dict[str, TraceabilityMatrix] = {}
    
    def create_traceability_matrix(
        self,
        specification: str,
        functional_tests: List[Dict],
        security_tests: List[Dict],
        compliance_tests: List[Dict]
    ) -> Dict[str, TraceabilityMatrix]:
        """Create comprehensive traceability matrix"""
        
        # Extract requirements from specification
        requirements = self._extract_requirements(specification)
        
        for req_id, req_text in requirements.items():
            matrix = TraceabilityMatrix(
                requirement_id=req_id,
                specification_section=req_text[:100] + "..." if len(req_text) > 100 else req_text
            )
            
            # Map functional tests
            matrix.functional_test_ids = [
                test['id'] for test in functional_tests 
                if self._is_test_related_to_requirement(test, req_text)
            ]
            
            # Map security tests
            matrix.security_test_ids = [
                test['id'] for test in security_tests 
                if self._is_test_related_to_requirement(test, req_text)
            ]
            
            # Map compliance tests
            matrix.compliance_test_ids = [
                test['id'] for test in compliance_tests 
                if self._is_test_related_to_requirement(test, req_text)
            ]
            
            # Calculate coverage
            total_test_count = len(matrix.functional_test_ids) + len(matrix.security_test_ids) + len(matrix.compliance_test_ids)
            matrix.coverage_percentage = min(100.0, (total_test_count / max(1, len(requirements))) * 100)
            
            self.matrices[req_id] = matrix
        
        return self.matrices
    
    def _extract_requirements(self, specification: str) -> Dict[str, str]:
        """Extract individual requirements from specification"""
        requirements = {}
        
        # Split by common requirement patterns
        req_patterns = [
            r'(?:REQ-\d+|Requirement \d+|R\d+):\s*([^.]+(?:\.[^.]*)*)',
            r'(?:The system|System|Application)\s+(?:shall|must|will|should)\s+([^.]+)',
            r'(?:User|Admin|Patient|Doctor)\s+(?:shall|must|will|should|can|may)\s+([^.]+)'
        ]
        
        req_counter = 1
        for pattern in req_patterns:
            matches = re.finditer(pattern, specification, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                req_id = f"REQ-{req_counter:03d}"
                requirements[req_id] = match.group(1 if match.groups() else 0).strip()
                req_counter += 1
        
        # If no specific patterns found, create requirements from sentences
        if not requirements:
            sentences = re.split(r'[.!?]+', specification)
            for i, sentence in enumerate(sentences[:10], 1):  # Limit to first 10 sentences
                if len(sentence.strip()) > 20:
                    requirements[f"REQ-{i:03d}"] = sentence.strip()
        
        return requirements
    
    def _is_test_related_to_requirement(self, test: Dict, requirement_text: str) -> bool:
        """Check if test is related to requirement using keyword matching"""
        test_description = test.get('description', '').lower()
        test_title = test.get('title', '').lower()
        req_lower = requirement_text.lower()
        
        # Extract key terms from requirement
        key_terms = re.findall(r'\b[a-z]{3,}\b', req_lower)
        
        # Check if test contains key terms from requirement
        relevance_score = sum(
            1 for term in key_terms 
            if term in test_description or term in test_title
        )
        
        return relevance_score >= max(1, len(key_terms) * 0.3)  # At least 30% overlap


class CrossVerificationSuggester:
    """Provides cross-verification and review suggestions"""
    
    def generate_cross_verification_plan(
        self,
        functional_tests: List[Dict],
        security_tests: List[Dict],
        compliance_tests: List[Dict],
        traceability_matrices: Dict[str, TraceabilityMatrix]
    ) -> Dict[str, Any]:
        """Generate comprehensive cross-verification plan"""
        
        plan = {
            "coverage_analysis": self._analyze_coverage(traceability_matrices),
            "test_dependencies": self._identify_test_dependencies(functional_tests, security_tests, compliance_tests),
            "review_checkpoints": self._define_review_checkpoints(),
            "validation_matrix": self._create_validation_matrix(functional_tests, security_tests, compliance_tests),
            "quality_metrics": self._define_quality_metrics(),
            "recommendations": self._generate_recommendations(functional_tests, security_tests, compliance_tests)
        }
        
        return plan
    
    def _analyze_coverage(self, matrices: Dict[str, TraceabilityMatrix]) -> Dict[str, Any]:
        """Analyze test coverage across requirements"""
        total_requirements = len(matrices)
        covered_requirements = sum(1 for matrix in matrices.values() if matrix.coverage_percentage > 0)
        avg_coverage = sum(matrix.coverage_percentage for matrix in matrices.values()) / max(1, total_requirements)
        
        coverage_gaps = [
            {
                "requirement_id": req_id,
                "coverage": matrix.coverage_percentage,
                "gap_reason": "Insufficient test mapping" if matrix.coverage_percentage < 50 else "Partial coverage"
            }
            for req_id, matrix in matrices.items()
            if matrix.coverage_percentage < 80
        ]
        
        return {
            "total_requirements": total_requirements,
            "covered_requirements": covered_requirements,
            "coverage_percentage": (covered_requirements / max(1, total_requirements)) * 100,
            "average_coverage_depth": avg_coverage,
            "coverage_gaps": coverage_gaps
        }
    
    def _identify_test_dependencies(
        self, 
        functional_tests: List[Dict], 
        security_tests: List[Dict], 
        compliance_tests: List[Dict]
    ) -> List[Dict