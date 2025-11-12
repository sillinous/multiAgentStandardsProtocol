"""
PCF Agent 1.1.1.3 - Identify Political and Regulatory Issues

APQC PCF Activity: Identify political and regulatory issues (10024)
Process: 1.1.1 - Assess the external environment
Process Group: 1.1 - Define the business concept and long-term vision
Category: 1.0 - Develop Vision and Strategy

This agent monitors and analyzes political developments, regulatory changes,
and compliance requirements that may impact business strategy and operations.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from superstandard.agents.pcf.base import (
    ActivityAgentBase,
    PCFAgentConfig,
    PCFMetadata
)


class IdentifyPoliticalRegulatoryAgent(ActivityAgentBase):
    """
    PCF Agent 1.1.1.3 - Identify Political and Regulatory Issues

    Monitors political landscape and regulatory environment to identify
    risks, opportunities, and compliance requirements.

    Key Capabilities:
    1. Political Risk Assessment
       - Government stability analysis
       - Policy change monitoring
       - Election/transition impacts
       - Geopolitical tensions
       - Trade policy shifts

    2. Regulatory Monitoring
       - New regulations tracking
       - Upcoming compliance deadlines
       - Regulatory body announcements
       - Industry-specific rules
       - Cross-border regulations

    3. Compliance Analysis
       - Current compliance status
       - Gap identification
       - Resource requirements
       - Implementation timelines
       - Cost implications

    4. Impact Assessment
       - Business impact severity
       - Operational changes required
       - Financial implications
       - Timeline urgency
       - Strategic implications

    5. Risk Mitigation Planning
       - Compliance strategies
       - Advocacy opportunities
       - Risk mitigation approaches
       - Contingency planning
       - Stakeholder engagement

    Data Sources (configured for real integration):
    - Government databases and registries
    - Regulatory body websites (SEC, FDA, FCC, etc.)
    - Policy monitoring services
    - Legal research databases (LexisNexis, Westlaw)
    - Industry associations
    - Political risk consulting firms

    PCF Metadata:
    - Element ID: 10024
    - Hierarchy ID: 1.1.1.3
    - Level: 4 (Activity)
    - Parent Process: 1.1.1 (Assess the external environment)

    Usage Example:
    >>> agent = IdentifyPoliticalRegulatoryAgent()
    >>> result = await agent.execute({
    ...     "geographic_scope": "United States",
    ...     "industry_sectors": ["Technology", "Financial Services"]
    ... })
    >>> print(f"Issues identified: {len(result['regulatory_changes'])}")
    >>> print(f"Risk level: {result['political_risks']['overall_risk_level']}")
    """

    def __init__(self, config: Optional[PCFAgentConfig] = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        """Create default configuration with PCF metadata"""
        metadata = PCFMetadata(
            pcf_element_id="10024",
            hierarchy_id="1.1.1.3",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.1",
            process_name="Assess the external environment",
            activity_id="1.1.1.3",
            activity_name="Identify political and regulatory issues",
            parent_element_id="10021",  # Parent process element ID
            kpis=[
                {"name": "issues_identified", "type": "count", "unit": "number"},
                {"name": "risk_level", "type": "enum", "unit": "category"},
                {"name": "compliance_gap_count", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="identify_political_regulatory_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180  # 3 minutes
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute political and regulatory analysis.

        Args:
            input_data: Dictionary containing:
                - geographic_scope: Region for analysis (required)
                - industry_sectors: List of industries (required)
                - lookback_months: Historical analysis period (default: 6)
                - lookahead_months: Future horizon (default: 12)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - regulatory_changes: Recent and upcoming regulations
                - political_risks: Political risk assessment
                - compliance_requirements: Compliance obligations
                - impact_assessment: Business impact analysis
                - recommendations: Strategic recommendations
                - metadata: Execution metadata including KPIs
        """
        # Extract inputs
        geographic_scope = input_data.get("geographic_scope", "Global")
        industry_sectors = input_data.get("industry_sectors", [])
        lookback_months = input_data.get("lookback_months", 6)
        lookahead_months = input_data.get("lookahead_months", 12)

        if not industry_sectors:
            return {
                "success": False,
                "error": "industry_sectors is required"
            }

        self.logger.info(
            f"Analyzing political/regulatory landscape for {geographic_scope}, "
            f"industries: {industry_sectors}"
        )

        # Step 1: Monitor regulatory changes
        regulatory_changes = await self._monitor_regulatory_changes(
            geographic_scope,
            industry_sectors,
            lookback_months,
            lookahead_months
        )

        # Step 2: Assess political risks
        political_risks = await self._assess_political_risks(
            geographic_scope,
            industry_sectors
        )

        # Step 3: Analyze compliance requirements
        compliance_requirements = await self._analyze_compliance_requirements(
            geographic_scope,
            industry_sectors,
            regulatory_changes
        )

        # Step 4: Assess business impact
        impact_assessment = await self._assess_business_impact(
            regulatory_changes,
            political_risks,
            compliance_requirements,
            industry_sectors
        )

        # Step 5: Generate recommendations
        recommendations = await self._generate_recommendations(
            regulatory_changes,
            political_risks,
            compliance_requirements,
            impact_assessment
        )

        # Calculate KPIs
        kpis = {
            "issues_identified": (
                len(regulatory_changes.get("recent", [])) +
                len(regulatory_changes.get("upcoming", [])) +
                len(political_risks.get("risk_factors", []))
            ),
            "risk_level": political_risks.get("overall_risk_level", "medium"),
            "compliance_gap_count": len(compliance_requirements.get("gaps", []))
        }

        return {
            "success": True,
            "geographic_scope": geographic_scope,
            "industry_sectors": industry_sectors,
            "regulatory_changes": regulatory_changes,
            "political_risks": political_risks,
            "compliance_requirements": compliance_requirements,
            "impact_assessment": impact_assessment,
            "recommendations": recommendations,
            "metadata": {
                "pcf_element_id": self.config.pcf_metadata.pcf_element_id,
                "hierarchy_id": self.config.pcf_metadata.hierarchy_id,
                "execution_timestamp": datetime.now().isoformat(),
                "kpis": kpis
            }
        }

    async def _monitor_regulatory_changes(
        self,
        geographic_scope: str,
        industry_sectors: List[str],
        lookback_months: int,
        lookahead_months: int
    ) -> Dict[str, Any]:
        """
        Monitor recent and upcoming regulatory changes.

        In production, would fetch from:
        - Federal Register (US)
        - EUR-Lex (EU)
        - Government regulatory databases
        - Thomson Reuters Regulatory Intelligence
        - Compliance management platforms
        """
        self.logger.debug(f"Monitoring regulatory changes for {industry_sectors}")

        await asyncio.sleep(0.1)

        # Generate realistic mock data
        recent_changes = []
        upcoming_changes = []

        # Technology sector regulations
        if "Technology" in industry_sectors:
            recent_changes.append({
                "regulation_id": "REG-2024-TECH-001",
                "title": "Digital Markets and Consumer Protection Act",
                "effective_date": (datetime.now() - timedelta(days=60)).isoformat(),
                "jurisdiction": geographic_scope,
                "regulatory_body": "Federal Trade Commission",
                "category": "consumer_protection",
                "summary": "New requirements for data privacy, algorithm transparency, and consumer consent mechanisms",
                "impact_severity": "high",
                "compliance_deadline": (datetime.now() + timedelta(days=120)).isoformat()
            })

            upcoming_changes.append({
                "regulation_id": "PROP-2025-TECH-003",
                "title": "AI Ethics and Accountability Framework",
                "proposed_effective_date": (datetime.now() + timedelta(days=180)).isoformat(),
                "jurisdiction": geographic_scope,
                "regulatory_body": "Department of Commerce",
                "category": "ai_governance",
                "summary": "Proposed framework for ethical AI development, bias testing, and accountability measures",
                "impact_severity": "high",
                "status": "proposed",
                "comment_period_ends": (datetime.now() + timedelta(days=45)).isoformat()
            })

        # Financial Services regulations
        if "Financial Services" in industry_sectors:
            recent_changes.append({
                "regulation_id": "REG-2024-FIN-002",
                "title": "Enhanced Cybersecurity Requirements for Financial Institutions",
                "effective_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "jurisdiction": geographic_scope,
                "regulatory_body": "Financial Services Regulatory Authority",
                "category": "cybersecurity",
                "summary": "Mandatory incident reporting, penetration testing, and security controls",
                "impact_severity": "high",
                "compliance_deadline": (datetime.now() + timedelta(days=180)).isoformat()
            })

            recent_changes.append({
                "regulation_id": "REG-2024-FIN-005",
                "title": "Anti-Money Laundering Modernization Act",
                "effective_date": (datetime.now() - timedelta(days=90)).isoformat(),
                "jurisdiction": geographic_scope,
                "regulatory_body": "Financial Crimes Enforcement Network",
                "category": "aml_compliance",
                "summary": "Updated beneficial ownership requirements and enhanced due diligence procedures",
                "impact_severity": "medium",
                "compliance_deadline": (datetime.now() + timedelta(days=90)).isoformat()
            })

        # Add cross-industry regulations
        recent_changes.append({
            "regulation_id": "REG-2024-GEN-001",
            "title": "Environmental Sustainability Reporting Requirements",
            "effective_date": (datetime.now() - timedelta(days=45)).isoformat(),
            "jurisdiction": geographic_scope,
            "regulatory_body": "Environmental Protection Agency",
            "category": "environmental",
            "summary": "Mandatory ESG disclosures and carbon emission reporting for large enterprises",
            "impact_severity": "medium",
            "compliance_deadline": (datetime.now() + timedelta(days=365)).isoformat()
        })

        return {
            "recent": recent_changes,
            "upcoming": upcoming_changes,
            "total_tracked": len(recent_changes) + len(upcoming_changes),
            "lookback_months": lookback_months,
            "lookahead_months": lookahead_months,
            "last_updated": datetime.now().isoformat()
        }

    async def _assess_political_risks(
        self,
        geographic_scope: str,
        industry_sectors: List[str]
    ) -> Dict[str, Any]:
        """
        Assess political risks affecting business operations.

        In production, would use:
        - Political risk indices (World Bank, IMF)
        - Country risk ratings (S&P, Moody's, Fitch)
        - Political consulting firms (Eurasia Group, Control Risks)
        - News analysis and sentiment
        """
        self.logger.debug(f"Assessing political risks for {geographic_scope}")

        await asyncio.sleep(0.08)

        # Generate risk assessment
        risk_factors = []

        # Government stability
        stability_score = random.uniform(0.6, 0.9)
        if stability_score < 0.7:
            risk_factors.append({
                "risk_type": "government_stability",
                "severity": "high",
                "description": "Political transition period increasing policy uncertainty",
                "likelihood": "medium",
                "impact": "high"
            })
        elif stability_score < 0.8:
            risk_factors.append({
                "risk_type": "government_stability",
                "severity": "medium",
                "description": "Moderate political volatility with potential policy shifts",
                "likelihood": "medium",
                "impact": "medium"
            })

        # Regulatory environment
        risk_factors.append({
            "risk_type": "regulatory_changes",
            "severity": "medium",
            "description": "Increased regulatory scrutiny in technology and financial sectors",
            "likelihood": "high",
            "impact": "medium"
        })

        # Trade policy
        if geographic_scope in ["United States", "Global"]:
            risk_factors.append({
                "risk_type": "trade_policy",
                "severity": "medium",
                "description": "Ongoing trade negotiations may impact tariffs and market access",
                "likelihood": "medium",
                "impact": "medium"
            })

        # Determine overall risk level
        high_severity_count = sum(1 for r in risk_factors if r["severity"] == "high")
        if high_severity_count >= 2:
            overall_risk = "high"
        elif high_severity_count == 1:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk_level": overall_risk,
            "risk_factors": risk_factors,
            "government_stability_score": round(stability_score, 2),
            "regulatory_intensity": "increasing",
            "policy_predictability": "moderate",
            "assessment_date": datetime.now().isoformat(),
            "confidence_level": "high"
        }

    async def _analyze_compliance_requirements(
        self,
        geographic_scope: str,
        industry_sectors: List[str],
        regulatory_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze compliance requirements and identify gaps"""
        self.logger.debug("Analyzing compliance requirements")

        await asyncio.sleep(0.06)

        current_compliance = []
        gaps = []

        # Analyze each regulation for compliance status
        for reg in regulatory_changes.get("recent", []):
            compliance_deadline = datetime.fromisoformat(reg["compliance_deadline"])
            days_until_deadline = (compliance_deadline - datetime.now()).days

            if days_until_deadline < 90:
                urgency = "high"
            elif days_until_deadline < 180:
                urgency = "medium"
            else:
                urgency = "low"

            # Simulate compliance status
            is_compliant = random.choice([True, False, False])  # More likely to have gaps

            requirement = {
                "regulation_id": reg["regulation_id"],
                "title": reg["title"],
                "compliance_status": "compliant" if is_compliant else "non_compliant",
                "deadline": reg["compliance_deadline"],
                "days_until_deadline": days_until_deadline,
                "urgency": urgency,
                "estimated_effort": f"{random.randint(100, 500)} hours",
                "estimated_cost": f"${random.randint(50, 500)}K"
            }

            current_compliance.append(requirement)

            if not is_compliant:
                gaps.append({
                    "regulation_id": reg["regulation_id"],
                    "gap_description": f"Non-compliant with {reg['category']} requirements",
                    "remediation_steps": [
                        f"Conduct gap analysis for {reg['title']}",
                        "Develop implementation plan",
                        "Allocate resources and budget",
                        "Implement required controls",
                        "Conduct compliance testing"
                    ],
                    "priority": urgency,
                    "estimated_completion": (datetime.now() + timedelta(days=days_until_deadline-30)).isoformat()
                })

        return {
            "current_requirements": current_compliance,
            "gaps": gaps,
            "compliance_rate": round((1 - len(gaps) / max(len(current_compliance), 1)) * 100, 1) if current_compliance else 100.0,
            "high_priority_gaps": len([g for g in gaps if g["priority"] == "high"]),
            "total_estimated_cost": f"${sum(random.randint(50, 500) for _ in gaps)}K",
            "analysis_date": datetime.now().isoformat()
        }

    async def _assess_business_impact(
        self,
        regulatory_changes: Dict[str, Any],
        political_risks: Dict[str, Any],
        compliance_requirements: Dict[str, Any],
        industry_sectors: List[str]
    ) -> Dict[str, Any]:
        """Assess overall business impact"""
        self.logger.debug("Assessing business impact")

        await asyncio.sleep(0.05)

        impacts = []

        # Regulatory impact
        high_severity_regs = [
            r for r in regulatory_changes.get("recent", [])
            if r["impact_severity"] == "high"
        ]

        if high_severity_regs:
            impacts.append({
                "category": "Regulatory Compliance",
                "severity": "high",
                "description": f"{len(high_severity_regs)} high-impact regulations require immediate attention",
                "affected_areas": ["Operations", "Technology", "Finance"],
                "financial_impact": "High compliance costs expected",
                "timeline": "Immediate to 6 months"
            })

        # Political risk impact
        if political_risks["overall_risk_level"] in ["high", "medium"]:
            impacts.append({
                "category": "Political Risk",
                "severity": political_risks["overall_risk_level"],
                "description": "Political uncertainty may affect strategic planning and investment decisions",
                "affected_areas": ["Strategy", "Investment", "Operations"],
                "financial_impact": "Potential delays in expansion plans",
                "timeline": "6-12 months"
            })

        # Compliance gap impact
        if compliance_requirements["high_priority_gaps"] > 0:
            impacts.append({
                "category": "Compliance Gaps",
                "severity": "high",
                "description": f"{compliance_requirements['high_priority_gaps']} high-priority compliance gaps identified",
                "affected_areas": ["Legal", "Risk Management", "Operations"],
                "financial_impact": f"Estimated remediation cost: {compliance_requirements['total_estimated_cost']}",
                "timeline": "Immediate"
            })

        return {
            "overall_impact_level": "high" if any(i["severity"] == "high" for i in impacts) else "medium",
            "impact_areas": impacts,
            "total_impact_count": len(impacts),
            "strategic_implications": self._generate_strategic_implications(impacts, industry_sectors),
            "assessment_confidence": "high"
        }

    def _generate_strategic_implications(
        self,
        impacts: List[Dict[str, Any]],
        industry_sectors: List[str]
    ) -> List[str]:
        """Generate strategic implications"""
        implications = []

        if any(i["category"] == "Regulatory Compliance" for i in impacts):
            implications.append(
                "Increased regulatory burden may require expansion of compliance team and systems"
            )

        if any(i["category"] == "Political Risk" for i in impacts):
            implications.append(
                "Political uncertainty suggests need for more flexible strategic planning and scenario analysis"
            )

        if any(i["category"] == "Compliance Gaps" for i in impacts):
            implications.append(
                "Immediate remediation required to avoid penalties and reputational damage"
            )

        return implications

    async def _generate_recommendations(
        self,
        regulatory_changes: Dict[str, Any],
        political_risks: Dict[str, Any],
        compliance_requirements: Dict[str, Any],
        impact_assessment: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate strategic recommendations"""
        self.logger.debug("Generating recommendations")

        await asyncio.sleep(0.03)

        recommendations = []

        # Compliance recommendations
        if compliance_requirements["high_priority_gaps"] > 0:
            recommendations.append({
                "category": "Compliance Management",
                "priority": "high",
                "recommendation": "Establish cross-functional compliance task force to address high-priority gaps",
                "action_items": [
                    "Assign executive sponsor for compliance initiative",
                    "Conduct detailed gap analysis for each non-compliant area",
                    "Develop remediation roadmap with clear milestones",
                    "Allocate budget for compliance investments"
                ],
                "timeline": "Immediate - 30 days"
            })

        # Regulatory monitoring
        if len(regulatory_changes.get("upcoming", [])) > 0:
            recommendations.append({
                "category": "Regulatory Intelligence",
                "priority": "medium",
                "recommendation": "Enhance regulatory monitoring and early warning systems",
                "action_items": [
                    "Subscribe to regulatory intelligence services",
                    "Establish regulatory monitoring process",
                    "Create regulatory impact assessment framework",
                    "Build relationships with regulators and industry associations"
                ],
                "timeline": "30-90 days"
            })

        # Political risk mitigation
        if political_risks["overall_risk_level"] == "high":
            recommendations.append({
                "category": "Risk Mitigation",
                "priority": "high",
                "recommendation": "Develop political risk mitigation and contingency plans",
                "action_items": [
                    "Conduct scenario planning for key political risks",
                    "Diversify geographic exposure where possible",
                    "Strengthen stakeholder relationships",
                    "Consider political risk insurance for high-risk markets"
                ],
                "timeline": "30-60 days"
            })

        # Advocacy opportunity
        for upcoming in regulatory_changes.get("upcoming", []):
            if "comment_period_ends" in upcoming:
                recommendations.append({
                    "category": "Regulatory Advocacy",
                    "priority": "medium",
                    "recommendation": f"Participate in comment process for {upcoming['title']}",
                    "action_items": [
                        "Draft formal comment letter",
                        "Coordinate with industry associations",
                        "Engage legal counsel for technical review",
                        "Submit before deadline"
                    ],
                    "timeline": f"Before {upcoming['comment_period_ends']}"
                })
                break  # Only recommend one advocacy action

        return recommendations


# Test execution
async def main():
    """Test the political/regulatory agent"""
    print("=" * 80)
    print("PCF Agent 1.1.1.3 - Identify Political and Regulatory Issues")
    print("=" * 80)
    print()

    # Create agent
    agent = IdentifyPoliticalRegulatoryAgent()

    print(f"Agent ID: {agent.config.agent_id}")
    print(f"PCF Element ID: {agent.config.pcf_metadata.pcf_element_id}")
    print(f"Hierarchy ID: {agent.config.pcf_metadata.hierarchy_id}")
    print(f"Category: {agent.config.pcf_metadata.category_name}")
    print(f"Process: {agent.config.pcf_metadata.process_name}")
    print(f"Activity: {agent.config.pcf_metadata.activity_name}")
    print()

    # Test execution
    print("Executing agent...")
    print()

    result = await agent.execute({
        "geographic_scope": "United States",
        "industry_sectors": ["Technology", "Financial Services"],
        "lookback_months": 6,
        "lookahead_months": 12
    })

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Success: {result['success']}")
    print(f"Geographic Scope: {result['geographic_scope']}")
    print(f"Industry Sectors: {', '.join(result['industry_sectors'])}")
    print()

    # Regulatory changes
    reg_changes = result['regulatory_changes']
    print("Regulatory Changes:")
    print("-" * 40)
    print(f"  Recent Regulations: {len(reg_changes['recent'])}")
    print(f"  Upcoming Regulations: {len(reg_changes['upcoming'])}")
    print()

    print("  Recent (Sample):")
    for reg in reg_changes['recent'][:2]:
        print(f"    • {reg['title']}")
        print(f"      Category: {reg['category']}, Severity: {reg['impact_severity']}")
        print(f"      Compliance Deadline: {reg['compliance_deadline'][:10]}")
    print()

    if reg_changes['upcoming']:
        print("  Upcoming (Sample):")
        for reg in reg_changes['upcoming'][:1]:
            print(f"    • {reg['title']}")
            print(f"      Status: {reg['status']}, Severity: {reg['impact_severity']}")
            print(f"      Proposed Effective: {reg['proposed_effective_date'][:10]}")
        print()

    # Political risks
    print("Political Risk Assessment:")
    print("-" * 40)
    pol_risks = result['political_risks']
    print(f"  Overall Risk Level: {pol_risks['overall_risk_level'].upper()}")
    print(f"  Government Stability Score: {pol_risks['government_stability_score']}")
    print(f"  Regulatory Intensity: {pol_risks['regulatory_intensity']}")
    print(f"  Risk Factors Identified: {len(pol_risks['risk_factors'])}")
    print()

    print("  Key Risks:")
    for risk in pol_risks['risk_factors']:
        print(f"    • {risk['risk_type'].replace('_', ' ').title()}: {risk['severity'].upper()}")
        print(f"      {risk['description']}")
    print()

    # Compliance
    print("Compliance Status:")
    print("-" * 40)
    compliance = result['compliance_requirements']
    print(f"  Compliance Rate: {compliance['compliance_rate']}%")
    print(f"  Total Gaps: {len(compliance['gaps'])}")
    print(f"  High Priority Gaps: {compliance['high_priority_gaps']}")
    print(f"  Total Estimated Cost: {compliance['total_estimated_cost']}")
    print()

    if compliance['gaps']:
        print("  Critical Gaps:")
        for gap in compliance['gaps'][:2]:
            print(f"    • {gap['regulation_id']}: {gap['gap_description']}")
            print(f"      Priority: {gap['priority'].upper()}")
        print()

    # Impact assessment
    print("Business Impact Assessment:")
    print("-" * 40)
    impact = result['impact_assessment']
    print(f"  Overall Impact Level: {impact['overall_impact_level'].upper()}")
    print(f"  Impact Areas: {impact['total_impact_count']}")
    print()

    for imp in impact['impact_areas']:
        print(f"  [{imp['severity'].upper()}] {imp['category']}")
        print(f"    {imp['description']}")
        print(f"    Financial Impact: {imp['financial_impact']}")
        print(f"    Timeline: {imp['timeline']}")
        print()

    # Recommendations
    print("Strategic Recommendations:")
    print("-" * 40)
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['category']}")
        print(f"     {rec['recommendation']}")
        print(f"     Timeline: {rec['timeline']}")
        print()

    # KPIs
    print("KPIs:")
    print("-" * 40)
    kpis = result['metadata']['kpis']
    for kpi_name, kpi_value in kpis.items():
        print(f"  {kpi_name}: {kpi_value}")
    print()

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
