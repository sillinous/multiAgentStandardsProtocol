"""
Documentation Maintenance Agent
APQC Process Classification Framework: 11.2.5 - Manage IT Knowledge

Specialized agent for maintaining, tracking, and ensuring consistency of
architectural decisions, technical documentation, and knowledge management.
"""

import asyncio
import logging
import ast
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict
import difflib

logger = logging.getLogger(__name__)

class DocumentationType(Enum):
    """Types of documentation following APQC knowledge management classification"""
    ARCHITECTURAL_DECISION = "architectural_decision"      # 11.2.5.1 - Manage architectural decisions
    API_DOCUMENTATION = "api_documentation"               # 11.2.5.2 - Maintain API documentation
    CODE_DOCUMENTATION = "code_documentation"             # 11.2.5.3 - Manage code documentation
    OPERATIONAL_DOCUMENTATION = "operational_documentation" # 11.2.5.4 - Maintain operational docs
    SECURITY_DOCUMENTATION = "security_documentation"     # 11.2.5.5 - Document security practices
    DEPLOYMENT_DOCUMENTATION = "deployment_documentation"  # 11.2.5.6 - Maintain deployment guides
    USER_DOCUMENTATION = "user_documentation"             # 11.2.5.7 - Manage user documentation
    COMPLIANCE_DOCUMENTATION = "compliance_documentation"  # 11.2.5.8 - Maintain compliance docs
    PROCESS_DOCUMENTATION = "process_documentation"       # 11.2.5.9 - Document processes

class DocumentationStatus(Enum):
    """Status of documentation items"""
    CURRENT = "current"          # Up-to-date and accurate
    OUTDATED = "outdated"        # Needs updating
    MISSING = "missing"          # Required but doesn't exist
    DEPRECATED = "deprecated"    # No longer relevant
    DRAFT = "draft"             # Work in progress

class DocumentationPriority(Enum):
    """Priority levels for documentation maintenance"""
    CRITICAL = "critical"        # Required for compliance/security
    HIGH = "high"               # Important for operations
    MEDIUM = "medium"           # Helpful for development
    LOW = "low"                 # Nice to have

@dataclass
class ArchitecturalDecision:
    """Architectural Decision Record (ADR) following industry standards"""
    id: str
    title: str
    status: str  # proposed, accepted, deprecated, superseded
    date: datetime
    context: str
    decision: str
    consequences: str
    alternatives_considered: List[str]
    stakeholders: List[str]
    related_decisions: List[str] = field(default_factory=list)
    implementation_status: str = "not_started"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentationItem:
    """Individual documentation item with tracking metadata"""
    id: str
    title: str
    documentation_type: DocumentationType
    file_path: Optional[str]
    url: Optional[str]
    status: DocumentationStatus
    priority: DocumentationPriority
    description: str
    content_hash: Optional[str]
    last_updated: datetime
    last_verified: Optional[datetime]
    assigned_maintainer: Optional[str]
    related_code_files: List[str] = field(default_factory=list)
    related_documentation: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    review_frequency: Optional[str] = None  # weekly, monthly, quarterly
    next_review_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentationGap:
    """Identified gap in documentation coverage"""
    id: str
    gap_type: str
    title: str
    description: str
    affected_components: List[str]
    suggested_documentation_type: DocumentationType
    priority: DocumentationPriority
    effort_estimate: str
    business_impact: str
    detected_at: datetime
    related_code_changes: List[str] = field(default_factory=list)

@dataclass
class DocumentationReport:
    """Comprehensive documentation health report"""
    report_id: str
    generated_at: datetime
    project_root: str
    overall_score: float
    coverage_percentage: float
    documentation_items: List[DocumentationItem]
    architectural_decisions: List[ArchitecturalDecision]
    identified_gaps: List[DocumentationGap]
    maintenance_recommendations: List[str]
    compliance_status: Dict[str, Any]
    quality_metrics: Dict[str, float]

class DocumentationMaintenanceAgent:
    """
    Enterprise-grade documentation maintenance agent

    Implements APQC Process 11.2.5 - Manage IT Knowledge
    Provides systematic documentation tracking, gap analysis, and maintenance planning
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.documentation_registry: Dict[str, DocumentationItem] = {}
        self.architectural_decisions: Dict[str, ArchitecturalDecision] = {}
        self.documentation_templates = self._initialize_documentation_templates()
        self.compliance_requirements = self._initialize_compliance_requirements()
        self.documentation_rules = self._initialize_documentation_rules()

    def _initialize_documentation_templates(self) -> Dict[str, str]:
        """Initialize templates for different documentation types"""
        return {
            "architectural_decision": """# ADR-{id}: {title}

## Status
{status}

## Context
{context}

## Decision
{decision}

## Consequences
{consequences}

## Alternatives Considered
{alternatives}

## Implementation Notes
{implementation_notes}

## Related Decisions
{related_decisions}

Date: {date}
Stakeholders: {stakeholders}
""",
            "api_documentation": """# {api_name} API Documentation

## Overview
{overview}

## Authentication
{authentication}

## Endpoints
{endpoints}

## Error Handling
{error_handling}

## Rate Limiting
{rate_limiting}

## Examples
{examples}

Last Updated: {last_updated}
""",
            "security_documentation": """# Security Documentation: {title}

## Security Requirements
{requirements}

## Threat Model
{threat_model}

## Security Controls
{controls}

