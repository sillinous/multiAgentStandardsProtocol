"""
Agent Template System - Core component of Global Agent Factory

This system provides a library of APQC-aligned agent templates that serve as
blueprints for generating production-ready agents. Templates include:
- Business logic scaffolding
- Compliance requirements
- Performance optimizations
- Testing frameworks
- Documentation

Part of the Global Agent Factory as a Service (AgentFaaS) vision.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import sqlite3

logger = logging.getLogger(__name__)


class APQCCategory(Enum):
    """APQC Process Classification Framework Categories"""
    VISION_STRATEGY = "1.0"  # Develop Vision and Strategy
    PRODUCTS_SERVICES = "2.0"  # Develop and Manage Products and Services
    MARKET_CUSTOMERS = "3.0"  # Market and Sell Products and Services
    DELIVER = "4.0"  # Deliver Products and Services
    CUSTOMER_SERVICE = "5.0"  # Manage Customer Service
    HUMAN_CAPITAL = "6.0"  # Develop and Manage Human Capital
    IT = "7.0"  # Manage Information Technology
    FINANCIAL_RESOURCES = "8.0"  # Manage Financial Resources
    ASSETS = "9.0"  # Acquire, Construct, and Manage Assets
    RISK_COMPLIANCE = "10.0"  # Manage Enterprise Risk and Compliance
    RELATIONSHIPS = "11.0"  # Manage External Relationships
    KNOWLEDGE = "12.0"  # Develop and Manage Business Capabilities


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"  # General Data Protection Regulation
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"  # Service Organization Control 2
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO_27001 = "iso_27001"  # Information Security Management
    CCPA = "ccpa"  # California Consumer Privacy Act
    NIST = "nist"  # National Institute of Standards and Technology


class PerformanceTier(Enum):
    """Performance optimization tiers"""
    BASIC = "basic"  # Standard performance
    OPTIMIZED = "optimized"  # Enhanced performance
    ENTERPRISE = "enterprise"  # Maximum performance and scalability


class DeploymentFormat(Enum):
    """Agent deployment formats"""
    DOCKER = "docker"  # Docker container
    SERVERLESS = "serverless"  # AWS Lambda, Azure Functions
    KUBERNETES = "kubernetes"  # K8s deployment
    STANDALONE = "standalone"  # Standalone Python package


@dataclass
class TemplateCapability:
    """A specific capability provided by a template"""
    name: str
    description: str
    category: str  # learning, analysis, optimization, monitoring, etc.
    complexity: str  # low, medium, high
    estimated_lines: int
    dependencies: List[str] = field(default_factory=list)
    protocols_used: List[str] = field(default_factory=list)  # A2A, A2P, MCP, etc.


@dataclass
class TemplateRequirement:
    """Business or technical requirement"""
    requirement_id: str
    description: str
    category: str  # business, technical, compliance, performance
    priority: str  # must_have, should_have, nice_to_have
    validation_method: str  # How to verify requirement is met


@dataclass
class AgentTemplate:
    """Complete agent template specification"""
    template_id: str
    name: str
    description: str
    apqc_process: str  # e.g., "1.3.2"
    apqc_category: APQCCategory

    # Business context
    business_value: str  # Clear statement of business value
    use_cases: List[str]  # Concrete use cases
    target_personas: List[str]  # Who uses this agent

    # Technical specification
    capabilities: List[TemplateCapability]
    requirements: List[TemplateRequirement]
    suggested_integrations: List[str]  # Other agents to collaborate with

    # Code structure
    base_class: str = "EnhancedBaseAgent"  # Base class to inherit from
    actions: List[str] = field(default_factory=list)  # Agent actions
    data_models: List[str] = field(default_factory=list)  # Required data models

    # Compliance and standards
    default_compliance: List[ComplianceFramework] = field(default_factory=list)
    industry_standards: List[str] = field(default_factory=list)

    # Performance characteristics
    performance_tier: PerformanceTier = PerformanceTier.OPTIMIZED
    estimated_complexity: str = "medium"  # low, medium, high
    estimated_dev_time_hours: int = 8

    # Metadata
    version: str = "1.0.0"
    author: str = "Agent Factory"
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0

    # Template code
    template_code: Optional[str] = None  # Jinja2 template
    test_template: Optional[str] = None  # Test code template

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['apqc_category'] = self.apqc_category.value
        result['default_compliance'] = [c.value for c in self.default_compliance]
        result['performance_tier'] = self.performance_tier.value
        result['created_date'] = self.created_date.isoformat()
        result['last_updated'] = self.last_updated.isoformat()
        return result


@dataclass
class AgentSpecification:
    """User-provided specification for generating an agent"""
    # Basic information
    agent_name: str
    description: str
    business_objective: str

    # Template selection
    template_id: Optional[str] = None  # Specific template to use
    apqc_process: Optional[str] = None  # Auto-select template by APQC process

    # Customization
    custom_capabilities: List[str] = field(default_factory=list)
    integration_targets: List[str] = field(default_factory=list)  # Other agents

    # Compliance requirements
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    data_residency: Optional[str] = None  # e.g., "EU", "US"
    encryption_required: bool = True

    # Performance requirements
    performance_tier: PerformanceTier = PerformanceTier.OPTIMIZED
    max_response_time_ms: int = 1000
    concurrent_users: int = 100

    # Deployment preferences
    deployment_format: DeploymentFormat = DeploymentFormat.DOCKER
    cloud_provider: Optional[str] = None  # aws, azure, gcp

    # Additional metadata
    industry: Optional[str] = None
    organization_size: Optional[str] = None  # startup, smb, enterprise
    budget_tier: str = "standard"  # basic, standard, premium


class AgentTemplateSystem:
    """
    Manages agent templates and enables intelligent template selection,
    composition, and customization.
    """

    def __init__(self, db_path: str = "agent_templates.db"):
        self.db_path = db_path
        self._init_database()
        self._load_builtin_templates()

    def _init_database(self):
        """Initialize template database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                template_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                apqc_process TEXT,
                apqc_category TEXT,
                business_value TEXT,
                template_data TEXT,  -- JSON
                template_code TEXT,
                test_template TEXT,
                version TEXT,
                created_date TEXT,
                last_updated TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
        """)

        # Template capabilities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_capabilities (
                capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                name TEXT,
                description TEXT,
                category TEXT,
                complexity TEXT,
                estimated_lines INTEGER,
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            )
        """)

        # Template usage analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                agent_name TEXT,
                created_date TEXT,
                deployment_format TEXT,
                compliance_frameworks TEXT,  -- JSON
                success BOOLEAN,
                performance_metrics TEXT,  -- JSON
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            )
        """)

        # Template ratings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                user_id TEXT,
                rating INTEGER,  -- 1-5
                feedback TEXT,
                created_date TEXT,
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_apqc ON templates(apqc_process)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(apqc_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_template ON template_usage(template_id)")

        conn.commit()
        conn.close()

        logger.info(f"Agent template database initialized at {self.db_path}")

    def _load_builtin_templates(self):
        """Load built-in APQC-aligned templates"""
        # Check if templates already loaded
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            logger.info(f"Templates already loaded ({count} templates)")
            return

        # Create 10 high-value APQC templates
        templates = [
            self._create_strategic_initiative_template(),
            self._create_market_research_template(),
            self._create_customer_service_template(),
            self._create_talent_acquisition_template(),
            self._create_it_project_template(),
            self._create_financial_planning_template(),
            self._create_risk_management_template(),
            self._create_supplier_relationship_template(),
            self._create_knowledge_management_template(),
            self._create_quality_assurance_template(),
        ]

        for template in templates:
            self.register_template(template)

        logger.info(f"Loaded {len(templates)} built-in templates")

    def _create_strategic_initiative_template(self) -> AgentTemplate:
        """APQC 1.3 - Manage Strategic Initiatives"""
        return AgentTemplate(
            template_id="apqc-1.3-strategic-initiative-manager",
            name="Strategic Initiative Manager",
            description="Manages strategic initiatives with success prediction, blocker detection, and resource optimization",
            apqc_process="1.3",
            apqc_category=APQCCategory.VISION_STRATEGY,
            business_value="Increase initiative success rate by 40% through predictive analytics and autonomous optimization",
            use_cases=[
                "Digital transformation program management",
                "Market expansion initiatives",
                "Product launch coordination",
                "Organizational change programs"
            ],
            target_personas=["Chief Strategy Officer", "VP of Strategy", "Program Manager"],
            capabilities=[
                TemplateCapability(
                    name="Initiative Tracking",
                    description="Monitor initiative progress with health scoring",
                    category="monitoring",
                    complexity="medium",
                    estimated_lines=150,
                    protocols_used=["A2P", "ANP"]
                ),
                TemplateCapability(
                    name="Success Prediction",
                    description="ML-based success probability analysis",
                    category="analysis",
                    complexity="high",
                    estimated_lines=200,
                    dependencies=["sklearn"],
                    protocols_used=["A2A", "ACP"]
                ),
                TemplateCapability(
                    name="Blocker Detection",
                    description="Autonomous identification and resolution of blockers",
                    category="optimization",
                    complexity="high",
                    estimated_lines=180,
                    protocols_used=["A2A", "MCP"]
                ),
            ],
            requirements=[
                TemplateRequirement(
                    requirement_id="REQ-001",
                    description="Track at least 5 KPIs per initiative",
                    category="business",
                    priority="must_have",
                    validation_method="Unit test verification"
                ),
                TemplateRequirement(
                    requirement_id="REQ-002",
                    description="Predict success with >70% accuracy",
                    category="performance",
                    priority="should_have",
                    validation_method="Backtesting on historical data"
                ),
            ],
            suggested_integrations=["Project Management Agent", "Resource Allocation Agent"],
            actions=["track_initiative", "predict_success", "detect_blockers", "optimize_resources"],
            data_models=["Initiative", "Milestone", "Resource", "Risk"],
            default_compliance=[ComplianceFramework.SOC2],
            performance_tier=PerformanceTier.ENTERPRISE,
            estimated_complexity="high",
            estimated_dev_time_hours=16
        )

    def _create_market_research_template(self) -> AgentTemplate:
        """APQC 3.1 - Understand Markets, Customers, and Capabilities"""
        return AgentTemplate(
            template_id="apqc-3.1-market-research-analyst",
            name="Market Research Analyst",
            description="Analyzes market trends, competitor activities, and customer insights",
            apqc_process="3.1",
            apqc_category=APQCCategory.MARKET_CUSTOMERS,
            business_value="Reduce research time by 70% while increasing insight quality by 50%",
            use_cases=[
                "Competitive intelligence gathering",
                "Market sizing and segmentation",
                "Customer sentiment analysis",
                "Trend forecasting"
            ],
            target_personas=["CMO", "Market Research Manager", "Product Manager"],
            capabilities=[
                TemplateCapability(
                    name="Trend Analysis",
                    description="Identify emerging market trends from multiple sources",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=180,
                    protocols_used=["A2P", "MCP"]
                ),
                TemplateCapability(
                    name="Competitor Monitoring",
                    description="Track competitor activities and strategies",
                    category="monitoring",
                    complexity="medium",
                    estimated_lines=160,
                    protocols_used=["A2P"]
                ),
            ],
            requirements=[
                TemplateRequirement(
                    requirement_id="REQ-003",
                    description="Analyze at least 10 data sources",
                    category="technical",
                    priority="must_have",
                    validation_method="Integration test"
                ),
            ],
            suggested_integrations=["Content Analysis Agent", "Visualization Agent"],
            actions=["analyze_trends", "monitor_competitors", "segment_market"],
            data_models=["MarketTrend", "Competitor", "CustomerSegment"],
            default_compliance=[ComplianceFramework.GDPR, ComplianceFramework.CCPA],
            performance_tier=PerformanceTier.OPTIMIZED,
            estimated_complexity="medium",
            estimated_dev_time_hours=12
        )

    def _create_customer_service_template(self) -> AgentTemplate:
        """APQC 5.1 - Develop Customer Care/Customer Service Strategy"""
        return AgentTemplate(
            template_id="apqc-5.1-customer-service-optimizer",
            name="Customer Service Optimizer",
            description="Optimizes customer service operations with sentiment analysis and response automation",
            apqc_process="5.1",
            apqc_category=APQCCategory.CUSTOMER_SERVICE,
            business_value="Improve customer satisfaction by 35% while reducing response time by 60%",
            use_cases=[
                "Ticket routing and prioritization",
                "Sentiment-based escalation",
                "Response quality analysis",
                "Agent performance optimization"
            ],
            target_personas=["VP of Customer Success", "Customer Service Manager"],
            capabilities=[
                TemplateCapability(
                    name="Sentiment Analysis",
                    description="Real-time sentiment detection from customer interactions",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=140,
                    dependencies=["transformers"],
                    protocols_used=["A2P"]
                ),
                TemplateCapability(
                    name="Auto-Response Generation",
                    description="Generate contextual responses to common queries",
                    category="automation",
                    complexity="high",
                    estimated_lines=200,
                    dependencies=["openai"],
                    protocols_used=["A2P", "MCP"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Knowledge Base Agent", "Escalation Agent"],
            actions=["analyze_sentiment", "route_ticket", "generate_response"],
            data_models=["Ticket", "CustomerInteraction", "Response"],
            default_compliance=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
            performance_tier=PerformanceTier.ENTERPRISE,
            estimated_complexity="medium",
            estimated_dev_time_hours=10
        )

    def _create_talent_acquisition_template(self) -> AgentTemplate:
        """APQC 6.2 - Recruit, Source, and Select Employees"""
        return AgentTemplate(
            template_id="apqc-6.2-talent-acquisition-agent",
            name="Talent Acquisition Agent",
            description="Automates candidate sourcing, screening, and matching",
            apqc_process="6.2",
            apqc_category=APQCCategory.HUMAN_CAPITAL,
            business_value="Reduce time-to-hire by 50% while improving candidate quality by 30%",
            use_cases=[
                "Resume screening and ranking",
                "Candidate-job matching",
                "Interview scheduling optimization",
                "Diversity hiring analytics"
            ],
            target_personas=["CHRO", "Talent Acquisition Manager", "Recruiter"],
            capabilities=[
                TemplateCapability(
                    name="Resume Analysis",
                    description="Extract skills, experience, and qualifications from resumes",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=160,
                    protocols_used=["A2P"]
                ),
                TemplateCapability(
                    name="Candidate Matching",
                    description="Match candidates to roles using ML similarity",
                    category="optimization",
                    complexity="high",
                    estimated_lines=180,
                    dependencies=["sklearn"],
                    protocols_used=["A2A", "ACP"]
                ),
            ],
            requirements=[
                TemplateRequirement(
                    requirement_id="REQ-004",
                    description="Ensure bias-free screening (EEOC compliance)",
                    category="compliance",
                    priority="must_have",
                    validation_method="Bias audit test"
                ),
            ],
            suggested_integrations=["ATS Integration Agent", "Interview Scheduler Agent"],
            actions=["screen_resume", "match_candidate", "schedule_interview"],
            data_models=["Candidate", "JobPosting", "Interview"],
            default_compliance=[ComplianceFramework.GDPR],
            performance_tier=PerformanceTier.OPTIMIZED,
            estimated_complexity="medium",
            estimated_dev_time_hours=14
        )

    def _create_it_project_template(self) -> AgentTemplate:
        """APQC 7.3 - Manage IT Projects and Services"""
        return AgentTemplate(
            template_id="apqc-7.3-it-project-manager",
            name="IT Project Manager",
            description="Manages IT projects with automated tracking, risk detection, and resource optimization",
            apqc_process="7.3",
            apqc_category=APQCCategory.IT,
            business_value="Increase project delivery success rate by 45% through predictive risk management",
            use_cases=[
                "Software development project tracking",
                "Infrastructure upgrade management",
                "Security initiative coordination",
                "System integration projects"
            ],
            target_personas=["CIO", "IT Project Manager", "Development Lead"],
            capabilities=[
                TemplateCapability(
                    name="Project Tracking",
                    description="Monitor project metrics and milestones",
                    category="monitoring",
                    complexity="medium",
                    estimated_lines=150,
                    protocols_used=["A2P", "ANP"]
                ),
                TemplateCapability(
                    name="Risk Detection",
                    description="Identify and assess project risks proactively",
                    category="analysis",
                    complexity="high",
                    estimated_lines=170,
                    protocols_used=["A2A", "MCP"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Resource Planning Agent", "Bug Tracking Agent"],
            actions=["track_project", "detect_risks", "optimize_timeline"],
            data_models=["Project", "Task", "Risk", "Resource"],
            default_compliance=[ComplianceFramework.SOC2, ComplianceFramework.ISO_27001],
            performance_tier=PerformanceTier.ENTERPRISE,
            estimated_complexity="medium",
            estimated_dev_time_hours=12
        )

    def _create_financial_planning_template(self) -> AgentTemplate:
        """APQC 8.2 - Perform Planning, Budgeting, and Forecasting"""
        return AgentTemplate(
            template_id="apqc-8.2-financial-planning-agent",
            name="Financial Planning Agent",
            description="Automates financial planning, budgeting, and forecasting with scenario analysis",
            apqc_process="8.2",
            apqc_category=APQCCategory.FINANCIAL_RESOURCES,
            business_value="Improve forecast accuracy by 40% while reducing planning cycle time by 60%",
            use_cases=[
                "Annual budget creation",
                "Rolling forecasts",
                "Scenario planning",
                "Variance analysis"
            ],
            target_personas=["CFO", "FP&A Manager", "Controller"],
            capabilities=[
                TemplateCapability(
                    name="Budget Optimization",
                    description="Optimize budget allocation across departments",
                    category="optimization",
                    complexity="high",
                    estimated_lines=190,
                    dependencies=["scipy"],
                    protocols_used=["A2A", "ACP"]
                ),
                TemplateCapability(
                    name="Forecast Generation",
                    description="Generate financial forecasts using time series analysis",
                    category="analysis",
                    complexity="high",
                    estimated_lines=210,
                    dependencies=["statsmodels"],
                    protocols_used=["A2P"]
                ),
            ],
            requirements=[
                TemplateRequirement(
                    requirement_id="REQ-005",
                    description="Support SOX compliance for financial data",
                    category="compliance",
                    priority="must_have",
                    validation_method="Compliance audit"
                ),
            ],
            suggested_integrations=["ERP Integration Agent", "Reporting Agent"],
            actions=["optimize_budget", "generate_forecast", "analyze_variance"],
            data_models=["Budget", "Forecast", "Expense", "Revenue"],
            default_compliance=[ComplianceFramework.SOC2],
            performance_tier=PerformanceTier.ENTERPRISE,
            estimated_complexity="high",
            estimated_dev_time_hours=18
        )

    def _create_risk_management_template(self) -> AgentTemplate:
        """APQC 10.1 - Manage Enterprise Risk"""
        return AgentTemplate(
            template_id="apqc-10.1-risk-management-agent",
            name="Enterprise Risk Management Agent",
            description="Identifies, assesses, and monitors enterprise risks across all domains",
            apqc_process="10.1",
            apqc_category=APQCCategory.RISK_COMPLIANCE,
            business_value="Reduce risk exposure by 35% through proactive identification and mitigation",
            use_cases=[
                "Operational risk assessment",
                "Cybersecurity risk monitoring",
                "Financial risk analysis",
                "Regulatory compliance tracking"
            ],
            target_personas=["Chief Risk Officer", "Compliance Manager", "Audit Director"],
            capabilities=[
                TemplateCapability(
                    name="Risk Identification",
                    description="Autonomous identification of risks from multiple sources",
                    category="analysis",
                    complexity="high",
                    estimated_lines=180,
                    protocols_used=["A2P", "MCP"]
                ),
                TemplateCapability(
                    name="Risk Scoring",
                    description="Quantitative risk assessment and prioritization",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=150,
                    protocols_used=["A2A"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Security Monitoring Agent", "Compliance Agent"],
            actions=["identify_risks", "score_risk", "monitor_mitigation"],
            data_models=["Risk", "Control", "Incident", "Mitigation"],
            default_compliance=[ComplianceFramework.SOC2, ComplianceFramework.ISO_27001],
            performance_tier=PerformanceTier.ENTERPRISE,
            estimated_complexity="high",
            estimated_dev_time_hours=16
        )

    def _create_supplier_relationship_template(self) -> AgentTemplate:
        """APQC 11.2 - Manage Supplier Relationships"""
        return AgentTemplate(
            template_id="apqc-11.2-supplier-relationship-agent",
            name="Supplier Relationship Manager",
            description="Optimizes supplier relationships with performance tracking and risk assessment",
            apqc_process="11.2",
            apqc_category=APQCCategory.RELATIONSHIPS,
            business_value="Improve supplier performance by 30% while reducing procurement costs by 20%",
            use_cases=[
                "Supplier performance scorecarding",
                "Contract compliance monitoring",
                "Supplier risk assessment",
                "Negotiation support"
            ],
            target_personas=["CPO", "Procurement Manager", "Supplier Manager"],
            capabilities=[
                TemplateCapability(
                    name="Performance Tracking",
                    description="Monitor supplier KPIs and SLA compliance",
                    category="monitoring",
                    complexity="medium",
                    estimated_lines=140,
                    protocols_used=["A2P"]
                ),
                TemplateCapability(
                    name="Risk Assessment",
                    description="Assess supplier risks (financial, operational, geopolitical)",
                    category="analysis",
                    complexity="high",
                    estimated_lines=170,
                    protocols_used=["A2A", "MCP"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Contract Management Agent", "Payment Processing Agent"],
            actions=["track_performance", "assess_risk", "optimize_portfolio"],
            data_models=["Supplier", "Contract", "Performance", "Risk"],
            default_compliance=[ComplianceFramework.SOC2],
            performance_tier=PerformanceTier.OPTIMIZED,
            estimated_complexity="medium",
            estimated_dev_time_hours=12
        )

    def _create_knowledge_management_template(self) -> AgentTemplate:
        """APQC 12.1 - Manage Knowledge and Content"""
        return AgentTemplate(
            template_id="apqc-12.1-knowledge-management-agent",
            name="Knowledge Management Agent",
            description="Captures, organizes, and distributes organizational knowledge",
            apqc_process="12.1",
            apqc_category=APQCCategory.KNOWLEDGE,
            business_value="Reduce knowledge search time by 80% while improving knowledge reuse by 60%",
            use_cases=[
                "Document classification and tagging",
                "Knowledge graph construction",
                "Expert identification",
                "Content recommendation"
            ],
            target_personas=["CKO", "Knowledge Manager", "Information Architect"],
            capabilities=[
                TemplateCapability(
                    name="Content Classification",
                    description="Automatically classify and tag documents",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=160,
                    dependencies=["transformers"],
                    protocols_used=["A2P"]
                ),
                TemplateCapability(
                    name="Knowledge Graph",
                    description="Build and maintain knowledge graph of organizational knowledge",
                    category="learning",
                    complexity="high",
                    estimated_lines=200,
                    dependencies=["networkx"],
                    protocols_used=["A2A", "ACP"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Search Agent", "Content Creation Agent"],
            actions=["classify_content", "build_graph", "recommend_content"],
            data_models=["Document", "Tag", "KnowledgeNode", "Relationship"],
            default_compliance=[ComplianceFramework.GDPR, ComplianceFramework.SOC2],
            performance_tier=PerformanceTier.OPTIMIZED,
            estimated_complexity="high",
            estimated_dev_time_hours=14
        )

    def _create_quality_assurance_template(self) -> AgentTemplate:
        """APQC 2.4 - Manage Product and Service Quality"""
        return AgentTemplate(
            template_id="apqc-2.4-quality-assurance-agent",
            name="Quality Assurance Agent",
            description="Automates quality monitoring, defect detection, and process improvement",
            apqc_process="2.4",
            apqc_category=APQCCategory.PRODUCTS_SERVICES,
            business_value="Reduce defect rate by 45% while improving process efficiency by 35%",
            use_cases=[
                "Automated testing coordination",
                "Defect pattern analysis",
                "Quality metrics tracking",
                "Process improvement identification"
            ],
            target_personas=["VP of Quality", "QA Manager", "Process Improvement Lead"],
            capabilities=[
                TemplateCapability(
                    name="Defect Detection",
                    description="Identify defect patterns and root causes",
                    category="analysis",
                    complexity="medium",
                    estimated_lines=170,
                    protocols_used=["A2P", "A2A"]
                ),
                TemplateCapability(
                    name="Process Optimization",
                    description="Recommend process improvements based on quality data",
                    category="optimization",
                    complexity="high",
                    estimated_lines=190,
                    protocols_used=["A2A", "ACP"]
                ),
            ],
            requirements=[],
            suggested_integrations=["Testing Agent", "CI/CD Agent"],
            actions=["detect_defects", "track_metrics", "optimize_process"],
            data_models=["Defect", "TestCase", "QualityMetric", "Process"],
            default_compliance=[ComplianceFramework.ISO_27001],
            performance_tier=PerformanceTier.OPTIMIZED,
            estimated_complexity="medium",
            estimated_dev_time_hours=12
        )

    def register_template(self, template: AgentTemplate):
        """Register a new template in the system"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        template_dict = template.to_dict()

        cursor.execute("""
            INSERT OR REPLACE INTO templates (
                template_id, name, description, apqc_process, apqc_category,
                business_value, template_data, template_code, test_template,
                version, created_date, last_updated, usage_count, success_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template.template_id,
            template.name,
            template.description,
            template.apqc_process,
            template.apqc_category.value,
            template.business_value,
            json.dumps(template_dict),
            template.template_code,
            template.test_template,
            template.version,
            template.created_date.isoformat(),
            template.last_updated.isoformat(),
            template.usage_count,
            template.success_rate
        ))

        # Insert capabilities
        for cap in template.capabilities:
            cursor.execute("""
                INSERT INTO template_capabilities (
                    template_id, name, description, category, complexity, estimated_lines
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template.template_id,
                cap.name,
                cap.description,
                cap.category,
                cap.complexity,
                cap.estimated_lines
            ))

        conn.commit()
        conn.close()

        logger.info(f"Registered template: {template.template_id}")

    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """Retrieve a template by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT template_data FROM templates WHERE template_id = ?
        """, (template_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            template_dict = json.loads(row[0])
            # Reconstruct template (simplified - full reconstruction would need all fields)
            return template_dict

        return None

    def search_templates(
        self,
        apqc_process: Optional[str] = None,
        apqc_category: Optional[APQCCategory] = None,
        keyword: Optional[str] = None,
        min_success_rate: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search templates by various criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT template_id, name, description, apqc_process, business_value, success_rate FROM templates WHERE 1=1"
        params = []

        if apqc_process:
            query += " AND apqc_process = ?"
            params.append(apqc_process)

        if apqc_category:
            query += " AND apqc_category = ?"
            params.append(apqc_category.value)

        if keyword:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        if min_success_rate > 0:
            query += " AND success_rate >= ?"
            params.append(min_success_rate)

        query += " ORDER BY success_rate DESC, usage_count DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "template_id": row[0],
                "name": row[1],
                "description": row[2],
                "apqc_process": row[3],
                "business_value": row[4],
                "success_rate": row[5]
            }
            for row in rows
        ]

    def recommend_template(self, spec: AgentSpecification) -> List[Dict[str, Any]]:
        """Recommend templates based on agent specification"""
        recommendations = []

        # Primary: Match by APQC process if specified
        if spec.apqc_process:
            templates = self.search_templates(apqc_process=spec.apqc_process)
            if templates:
                return templates

        # Secondary: Keyword search on description and business objective
        keywords = spec.business_objective.lower().split()
        for keyword in keywords:
            if len(keyword) > 4:  # Skip short words
                templates = self.search_templates(keyword=keyword)
                recommendations.extend(templates)

        # Deduplicate and sort by success rate
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec['template_id'] not in seen:
                seen.add(rec['template_id'])
                unique_recs.append(rec)

        return sorted(unique_recs, key=lambda x: x['success_rate'], reverse=True)[:5]

    def record_usage(
        self,
        template_id: str,
        agent_name: str,
        deployment_format: DeploymentFormat,
        compliance_frameworks: List[ComplianceFramework],
        success: bool,
        performance_metrics: Optional[Dict[str, Any]] = None
    ):
        """Record template usage for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO template_usage (
                template_id, agent_name, created_date, deployment_format,
                compliance_frameworks, success, performance_metrics
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            template_id,
            agent_name,
            datetime.now().isoformat(),
            deployment_format.value,
            json.dumps([c.value for c in compliance_frameworks]),
            success,
            json.dumps(performance_metrics or {})
        ))

        # Update template statistics
        cursor.execute("""
            UPDATE templates
            SET usage_count = usage_count + 1,
                success_rate = (
                    SELECT AVG(CAST(success AS FLOAT))
                    FROM template_usage
                    WHERE template_id = ?
                )
            WHERE template_id = ?
        """, (template_id, template_id))

        conn.commit()
        conn.close()

        logger.info(f"Recorded usage for template {template_id}: success={success}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get template system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM templates")
        total_templates = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM template_usage")
        total_usage = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(success_rate) FROM templates")
        avg_success = cursor.fetchone()[0] or 0.0

        cursor.execute("""
            SELECT template_id, name, usage_count
            FROM templates
            ORDER BY usage_count DESC
            LIMIT 5
        """)
        top_templates = [
            {"template_id": row[0], "name": row[1], "usage_count": row[2]}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "total_templates": total_templates,
            "total_usage": total_usage,
            "average_success_rate": avg_success,
            "top_templates": top_templates
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        print("=== Agent Template System Demo ===\n")

        # Initialize system
        system = AgentTemplateSystem(db_path="agent_templates_demo.db")

        # Get statistics
        stats = system.get_statistics()
        print(f"Template Library Statistics:")
        print(f"  Total Templates: {stats['total_templates']}")
        print(f"  Total Usage: {stats['total_usage']}")
        print(f"  Average Success Rate: {stats['average_success_rate']:.1%}\n")

        # Search templates by APQC category
        print("Searching for Strategic Planning templates (APQC 1.x)...")
        results = system.search_templates(apqc_process="1.3")
        for result in results:
            print(f"  - {result['name']} (APQC {result['apqc_process']})")
            print(f"    Value: {result['business_value']}")
            print(f"    Success Rate: {result['success_rate']:.1%}\n")

        # Recommend template based on spec
        spec = AgentSpecification(
            agent_name="MyMarketAnalyzer",
            description="Analyze market trends and competitors",
            business_objective="Understand competitive landscape and market opportunities",
            compliance_frameworks=[ComplianceFramework.GDPR],
            performance_tier=PerformanceTier.OPTIMIZED
        )

        print(f"Recommending templates for: {spec.business_objective}")
        recommendations = system.recommend_template(spec)
        for rec in recommendations[:3]:
            print(f"  - {rec['name']} (Match score: {rec['success_rate']:.1%})")

        print("\n=== Demo Complete ===")

    asyncio.run(main())
