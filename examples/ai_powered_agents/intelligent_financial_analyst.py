"""
Intelligent Financial Analyst Agent - Example Implementation

Demonstrates the full capabilities of AI-powered agents:
- Deep financial analysis with AI-driven insights
- Risk assessment and portfolio optimization
- Anomaly detection in transactions
- Forecasting with confidence intervals
- Multi-provider AI support (OpenAI, Anthropic, Ollama)

This is a reference implementation showing best practices for
building AI-powered APQC-compliant agents.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json


@dataclass
class FinancialAnalystConfig:
    """Configuration for the Financial Analyst Agent"""
    agent_id: str = "intelligent_financial_analyst_001"
    agent_name: str = "Intelligent Financial Analyst"

    # AI Configuration
    ai_provider: str = "auto"  # auto, openai, anthropic, ollama, mock
    confidence_threshold: float = 0.75
    max_analysis_depth: int = 3

    # Analysis Modes
    enable_risk_analysis: bool = True
    enable_anomaly_detection: bool = True
    enable_forecasting: bool = True
    enable_optimization: bool = True

    # Thresholds
    risk_threshold: float = 0.7
    anomaly_sensitivity: float = 0.85
    forecast_horizon_days: int = 90


class IntelligentFinancialAnalyst:
    """
    AI-Powered Financial Analysis Agent

    Capabilities:
    - Real-time financial data analysis
    - Risk profiling and assessment
    - Anomaly detection in transactions
    - Portfolio optimization recommendations
    - Revenue and expense forecasting
    - Compliance monitoring

    Integration:
    - Uses FinanceProcessor from smart_processing
    - Integrates with AIService for advanced reasoning
    - APQC Process: 8.0 - Manage Financial Resources
    """

    APQC_CATEGORY_ID = "8.0"
    APQC_PROCESS_ID = "8.2.1"

    def __init__(self, config: Optional[FinancialAnalystConfig] = None):
        self.config = config or FinancialAnalystConfig()
        self.analysis_cache = {}
        self.state = {
            "analyses_performed": 0,
            "alerts_generated": 0,
            "recommendations_made": 0,
            "last_analysis": None
        }

    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered portfolio analysis

        Args:
            portfolio_data: Dict containing:
                - holdings: List of current positions
                - transactions: Recent transaction history
                - market_context: Current market conditions
                - risk_profile: Client risk tolerance

        Returns:
            Comprehensive analysis with AI-driven insights
        """
        from superstandard.services.smart_processing import get_processor
        from superstandard.services.ai_service import get_ai_service

        start_time = datetime.now()

        # Get domain processor and AI service
        processor = get_processor("finance")
        ai_service = get_ai_service()

        # Step 1: Basic Financial Analysis
        basic_analysis = await processor.analyze_financial_data({
            "data": portfolio_data.get("holdings", []),
            "analysis_type": "portfolio_composition"
        })

        # Step 2: AI-Powered Deep Analysis
        ai_insights = await ai_service.analyze(
            prompt=f"""Analyze this portfolio and provide insights:
            - Holdings: {json.dumps(portfolio_data.get('holdings', [])[:5])}
            - Risk Profile: {portfolio_data.get('risk_profile', 'moderate')}
            - Market Context: {portfolio_data.get('market_context', 'neutral')}

            Focus on:
            1. Diversification assessment
            2. Risk-adjusted return potential
            3. Alignment with stated risk profile
            4. Sector concentration risks
            """,
            data={"portfolio": portfolio_data}
        )

        results = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "apqc_process": self.APQC_PROCESS_ID,
            "analysis": {
                "basic_metrics": basic_analysis,
                "ai_insights": ai_insights,
            },
            "components": {}
        }

        # Step 3: Risk Analysis (if enabled)
        if self.config.enable_risk_analysis:
            risk_result = await self._analyze_risk(portfolio_data, processor)
            results["components"]["risk_analysis"] = risk_result

        # Step 4: Anomaly Detection (if enabled)
        if self.config.enable_anomaly_detection:
            anomalies = await self._detect_anomalies(
                portfolio_data.get("transactions", []),
                processor
            )
            results["components"]["anomaly_detection"] = anomalies

        # Step 5: Forecasting (if enabled)
        if self.config.enable_forecasting:
            forecast = await self._generate_forecast(portfolio_data, ai_service)
            results["components"]["forecast"] = forecast

        # Step 6: Generate Recommendations
        recommendations = await self._generate_recommendations(
            results["analysis"],
            results.get("components", {}),
            ai_service
        )
        results["recommendations"] = recommendations

        # Step 7: Compliance Check
        compliance = await self._check_compliance(portfolio_data)
        results["compliance"] = compliance

        # Update metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        results["metrics"] = {
            "processing_time_seconds": processing_time,
            "components_analyzed": len(results.get("components", {})),
            "recommendations_count": len(recommendations),
            "confidence_score": self._calculate_confidence(results)
        }

        # Update state
        self.state["analyses_performed"] += 1
        self.state["last_analysis"] = datetime.now().isoformat()
        self.state["recommendations_made"] += len(recommendations)

        return results

    async def _analyze_risk(
        self,
        portfolio_data: Dict[str, Any],
        processor
    ) -> Dict[str, Any]:
        """Perform detailed risk analysis"""
        risk_assessment = await processor.assess_financial_risk({
            "financial_data": portfolio_data.get("holdings", []),
            "risk_factors": ["market", "credit", "liquidity", "operational"]
        })

        return {
            "overall_risk_score": risk_assessment.get("risk_score", 0.5),
            "risk_breakdown": risk_assessment.get("risk_breakdown", {}),
            "risk_factors": risk_assessment.get("risk_factors", []),
            "risk_level": self._categorize_risk(risk_assessment.get("risk_score", 0.5)),
            "mitigation_suggestions": risk_assessment.get("mitigation_suggestions", [])
        }

    async def _detect_anomalies(
        self,
        transactions: List[Dict],
        processor
    ) -> Dict[str, Any]:
        """Detect anomalies in transaction patterns"""
        if not transactions:
            return {"anomalies_found": 0, "details": []}

        # Use AI for pattern analysis
        anomaly_result = await processor.process({
            "data": transactions,
            "analysis_type": "anomaly_detection",
            "sensitivity": self.config.anomaly_sensitivity
        }, "anomaly_detection")

        anomalies = anomaly_result.get("anomalies", [])

        if anomalies:
            self.state["alerts_generated"] += len(anomalies)

        return {
            "anomalies_found": len(anomalies),
            "details": anomalies,
            "severity_distribution": self._categorize_anomalies(anomalies),
            "recommended_actions": self._get_anomaly_actions(anomalies)
        }

    async def _generate_forecast(
        self,
        portfolio_data: Dict[str, Any],
        ai_service
    ) -> Dict[str, Any]:
        """Generate AI-powered financial forecasts"""
        forecast_result = await ai_service.analyze(
            prompt=f"""Based on the portfolio data and current market conditions,
            generate a {self.config.forecast_horizon_days}-day forecast for:
            1. Expected returns (with confidence intervals)
            2. Risk trajectory
            3. Key inflection points to monitor

            Portfolio value: ${portfolio_data.get('total_value', 100000)}
            Current allocation: {json.dumps(portfolio_data.get('allocation', {}))}
            """,
            data={"portfolio": portfolio_data}
        )

        return {
            "horizon_days": self.config.forecast_horizon_days,
            "generated_at": datetime.now().isoformat(),
            "forecast": forecast_result,
            "confidence": forecast_result.get("confidence", 0.7)
        }

    async def _generate_recommendations(
        self,
        analysis: Dict[str, Any],
        components: Dict[str, Any],
        ai_service
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        recommendations = await ai_service.generate_recommendations(
            context={
                "analysis_summary": analysis,
                "risk_analysis": components.get("risk_analysis", {}),
                "anomalies": components.get("anomaly_detection", {}),
                "forecast": components.get("forecast", {})
            },
            constraints=[
                "Recommendations must be actionable",
                "Consider risk tolerance",
                "Include priority levels",
                "Provide expected impact"
            ]
        )

        return recommendations

    async def _check_compliance(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check portfolio against compliance rules"""
        # Simulated compliance checks
        return {
            "compliant": True,
            "checks_performed": [
                "concentration_limits",
                "asset_class_restrictions",
                "liquidity_requirements"
            ],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        scores = []

        if "components" in results:
            if "risk_analysis" in results["components"]:
                scores.append(0.8)  # Risk analysis adds confidence
            if "forecast" in results["components"]:
                scores.append(results["components"]["forecast"].get("confidence", 0.7))

        if results.get("ai_powered"):
            scores.append(0.85)  # AI analysis adds confidence

        return sum(scores) / len(scores) if scores else 0.7

    def _categorize_risk(self, score: float) -> str:
        """Categorize risk score into levels"""
        if score < 0.3:
            return "low"
        elif score < 0.6:
            return "moderate"
        elif score < 0.8:
            return "elevated"
        else:
            return "high"

    def _categorize_anomalies(self, anomalies: List[Dict]) -> Dict[str, int]:
        """Categorize anomalies by severity"""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            if severity in distribution:
                distribution[severity] += 1
        return distribution

    def _get_anomaly_actions(self, anomalies: List[Dict]) -> List[str]:
        """Get recommended actions for anomalies"""
        actions = []
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            if severity in ["high", "critical"]:
                actions.append(f"Investigate {anomaly.get('type', 'anomaly')} immediately")
        return actions


async def demo():
    """Demonstrate the Intelligent Financial Analyst"""
    print("=" * 60)
    print("Intelligent Financial Analyst - Demo")
    print("=" * 60)

    analyst = IntelligentFinancialAnalyst()

    # Sample portfolio data
    portfolio = {
        "total_value": 250000,
        "holdings": [
            {"symbol": "AAPL", "shares": 100, "value": 17500},
            {"symbol": "MSFT", "shares": 80, "value": 30000},
            {"symbol": "GOOGL", "shares": 50, "value": 7000},
            {"symbol": "BND", "shares": 500, "value": 45000},
            {"symbol": "VTI", "shares": 300, "value": 75000},
        ],
        "allocation": {
            "stocks": 0.65,
            "bonds": 0.25,
            "cash": 0.10
        },
        "transactions": [
            {"date": "2024-01-15", "type": "buy", "symbol": "AAPL", "amount": 5000},
            {"date": "2024-01-20", "type": "sell", "symbol": "MSFT", "amount": 3000},
            {"date": "2024-02-01", "type": "buy", "symbol": "BND", "amount": 10000},
        ],
        "risk_profile": "moderate",
        "market_context": "bullish with volatility"
    }

    print("\nAnalyzing portfolio...")
    print(f"Total Value: ${portfolio['total_value']:,}")
    print(f"Holdings: {len(portfolio['holdings'])} positions")
    print(f"Risk Profile: {portfolio['risk_profile']}")

    try:
        result = await analyst.analyze_portfolio(portfolio)

        print("\n" + "-" * 40)
        print("Analysis Results:")
        print("-" * 40)
        print(f"Status: {result['status']}")
        print(f"AI-Powered: {result['ai_powered']}")
        print(f"Processing Time: {result['metrics']['processing_time_seconds']:.2f}s")
        print(f"Confidence Score: {result['metrics']['confidence_score']:.2%}")

        if "components" in result:
            if "risk_analysis" in result["components"]:
                risk = result["components"]["risk_analysis"]
                print(f"\nRisk Level: {risk['risk_level']}")
                print(f"Risk Score: {risk['overall_risk_score']:.2f}")

        print(f"\nRecommendations: {len(result.get('recommendations', []))}")
        for i, rec in enumerate(result.get("recommendations", [])[:3], 1):
            print(f"  {i}. {rec.get('action', rec.get('recommendation', 'N/A'))}")

    except ImportError as e:
        print(f"\nNote: Run from project root with proper imports. Error: {e}")
        print("This demo requires the smart_processing and ai_service modules.")


if __name__ == "__main__":
    asyncio.run(demo())