## Compliance
{compliance}

## Incident Response
{incident_response}

## Review Schedule
{review_schedule}
""",
            "deployment_guide": """# Deployment Guide: {service_name}

## Prerequisites
{prerequisites}

## Deployment Steps
{deployment_steps}

## Configuration
{configuration}

## Monitoring
{monitoring}

## Rollback Procedures
{rollback}

## Troubleshooting
{troubleshooting}
"""
        }

    def _initialize_compliance_requirements(self) -> Dict[str, List[str]]:
        """Initialize compliance requirements for documentation"""
        return {
            "security": [
                "Security architecture documentation",
                "Threat model documentation",
                "Security control documentation",
                "Incident response procedures",
                "Security review schedules"
            ],
            "api": [
                "API specification documentation",
                "Authentication documentation",
                "Rate limiting documentation",
                "Error handling documentation",
                "API versioning strategy"
            ],
            "deployment": [
                "Deployment procedure documentation",
                "Environment configuration documentation",
                "Rollback procedure documentation",
                "Monitoring and alerting documentation",
                "Disaster recovery procedures"
            ],
            "architecture": [
                "System architecture overview",
                "Component interaction diagrams",
                "Data flow documentation",
                "Integration point documentation",
                "Architectural decision records"
            ]
        }

    def _initialize_documentation_rules(self) -> Dict[str, Dict]:
        """Initialize rules for documentation requirements"""
        return {
            "code_documentation": {
                "min_docstring_coverage": 80.0,
                "required_for_public_apis": True,
                "required_for_complex_functions": True,
                "complexity_threshold": 10
            },
            "api_documentation": {
                "required_for_all_endpoints": True,
                "must_include_examples": True,
                "must_include_error_codes": True,
                "review_frequency": "monthly"
            },
            "architectural_decisions": {
                "required_for_major_changes": True,
                "must_include_alternatives": True,
                "stakeholder_approval_required": True,
                "review_frequency": "quarterly"
            },
            "security_documentation": {
                "required_for_sensitive_components": True,
                "must_include_threat_model": True,
                "review_frequency": "monthly",
                "compliance_audit_required": True
            }
        }

    async def analyze_documentation_health(self) -> DocumentationReport:
        """
        Perform comprehensive documentation health analysis

        Returns:
            Detailed documentation health report
        """
        logger.info("📚 Starting comprehensive documentation health analysis...")

        report_id = f"doc_health_{int(datetime.now().timestamp())}"
        start_time = datetime.now()

        # Step 1: Discover existing documentation
        await self._discover_documentation()

        # Step 2: Analyze code documentation coverage
        code_doc_analysis = await self._analyze_code_documentation()

        # Step 3: Identify documentation gaps
        gaps = await self._identify_documentation_gaps()

        # Step 4: Assess architectural decision coverage
        adr_analysis = await self._analyze_architectural_decisions()

        # Step 5: Check compliance requirements
        compliance_status = await self._assess_compliance_status()

        # Step 6: Calculate quality metrics
        quality_metrics = await self._calculate_documentation_metrics()

        # Step 7: Generate maintenance recommendations
        recommendations = await self._generate_maintenance_recommendations(gaps, quality_metrics)

        # Step 8: Calculate overall documentation score
        overall_score, coverage_percentage = await self._calculate_documentation_score(quality_metrics)

        # Compile comprehensive report
        report = DocumentationReport(
            report_id=report_id,
            generated_at=start_time,
            project_root=str(self.project_root),
            overall_score=overall_score,
            coverage_percentage=coverage_percentage,
            documentation_items=list(self.documentation_registry.values()),
            architectural_decisions=list(self.architectural_decisions.values()),
            identified_gaps=gaps,
            maintenance_recommendations=recommendations,
            compliance_status=compliance_status,
            quality_metrics=quality_metrics
        )

        analysis_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Documentation analysis completed in {analysis_time:.2f}s - Score: {overall_score:.1f}/100")

        return report

    async def _discover_documentation(self):
        """Discover existing documentation across the project"""
        # Look for markdown files
        markdown_files = list(self.project_root.rglob("*.md"))

        for md_file in markdown_files:
            if self._should_include_file(str(md_file)):
                doc_item = await self._analyze_markdown_file(md_file)
                if doc_item:
                    self.documentation_registry[doc_item.id] = doc_item

        # Look for documentation in code comments
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            if self._should_include_file(str(py_file)):
                inline_docs = await self._extract_inline_documentation(py_file)
                for doc in inline_docs:
                    self.documentation_registry[doc.id] = doc

        # Look for specific documentation patterns
        await self._discover_api_documentation()
        await self._discover_architectural_decisions()
        await self._discover_deployment_documentation()

    async def _analyze_markdown_file(self, file_path: Path) -> Optional[DocumentationItem]:
        """Analyze a markdown file and create documentation item"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract title from first heading
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem

            # Determine documentation type
            doc_type = self._classify_documentation_type(file_path, content)

            # Calculate content hash
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

            # Get file modification time
            last_updated = datetime.fromtimestamp(file_path.stat().st_mtime)

            # Determine priority based on file location and content
            priority = self._determine_documentation_priority(file_path, content)

            # Check if documentation is current
            status = await self._assess_documentation_status(file_path, content)

            doc_item = DocumentationItem(
                id=f"md_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                title=title,
                documentation_type=doc_type,
                file_path=str(file_path.relative_to(self.project_root)),
                url=None,
                status=status,
                priority=priority,
                description=self._extract_description(content),
                content_hash=content_hash,
                last_updated=last_updated,
                last_verified=None,
                assigned_maintainer=None,
                related_code_files=self._find_related_code_files(content),
                tags=self._extract_tags(content),
                metadata={
                    "file_size": file_path.stat().st_size,
                    "line_count": len(content.split('\n')),
                    "word_count": len(content.split())
                }
            )

            return doc_item

        except Exception as e:
            logger.error(f"Error analyzing markdown file {file_path}: {e}")
            return None

    async def _extract_inline_documentation(self, file_path: Path) -> List[DocumentationItem]:
        """Extract inline documentation from code files"""
        docs = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                doc_item = DocumentationItem(
                    id=f"module_doc_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                    title=f"Module documentation: {file_path.stem}",
                    documentation_type=DocumentationType.CODE_DOCUMENTATION,
                    file_path=str(file_path.relative_to(self.project_root)),
                    url=None,
                    status=DocumentationStatus.CURRENT,
                    priority=DocumentationPriority.MEDIUM,
                    description=module_docstring[:200] + "..." if len(module_docstring) > 200 else module_docstring,
                    content_hash=hashlib.md5(module_docstring.encode()).hexdigest(),
                    last_updated=datetime.fromtimestamp(file_path.stat().st_mtime),
                    last_verified=None,
                    assigned_maintainer=None,
                    tags=["inline", "module", "docstring"],
                    metadata={"docstring_length": len(module_docstring)}
                )
                docs.append(doc_item)

            # Extract class and function docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        doc_item = DocumentationItem(
                            id=f"{node.__class__.__name__.lower()}_doc_{file_path.stem}_{node.name}",
                            title=f"{node.__class__.__name__} documentation: {node.name}",
                            documentation_type=DocumentationType.CODE_DOCUMENTATION,
                            file_path=str(file_path.relative_to(self.project_root)),
                            url=None,
                            status=DocumentationStatus.CURRENT,
                            priority=DocumentationPriority.MEDIUM,
                            description=docstring[:200] + "..." if len(docstring) > 200 else docstring,
                            content_hash=hashlib.md5(docstring.encode()).hexdigest(),
                            last_updated=datetime.fromtimestamp(file_path.stat().st_mtime),
                            last_verified=None,
                            assigned_maintainer=None,
                            tags=["inline", node.__class__.__name__.lower(), "docstring"],
                            metadata={
                                "component_name": node.name,
                                "line_number": node.lineno,
                                "docstring_length": len(docstring)
                            }
                        )
                        docs.append(doc_item)

        except Exception as e:
            logger.error(f"Error extracting inline documentation from {file_path}: {e}")

        return docs

    async def _discover_api_documentation(self):
        """Discover API documentation"""
        # Look for OpenAPI/Swagger specifications
        api_spec_files = list(self.project_root.rglob("*.yaml")) + \
                        list(self.project_root.rglob("*.yml")) + \
                        list(self.project_root.rglob("openapi.json")) + \
                        list(self.project_root.rglob("swagger.json"))

        for spec_file in api_spec_files:
            if "api" in str(spec_file).lower() or "swagger" in str(spec_file).lower():
                doc_item = DocumentationItem(
                    id=f"api_spec_{hashlib.md5(str(spec_file).encode()).hexdigest()[:8]}",
                    title=f"API Specification: {spec_file.name}",
                    documentation_type=DocumentationType.API_DOCUMENTATION,
                    file_path=str(spec_file.relative_to(self.project_root)),
                    url=None,
                    status=DocumentationStatus.CURRENT,
                    priority=DocumentationPriority.HIGH,
                    description="API specification document",
                    content_hash=None,
                    last_updated=datetime.fromtimestamp(spec_file.stat().st_mtime),
                    last_verified=None,
                    assigned_maintainer=None,
                    tags=["api", "specification", "openapi"],
                    metadata={"spec_format": spec_file.suffix}
                )
                self.documentation_registry[doc_item.id] = doc_item

    async def _discover_architectural_decisions(self):
        """Discover Architectural Decision Records (ADRs)"""
        # Look for ADR files
        adr_patterns = ["adr", "decision", "architectural"]

        for pattern in adr_patterns:
            adr_files = list(self.project_root.rglob(f"*{pattern}*/*.md")) + \
                       list(self.project_root.rglob(f"*{pattern}*.md"))

            for adr_file in adr_files:
                if self._is_adr_file(adr_file):
                    adr = await self._parse_adr_file(adr_file)
                    if adr:
                        self.architectural_decisions[adr.id] = adr

    async def _discover_deployment_documentation(self):
        """Discover deployment and operational documentation"""
        deployment_patterns = ["deploy", "docker", "k8s", "kubernetes", "ci", "cd"]

        for pattern in deployment_patterns:
            deployment_files = list(self.project_root.rglob(f"*{pattern}*")) + \
                             list(self.project_root.rglob("Dockerfile*")) + \
                             list(self.project_root.rglob("docker-compose*")) + \
                             list(self.project_root.rglob("*.dockerfile"))

            for deploy_file in deployment_files:
                if deploy_file.is_file() and deploy_file.suffix in ['.md', '.yml', '.yaml', '.json']:
                    doc_item = DocumentationItem(
                        id=f"deploy_doc_{hashlib.md5(str(deploy_file).encode()).hexdigest()[:8]}",
                        title=f"Deployment Documentation: {deploy_file.name}",
                        documentation_type=DocumentationType.DEPLOYMENT_DOCUMENTATION,
                        file_path=str(deploy_file.relative_to(self.project_root)),
                        url=None,
                        status=DocumentationStatus.CURRENT,
                        priority=DocumentationPriority.HIGH,
                        description="Deployment and operational documentation",
                        content_hash=None,
                        last_updated=datetime.fromtimestamp(deploy_file.stat().st_mtime),
                        last_verified=None,
                        assigned_maintainer=None,
                        tags=["deployment", "operations", pattern],
                        metadata={"file_type": deploy_file.suffix}
                    )
                    self.documentation_registry[doc_item.id] = doc_item

    def _classify_documentation_type(self, file_path: Path, content: str) -> DocumentationType:
        """Classify the type of documentation based on path and content"""
        file_path_str = str(file_path).lower()
        content_lower = content.lower()

        if any(term in file_path_str for term in ["adr", "decision", "architectural"]):
            return DocumentationType.ARCHITECTURAL_DECISION
        elif any(term in file_path_str for term in ["api", "swagger", "openapi"]):
            return DocumentationType.API_DOCUMENTATION
        elif any(term in file_path_str for term in ["deploy", "docker", "k8s", "ci", "cd"]):
            return DocumentationType.DEPLOYMENT_DOCUMENTATION
        elif any(term in file_path_str for term in ["security", "auth", "encryption"]):
            return DocumentationType.SECURITY_DOCUMENTATION
        elif any(term in file_path_str for term in ["user", "guide", "tutorial", "how-to"]):
            return DocumentationType.USER_DOCUMENTATION
        elif any(term in file_path_str for term in ["process", "procedure", "workflow"]):
            return DocumentationType.PROCESS_DOCUMENTATION
        elif any(term in file_path_str for term in ["compliance", "audit", "regulation"]):
            return DocumentationType.COMPLIANCE_DOCUMENTATION
        elif any(term in content_lower for term in ["api", "endpoint", "request", "response"]):
            return DocumentationType.API_DOCUMENTATION
        else:
            return DocumentationType.OPERATIONAL_DOCUMENTATION

    def _determine_documentation_priority(self, file_path: Path, content: str) -> DocumentationPriority:
        """Determine priority based on file location and content"""
        file_path_str = str(file_path).lower()
        content_lower = content.lower()

        # Critical priority indicators
        if any(term in file_path_str for term in ["security", "compliance", "emergency"]):
            return DocumentationPriority.CRITICAL
        if any(term in content_lower for term in ["critical", "security", "vulnerability", "compliance"]):
            return DocumentationPriority.CRITICAL

        # High priority indicators
        if any(term in file_path_str for term in ["api", "deploy", "architecture", "readme"]):
            return DocumentationPriority.HIGH
        if file_path.name.lower() == "readme.md":
            return DocumentationPriority.HIGH

        # Medium priority indicators
        if any(term in file_path_str for term in ["guide", "tutorial", "process"]):
            return DocumentationPriority.MEDIUM

        return DocumentationPriority.LOW

    async def _assess_documentation_status(self, file_path: Path, content: str) -> DocumentationStatus:
        """Assess the current status of documentation"""
        # Check last modification time
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        age_days = (datetime.now() - last_modified).days

        # Check for outdated indicators
        if age_days > 365:  # Over a year old
            return DocumentationStatus.OUTDATED
        elif any(term in content.lower() for term in ["todo", "fixme", "outdated", "deprecated"]):
            return DocumentationStatus.OUTDATED
        elif any(term in content.lower() for term in ["draft", "work in progress", "wip"]):
            return DocumentationStatus.DRAFT
        elif any(term in content.lower() for term in ["deprecated", "obsolete", "no longer"]):
            return DocumentationStatus.DEPRECATED
        else:
            return DocumentationStatus.CURRENT

    def _extract_description(self, content: str) -> str:
        """Extract description from documentation content"""
        # Look for description after title
        lines = content.split('\n')
        description_lines = []

        in_description = False
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                in_description = True
                continue
            elif line.startswith('#') and in_description:
                break
            elif in_description and line:
                description_lines.append(line)
                if len(' '.join(description_lines)) > 200:
                    break

        description = ' '.join(description_lines)
        return description[:200] + "..." if len(description) > 200 else description

    def _find_related_code_files(self, content: str) -> List[str]:
        """Find code files referenced in documentation"""
        # Look for file references in content
        file_patterns = [
            r'`([^`]+\.py)`',
            r'`([^`]+\.js)`',
            r'`([^`]+\.ts)`',
            r'\[.*\]\(([^)]+\.py)\)',
            r'\[.*\]\(([^)]+\.js)\)',
            r'(app/[^\\s\\)]+\\.py)',
        ]

        related_files = []
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            related_files.extend(matches)

        return list(set(related_files))

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from documentation content"""
        tags = []

        # Look for explicit tags
        tag_patterns = [
            r'(?i)tags?:\s*([^\n]+)',
            r'(?i)keywords?:\s*([^\n]+)',
            r'#(\w+)',  # Hashtags
        ]

        for pattern in tag_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    tags.extend([tag.strip() for tag in match.split(',')])

        # Infer tags from content
        content_lower = content.lower()
        if 'api' in content_lower:
            tags.append('api')
        if 'security' in content_lower:
            tags.append('security')
        if 'deployment' in content_lower:
            tags.append('deployment')

        return list(set(tags))

    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included in documentation analysis"""
        exclude_patterns = [
            '.git/', '.venv/', 'venv/', 'node_modules/',
            '__pycache__/', '.pytest_cache/', '.idea/',
            'target/', 'build/', 'dist/'
        ]

        for pattern in exclude_patterns:
            if pattern in file_path:
                return False

        return True

    def _is_adr_file(self, file_path: Path) -> bool:
        """Check if file is an Architectural Decision Record"""
        file_name = file_path.name.lower()
        return (any(term in file_name for term in ['adr', 'decision']) or
                file_path.parent.name.lower() in ['adr', 'adrs', 'decisions'])

    async def _parse_adr_file(self, file_path: Path) -> Optional[ArchitecturalDecision]:
        """Parse an ADR file and extract structured information"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract ADR components using patterns
            title_match = re.search(r'^#\s+ADR[-\s]*(\d+):\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
            if not title_match:
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)

            if not title_match:
                return None

            adr_id = title_match.group(1) if title_match.group(1).isdigit() else str(hash(file_path))
            title = title_match.group(2) if title_match.group(1).isdigit() else title_match.group(1)

            # Extract sections
            status = self._extract_adr_section(content, "status") or "draft"
            context = self._extract_adr_section(content, "context") or ""
            decision = self._extract_adr_section(content, "decision") or ""
            consequences = self._extract_adr_section(content, "consequences") or ""

            # Extract alternatives
            alternatives_section = self._extract_adr_section(content, "alternatives")
            alternatives = [alt.strip() for alt in alternatives_section.split('\n') if alt.strip()] if alternatives_section else []

            # Extract stakeholders
            stakeholders_section = self._extract_adr_section(content, "stakeholders")
            stakeholders = [sh.strip() for sh in stakeholders_section.split(',') if sh.strip()] if stakeholders_section else []

            adr = ArchitecturalDecision(
                id=f"adr_{adr_id}",
                title=title,
                status=status.lower(),
                date=datetime.fromtimestamp(file_path.stat().st_mtime),
                context=context,
                decision=decision,
                consequences=consequences,
                alternatives_considered=alternatives,
                stakeholders=stakeholders,
                tags=["adr", "architecture", "decision"],
                metadata={
                    "file_path": str(file_path.relative_to(self.project_root)),
                    "word_count": len(content.split())
                }
            )

            return adr

        except Exception as e:
            logger.error(f"Error parsing ADR file {file_path}: {e}")
            return None

    def _extract_adr_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract a specific section from ADR content"""
        pattern = rf"##\s*{section_name}\s*\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def _analyze_code_documentation(self) -> Dict[str, Any]:
        """Analyze code documentation coverage"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if self._should_include_file(str(f))]

        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        total_modules = len(python_files)
        documented_modules = 0

        documentation_quality_scores = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                # Check module docstring
                if ast.get_docstring(tree):
                    documented_modules += 1

                # Analyze functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1

                        # Check documentation quality
                        docstring = ast.get_docstring(node)
                        if docstring:
                            quality_score = self._assess_docstring_quality(docstring)
                            documentation_quality_scores.append(quality_score)

                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                        if ast.get_docstring(node):
                            documented_classes += 1

            except Exception as e:
                logger.error(f"Error analyzing code documentation for {py_file}: {e}")

        # Calculate coverage percentages
        function_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        class_coverage = (documented_classes / total_classes * 100) if total_classes > 0 else 0
        module_coverage = (documented_modules / total_modules * 100) if total_modules > 0 else 0

        avg_quality_score = sum(documentation_quality_scores) / len(documentation_quality_scores) if documentation_quality_scores else 0

        return {
            "function_coverage": function_coverage,
            "class_coverage": class_coverage,
            "module_coverage": module_coverage,
            "average_quality_score": avg_quality_score,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_modules": total_modules,
            "documented_functions": documented_functions,
            "documented_classes": documented_classes,
            "documented_modules": documented_modules
        }

    def _assess_docstring_quality(self, docstring: str) -> float:
        """Assess the quality of a docstring"""
        score = 0

        # Basic existence (20 points)
        if docstring:
            score += 20

        # Length (20 points)
        if len(docstring) > 50:
            score += 20

        # Contains parameter documentation (20 points)
        if any(keyword in docstring.lower() for keyword in ['param', 'arg', 'parameter']):
            score += 20

        # Contains return documentation (20 points)
        if any(keyword in docstring.lower() for keyword in ['return', 'returns']):
            score += 20

        # Contains examples (20 points)
        if any(keyword in docstring.lower() for keyword in ['example', 'usage', '>>>']):
            score += 20

        return score

    async def _identify_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in documentation coverage"""
        gaps = []

        # Check for missing API documentation
        api_gaps = await self._identify_api_documentation_gaps()
        gaps.extend(api_gaps)

        # Check for missing architectural documentation
        arch_gaps = await self._identify_architectural_documentation_gaps()
        gaps.extend(arch_gaps)

        # Check for missing security documentation
        security_gaps = await self._identify_security_documentation_gaps()
        gaps.extend(security_gaps)

        # Check for missing deployment documentation
        deployment_gaps = await self._identify_deployment_documentation_gaps()
        gaps.extend(deployment_gaps)

        # Check for missing code documentation
        code_gaps = await self._identify_code_documentation_gaps()
        gaps.extend(code_gaps)

        return gaps

    async def _identify_api_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in API documentation"""
        gaps = []

        # Find API endpoints in code
        python_files = list(self.project_root.rglob("*.py"))
        api_endpoints = []

        for py_file in python_files:
            if "api" in str(py_file) or "endpoint" in str(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Look for FastAPI/Flask route decorators
                    route_patterns = [
                        r'@\w*\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                        r'@app\.route\s*\(\s*["\']([^"\']+)["\']'
                    ]

                    for pattern in route_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            api_endpoints.append({
                                "endpoint": match,
                                "file": str(py_file.relative_to(self.project_root))
                            })

                except Exception as e:
                    logger.error(f"Error analyzing API endpoints in {py_file}: {e}")

        # Check if API endpoints have documentation
        documented_endpoints = set()
        for doc_item in self.documentation_registry.values():
            if doc_item.documentation_type == DocumentationType.API_DOCUMENTATION:
                # Extract endpoints from documentation
                if doc_item.file_path:
                    try:
                        with open(self.project_root / doc_item.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            doc_content = f.read()
                        endpoint_matches = re.findall(r'/api/[^\s\)]+', doc_content)
                        documented_endpoints.update(endpoint_matches)
                    except Exception:
                        pass

        # Identify undocumented endpoints
        for endpoint_info in api_endpoints:
            endpoint = endpoint_info["endpoint"]
            if not any(documented_endpoint in endpoint for documented_endpoint in documented_endpoints):
                gap = DocumentationGap(
                    id=f"api_gap_{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                    gap_type="missing_api_documentation",
                    title=f"Missing API documentation for {endpoint}",
                    description=f"API endpoint {endpoint} lacks comprehensive documentation",
                    affected_components=[endpoint_info["file"]],
                    suggested_documentation_type=DocumentationType.API_DOCUMENTATION,
                    priority=DocumentationPriority.HIGH,
                    effort_estimate="2-4 hours",
                    business_impact="Developers may struggle to use API correctly",
                    detected_at=datetime.now()
                )
                gaps.append(gap)

        return gaps

    async def _identify_architectural_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in architectural documentation"""
        gaps = []

        # Check for major architectural components without documentation
        major_components = [
            "database.py", "models.py", "config.py", "main.py",
            "security.py", "auth.py", "middleware.py"
        ]

        for component in major_components:
            component_files = list(self.project_root.rglob(component))
            for comp_file in component_files:
                # Check if component has architectural documentation
                has_arch_doc = any(
                    doc.documentation_type == DocumentationType.ARCHITECTURAL_DECISION and
                    str(comp_file.relative_to(self.project_root)) in doc.related_code_files
                    for doc in self.documentation_registry.values()
                )

                if not has_arch_doc:
                    gap = DocumentationGap(
                        id=f"arch_gap_{hashlib.md5(str(comp_file).encode()).hexdigest()[:8]}",
                        gap_type="missing_architectural_documentation",
                        title=f"Missing architectural documentation for {comp_file.name}",
                        description=f"Core component {comp_file.name} lacks architectural decision documentation",
                        affected_components=[str(comp_file.relative_to(self.project_root))],
                        suggested_documentation_type=DocumentationType.ARCHITECTURAL_DECISION,
                        priority=DocumentationPriority.HIGH,
                        effort_estimate="4-8 hours",
                        business_impact="Architectural decisions may not be tracked or understood",
                        detected_at=datetime.now()
                    )
                    gaps.append(gap)

        return gaps

    async def _identify_security_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in security documentation"""
        gaps = []

        # Look for security-related code without documentation
        security_patterns = [
            "auth", "security", "encrypt", "decrypt", "hash", "token",
            "jwt", "oauth", "password", "credential"
        ]

        python_files = list(self.project_root.rglob("*.py"))
        security_files = []

        for py_file in python_files:
            if any(pattern in str(py_file).lower() for pattern in security_patterns):
                security_files.append(py_file)

        # Check if security files have security documentation
        for sec_file in security_files:
            has_security_doc = any(
                doc.documentation_type == DocumentationType.SECURITY_DOCUMENTATION and
                str(sec_file.relative_to(self.project_root)) in doc.related_code_files
                for doc in self.documentation_registry.values()
            )

            if not has_security_doc:
                gap = DocumentationGap(
                    id=f"security_gap_{hashlib.md5(str(sec_file).encode()).hexdigest()[:8]}",
                    gap_type="missing_security_documentation",
                    title=f"Missing security documentation for {sec_file.name}",
                    description=f"Security-related component {sec_file.name} lacks security documentation",
                    affected_components=[str(sec_file.relative_to(self.project_root))],
                    suggested_documentation_type=DocumentationType.SECURITY_DOCUMENTATION,
                    priority=DocumentationPriority.CRITICAL,
                    effort_estimate="2-6 hours",
                    business_impact="Security vulnerabilities may not be properly documented",
                    detected_at=datetime.now()
                )
                gaps.append(gap)

        return gaps

    async def _identify_deployment_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in deployment documentation"""
        gaps = []

        # Check for deployment files without documentation
        deployment_files = list(self.project_root.rglob("Dockerfile*")) + \
                          list(self.project_root.rglob("docker-compose*")) + \
                          list(self.project_root.rglob("*.yml")) + \
                          list(self.project_root.rglob("*.yaml"))

        deployment_files = [f for f in deployment_files if
                          any(term in str(f).lower() for term in ["deploy", "docker", "k8s", "ci", "cd"])]

        for deploy_file in deployment_files:
            has_deploy_doc = any(
                doc.documentation_type == DocumentationType.DEPLOYMENT_DOCUMENTATION and
                str(deploy_file.relative_to(self.project_root)) in doc.related_code_files
                for doc in self.documentation_registry.values()
            )

            if not has_deploy_doc:
                gap = DocumentationGap(
                    id=f"deploy_gap_{hashlib.md5(str(deploy_file).encode()).hexdigest()[:8]}",
                    gap_type="missing_deployment_documentation",
                    title=f"Missing deployment documentation for {deploy_file.name}",
                    description=f"Deployment configuration {deploy_file.name} lacks comprehensive documentation",
                    affected_components=[str(deploy_file.relative_to(self.project_root))],
                    suggested_documentation_type=DocumentationType.DEPLOYMENT_DOCUMENTATION,
                    priority=DocumentationPriority.HIGH,
                    effort_estimate="1-3 hours",
                    business_impact="Deployment process may be unclear or error-prone",
                    detected_at=datetime.now()
                )
                gaps.append(gap)

        return gaps

    async def _identify_code_documentation_gaps(self) -> List[DocumentationGap]:
        """Identify gaps in code documentation"""
        gaps = []

        # Check for complex functions without documentation
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if self._should_include_file(str(f))]

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Calculate function complexity
                        complexity = self._calculate_function_complexity(node)

                        # Check if complex function lacks documentation
                        if complexity > 5 and not ast.get_docstring(node):
                            gap = DocumentationGap(
                                id=f"code_gap_{py_file.stem}_{node.name}",
                                gap_type="missing_function_documentation",
                                title=f"Missing documentation for complex function {node.name}",
                                description=f"Function {node.name} has complexity {complexity} but lacks documentation",
                                affected_components=[str(py_file.relative_to(self.project_root))],
                                suggested_documentation_type=DocumentationType.CODE_DOCUMENTATION,
                                priority=DocumentationPriority.MEDIUM,
                                effort_estimate="30-60 minutes",
                                business_impact="Function behavior may be unclear to developers",
                                detected_at=datetime.now()
                            )
                            gaps.append(gap)

            except Exception as e:
                logger.error(f"Error analyzing code documentation gaps for {py_file}: {e}")

        return gaps

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    async def _analyze_architectural_decisions(self) -> Dict[str, Any]:
        """Analyze architectural decision coverage and quality"""
        total_adrs = len(self.architectural_decisions)

        # Analyze ADR status distribution
        status_distribution = {}
        for adr in self.architectural_decisions.values():
            status_distribution[adr.status] = status_distribution.get(adr.status, 0) + 1

        # Calculate ADR quality metrics
        quality_scores = []
        for adr in self.architectural_decisions.values():
            score = 0
            if adr.context:
                score += 25
            if adr.decision:
                score += 25
            if adr.consequences:
                score += 25
            if adr.alternatives_considered:
                score += 25
            quality_scores.append(score)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Check for recent ADRs
        recent_adrs = [adr for adr in self.architectural_decisions.values()
                      if (datetime.now() - adr.date).days <= 90]

        return {
            "total_adrs": total_adrs,
            "status_distribution": status_distribution,
            "average_quality_score": avg_quality,
            "recent_adrs": len(recent_adrs),
            "quality_scores": quality_scores
        }

    async def _assess_compliance_status(self) -> Dict[str, Any]:
        """Assess compliance with documentation requirements"""
        compliance_status = {}

        for category, requirements in self.compliance_requirements.items():
            category_compliance = {
                "total_requirements": len(requirements),
                "met_requirements": 0,
                "missing_requirements": [],
                "compliance_percentage": 0
            }

            for requirement in requirements:
                # Check if requirement is met by existing documentation
                requirement_met = any(
                    requirement.lower() in doc.title.lower() or
                    requirement.lower() in doc.description.lower()
                    for doc in self.documentation_registry.values()
                )

                if requirement_met:
                    category_compliance["met_requirements"] += 1
                else:
                    category_compliance["missing_requirements"].append(requirement)

            category_compliance["compliance_percentage"] = (
                category_compliance["met_requirements"] /
                category_compliance["total_requirements"] * 100
            )

            compliance_status[category] = category_compliance

        # Calculate overall compliance
        total_requirements = sum(len(reqs) for reqs in self.compliance_requirements.values())
        total_met = sum(status["met_requirements"] for status in compliance_status.values())

        compliance_status["overall"] = {
            "total_requirements": total_requirements,
            "met_requirements": total_met,
            "compliance_percentage": (total_met / total_requirements * 100) if total_requirements > 0 else 0
        }

        return compliance_status

    async def _calculate_documentation_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive documentation quality metrics"""
        total_docs = len(self.documentation_registry)

        # Status distribution
        status_counts = {}
        for doc in self.documentation_registry.values():
            status_counts[doc.status.value] = status_counts.get(doc.status.value, 0) + 1

        # Priority distribution
        priority_counts = {}
        for doc in self.documentation_registry.values():
            priority_counts[doc.priority.value] = priority_counts.get(doc.priority.value, 0) + 1

        # Type distribution
        type_counts = {}
        for doc in self.documentation_registry.values():
            type_counts[doc.documentation_type.value] = type_counts.get(doc.documentation_type.value, 0) + 1

        # Calculate freshness score
        current_docs = status_counts.get("current", 0)
        freshness_score = (current_docs / total_docs * 100) if total_docs > 0 else 0

        # Calculate completeness score based on compliance
        compliance_status = await self._assess_compliance_status()
        completeness_score = compliance_status["overall"]["compliance_percentage"]

        # Calculate quality score based on code documentation analysis
        code_analysis = await self._analyze_code_documentation()
        quality_score = (
            code_analysis["function_coverage"] * 0.3 +
            code_analysis["class_coverage"] * 0.3 +
            code_analysis["module_coverage"] * 0.2 +
            code_analysis["average_quality_score"] * 0.2
        )

        return {
            "total_documentation_items": total_docs,
            "freshness_score": freshness_score,
            "completeness_score": completeness_score,
            "quality_score": quality_score,
            "current_documents": status_counts.get("current", 0),
            "outdated_documents": status_counts.get("outdated", 0),
            "missing_documents": status_counts.get("missing", 0),
            "critical_priority_docs": priority_counts.get("critical", 0),
            "high_priority_docs": priority_counts.get("high", 0),
            "code_documentation_coverage": code_analysis["function_coverage"],
            "api_documentation_items": type_counts.get("api_documentation", 0),
            "architectural_decisions": len(self.architectural_decisions)
        }

    async def _calculate_documentation_score(self, metrics: Dict[str, float]) -> Tuple[float, float]:
        """Calculate overall documentation score and coverage percentage"""
        # Weight different aspects of documentation quality
        weights = {
            "freshness_score": 0.25,
            "completeness_score": 0.35,
            "quality_score": 0.25,
            "code_documentation_coverage": 0.15
        }

        overall_score = sum(
            metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )

        # Coverage percentage is based on completeness and code coverage
        coverage_percentage = (
            metrics.get("completeness_score", 0) * 0.7 +
            metrics.get("code_documentation_coverage", 0) * 0.3
        )

        return overall_score, coverage_percentage

    async def _generate_maintenance_recommendations(self, gaps: List[DocumentationGap], metrics: Dict[str, float]) -> List[str]:
        """Generate actionable maintenance recommendations"""
        recommendations = []

        # Critical gaps
        critical_gaps = [gap for gap in gaps if gap.priority == DocumentationPriority.CRITICAL]
        if critical_gaps:
            recommendations.append(
                f"🚨 URGENT: Address {len(critical_gaps)} critical documentation gaps immediately"
            )

        # Security documentation
        security_gaps = [gap for gap in gaps if "security" in gap.gap_type]
        if security_gaps:
            recommendations.append(
                f"🔒 Security: Create documentation for {len(security_gaps)} security-related components"
            )

        # API documentation
        api_gaps = [gap for gap in gaps if "api" in gap.gap_type]
        if api_gaps:
            recommendations.append(
                f"📡 API: Document {len(api_gaps)} undocumented API endpoints"
            )

        # Code documentation coverage
        code_coverage = metrics.get("code_documentation_coverage", 0)
        if code_coverage < 80:
            recommendations.append(
                f"📝 Code: Improve code documentation coverage from {code_coverage:.1f}% to 80%+"
            )

        # Outdated documentation
        outdated_count = metrics.get("outdated_documents", 0)
        if outdated_count > 0:
            recommendations.append(
                f"📅 Maintenance: Update {outdated_count} outdated documentation items"
            )

        # ADR recommendations
        adr_count = metrics.get("architectural_decisions", 0)
        if adr_count < 5:
            recommendations.append(
                f"🏗️  Architecture: Create more ADRs - currently only {adr_count} documented decisions"
            )

        # Compliance recommendations
        completeness_score = metrics.get("completeness_score", 0)
        if completeness_score < 90:
            recommendations.append(
                f"✅ Compliance: Improve documentation completeness from {completeness_score:.1f}% to 90%+"
            )

        # Positive reinforcement
        overall_score = metrics.get("freshness_score", 0) + metrics.get("quality_score", 0)
        if overall_score > 150:
            recommendations.append(
                f"🎉 Good progress: Documentation quality is improving - maintain momentum"
            )

        return recommendations

    async def create_documentation_template(self, doc_type: DocumentationType, context: Dict[str, Any]) -> str:
        """Create documentation template based on type and context"""
        template_key = doc_type.value
        if template_key in self.documentation_templates:
            template = self.documentation_templates[template_key]

            # Fill template with context
            try:
                filled_template = template.format(**context)
                return filled_template
            except KeyError as e:
                logger.warning(f"Missing context key for template: {e}")
                return template

        return f"# {doc_type.value.replace('_', ' ').title()}\n\nTODO: Add documentation content"

    async def export_documentation_report(self, report: DocumentationReport, output_path: str) -> str:
        """Export documentation report to file"""
        report_data = asdict(report)

        # Convert datetime objects for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (DocumentationType, DocumentationStatus, DocumentationPriority)):
                return obj.value
            return str(obj)

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=json_serializer)

        logger.info(f"📚 Documentation report exported to {output_path}")
        return output_path

# Initialize the documentation maintenance agent
documentation_maintainer = DocumentationMaintenanceAgent(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)