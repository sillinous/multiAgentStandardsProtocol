"""
PCF Agent 1.1.1.4 - Identify Technology Innovations

APQC PCF Activity: Identify technology innovations (10025)
Process: 1.1.1 - Assess the external environment
Process Group: 1.1 - Define the business concept and long-term vision
Category: 1.0 - Develop Vision and Strategy

This agent tracks emerging technologies, innovations, and digital trends
that could disrupt or enhance business operations and strategy.
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


class IdentifyTechnologyInnovationsAgent(ActivityAgentBase):
    """
    PCF Agent 1.1.1.4 - Identify Technology Innovations

    Tracks emerging technologies and innovation trends to identify
    opportunities and disruption threats.

    Key Capabilities:
    1. Technology Trend Tracking
       - Emerging technology identification
       - Technology maturity assessment
       - Adoption curve analysis
       - Market penetration metrics
       - Investment trend analysis

    2. Innovation Opportunity Analysis
       - Business value assessment
       - Implementation feasibility
       - Competitive advantage potential
       - ROI estimation
       - Strategic fit evaluation

    3. Disruption Threat Assessment
       - Industry disruption potential
       - Business model threats
       - Competitive disadvantage risks
       - Response urgency evaluation
       - Mitigation strategy development

    4. Technology Domain Analysis
       - AI/Machine Learning
       - Cloud Computing
       - Blockchain/Distributed Ledger
       - IoT/Edge Computing
       - Quantum Computing
       - Biotechnology
       - Nanotechnology
       - Robotics/Automation
       - AR/VR/Metaverse
       - 5G/6G Networks

    5. Adoption Readiness Assessment
       - Technology maturity level
       - Organizational readiness
       - Skill gap analysis
       - Infrastructure requirements
       - Change management needs

    Data Sources (configured for real integration):
    - Gartner Hype Cycle
    - Forrester Wave reports
    - CB Insights tech trends
    - MIT Technology Review
    - IEEE Spectrum
    - arXiv preprints
    - Patent databases (USPTO, EPO)
    - Venture capital databases
    - Technology conferences/publications

    PCF Metadata:
    - Element ID: 10025
    - Hierarchy ID: 1.1.1.4
    - Level: 4 (Activity)
    - Parent Process: 1.1.1 (Assess the external environment)

    Usage Example:
    >>> agent = IdentifyTechnologyInnovationsAgent()
    >>> result = await agent.execute({
    ...     "technology_domains": ["AI/ML", "Cloud Computing", "IoT"],
    ...     "innovation_stage": "emerging"
    ... })
    >>> print(f"Technologies tracked: {len(result['technology_trends'])}")
    >>> print(f"Opportunities identified: {len(result['innovation_opportunities'])}")
    """

    def __init__(self, config: Optional[PCFAgentConfig] = None):
        if config is None:
            config = self._create_default_config()
        super().__init__(config)

    @staticmethod
    def _create_default_config() -> PCFAgentConfig:
        """Create default configuration with PCF metadata"""
        metadata = PCFMetadata(
            pcf_element_id="10025",
            hierarchy_id="1.1.1.4",
            level=4,
            level_name="Activity",
            category_id="1.0",
            category_name="Develop Vision and Strategy",
            process_group_id="1.1",
            process_group_name="Define the business concept and long-term vision",
            process_id="1.1.1",
            process_name="Assess the external environment",
            activity_id="1.1.1.4",
            activity_name="Identify technology innovations",
            parent_element_id="10021",  # Parent process element ID
            kpis=[
                {"name": "innovations_tracked", "type": "count", "unit": "number"},
                {"name": "relevance_score", "type": "percentage", "unit": "%"},
                {"name": "high_impact_count", "type": "count", "unit": "number"}
            ]
        )

        return PCFAgentConfig(
            agent_id="identify_technology_innovations_agent_001",
            pcf_metadata=metadata,
            track_kpis=True,
            execution_timeout=180  # 3 minutes
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute technology innovation analysis.

        Args:
            input_data: Dictionary containing:
                - technology_domains: List of tech domains to track (required)
                - innovation_stage: Filter by maturity (optional: emerging/growth/mature)
                - industry_context: Industry for relevance filtering (optional)
                - time_horizon: Forecast period in months (optional, default: 24)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - technology_trends: Emerging technology trends
                - innovation_opportunities: Strategic opportunities
                - disruption_threats: Potential disruption threats
                - adoption_roadmap: Technology adoption recommendations
                - metadata: Execution metadata including KPIs
        """
        # Extract inputs
        technology_domains = input_data.get("technology_domains", [])
        innovation_stage = input_data.get("innovation_stage", "all")
        industry_context = input_data.get("industry_context")
        time_horizon = input_data.get("time_horizon", 24)

        if not technology_domains:
            return {
                "success": False,
                "error": "technology_domains is required"
            }

        self.logger.info(
            f"Analyzing technology innovations in domains: {technology_domains}, "
            f"stage: {innovation_stage}"
        )

        # Step 1: Track technology trends
        technology_trends = await self._track_technology_trends(
            technology_domains,
            innovation_stage,
            time_horizon
        )

        # Step 2: Identify innovation opportunities
        innovation_opportunities = await self._identify_opportunities(
            technology_trends,
            industry_context
        )

        # Step 3: Assess disruption threats
        disruption_threats = await self._assess_disruption_threats(
            technology_trends,
            industry_context
        )

        # Step 4: Generate adoption roadmap
        adoption_roadmap = await self._generate_adoption_roadmap(
            technology_trends,
            innovation_opportunities,
            disruption_threats
        )

        # Calculate KPIs
        high_impact = [
            t for t in technology_trends
            if t.get("business_impact") == "high"
        ]

        kpis = {
            "innovations_tracked": len(technology_trends),
            "relevance_score": round(
                sum(t.get("relevance_score", 0) for t in technology_trends) /
                max(len(technology_trends), 1) * 100,
                1
            ),
            "high_impact_count": len(high_impact)
        }

        return {
            "success": True,
            "technology_domains": technology_domains,
            "innovation_stage": innovation_stage,
            "time_horizon_months": time_horizon,
            "technology_trends": technology_trends,
            "innovation_opportunities": innovation_opportunities,
            "disruption_threats": disruption_threats,
            "adoption_roadmap": adoption_roadmap,
            "metadata": {
                "pcf_element_id": self.config.pcf_metadata.pcf_element_id,
                "hierarchy_id": self.config.pcf_metadata.hierarchy_id,
                "execution_timestamp": datetime.now().isoformat(),
                "kpis": kpis
            }
        }

    async def _track_technology_trends(
        self,
        technology_domains: List[str],
        innovation_stage: str,
        time_horizon: int
    ) -> List[Dict[str, Any]]:
        """
        Track emerging technology trends.

        In production, would fetch from:
        - Gartner Hype Cycle API
        - Forrester research database
        - CB Insights API
        - Patent database APIs
        - Academic publication databases
        - VC investment databases
        """
        self.logger.debug(f"Tracking technology trends for {technology_domains}")

        await asyncio.sleep(0.12)

        trends = []

        # AI/Machine Learning trends
        if "AI/ML" in technology_domains or "AI" in technology_domains:
            trends.append({
                "technology_id": "TECH-2024-AI-001",
                "name": "Generative AI for Enterprise",
                "domain": "AI/ML",
                "maturity_stage": "growth",
                "adoption_level": "early_majority",
                "description": "Large language models and generative AI applications for business automation, content creation, and decision support",
                "business_impact": "high",
                "disruption_potential": "high",
                "time_to_mainstream": "12-24 months",
                "investment_trend": "rapidly_increasing",
                "relevance_score": 0.95,
                "key_players": ["OpenAI", "Google", "Anthropic", "Microsoft"],
                "use_cases": [
                    "Automated content generation",
                    "Code assistance and development",
                    "Customer service automation",
                    "Business intelligence and analytics"
                ]
            })

            trends.append({
                "technology_id": "TECH-2024-AI-002",
                "name": "Edge AI and TinyML",
                "domain": "AI/ML",
                "maturity_stage": "emerging",
                "adoption_level": "innovators",
                "description": "Deploying AI models on edge devices for real-time, low-latency processing",
                "business_impact": "medium",
                "disruption_potential": "medium",
                "time_to_mainstream": "24-36 months",
                "investment_trend": "increasing",
                "relevance_score": 0.75,
                "key_players": ["NVIDIA", "Intel", "ARM", "Google"],
                "use_cases": [
                    "IoT device intelligence",
                    "Real-time video analytics",
                    "Predictive maintenance",
                    "Autonomous systems"
                ]
            })

        # Cloud Computing trends
        if "Cloud" in technology_domains or "Cloud Computing" in technology_domains:
            trends.append({
                "technology_id": "TECH-2024-CLOUD-001",
                "name": "Serverless and Event-Driven Architecture",
                "domain": "Cloud Computing",
                "maturity_stage": "growth",
                "adoption_level": "early_majority",
                "description": "Function-as-a-Service and event-driven patterns for scalable, cost-effective applications",
                "business_impact": "high",
                "disruption_potential": "medium",
                "time_to_mainstream": "6-12 months",
                "investment_trend": "steady",
                "relevance_score": 0.88,
                "key_players": ["AWS", "Azure", "Google Cloud", "Cloudflare"],
                "use_cases": [
                    "Microservices architecture",
                    "API backends",
                    "Data processing pipelines",
                    "Real-time event processing"
                ]
            })

            trends.append({
                "technology_id": "TECH-2024-CLOUD-002",
                "name": "Multi-Cloud and Hybrid Cloud Management",
                "domain": "Cloud Computing",
                "maturity_stage": "mature",
                "adoption_level": "early_majority",
                "description": "Tools and platforms for managing workloads across multiple cloud providers",
                "business_impact": "high",
                "disruption_potential": "low",
                "time_to_mainstream": "mainstream",
                "investment_trend": "steady",
                "relevance_score": 0.82,
                "key_players": ["VMware", "Red Hat", "HashiCorp", "Kubernetes"],
                "use_cases": [
                    "Cloud portability",
                    "Disaster recovery",
                    "Cost optimization",
                    "Vendor lock-in avoidance"
                ]
            })

        # IoT trends
        if "IoT" in technology_domains:
            trends.append({
                "technology_id": "TECH-2024-IOT-001",
                "name": "Industrial IoT (IIoT) and Digital Twins",
                "domain": "IoT",
                "maturity_stage": "growth",
                "adoption_level": "early_adopters",
                "description": "IoT sensors and digital twin technology for manufacturing and industrial optimization",
                "business_impact": "high",
                "disruption_potential": "high",
                "time_to_mainstream": "18-30 months",
                "investment_trend": "increasing",
                "relevance_score": 0.85,
                "key_players": ["Siemens", "GE Digital", "PTC", "Microsoft"],
                "use_cases": [
                    "Predictive maintenance",
                    "Production optimization",
                    "Supply chain visibility",
                    "Asset performance management"
                ]
            })

        # Blockchain trends
        if "Blockchain" in technology_domains:
            trends.append({
                "technology_id": "TECH-2024-BLOCK-001",
                "name": "Enterprise Blockchain for Supply Chain",
                "domain": "Blockchain",
                "maturity_stage": "growth",
                "adoption_level": "early_adopters",
                "description": "Permissioned blockchain networks for supply chain transparency and traceability",
                "business_impact": "medium",
                "disruption_potential": "medium",
                "time_to_mainstream": "24-36 months",
                "investment_trend": "steady",
                "relevance_score": 0.68,
                "key_players": ["IBM", "Oracle", "SAP", "Hyperledger"],
                "use_cases": [
                    "Product provenance tracking",
                    "Supply chain transparency",
                    "Smart contracts",
                    "Cross-border transactions"
                ]
            })

        # Quantum Computing trends
        if "Quantum" in technology_domains:
            trends.append({
                "technology_id": "TECH-2024-QUANTUM-001",
                "name": "Quantum Computing as a Service",
                "domain": "Quantum Computing",
                "maturity_stage": "emerging",
                "adoption_level": "innovators",
                "description": "Cloud-based quantum computing access for optimization and simulation problems",
                "business_impact": "low",
                "disruption_potential": "very_high",
                "time_to_mainstream": "60+ months",
                "investment_trend": "increasing",
                "relevance_score": 0.45,
                "key_players": ["IBM", "Google", "Amazon", "Microsoft"],
                "use_cases": [
                    "Drug discovery",
                    "Financial modeling",
                    "Cryptography",
                    "Optimization problems"
                ]
            })

        # Filter by innovation stage if specified
        if innovation_stage != "all":
            trends = [t for t in trends if t["maturity_stage"] == innovation_stage]

        return trends

    async def _identify_opportunities(
        self,
        technology_trends: List[Dict[str, Any]],
        industry_context: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Identify innovation opportunities from technology trends"""
        self.logger.debug("Identifying innovation opportunities")

        await asyncio.sleep(0.08)

        opportunities = []

        for trend in technology_trends:
            if trend["business_impact"] in ["high", "medium"]:
                opportunity = {
                    "opportunity_id": f"OPP-{trend['technology_id']}",
                    "technology": trend["name"],
                    "domain": trend["domain"],
                    "opportunity_type": self._determine_opportunity_type(trend),
                    "business_value": self._assess_business_value(trend),
                    "implementation_complexity": self._assess_complexity(trend),
                    "time_to_value": self._estimate_time_to_value(trend),
                    "estimated_roi": f"{random.randint(150, 400)}%",
                    "strategic_fit": random.choice(["high", "medium", "low"]),
                    "recommended_action": self._recommend_action(trend),
                    "priority": self._calculate_priority(trend)
                }
                opportunities.append(opportunity)

        # Sort by priority
        opportunities.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)

        return opportunities

    def _determine_opportunity_type(self, trend: Dict[str, Any]) -> str:
        """Determine type of opportunity"""
        if trend["disruption_potential"] == "high":
            return "competitive_advantage"
        elif trend["business_impact"] == "high":
            return "operational_efficiency"
        else:
            return "incremental_improvement"

    def _assess_business_value(self, trend: Dict[str, Any]) -> str:
        """Assess business value of technology"""
        impact_score = {
            "high": 3,
            "medium": 2,
            "low": 1
        }.get(trend["business_impact"], 1)

        if impact_score >= 3:
            return "High - significant competitive advantage and ROI"
        elif impact_score >= 2:
            return "Medium - measurable efficiency gains"
        else:
            return "Low - incremental benefits"

    def _assess_complexity(self, trend: Dict[str, Any]) -> str:
        """Assess implementation complexity"""
        if trend["maturity_stage"] == "emerging":
            return "High - requires significant R&D and expertise"
        elif trend["maturity_stage"] == "growth":
            return "Medium - established patterns but evolving"
        else:
            return "Low - mature technology with proven implementations"

    def _estimate_time_to_value(self, trend: Dict[str, Any]) -> str:
        """Estimate time to realize value"""
        stages = {
            "emerging": "12-24 months",
            "growth": "6-12 months",
            "mature": "3-6 months"
        }
        return stages.get(trend["maturity_stage"], "12-18 months")

    def _recommend_action(self, trend: Dict[str, Any]) -> str:
        """Recommend action based on trend characteristics"""
        if trend["business_impact"] == "high" and trend["maturity_stage"] in ["growth", "mature"]:
            return "Immediate evaluation and pilot project"
        elif trend["disruption_potential"] == "high":
            return "Strategic monitoring and capability building"
        elif trend["maturity_stage"] == "emerging":
            return "Research and experimentation"
        else:
            return "Continuous monitoring"

    def _calculate_priority(self, trend: Dict[str, Any]) -> str:
        """Calculate opportunity priority"""
        score = 0

        # Business impact
        score += {"high": 3, "medium": 2, "low": 1}.get(trend["business_impact"], 0)

        # Disruption potential
        score += {"very_high": 3, "high": 3, "medium": 2, "low": 1}.get(trend["disruption_potential"], 0)

        # Time to mainstream (inverse - closer = higher priority)
        if "12" in trend["time_to_mainstream"] or "mainstream" in trend["time_to_mainstream"]:
            score += 2
        elif "24" in trend["time_to_mainstream"]:
            score += 1

        if score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"

    async def _assess_disruption_threats(
        self,
        technology_trends: List[Dict[str, Any]],
        industry_context: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Assess disruption threats from emerging technologies"""
        self.logger.debug("Assessing disruption threats")

        await asyncio.sleep(0.06)

        threats = []

        for trend in technology_trends:
            if trend["disruption_potential"] in ["very_high", "high"]:
                threat = {
                    "threat_id": f"THREAT-{trend['technology_id']}",
                    "technology": trend["name"],
                    "threat_level": trend["disruption_potential"],
                    "threat_type": self._categorize_threat(trend),
                    "description": f"{trend['name']} could disrupt traditional business models in {trend['domain']}",
                    "affected_areas": self._identify_affected_areas(trend),
                    "response_urgency": self._assess_urgency(trend),
                    "mitigation_strategies": self._generate_mitigation_strategies(trend),
                    "competitive_response": self._analyze_competitive_response(trend)
                }
                threats.append(threat)

        return threats

    def _categorize_threat(self, trend: Dict[str, Any]) -> str:
        """Categorize type of disruption threat"""
        if trend["domain"] in ["AI/ML", "Cloud Computing"]:
            return "technology_obsolescence"
        elif trend["domain"] == "Blockchain":
            return "business_model_disruption"
        else:
            return "competitive_disadvantage"

    def _identify_affected_areas(self, trend: Dict[str, Any]) -> List[str]:
        """Identify business areas affected by disruption"""
        areas = ["Technology Infrastructure", "Operations"]

        if trend["business_impact"] == "high":
            areas.extend(["Strategy", "Product Development"])

        if "customer" in trend["description"].lower():
            areas.append("Customer Experience")

        return areas

    def _assess_urgency(self, trend: Dict[str, Any]) -> str:
        """Assess response urgency"""
        if "12" in trend["time_to_mainstream"]:
            return "high"
        elif "24" in trend["time_to_mainstream"]:
            return "medium"
        else:
            return "low"

    def _generate_mitigation_strategies(self, trend: Dict[str, Any]) -> List[str]:
        """Generate mitigation strategies"""
        strategies = []

        if trend["maturity_stage"] == "emerging":
            strategies.append("Establish innovation lab for experimentation")
            strategies.append("Partner with technology vendors or startups")
        else:
            strategies.append("Accelerate technology adoption program")
            strategies.append("Upskill workforce in new technology")

        strategies.append(f"Monitor {trend['domain']} developments continuously")
        strategies.append("Develop contingency plans for rapid adoption if needed")

        return strategies

    def _analyze_competitive_response(self, trend: Dict[str, Any]) -> str:
        """Analyze how competitors might respond"""
        if trend["adoption_level"] == "innovators":
            return "Few competitors have adopted; first-mover advantage available"
        elif trend["adoption_level"] == "early_adopters":
            return "Leading competitors are piloting; window closing for early adoption"
        elif trend["adoption_level"] == "early_majority":
            return "Technology becoming table stakes; adoption required to remain competitive"
        else:
            return "Mainstream adoption; late adopters face significant disadvantage"

    async def _generate_adoption_roadmap(
        self,
        technology_trends: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
        threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate technology adoption roadmap"""
        self.logger.debug("Generating adoption roadmap")

        await asyncio.sleep(0.05)

        # Categorize by timeframe
        immediate = []  # 0-6 months
        near_term = []  # 6-12 months
        medium_term = []  # 12-24 months
        long_term = []  # 24+ months

        for opp in opportunities:
            if opp["priority"] == "high":
                if "3-6" in opp["time_to_value"]:
                    immediate.append(opp)
                elif "6-12" in opp["time_to_value"]:
                    near_term.append(opp)
                elif "12-24" in opp["time_to_value"]:
                    medium_term.append(opp)
                else:
                    long_term.append(opp)
            elif opp["priority"] == "medium":
                near_term.append(opp)
            else:
                medium_term.append(opp)

        return {
            "immediate_actions": immediate[:2],  # Top 2 priorities
            "near_term_initiatives": near_term[:3],
            "medium_term_investments": medium_term[:3],
            "long_term_exploration": long_term[:2],
            "overall_strategy": self._formulate_strategy(opportunities, threats),
            "success_metrics": [
                "Technology adoption rate",
                "Innovation pipeline value",
                "Time to market for new capabilities",
                "Competitive technology gap"
            ]
        }

    def _formulate_strategy(
        self,
        opportunities: List[Dict[str, Any]],
        threats: List[Dict[str, Any]]
    ) -> str:
        """Formulate overall technology strategy"""
        high_priority_count = len([o for o in opportunities if o["priority"] == "high"])
        high_threat_count = len([t for t in threats if t["threat_level"] in ["high", "very_high"]])

        if high_priority_count >= 2 and high_threat_count >= 1:
            return "Aggressive innovation: Pursue multiple high-priority opportunities while addressing disruption threats"
        elif high_priority_count >= 2:
            return "Opportunity-focused: Invest in high-value technologies for competitive advantage"
        elif high_threat_count >= 1:
            return "Defensive positioning: Address disruption threats to maintain market position"
        else:
            return "Selective adoption: Focus on proven technologies with clear ROI"


# Test execution
async def main():
    """Test the technology innovations agent"""
    print("=" * 80)
    print("PCF Agent 1.1.1.4 - Identify Technology Innovations")
    print("=" * 80)
    print()

    # Create agent
    agent = IdentifyTechnologyInnovationsAgent()

    print(f"Agent ID: {agent.config.agent_id}")
    print(f"PCF Element ID: {agent.config.pcf_metadata.pcf_element_id}")
    print(f"Hierarchy ID: {agent.config.pcf_metadata.hierarchy_id}")
    print(f"Activity: {agent.config.pcf_metadata.activity_name}")
    print()

    # Test execution
    print("Executing agent...")
    print()

    result = await agent.execute({
        "technology_domains": ["AI/ML", "Cloud Computing", "IoT", "Blockchain"],
        "innovation_stage": "all",
        "industry_context": "Technology",
        "time_horizon": 24
    })

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print(f"Success: {result['success']}")
    print(f"Domains Analyzed: {', '.join(result['technology_domains'])}")
    print(f"Time Horizon: {result['time_horizon_months']} months")
    print()

    # Technology trends
    print("Technology Trends:")
    print("-" * 40)
    print(f"  Total Tracked: {len(result['technology_trends'])}")
    print()

    for trend in result['technology_trends'][:3]:
        print(f"  • {trend['name']} ({trend['domain']})")
        print(f"    Maturity: {trend['maturity_stage']}, Impact: {trend['business_impact']}")
        print(f"    Disruption Potential: {trend['disruption_potential']}")
        print(f"    Time to Mainstream: {trend['time_to_mainstream']}")
        print(f"    Relevance Score: {trend['relevance_score']:.0%}")
        print()

    # Innovation opportunities
    print("Innovation Opportunities:")
    print("-" * 40)
    print(f"  Total Identified: {len(result['innovation_opportunities'])}")
    print()

    for opp in result['innovation_opportunities'][:2]:
        print(f"  [{opp['priority'].upper()}] {opp['technology']}")
        print(f"    Type: {opp['opportunity_type']}")
        print(f"    Business Value: {opp['business_value']}")
        print(f"    Estimated ROI: {opp['estimated_roi']}")
        print(f"    Action: {opp['recommended_action']}")
        print()

    # Disruption threats
    print("Disruption Threats:")
    print("-" * 40)
    print(f"  Total Threats: {len(result['disruption_threats'])}")
    print()

    for threat in result['disruption_threats']:
        print(f"  [{threat['threat_level'].upper()}] {threat['technology']}")
        print(f"    Type: {threat['threat_type']}")
        print(f"    Urgency: {threat['response_urgency']}")
        print(f"    Affected: {', '.join(threat['affected_areas'])}")
        print()

    # Adoption roadmap
    print("Adoption Roadmap:")
    print("-" * 40)
    roadmap = result['adoption_roadmap']
    print(f"  Strategy: {roadmap['overall_strategy']}")
    print()

    if roadmap['immediate_actions']:
        print("  Immediate (0-6 months):")
        for action in roadmap['immediate_actions']:
            print(f"    • {action['technology']}")

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
