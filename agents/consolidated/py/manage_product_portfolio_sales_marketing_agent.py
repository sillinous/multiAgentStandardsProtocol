"""
ManageProductPortfolioSalesMarketingAgent - APQC 3.0 Agent

3.2.3 Manage Product Portfolio

This agent implements APQC process 3.2.3 from category 3.0: Market and Sell Products and Services.

Domain: sales_marketing
Type: strategic

Fully compliant with Architectural Standards v1.0.0

APQC Blueprint ID: apqc_3_0_b3c4d5e6
APQC Category: 3.0 - Market and Sell Products and Services
APQC Process: 3.2.3 - Manage Product Portfolio

Version: 1.0.0
Date: 2025-10-17
Framework: APQC 7.0.1
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from superstandard.agents.base.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class ManageProductPortfolioSalesMarketingAgentConfig:
    """Configuration for ManageProductPortfolioSalesMarketingAgent"""

    # APQC Metadata
    apqc_agent_id: str = "apqc_3_0_b3c4d5e6"
    apqc_category_id: str = "3.0"
    apqc_category_name: str = "Market and Sell Products and Services"
    apqc_process_id: str = "3.2.3"
    apqc_process_name: str = "3.2.3 Manage Product Portfolio"

    # Agent Identity
    agent_id: str = "apqc_3_0_b3c4d5e6"
    agent_name: str = "manage_product_portfolio_sales_marketing_agent"
    agent_type: str = "strategic"
    domain: str = "sales_marketing"
    version: str = "1.0.0"

    # Behavior Configuration
    autonomous_level: float = 0.9
    collaboration_mode: str = "orchestrated"
    learning_enabled: bool = True
    self_improvement: bool = True

    # Resource Configuration
    compute_mode: str = "adaptive"
    memory_mode: str = "adaptive"
    api_budget_mode: str = "dynamic"
    priority: str = "high"

    # Quality Configuration
    testing_required: bool = True
    qa_threshold: float = 0.85
    consensus_weight: float = 1.0
    error_handling: str = "graceful_degradation"

    # Deployment Configuration
    runtime: str = "ray_actor"
    scaling: str = "horizontal"
    health_checks: bool = True
    monitoring: bool = True

    # Environment Variables
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "300")))

    @classmethod
    def from_environment(cls) -> "ManageProductPortfolioSalesMarketingAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            agent_id=os.getenv("AGENT_ID", "apqc_3_0_b3c4d5e6"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "300"))
        )


class ManageProductPortfolioSalesMarketingAgent(BaseAgent, ProtocolMixin):
    """
    ManageProductPortfolioSalesMarketingAgent - APQC 3.0 Agent

    3.2.3 Manage Product Portfolio

    Capabilities:
    - portfolio_optimization
    - profitability_analysis
    - bcg_matrix_analysis
    - lifecycle_management
    - strategic_planning

    Skills:
    - portfolio_optimization: 0.9
    - profitability_analysis: 0.87
    - bcg_matrix: 0.85

    Compliance: FULL (All 8 architectural principles)
    Protocols: A2A, A2P, ACP, ANP, MCP
    """

    VERSION = "1.0.0"
    MIN_COMPATIBLE_VERSION = "1.0.0"
    APQC_AGENT_ID = "apqc_3_0_b3c4d5e6"
    APQC_CATEGORY_ID = "3.0"
    APQC_PROCESS_ID = "3.2.3"
    APQC_FRAMEWORK_VERSION = "7.0.1"

    def __init__(self, config: ManageProductPortfolioSalesMarketingAgentConfig):
        """Initialize agent"""
        super().__init__(
            agent_id=config.agent_id,
            agent_type=config.agent_type,
            version=config.version
        )

        self.config = config
        self.capabilities_list = ['portfolio_optimization', 'profitability_analysis', 'bcg_matrix_analysis', 'lifecycle_management', 'strategic_planning']
        self.skills = {'portfolio_optimization': 0.9, 'profitability_analysis': 0.87, 'bcg_matrix': 0.85}
        self.interfaces = {
            'inputs': ['product_data', 'financial_data', 'market_data', 'strategic_goals'],
            'outputs': ['portfolio_analysis', 'recommendations', 'action_plan', 'metrics'],
            'protocols': ['message_passing', 'event_driven', 'api_rest']
        }

        self.state = {
            "status": "initialized",
            "tasks_processed": 0,
            "last_activity": datetime.now().isoformat(),
            "performance_metrics": {},
            "learning_data": {} if self.config.learning_enabled else None
        }

        self._initialize_protocols()
        self._initialize_monitoring()

    @classmethod
    def from_environment(cls) -> "ManageProductPortfolioSalesMarketingAgent":
        """Create agent from environment variables"""
        config = ManageProductPortfolioSalesMarketingAgentConfig.from_environment()
        return cls(config)

    def _initialize_protocols(self):
        """Initialize protocol support"""
        self.log("info", f"Protocols initialized: A2A, A2P, ACP, ANP, MCP")

    def _initialize_monitoring(self):
        """Initialize monitoring and health checks"""
        if self.config.monitoring:
            self.log("info", f"Monitoring enabled for {self.config.agent_name}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's primary function"""
        self.log("info", f"Executing {self.config.apqc_process_name}")

        try:
            if not self._validate_input(input_data):
                return {
                    "status": "error",
                    "message": "Invalid input data",
                    "error_handling": self.config.error_handling
                }

            result = await self._process_portfolio_management(input_data)

            self.state["tasks_processed"] += 1
            self.state["last_activity"] = datetime.now().isoformat()

            if self.config.learning_enabled:
                await self._learn_from_execution(input_data, result)

            return result

        except Exception as e:
            self.log("error", f"Execution error: {str(e)}")
            if self.config.error_handling == "graceful_degradation":
                return {
                    "status": "degraded",
                    "message": str(e),
                    "partial_result": {}
                }
            raise

    async def _process_portfolio_management(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process product portfolio management with BCG Matrix analysis

        Business Logic:
        1. Calculate BCG Matrix classifications (Stars, Cash Cows, Question Marks, Dogs)
        2. Analyze profitability metrics
        3. Assess portfolio balance
        4. Generate strategic recommendations
        """
        self.log("info", "Processing product portfolio management")

        product_data = input_data.get('product_data', [])
        market_data = input_data.get('market_data', {})
        strategic_goals = input_data.get('strategic_goals', {})

        # BCG Matrix Analysis
        bcg_analysis = self._perform_bcg_analysis(product_data, market_data)

        # Profitability Analysis
        profitability = self._analyze_profitability(product_data)

        # Portfolio Balance Assessment
        balance = self._assess_portfolio_balance(bcg_analysis, profitability)

        # Strategic Recommendations
        recommendations = self._generate_strategic_recommendations(bcg_analysis, balance, strategic_goals)

        # Risk Assessment
        risk_analysis = self._assess_portfolio_risk(product_data, bcg_analysis)

        result = {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "agent_id": self.config.agent_id,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "portfolio_analysis": {
                    "total_products": len(product_data),
                    "bcg_matrix": bcg_analysis,
                    "profitability": profitability,
                    "balance_score": balance['overall_score'],
                    "risk_level": risk_analysis['overall_risk']
                },
                "recommendations": recommendations,
                "action_plan": self._create_action_plan(recommendations),
                "metrics": {
                    "portfolio_value": profitability['total_revenue'],
                    "average_margin": profitability['average_margin'],
                    "diversification_index": balance['diversification_index'],
                    "risk_score": risk_analysis['risk_score']
                }
            }
        }

        return result

    def _perform_bcg_analysis(self, product_data: List[Dict[str, Any]], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform BCG Matrix analysis classifying products into:
        - Stars: High growth, high market share
        - Cash Cows: Low growth, high market share
        - Question Marks: High growth, low market share
        - Dogs: Low growth, low market share
        """
        if not product_data:
            return {"stars": [], "cash_cows": [], "question_marks": [], "dogs": []}

        # Calculate median values for classification thresholds
        growth_rates = [p.get('growth_rate', 0) for p in product_data]
        market_shares = [p.get('market_share', 0) for p in product_data]

        median_growth = np.median(growth_rates) if growth_rates else 10
        median_share = np.median(market_shares) if market_shares else 20

        # Classify products
        stars = []
        cash_cows = []
        question_marks = []
        dogs = []

        for product in product_data:
            product_id = product.get('product_id', 'unknown')
            product_name = product.get('name', 'Unknown Product')
            growth = product.get('growth_rate', 0)
            share = product.get('market_share', 0)
            revenue = product.get('revenue', 0)
            margin = product.get('profit_margin', 0)

            product_info = {
                "product_id": product_id,
                "name": product_name,
                "growth_rate": growth,
                "market_share": share,
                "revenue": revenue,
                "profit_margin": margin
            }

            # Classification logic
            if growth >= median_growth and share >= median_share:
                stars.append(product_info)
            elif growth < median_growth and share >= median_share:
                cash_cows.append(product_info)
            elif growth >= median_growth and share < median_share:
                question_marks.append(product_info)
            else:
                dogs.append(product_info)

        return {
            "stars": stars,
            "cash_cows": cash_cows,
            "question_marks": question_marks,
            "dogs": dogs,
            "classification_thresholds": {
                "growth_threshold": round(median_growth, 2),
                "share_threshold": round(median_share, 2)
            },
            "distribution": {
                "stars_count": len(stars),
                "cash_cows_count": len(cash_cows),
                "question_marks_count": len(question_marks),
                "dogs_count": len(dogs)
            }
        }

    def _analyze_profitability(self, product_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze profitability metrics across the portfolio
        """
        if not product_data:
            return {
                "total_revenue": 0,
                "total_profit": 0,
                "average_margin": 0,
                "top_performers": [],
                "underperformers": []
            }

        total_revenue = sum(p.get('revenue', 0) for p in product_data)
        profits = []
        margins = []

        product_profitability = []

        for product in product_data:
            revenue = product.get('revenue', 0)
            margin = product.get('profit_margin', 0)
            profit = revenue * (margin / 100)

            profits.append(profit)
            margins.append(margin)

            product_profitability.append({
                "product_id": product.get('product_id'),
                "name": product.get('name'),
                "revenue": revenue,
                "profit": round(profit, 2),
                "margin": margin,
                "revenue_contribution": round((revenue / total_revenue * 100), 2) if total_revenue > 0 else 0
            })

        # Sort by profit
        product_profitability.sort(key=lambda x: x['profit'], reverse=True)

        total_profit = sum(profits)
        average_margin = np.mean(margins) if margins else 0

        # Identify top performers (top 20%) and underperformers (bottom 20%)
        top_count = max(1, len(product_profitability) // 5)
        top_performers = product_profitability[:top_count]
        underperformers = product_profitability[-top_count:]

        return {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "average_margin": round(average_margin, 2),
            "top_performers": top_performers,
            "underperformers": underperformers,
            "profitability_distribution": {
                "high_margin_products": len([m for m in margins if m > 30]),
                "medium_margin_products": len([m for m in margins if 15 <= m <= 30]),
                "low_margin_products": len([m for m in margins if m < 15])
            }
        }

    def _assess_portfolio_balance(self, bcg: Dict[str, Any], profitability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess portfolio balance and diversification
        """
        distribution = bcg['distribution']
        total_products = sum(distribution.values())

        if total_products == 0:
            return {"overall_score": 0, "diversification_index": 0, "balance_status": "empty"}

        # Calculate balance scores
        stars_ratio = distribution['stars_count'] / total_products
        cash_cows_ratio = distribution['cash_cows_count'] / total_products
        question_marks_ratio = distribution['question_marks_count'] / total_products
        dogs_ratio = distribution['dogs_count'] / total_products

        # Ideal ratios: Stars 25%, Cash Cows 35%, Question Marks 25%, Dogs 15%
        ideal = {'stars': 0.25, 'cash_cows': 0.35, 'question_marks': 0.25, 'dogs': 0.15}
        actual = {
            'stars': stars_ratio,
            'cash_cows': cash_cows_ratio,
            'question_marks': question_marks_ratio,
            'dogs': dogs_ratio
        }

        # Calculate deviation from ideal
        balance_score = 100
        for category in ideal:
            deviation = abs(ideal[category] - actual[category])
            balance_score -= (deviation * 100)

        balance_score = max(0, balance_score)

        # Calculate diversification index (Shannon entropy)
        ratios = [stars_ratio, cash_cows_ratio, question_marks_ratio, dogs_ratio]
        ratios = [r for r in ratios if r > 0]  # Filter out zeros

        if ratios:
            entropy = -sum(r * np.log(r) for r in ratios)
            max_entropy = np.log(4)  # Max entropy for 4 categories
            diversification_index = (entropy / max_entropy) * 100
        else:
            diversification_index = 0

        # Determine balance status
        if balance_score >= 80:
            balance_status = "excellent"
        elif balance_score >= 60:
            balance_status = "good"
        elif balance_score >= 40:
            balance_status = "fair"
        else:
            balance_status = "poor"

        return {
            "overall_score": round(balance_score, 2),
            "diversification_index": round(diversification_index, 2),
            "balance_status": balance_status,
            "category_ratios": {
                "stars": round(stars_ratio * 100, 2),
                "cash_cows": round(cash_cows_ratio * 100, 2),
                "question_marks": round(question_marks_ratio * 100, 2),
                "dogs": round(dogs_ratio * 100, 2)
            },
            "ideal_vs_actual": {
                category: {
                    "ideal": round(ideal[category] * 100, 2),
                    "actual": round(actual[category] * 100, 2),
                    "deviation": round(abs(ideal[category] - actual[category]) * 100, 2)
                }
                for category in ideal
            }
        }

    def _assess_portfolio_risk(self, product_data: List[Dict[str, Any]], bcg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess portfolio risk factors
        """
        if not product_data:
            return {"overall_risk": "unknown", "risk_score": 0, "risk_factors": []}

        risk_factors = []
        risk_score = 0

        # Check for over-reliance on few products
        total_revenue = sum(p.get('revenue', 0) for p in product_data)
        if total_revenue > 0:
            sorted_products = sorted(product_data, key=lambda x: x.get('revenue', 0), reverse=True)
            top_3_revenue = sum(p.get('revenue', 0) for p in sorted_products[:3])
            concentration = (top_3_revenue / total_revenue) * 100

            if concentration > 70:
                risk_factors.append("High revenue concentration in top 3 products")
                risk_score += 25

        # Check for too many Dogs
        dogs_ratio = bcg['distribution']['dogs_count'] / len(product_data) if len(product_data) > 0 else 0
        if dogs_ratio > 0.3:
            risk_factors.append("High proportion of underperforming products (Dogs)")
            risk_score += 20

        # Check for lack of Stars
        stars_ratio = bcg['distribution']['stars_count'] / len(product_data) if len(product_data) > 0 else 0
        if stars_ratio < 0.15:
            risk_factors.append("Insufficient high-growth, high-share products (Stars)")
            risk_score += 15

        # Check for aging portfolio (too many Cash Cows, not enough Question Marks)
        cash_cows_ratio = bcg['distribution']['cash_cows_count'] / len(product_data) if len(product_data) > 0 else 0
        qm_ratio = bcg['distribution']['question_marks_count'] / len(product_data) if len(product_data) > 0 else 0

        if cash_cows_ratio > 0.5 and qm_ratio < 0.15:
            risk_factors.append("Portfolio aging - need more growth opportunities")
            risk_score += 20

        # Determine overall risk level
        if risk_score >= 50:
            overall_risk = "high"
        elif risk_score >= 30:
            overall_risk = "medium"
        elif risk_score > 0:
            overall_risk = "low"
        else:
            overall_risk = "minimal"

        return {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "mitigation_priority": "immediate" if risk_score >= 50 else "planned" if risk_score >= 30 else "routine"
        }

    def _generate_strategic_recommendations(self, bcg: Dict[str, Any], balance: Dict[str, Any],
                                           strategic_goals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate strategic recommendations based on portfolio analysis
        """
        recommendations = []

        # Stars recommendations
        if bcg['stars']:
            recommendations.append({
                "priority": "high",
                "category": "stars",
                "action": "Invest in Stars for market dominance",
                "description": f"Invest heavily in {len(bcg['stars'])} Star products to maintain growth and market share",
                "products": [s['name'] for s in bcg['stars'][:3]],
                "expected_outcome": "Market leadership and sustained growth"
            })

        # Cash Cows recommendations
        if bcg['cash_cows']:
            recommendations.append({
                "priority": "medium",
                "category": "cash_cows",
                "action": "Harvest Cash Cows efficiently",
                "description": f"Optimize {len(bcg['cash_cows'])} Cash Cow products for maximum profit generation",
                "products": [c['name'] for c in bcg['cash_cows'][:3]],
                "expected_outcome": "Stable cash flow for reinvestment"
            })

        # Question Marks recommendations
        if bcg['question_marks']:
            recommendations.append({
                "priority": "high",
                "category": "question_marks",
                "action": "Decide on Question Marks",
                "description": f"Evaluate {len(bcg['question_marks'])} Question Mark products - invest or divest",
                "products": [q['name'] for q in bcg['question_marks'][:3]],
                "expected_outcome": "Convert to Stars or divest to free resources"
            })

        # Dogs recommendations
        if bcg['dogs']:
            recommendations.append({
                "priority": "medium",
                "category": "dogs",
                "action": "Phase out or reposition Dogs",
                "description": f"Consider divesting or repositioning {len(bcg['dogs'])} underperforming products",
                "products": [d['name'] for d in bcg['dogs'][:3]],
                "expected_outcome": "Resource reallocation to higher-value products"
            })

        # Balance recommendations
        if balance['balance_status'] in ['poor', 'fair']:
            recommendations.append({
                "priority": "high",
                "category": "portfolio_balance",
                "action": "Rebalance product portfolio",
                "description": f"Portfolio balance score is {balance['overall_score']:.1f} - rebalancing needed",
                "expected_outcome": "Improved portfolio resilience and growth potential"
            })

        return recommendations

    def _create_action_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create actionable plan from recommendations
        """
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_recs = sorted(recommendations, key=lambda x: priority_order.get(x['priority'], 3))

        immediate_actions = [r for r in sorted_recs if r['priority'] == 'high']
        planned_actions = [r for r in sorted_recs if r['priority'] == 'medium']

        return {
            "immediate_actions": [
                {
                    "action": r['action'],
                    "timeline": "0-3 months",
                    "category": r['category']
                }
                for r in immediate_actions
            ],
            "planned_actions": [
                {
                    "action": r['action'],
                    "timeline": "3-12 months",
                    "category": r['category']
                }
                for r in planned_actions
            ],
            "total_actions": len(recommendations),
            "priority_distribution": {
                "high": len([r for r in recommendations if r['priority'] == 'high']),
                "medium": len([r for r in recommendations if r['priority'] == 'medium']),
                "low": len([r for r in recommendations if r['priority'] == 'low'])
            }
        }

    async def _learn_from_execution(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Learn from execution for self-improvement"""
        if not self.config.self_improvement:
            return

        if self.state["learning_data"] is not None:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "input_summary": str(input_data)[:100],
                "result_status": result.get("status"),
                "performance": {
                    "balance_score": result.get("output", {}).get("portfolio_analysis", {}).get("balance_score", 0)
                }
            }

            if "learning_history" not in self.state["learning_data"]:
                self.state["learning_data"]["learning_history"] = []

            self.state["learning_data"]["learning_history"].append(learning_entry)

    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        if not isinstance(input_data, dict):
            return False
        if 'product_data' not in input_data:
            return False
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        return {
            "agent_id": self.config.agent_id,
            "agent_name": self.config.agent_name,
            "version": self.VERSION,
            "status": self.state["status"],
            "timestamp": datetime.now().isoformat(),
            "apqc_metadata": {
                "category_id": self.APQC_CATEGORY_ID,
                "process_id": self.APQC_PROCESS_ID,
                "framework_version": self.APQC_FRAMEWORK_VERSION
            }
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception:
            return 0.0

    def get_input_schema(self) -> Dict[str, Any]:
        """Get input data schema"""
        return {
            "type": "object",
            "description": f"Input schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "properties": {
                "product_data": {"type": "array", "description": "Product performance data"},
                "market_data": {"type": "object", "description": "Market context data"},
                "strategic_goals": {"type": "object", "description": "Strategic objectives"}
            },
            "required": ["product_data"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get output data schema"""
        return {
            "type": "object",
            "description": f"Output schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "properties": {
                "status": {"type": "string"},
                "output": {"type": "object"}
            }
        }

    def log(self, level: str, message: str):
        """Log message"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level.upper()}] [{self.config.agent_name}] {message}")


def create_manage_product_portfolio_sales_marketing_agent(
    config: Optional[ManageProductPortfolioSalesMarketingAgentConfig] = None
) -> ManageProductPortfolioSalesMarketingAgent:
    """Create ManageProductPortfolioSalesMarketingAgent instance"""
    if config is None:
        config = ManageProductPortfolioSalesMarketingAgentConfig()
    return ManageProductPortfolioSalesMarketingAgent(config)
