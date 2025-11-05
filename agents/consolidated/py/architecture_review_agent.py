"""
Architecture Review Agent
APQC Process Classification Framework: 11.2.1 - Develop IT Architecture

Specialized agent for assessing architectural patterns, identifying inconsistencies,
and recommending improvements aligned with enterprise architecture standards.
"""

import asyncio
import logging
import os
import ast
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class ArchitecturalViolationType(Enum):
    """Types of architectural violations following APQC IT architecture standards"""
    LAYERING_VIOLATION = "layering_violation"           # 11.2.1.1 - Define architecture layers
    CIRCULAR_DEPENDENCY = "circular_dependency"         # 11.2.1.2 - Manage dependencies
    TIGHT_COUPLING = "tight_coupling"                   # 11.2.1.3 - Ensure loose coupling
    SINGLE_RESPONSIBILITY = "single_responsibility"     # 11.2.1.4 - Design cohesive components
    INTERFACE_SEGREGATION = "interface_segregation"     # 11.2.1.5 - Define clean interfaces
    DEPENDENCY_INVERSION = "dependency_inversion"       # 11.2.1.6 - Manage abstractions
    OPEN_CLOSED = "open_closed"                        # 11.2.1.7 - Design extensible systems
    SECURITY_ARCHITECTURE = "security_architecture"    # 11.2.4.1 - Integrate security by design
    PERFORMANCE_ARCHITECTURE = "performance_architecture" # 11.2.3.1 - Design for performance
    SCALABILITY_PATTERN = "scalability_pattern"        # 11.2.3.2 - Design for scale

class ArchitecturalPatternCompliance(Enum):
    """Compliance levels for architectural patterns"""
    COMPLIANT = "compliant"
    MINOR_DEVIATION = "minor_deviation"
    SIGNIFICANT_VIOLATION = "significant_violation"
    CRITICAL_VIOLATION = "critical_violation"

@dataclass
class ArchitecturalComponent:
    """Representation of an architectural component"""
    name: str
    type: str  # module, class, function, service
    file_path: str
    dependencies: List[str]
    dependents: List[str]
    layer: Optional[str]
    responsibility: str
    complexity_metrics: Dict[str, float]
    security_implications: List[str]
    performance_characteristics: Dict[str, Any]

@dataclass
class ArchitecturalViolation:
    """Individual architectural violation with detailed analysis"""
    id: str
    violation_type: ArchitecturalViolationType
    severity: str  # critical, high, medium, low
    title: str
    description: str
    affected_components: List[str]
    violation_details: Dict[str, Any]
    impact_assessment: str
    architectural_principle: str
    recommended_refactoring: str
    effort_estimation: str
    business_justification: str
    compliance_level: ArchitecturalPatternCompliance
    detected_at: datetime
    apqc_process_reference: str

@dataclass
class ArchitecturalMetrics:
    """Comprehensive architectural quality metrics"""
    total_components: int
    dependency_count: int
    cyclic_dependencies: int
    average_coupling: float
    average_cohesion: float
    layer_violations: int
    abstraction_level: float
    modularity_score: float
    maintainability_index: float
    architectural_debt_ratio: float

class ArchitectureReviewAgent:
    """
    Enterprise-grade architectural review agent

    Implements APQC Process 11.2.1 - Develop IT Architecture
    Provides systematic assessment of architectural quality and compliance
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.components: Dict[str, ArchitecturalComponent] = {}
        self.violations: List[ArchitecturalViolation] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.layer_definitions = self._initialize_layer_definitions()
        self.architectural_patterns = self._initialize_architectural_patterns()

    def _initialize_layer_definitions(self) -> Dict[str, Dict]:
        """Define expected architectural layers following enterprise patterns"""
        return {
            "presentation": {
                "patterns": ["api", "endpoints", "routes", "controllers"],
                "allowed_dependencies": ["business", "data"],
                "description": "User interface and API layer"
            },
            "business": {
                "patterns": ["services", "domain", "core", "logic"],
                "allowed_dependencies": ["data", "infrastructure"],
                "description": "Business logic and domain models"
            },
            "data": {
                "patterns": ["models", "repositories", "database", "crud"],
                "allowed_dependencies": ["infrastructure"],
                "description": "Data access and persistence layer"
            },
            "infrastructure": {
                "patterns": ["config", "logging", "monitoring", "external"],
                "allowed_dependencies": [],
                "description": "Cross-cutting concerns and external integrations"
            }
        }

    def _initialize_architectural_patterns(self) -> Dict[str, Dict]:
        """Initialize architectural pattern definitions and rules"""
        return {
            "mvc_pattern": {
                "description": "Model-View-Controller architectural pattern",
                "required_separation": ["models", "views", "controllers"],
                "violation_indicators": ["mixed_concerns", "tight_coupling"]
            },
            "clean_architecture": {
                "description": "Clean Architecture principles",
                "dependency_rules": ["inward_dependencies_only"],
                "violation_indicators": ["outward_dependencies", "framework_coupling"]
            },
            "microservices": {
                "description": "Microservices architectural patterns",
                "required_patterns": ["service_independence", "api_contracts"],
                "violation_indicators": ["shared_databases", "synchronous_coupling"]
            },
            "event_driven": {
                "description": "Event-driven architecture patterns",
                "required_patterns": ["event_producers", "event_consumers", "message_bus"],
                "violation_indicators": ["direct_service_calls", "tight_temporal_coupling"]
            }
        }

    async def analyze_architecture(self) -> Dict[str, Any]:
        """
        Perform comprehensive architectural analysis

        Returns:
            Detailed architectural assessment report
        """
        logger.info("🏗️  Starting architectural analysis...")

        # Step 1: Discover architectural components
        await self._discover_components()

        # Step 2: Build dependency graph
        await self._build_dependency_graph()

        # Step 3: Analyze architectural violations
        await self._analyze_violations()

        # Step 4: Calculate architectural metrics
        metrics = await self._calculate_metrics()

        # Step 5: Generate recommendations
        recommendations = await self._generate_recommendations()

        # Compile comprehensive report
        analysis_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "components": {name: asdict(component) for name, component in self.components.items()},
            "violations": [asdict(violation) for violation in self.violations],
            "metrics": asdict(metrics),
            "dependency_analysis": await self._analyze_dependencies(),
            "layer_compliance": await self._analyze_layer_compliance(),
            "pattern_compliance": await self._analyze_pattern_compliance(),
            "recommendations": recommendations,
            "architectural_debt_assessment": await self._assess_architectural_debt()
        }

        logger.info(f"✅ Architectural analysis completed: {len(self.violations)} violations found")

        return analysis_report

    async def _discover_components(self):
        """Discover and catalog architectural components"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not self._should_exclude_file(str(f))]

        for file_path in python_files:
            try:
                components = await self._analyze_file_components(file_path)
                for component in components:
                    self.components[component.name] = component
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")

    async def _analyze_file_components(self, file_path: Path) -> List[ArchitecturalComponent]:
        """Analyze individual file for architectural components"""
        components = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                tree = ast.parse(content)

            # Analyze classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    component = await self._analyze_class_component(node, file_path, content)
                    components.append(component)

                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                    if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
                ):
                    component = await self._analyze_function_component(node, file_path, content)
                    components.append(component)

            # Create module-level component if no classes/functions found
            if not components:
                module_component = await self._analyze_module_component(file_path, content)
                components.append(module_component)

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")

        return components

    async def _analyze_class_component(self, node: ast.ClassDef, file_path: Path, content: str) -> ArchitecturalComponent:
        """Analyze class as architectural component"""
        # Extract dependencies from imports and usage
        dependencies = self._extract_dependencies(content)

        # Determine layer based on file path and naming patterns
        layer = self._determine_component_layer(str(file_path), node.name)

        # Calculate complexity metrics
        complexity_metrics = self._calculate_component_complexity(node, content)

        # Assess security implications
        security_implications = self._assess_security_implications(node, content)

        # Analyze performance characteristics
        performance_characteristics = self._analyze_performance_characteristics(node, content)

        return ArchitecturalComponent(
            name=f"{file_path.stem}.{node.name}",
            type="class",
            file_path=str(file_path.relative_to(self.project_root)),
            dependencies=dependencies,
            dependents=[],  # Will be populated during dependency graph building
            layer=layer,
            responsibility=self._determine_responsibility(node, content),
            complexity_metrics=complexity_metrics,
            security_implications=security_implications,
            performance_characteristics=performance_characteristics
        )

    async def _analyze_function_component(self, node: ast.FunctionDef, file_path: Path, content: str) -> ArchitecturalComponent:
        """Analyze function as architectural component"""
        dependencies = self._extract_dependencies(content)
        layer = self._determine_component_layer(str(file_path), node.name)
        complexity_metrics = self._calculate_component_complexity(node, content)

        return ArchitecturalComponent(
            name=f"{file_path.stem}.{node.name}",
            type="function",
            file_path=str(file_path.relative_to(self.project_root)),
            dependencies=dependencies,
            dependents=[],
            layer=layer,
            responsibility=self._determine_responsibility(node, content),
            complexity_metrics=complexity_metrics,
            security_implications=self._assess_security_implications(node, content),
            performance_characteristics=self._analyze_performance_characteristics(node, content)
        )

    async def _analyze_module_component(self, file_path: Path, content: str) -> ArchitecturalComponent:
        """Analyze module as architectural component"""
        dependencies = self._extract_dependencies(content)
        layer = self._determine_component_layer(str(file_path), file_path.stem)

        return ArchitecturalComponent(
            name=file_path.stem,
            type="module",
            file_path=str(file_path.relative_to(self.project_root)),
            dependencies=dependencies,
            dependents=[],
            layer=layer,
            responsibility=self._determine_module_responsibility(file_path, content),
            complexity_metrics=self._calculate_module_complexity(content),
            security_implications=self._assess_module_security_implications(content),
            performance_characteristics=self._analyze_module_performance_characteristics(content)
        )

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from code content"""
        dependencies = []

        # Extract import statements
        import_patterns = [
            r"from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import",
            r"import\s+([a-zA-Z_][a-zA-Z0-9_.]*)"
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)

        # Filter out standard library and external dependencies
        filtered_dependencies = []
        for dep in dependencies:
            if dep.startswith('app.') or not '.' in dep:
                filtered_dependencies.append(dep)

        return list(set(filtered_dependencies))

    def _determine_component_layer(self, file_path: str, component_name: str) -> Optional[str]:
        """Determine which architectural layer a component belongs to"""
        file_path_lower = file_path.lower()
        component_name_lower = component_name.lower()

        for layer_name, layer_config in self.layer_definitions.items():
            for pattern in layer_config["patterns"]:
                if pattern in file_path_lower or pattern in component_name_lower:
                    return layer_name

        return None

    def _calculate_component_complexity(self, node: ast.AST, content: str) -> Dict[str, float]:
        """Calculate complexity metrics for a component"""
        metrics = {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(node),
            "lines_of_code": len([line for line in content.split('\n') if line.strip()]),
            "method_count": len([n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]),
            "dependency_count": len(self._extract_dependencies(content))
        }

        # Calculate maintainability index (simplified)
        metrics["maintainability_index"] = max(0, (171 - 5.2 *
                                                   (metrics["lines_of_code"] / 100) -
                                                   0.23 * metrics["cyclomatic_complexity"] -
                                                   16.2 * (metrics["dependency_count"] / 10)))

        return metrics

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _assess_security_implications(self, node: ast.AST, content: str) -> List[str]:
        """Assess security implications of a component"""
        implications = []

        security_patterns = {
            "hardcoded_secrets": r"(password|secret|key)\s*=\s*['\"][^'\"]+['\"]",
            "sql_injection": r"execute\s*\(\s*['\"].*%.*['\"]",
            "unsafe_eval": r"eval\s*\(",
            "shell_injection": r"os\.system\s*\(",
            "unsafe_pickle": r"pickle\.loads\s*\("
        }

        for issue_type, pattern in security_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                implications.append(issue_type)

        return implications

    def _analyze_performance_characteristics(self, node: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze performance characteristics of a component"""
        characteristics = {
            "async_operations": len(re.findall(r"async\s+def", content)),
            "database_operations": len(re.findall(r"\.query\(|\.filter\(|\.all\(\)", content)),
            "loops": len([n for n in ast.walk(node) if isinstance(n, (ast.For, ast.While))]),
            "network_calls": len(re.findall(r"requests\.|http\.|aiohttp\.", content))
        }

        # Assess performance risk
        risk_score = (
            characteristics["database_operations"] * 0.3 +
            characteristics["loops"] * 0.2 +
            characteristics["network_calls"] * 0.4 +
            characteristics["async_operations"] * -0.1  # Async is good for performance
        )

        characteristics["performance_risk_score"] = max(0, risk_score)

        return characteristics

    def _determine_responsibility(self, node: ast.AST, content: str) -> str:
        """Determine the primary responsibility of a component"""
        # Analyze method names, docstrings, and patterns to infer responsibility
        responsibilities = {
            "data_access": ["crud", "repository", "dao", "query", "database"],
            "business_logic": ["service", "logic", "process", "business", "domain"],
            "presentation": ["controller", "endpoint", "route", "api", "view"],
            "configuration": ["config", "settings", "environment", "setup"],
            "utility": ["util", "helper", "tool", "common", "shared"],
            "authentication": ["auth", "login", "security", "permission"],
            "validation": ["validate", "check", "verify", "sanitize"],
            "integration": ["connector", "client", "adapter", "wrapper"]
        }

        content_lower = content.lower()
        for responsibility, keywords in responsibilities.items():
            if any(keyword in content_lower for keyword in keywords):
                return responsibility

        return "general"

    def _determine_module_responsibility(self, file_path: Path, content: str) -> str:
        """Determine responsibility for a module-level component"""
        file_name = file_path.name.lower()

        if any(term in file_name for term in ["main", "app"]):
            return "application_entry_point"
        elif any(term in file_name for term in ["config", "settings"]):
            return "configuration"
        elif any(term in file_name for term in ["model", "database", "db"]):
            return "data_modeling"
        elif any(term in file_name for term in ["api", "endpoint", "route"]):
            return "api_interface"
        else:
            return self._determine_responsibility(None, content)

    def _calculate_module_complexity(self, content: str) -> Dict[str, float]:
        """Calculate complexity metrics for a module"""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "lines_of_code": len(non_empty_lines),
            "import_count": len(re.findall(r"^(import|from)", content, re.MULTILINE)),
            "function_count": len(re.findall(r"^def\s+", content, re.MULTILINE)),
            "class_count": len(re.findall(r"^class\s+", content, re.MULTILINE))
        }

    def _assess_module_security_implications(self, content: str) -> List[str]:
        """Assess security implications for a module"""
        return self._assess_security_implications(None, content)

    def _analyze_module_performance_characteristics(self, content: str) -> Dict[str, Any]:
        """Analyze performance characteristics for a module"""
        return self._analyze_performance_characteristics(None, content)

    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from analysis"""
        exclusion_patterns = [
            r".*\.venv/.*", r".*venv/.*", r".*__pycache__/.*",
            r".*\.git/.*", r".*node_modules/.*", r".*\.dist/.*",
            r".*\.build/.*", r".*\.pytest_cache/.*", r".*migrations/.*"
        ]

        for pattern in exclusion_patterns:
            if re.search(pattern, file_path):
                return True
        return False

    async def _build_dependency_graph(self):
        """Build comprehensive dependency graph"""
        for component_name, component in self.components.items():
            for dependency in component.dependencies:
                # Find matching components
                for dep_component_name in self.components.keys():
                    if dependency in dep_component_name or dep_component_name in dependency:
                        self.dependency_graph[component_name].add(dep_component_name)
                        # Update dependents
                        self.components[dep_component_name].dependents.append(component_name)

    async def _analyze_violations(self):
        """Analyze architectural violations"""
        # Check for circular dependencies
        await self._check_circular_dependencies()

        # Check layer violations
        await self._check_layer_violations()

        # Check coupling violations
        await self._check_coupling_violations()

        # Check single responsibility violations
        await self._check_single_responsibility_violations()

        # Check security architecture violations
        await self._check_security_architecture_violations()

        # Check performance architecture violations
        await self._check_performance_architecture_violations()

    async def _check_circular_dependencies(self):
        """Detect circular dependency violations"""
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for component in self.components.keys():
            if component not in visited:
                if has_cycle(component):
                    violation = ArchitecturalViolation(
                        id=f"circular_dep_{hash(component)}",
                        violation_type=ArchitecturalViolationType.CIRCULAR_DEPENDENCY,
                        severity="high",
                        title=f"Circular dependency detected involving {component}",
                        description="Circular dependencies make code difficult to test, understand, and maintain",
                        affected_components=[component],
                        violation_details={"dependency_cycle": list(self.dependency_graph.get(component, []))},
                        impact_assessment="High impact on maintainability and testability",
                        architectural_principle="Dependency Acyclic Principle (DAP)",
                        recommended_refactoring="Break circular dependency through interface introduction or dependency inversion",
                        effort_estimation="4-8 hours",
                        business_justification="Improves code maintainability and reduces development time",
                        compliance_level=ArchitecturalPatternCompliance.SIGNIFICANT_VIOLATION,
                        detected_at=datetime.now(),
                        apqc_process_reference="11.2.1.2"
                    )
                    self.violations.append(violation)

    async def _check_layer_violations(self):
        """Check for architectural layer violations"""
        for component_name, component in self.components.items():
            if not component.layer:
                continue

            layer_config = self.layer_definitions.get(component.layer, {})
            allowed_dependencies = layer_config.get("allowed_dependencies", [])

            for dependency in component.dependencies:
                dep_component = next((c for c in self.components.values()
                                   if dependency in c.name), None)

                if dep_component and dep_component.layer:
                    if dep_component.layer not in allowed_dependencies:
                        violation = ArchitecturalViolation(
                            id=f"layer_violation_{hash(component_name + dependency)}",
                            violation_type=ArchitecturalViolationType.LAYERING_VIOLATION,
                            severity="medium",
                            title=f"Layer violation: {component.layer} depending on {dep_component.layer}",
                            description=f"Component in {component.layer} layer should not depend on {dep_component.layer} layer",
                            affected_components=[component_name, dep_component.name],
                            violation_details={
                                "violating_layer": component.layer,
                                "target_layer": dep_component.layer,
                                "allowed_dependencies": allowed_dependencies
                            },
                            impact_assessment="Violates architectural layering principles",
                            architectural_principle="Layered Architecture Pattern",
                            recommended_refactoring="Refactor dependency to follow proper layering",
                            effort_estimation="2-4 hours",
                            business_justification="Maintains architectural integrity and system comprehensibility",
                            compliance_level=ArchitecturalPatternCompliance.MINOR_DEVIATION,
                            detected_at=datetime.now(),
                            apqc_process_reference="11.2.1.1"
                        )
                        self.violations.append(violation)

    async def _check_coupling_violations(self):
        """Check for tight coupling violations"""
        for component_name, component in self.components.items():
            dependency_count = len(component.dependencies)
            dependent_count = len(component.dependents)

            # High coupling threshold
            if dependency_count > 10:
                violation = ArchitecturalViolation(
                    id=f"coupling_violation_{hash(component_name)}",
                    violation_type=ArchitecturalViolationType.TIGHT_COUPLING,
                    severity="medium",
                    title=f"High coupling detected in {component_name}",
                    description=f"Component has {dependency_count} dependencies, indicating tight coupling",
                    affected_components=[component_name],
                    violation_details={
                        "dependency_count": dependency_count,
                        "dependent_count": dependent_count,
                        "coupling_score": dependency_count + dependent_count
                    },
                    impact_assessment="High coupling reduces maintainability and increases change impact",
                    architectural_principle="Loose Coupling Principle",
                    recommended_refactoring="Reduce dependencies through interface segregation and dependency injection",
                    effort_estimation="8-16 hours",
                    business_justification="Improves system maintainability and reduces defect propagation",
                    compliance_level=ArchitecturalPatternCompliance.MINOR_DEVIATION,
                    detected_at=datetime.now(),
                    apqc_process_reference="11.2.1.3"
                )
                self.violations.append(violation)

    async def _check_single_responsibility_violations(self):
        """Check for single responsibility principle violations"""
        for component_name, component in self.components.items():
            complexity = component.complexity_metrics.get("cyclomatic_complexity", 0)
            method_count = component.complexity_metrics.get("method_count", 0)

            # High complexity indicates possible SRP violation
            if complexity > 15 or method_count > 20:
                violation = ArchitecturalViolation(
                    id=f"srp_violation_{hash(component_name)}",
                    violation_type=ArchitecturalViolationType.SINGLE_RESPONSIBILITY,
                    severity="medium",
                    title=f"Single Responsibility Principle violation in {component_name}",
                    description=f"Component has high complexity (CC: {complexity}) suggesting multiple responsibilities",
                    affected_components=[component_name],
                    violation_details={
                        "cyclomatic_complexity": complexity,
                        "method_count": method_count,
                        "responsibility": component.responsibility
                    },
                    impact_assessment="Violates SRP, making component difficult to maintain and test",
                    architectural_principle="Single Responsibility Principle (SRP)",
                    recommended_refactoring="Split component into smaller, focused components",
                    effort_estimation="16-32 hours",
                    business_justification="Improves code maintainability and testability",
                    compliance_level=ArchitecturalPatternCompliance.SIGNIFICANT_VIOLATION,
                    detected_at=datetime.now(),
                    apqc_process_reference="11.2.1.4"
                )
                self.violations.append(violation)

    async def _check_security_architecture_violations(self):
        """Check for security architecture violations"""
        for component_name, component in self.components.items():
            if component.security_implications:
                severity = "critical" if any(issue in ["hardcoded_secrets", "sql_injection"]
                                           for issue in component.security_implications) else "high"

                violation = ArchitecturalViolation(
                    id=f"security_violation_{hash(component_name)}",
                    violation_type=ArchitecturalViolationType.SECURITY_ARCHITECTURE,
                    severity=severity,
                    title=f"Security architecture violation in {component_name}",
                    description=f"Component contains security vulnerabilities: {', '.join(component.security_implications)}",
                    affected_components=[component_name],
                    violation_details={"security_issues": component.security_implications},
                    impact_assessment="Critical security risk requiring immediate attention",
                    architectural_principle="Security by Design",
                    recommended_refactoring="Implement secure coding practices and remove vulnerabilities",
                    effort_estimation="4-8 hours",
                    business_justification="Prevents security breaches and maintains regulatory compliance",
                    compliance_level=ArchitecturalPatternCompliance.CRITICAL_VIOLATION,
                    detected_at=datetime.now(),
                    apqc_process_reference="11.2.4.1"
                )
                self.violations.append(violation)

    async def _check_performance_architecture_violations(self):
        """Check for performance architecture violations"""
        for component_name, component in self.components.items():
            perf_risk = component.performance_characteristics.get("performance_risk_score", 0)

            if perf_risk > 5:
                violation = ArchitecturalViolation(
                    id=f"performance_violation_{hash(component_name)}",
                    violation_type=ArchitecturalViolationType.PERFORMANCE_ARCHITECTURE,
                    severity="medium",
                    title=f"Performance architecture concern in {component_name}",
                    description=f"Component has high performance risk score: {perf_risk}",
                    affected_components=[component_name],
                    violation_details=component.performance_characteristics,
                    impact_assessment="May impact system performance and user experience",
                    architectural_principle="Performance by Design",
                    recommended_refactoring="Optimize database operations and reduce synchronous dependencies",
                    effort_estimation="4-12 hours",
                    business_justification="Improves user experience and reduces infrastructure costs",
                    compliance_level=ArchitecturalPatternCompliance.MINOR_DEVIATION,
                    detected_at=datetime.now(),
                    apqc_process_reference="11.2.3.1"
                )
                self.violations.append(violation)

    async def _calculate_metrics(self) -> ArchitecturalMetrics:
        """Calculate comprehensive architectural metrics"""
        total_components = len(self.components)
        dependency_count = sum(len(comp.dependencies) for comp in self.components.values())

        # Count cyclic dependencies
        cyclic_dependencies = len([v for v in self.violations
                                 if v.violation_type == ArchitecturalViolationType.CIRCULAR_DEPENDENCY])

        # Calculate average coupling
        coupling_values = [len(comp.dependencies) + len(comp.dependents)
                          for comp in self.components.values()]
        average_coupling = sum(coupling_values) / len(coupling_values) if coupling_values else 0

        # Calculate average cohesion (simplified metric)
        cohesion_values = [comp.complexity_metrics.get("maintainability_index", 50)
                          for comp in self.components.values()]
        average_cohesion = sum(cohesion_values) / len(cohesion_values) if cohesion_values else 50

        # Count layer violations
        layer_violations = len([v for v in self.violations
                              if v.violation_type == ArchitecturalViolationType.LAYERING_VIOLATION])

        # Calculate abstraction level
        abstract_components = len([comp for comp in self.components.values()
                                 if comp.type in ["interface", "abstract"]])
        abstraction_level = abstract_components / total_components if total_components > 0 else 0

        # Calculate modularity score
        modularity_score = (100 - average_coupling * 5) if average_coupling < 20 else 0

        # Calculate architectural debt ratio
        violation_count = len(self.violations)
        architectural_debt_ratio = violation_count / total_components if total_components > 0 else 0

        return ArchitecturalMetrics(
            total_components=total_components,
            dependency_count=dependency_count,
            cyclic_dependencies=cyclic_dependencies,
            average_coupling=average_coupling,
            average_cohesion=average_cohesion,
            layer_violations=layer_violations,
            abstraction_level=abstraction_level,
            modularity_score=modularity_score,
            maintainability_index=average_cohesion,
            architectural_debt_ratio=architectural_debt_ratio
        )

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency patterns and health"""
        return {
            "total_dependencies": len(self.dependency_graph),
            "most_coupled_components": sorted(
                [(name, len(deps)) for name, deps in self.dependency_graph.items()],
                key=lambda x: x[1], reverse=True
            )[:10],
            "dependency_depth": await self._calculate_dependency_depth(),
            "fan_in_fan_out": await self._calculate_fan_metrics()
        }

    async def _calculate_dependency_depth(self) -> Dict[str, int]:
        """Calculate maximum dependency depth for each component"""
        depth_map = {}

        def calculate_depth(component, visited=None):
            if visited is None:
                visited = set()

            if component in visited:
                return 0  # Circular dependency

            if component in depth_map:
                return depth_map[component]

            visited.add(component)
            dependencies = self.dependency_graph.get(component, set())

            if not dependencies:
                depth = 0
            else:
                depth = 1 + max(calculate_depth(dep, visited.copy()) for dep in dependencies)

            depth_map[component] = depth
            return depth

        for component in self.components.keys():
            calculate_depth(component)

        return depth_map

    async def _calculate_fan_metrics(self) -> Dict[str, Dict[str, int]]:
        """Calculate fan-in and fan-out metrics"""
        fan_out = {comp: len(self.dependency_graph.get(comp, set()))
                  for comp in self.components.keys()}

        fan_in = {comp: len(self.components[comp].dependents)
                 for comp in self.components.keys()}

        return {"fan_in": fan_in, "fan_out": fan_out}

    async def _analyze_layer_compliance(self) -> Dict[str, Any]:
        """Analyze compliance with architectural layers"""
        layer_distribution = Counter(comp.layer for comp in self.components.values()
                                   if comp.layer)

        layer_violations = [v for v in self.violations
                          if v.violation_type == ArchitecturalViolationType.LAYERING_VIOLATION]

        return {
            "layer_distribution": dict(layer_distribution),
            "layer_violations": len(layer_violations),
            "compliance_percentage": (1 - len(layer_violations) / len(self.components)) * 100
                                   if self.components else 100
        }

    async def _analyze_pattern_compliance(self) -> Dict[str, Any]:
        """Analyze compliance with architectural patterns"""
        pattern_violations = defaultdict(int)

        for violation in self.violations:
            pattern_violations[violation.violation_type.value] += 1

        return {
            "pattern_violations": dict(pattern_violations),
            "overall_compliance": len([v for v in self.violations
                                     if v.compliance_level == ArchitecturalPatternCompliance.COMPLIANT]) /
                                len(self.violations) * 100 if self.violations else 100
        }

    async def _assess_architectural_debt(self) -> Dict[str, Any]:
        """Assess overall architectural debt"""
        critical_violations = len([v for v in self.violations if v.severity == "critical"])
        high_violations = len([v for v in self.violations if v.severity == "high"])

        total_effort_hours = sum(
            int(re.search(r"(\d+)", v.effort_estimation).group(1))
            if re.search(r"(\d+)", v.effort_estimation) else 4
            for v in self.violations
        )

        debt_score = (critical_violations * 10 + high_violations * 5 +
                     len(self.violations)) / len(self.components) if self.components else 0

        return {
            "total_violations": len(self.violations),
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "estimated_remediation_hours": total_effort_hours,
            "architectural_debt_score": debt_score,
            "debt_classification": (
                "Critical" if debt_score > 3 else
                "High" if debt_score > 2 else
                "Medium" if debt_score > 1 else
                "Low"
            )
        }

    async def _generate_recommendations(self) -> List[str]:
        """Generate actionable architectural recommendations"""
        recommendations = []

        # Critical violations
        critical_violations = [v for v in self.violations if v.severity == "critical"]
        if critical_violations:
            recommendations.append(
                f"🚨 URGENT: Address {len(critical_violations)} critical architectural violations immediately"
            )

        # Circular dependencies
        circular_deps = [v for v in self.violations
                        if v.violation_type == ArchitecturalViolationType.CIRCULAR_DEPENDENCY]
        if circular_deps:
            recommendations.append(
                f"🔄 Break {len(circular_deps)} circular dependencies to improve testability"
            )

        # Layer violations
        layer_violations = [v for v in self.violations
                          if v.violation_type == ArchitecturalViolationType.LAYERING_VIOLATION]
        if layer_violations:
            recommendations.append(
                f"🏗️  Fix {len(layer_violations)} layer violations to maintain architectural integrity"
            )

        # High coupling
        coupling_violations = [v for v in self.violations
                             if v.violation_type == ArchitecturalViolationType.TIGHT_COUPLING]
        if coupling_violations:
            recommendations.append(
                f"🔗 Reduce coupling in {len(coupling_violations)} components through dependency injection"
            )

        # Security issues
        security_violations = [v for v in self.violations
                             if v.violation_type == ArchitecturalViolationType.SECURITY_ARCHITECTURE]
        if security_violations:
            recommendations.append(
                f"🔒 Implement security by design principles in {len(security_violations)} components"
            )

        # General recommendations based on metrics
        total_violations = len(self.violations)
        if total_violations > len(self.components) * 0.5:
            recommendations.append(
                "📈 Consider architectural refactoring sprint - high violation density detected"
            )

        return recommendations

# Initialize the architecture review agent
architecture_reviewer = ArchitectureReviewAgent(
    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)