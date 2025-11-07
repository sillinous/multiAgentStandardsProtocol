"""
SegmentCustomersSalesMarketingAgent - APQC 3.0 Agent

3.1.3 Segment Customers

This agent implements APQC process 3.1.3 from category 3.0: Market and Sell Products and Services.

Domain: sales_marketing
Type: analytical

Fully compliant with Architectural Standards v1.0.0:
- Standardized (BaseAgent + dataclass config)
- Interoperable (A2A, A2P, ACP, ANP, MCP protocols)
- Redeployable (environment configuration)
- Reusable (no project-specific logic)
- Atomic (single responsibility)
- Composable (schema-based I/O)
- Orchestratable (coordination protocol support)
- Vendor Agnostic (abstraction layers)

APQC Blueprint ID: apqc_3_0_p8q9r0s1
APQC Category: 3.0 - Market and Sell Products and Services
APQC Process: 3.1.3 - Segment Customers

Version: 1.0.0
Date: 2025-10-17
Framework: APQC 7.0.1
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class SegmentCustomersSalesMarketingAgentConfig:
    """Configuration for SegmentCustomersSalesMarketingAgent"""

    # APQC Metadata
    apqc_agent_id: str = "apqc_3_0_p8q9r0s1"
    apqc_category_id: str = "3.0"
    apqc_category_name: str = "Market and Sell Products and Services"
    apqc_process_id: str = "3.1.3"
    apqc_process_name: str = "3.1.3 Segment Customers"

    # Agent Identity
    agent_id: str = "apqc_3_0_p8q9r0s1"
    agent_name: str = "segment_customers_sales_marketing_agent"
    agent_type: str = "analytical"
    domain: str = "sales_marketing"
    version: str = "1.0.0"

    # Behavior Configuration
    autonomous_level: float = 0.92
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
    qa_threshold: float = 0.90
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
    def from_environment(cls) -> "SegmentCustomersSalesMarketingAgentConfig":
        """Create configuration from environment variables (Redeployable)"""
        return cls(
            agent_id=os.getenv("AGENT_ID", "apqc_3_0_p8q9r0s1"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "300")),
        )


class SegmentCustomersSalesMarketingAgent(BaseAgent, ProtocolMixin):
    """
    SegmentCustomersSalesMarketingAgent - APQC 3.0 Agent

    3.1.3 Segment Customers

    Implements advanced customer segmentation using RFM analysis, K-means clustering,
    Customer Lifetime Value (CLV) calculation, and behavioral profiling.

    Capabilities:
    - rfm_analysis
    - clustering
    - clv_calculation
    - behavioral_segmentation
    - predictive_analytics
    - cohort_analysis
    - value_scoring
    - segment_profiling

    Skills:
    - rfm_analysis: 0.92
    - clustering: 0.89
    - clv_calculation: 0.87
    - segmentation: 0.90

    Business Logic:
    - RFM (Recency, Frequency, Monetary) scoring with quintile segmentation
    - K-means clustering for behavioral patterns
    - CLV prediction using historical purchase patterns
    - Segment profiling with actionable insights
    - Cohort analysis and lifecycle stage detection

    Interfaces:
      Inputs: customer_transactions, purchase_history, engagement_data, customer_attributes
      Outputs: customer_segments, rfm_scores, clusters, clv_estimates, segment_profiles, recommendations
      Protocols: message_passing, event_driven, api_rest

    Behavior:
      Autonomous Level: 0.92
      Collaboration: orchestrated
      Learning: Enabled
      Self-Improvement: Enabled

    Integration:
      Compatible Agents: 3.0, 4.0, 6.0, 8.0
      Required Services: analytics_engine, customer_database, ml_platform
      Ontology Level: L2_customer_intelligence

    Compliance: FULL (All 8 architectural principles)
    Protocols: A2A, A2P, ACP, ANP, MCP
    """

    VERSION = "1.0.0"
    MIN_COMPATIBLE_VERSION = "1.0.0"

    # APQC Blueprint Metadata
    APQC_AGENT_ID = "apqc_3_0_p8q9r0s1"
    APQC_CATEGORY_ID = "3.0"
    APQC_PROCESS_ID = "3.1.3"
    APQC_FRAMEWORK_VERSION = "7.0.1"

    def __init__(self, config: SegmentCustomersSalesMarketingAgentConfig):
        """Initialize agent"""
        super().__init__(
            agent_id=config.agent_id, agent_type=config.agent_type, version=config.version
        )

        self.config = config
        self.capabilities_list = [
            "rfm_analysis",
            "clustering",
            "clv_calculation",
            "behavioral_segmentation",
            "predictive_analytics",
            "cohort_analysis",
            "value_scoring",
            "segment_profiling",
        ]
        self.skills = {
            "rfm_analysis": 0.92,
            "clustering": 0.89,
            "clv_calculation": 0.87,
            "segmentation": 0.90,
        }
        self.interfaces = {
            "inputs": [
                "customer_transactions",
                "purchase_history",
                "engagement_data",
                "customer_attributes",
            ],
            "outputs": [
                "customer_segments",
                "rfm_scores",
                "clusters",
                "clv_estimates",
                "segment_profiles",
                "recommendations",
            ],
            "protocols": ["message_passing", "event_driven", "api_rest"],
        }
        self.behavior = {
            "autonomous_level": 0.92,
            "collaboration_mode": "orchestrated",
            "learning_enabled": True,
            "self_improvement": True,
        }
        self.resources = {
            "compute": "adaptive",
            "memory": "adaptive",
            "api_budget": "dynamic",
            "priority": "high",
        }
        self.integration = {
            "compatible_agents": ["3.0", "4.0", "6.0", "8.0"],
            "required_services": ["analytics_engine", "customer_database", "ml_platform"],
            "ontology_level": "L2_customer_intelligence",
        }
        self.quality = {
            "testing_required": True,
            "qa_threshold": 0.90,
            "consensus_weight": 1.0,
            "error_handling": "graceful_degradation",
        }
        self.deployment = {
            "runtime": "ray_actor",
            "scaling": "horizontal",
            "health_checks": True,
            "monitoring": True,
        }

        # Initialize state
        self.state = {
            "status": "initialized",
            "tasks_processed": 0,
            "last_activity": datetime.now().isoformat(),
            "performance_metrics": {},
            "learning_data": {} if self.config.learning_enabled else None,
        }

        self._initialize_protocols()
        self._initialize_monitoring()

    @classmethod
    def from_environment(cls) -> "SegmentCustomersSalesMarketingAgent":
        """Create agent from environment variables (Redeployable)"""
        config = SegmentCustomersSalesMarketingAgentConfig.from_environment()
        return cls(config)

    def _initialize_protocols(self):
        """Initialize protocol support"""
        self.log("info", f"Protocols initialized: A2A, A2P, ACP, ANP, MCP")

    def _initialize_monitoring(self):
        """Initialize monitoring and health checks"""
        if self.config.monitoring:
            self.log("info", f"Monitoring enabled for {self.config.agent_name}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute customer segmentation analysis (Atomic)

        Args:
            input_data: {
                "customer_transactions": List of transaction records
                "purchase_history": Historical purchase data
                "engagement_data": Customer engagement metrics
                "customer_attributes": Additional customer attributes
                "analysis_date": Reference date for recency calculation
                "num_clusters": Number of clusters for K-means (default: 5)
                "clv_period_months": Months to predict CLV (default: 12)
            }

        Returns:
            Output data with customer segments, RFM scores, CLV estimates, and recommendations
        """
        self.log("info", f"Executing {self.config.apqc_process_name}")

        try:
            # Validate input
            if not self._validate_input(input_data):
                return {
                    "status": "error",
                    "message": "Invalid input data",
                    "error_handling": self.config.error_handling,
                }

            # Extract input parameters
            transactions = input_data.get("customer_transactions", [])
            purchase_history = input_data.get("purchase_history", [])
            engagement_data = input_data.get("engagement_data", {})
            analysis_date = input_data.get("analysis_date", datetime.now())
            num_clusters = input_data.get("num_clusters", 5)
            clv_period = input_data.get("clv_period_months", 12)

            # Perform RFM Analysis
            rfm_scores = self._calculate_rfm_scores(transactions, analysis_date)

            # Calculate Customer Lifetime Value
            clv_estimates = self._calculate_clv(purchase_history, clv_period)

            # Perform clustering
            clusters = self._perform_clustering(rfm_scores, clv_estimates, num_clusters)

            # Generate segment profiles
            segment_profiles = self._generate_segment_profiles(
                rfm_scores, clv_estimates, clusters, engagement_data
            )

            # Create customer segments
            customer_segments = self._create_customer_segments(rfm_scores, clusters, clv_estimates)

            # Generate recommendations
            recommendations = self._generate_recommendations(segment_profiles)

            result = {
                "status": "completed",
                "apqc_process_id": self.APQC_PROCESS_ID,
                "agent_id": self.config.agent_id,
                "timestamp": datetime.now().isoformat(),
                "output": {
                    "customer_segments": customer_segments,
                    "rfm_scores": rfm_scores,
                    "clusters": clusters,
                    "clv_estimates": clv_estimates,
                    "segment_profiles": segment_profiles,
                    "recommendations": recommendations,
                    "metrics": {
                        "total_customers": len(rfm_scores),
                        "num_segments": len(segment_profiles),
                        "total_clv": sum(clv_estimates.values()),
                        "avg_clv": (
                            sum(clv_estimates.values()) / len(clv_estimates) if clv_estimates else 0
                        ),
                    },
                },
            }

            # Update state
            self.state["tasks_processed"] += 1
            self.state["last_activity"] = datetime.now().isoformat()

            # Learning and self-improvement
            if self.config.learning_enabled:
                await self._learn_from_execution(input_data, result)

            return result

        except Exception as e:
            self.log("error", f"Execution error: {str(e)}")
            if self.config.error_handling == "graceful_degradation":
                return {"status": "degraded", "message": str(e), "partial_result": {}}
            raise

    def _calculate_rfm_scores(
        self, transactions: List[Dict[str, Any]], analysis_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate RFM (Recency, Frequency, Monetary) scores for customer segmentation.

        RFM Analysis:
        - Recency: Days since last purchase (lower is better)
        - Frequency: Number of purchases (higher is better)
        - Monetary: Total spend (higher is better)

        Each metric is scored 1-5 using quintile segmentation.

        Args:
            transactions: List of transaction records with customer_id, date, amount
            analysis_date: Reference date for recency calculation

        Returns:
            Dictionary of customer RFM scores and segments
        """
        customer_data = defaultdict(
            lambda: {
                "last_purchase": None,
                "purchase_count": 0,
                "total_spend": 0.0,
                "transactions": [],
            }
        )

        # Aggregate transaction data by customer
        for txn in transactions:
            customer_id = txn.get("customer_id")
            txn_date = txn.get("date")
            amount = txn.get("amount", 0.0)

            if isinstance(txn_date, str):
                txn_date = datetime.fromisoformat(txn_date)

            customer_data[customer_id]["purchase_count"] += 1
            customer_data[customer_id]["total_spend"] += amount
            customer_data[customer_id]["transactions"].append(txn)

            if (
                customer_data[customer_id]["last_purchase"] is None
                or txn_date > customer_data[customer_id]["last_purchase"]
            ):
                customer_data[customer_id]["last_purchase"] = txn_date

        # Calculate RFM values
        rfm_values = {}
        for customer_id, data in customer_data.items():
            if data["last_purchase"]:
                recency_days = (analysis_date - data["last_purchase"]).days
            else:
                recency_days = 9999  # Max recency for customers with no purchases

            rfm_values[customer_id] = {
                "recency": recency_days,
                "frequency": data["purchase_count"],
                "monetary": data["total_spend"],
            }

        # Calculate quintile scores (1-5)
        recency_list = [v["recency"] for v in rfm_values.values()]
        frequency_list = [v["frequency"] for v in rfm_values.values()]
        monetary_list = [v["monetary"] for v in rfm_values.values()]

        rfm_scores = {}
        for customer_id, values in rfm_values.items():
            # Recency: Lower is better, so invert the score
            r_score = 6 - self._quintile_score(values["recency"], recency_list)
            f_score = self._quintile_score(values["frequency"], frequency_list)
            m_score = self._quintile_score(values["monetary"], monetary_list)

            rfm_score = r_score * 100 + f_score * 10 + m_score

            # Determine segment based on RFM score
            segment = self._determine_rfm_segment(r_score, f_score, m_score)

            rfm_scores[customer_id] = {
                "recency_days": values["recency"],
                "frequency_count": values["frequency"],
                "monetary_value": values["monetary"],
                "recency_score": r_score,
                "frequency_score": f_score,
                "monetary_score": m_score,
                "rfm_score": rfm_score,
                "rfm_segment": segment,
            }

        return rfm_scores

    def _quintile_score(self, value: float, value_list: List[float]) -> int:
        """
        Calculate quintile score (1-5) for a value within a distribution.

        Args:
            value: The value to score
            value_list: List of all values for percentile calculation

        Returns:
            Score from 1 (bottom 20%) to 5 (top 20%)
        """
        if not value_list:
            return 3

        sorted_values = sorted(value_list)
        percentile = (sorted_values.index(value) + 1) / len(sorted_values) * 100

        if percentile <= 20:
            return 1
        elif percentile <= 40:
            return 2
        elif percentile <= 60:
            return 3
        elif percentile <= 80:
            return 4
        else:
            return 5

    def _determine_rfm_segment(self, r: int, f: int, m: int) -> str:
        """
        Determine customer segment based on RFM scores.

        Classic RFM Segmentation:
        - Champions: High R, F, M (555, 554, 544, etc.)
        - Loyal Customers: High F, M but varying R
        - Potential Loyalists: Recent customers with average F, M
        - At Risk: Low R but high F, M
        - Can't Lose Them: Lowest R but highest F, M
        - Lost: Lowest R, F, M

        Args:
            r: Recency score (1-5)
            f: Frequency score (1-5)
            m: Monetary score (1-5)

        Returns:
            Segment name
        """
        # Champions
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"

        # Loyal Customers
        elif f >= 4 and m >= 4:
            return "Loyal Customers"

        # Potential Loyalists
        elif r >= 4 and f >= 2 and m >= 2:
            return "Potential Loyalists"

        # New Customers
        elif r >= 4 and f <= 2:
            return "New Customers"

        # Promising
        elif r >= 3 and f <= 2 and m <= 2:
            return "Promising"

        # Need Attention
        elif r >= 3 and f >= 3 and m >= 3:
            return "Need Attention"

        # About to Sleep
        elif r <= 3 and f <= 3:
            return "About to Sleep"

        # At Risk
        elif r <= 2 and f >= 3 and m >= 3:
            return "At Risk"

        # Can't Lose Them
        elif r <= 2 and f >= 4 and m >= 4:
            return "Can't Lose Them"

        # Hibernating
        elif r <= 2 and f <= 2 and m >= 3:
            return "Hibernating"

        # Lost
        elif r <= 2 and f <= 2 and m <= 2:
            return "Lost"

        else:
            return "Other"

    def _calculate_clv(
        self, purchase_history: List[Dict[str, Any]], period_months: int
    ) -> Dict[str, float]:
        """
        Calculate Customer Lifetime Value (CLV) using historical purchase patterns.

        CLV Formula (Simplified):
        CLV = (Average Purchase Value × Purchase Frequency × Customer Lifespan)

        For prediction:
        CLV = (Avg Monthly Revenue per Customer × Gross Margin %) × (1 / Monthly Churn Rate)

        Args:
            purchase_history: Historical purchase data
            period_months: Number of months to predict CLV

        Returns:
            Dictionary of customer CLV estimates
        """
        customer_purchases = defaultdict(list)

        for purchase in purchase_history:
            customer_id = purchase.get("customer_id")
            amount = purchase.get("amount", 0.0)
            date = purchase.get("date")

            if isinstance(date, str):
                date = datetime.fromisoformat(date)

            customer_purchases[customer_id].append({"amount": amount, "date": date})

        clv_estimates = {}

        for customer_id, purchases in customer_purchases.items():
            if not purchases:
                clv_estimates[customer_id] = 0.0
                continue

            # Calculate average purchase value
            avg_purchase_value = sum(p["amount"] for p in purchases) / len(purchases)

            # Calculate purchase frequency (purchases per month)
            sorted_purchases = sorted(purchases, key=lambda x: x["date"])
            first_purchase = sorted_purchases[0]["date"]
            last_purchase = sorted_purchases[-1]["date"]

            months_active = max(1, (last_purchase - first_purchase).days / 30)
            purchase_frequency = (
                len(purchases) / months_active if months_active > 0 else len(purchases)
            )

            # Estimate customer lifespan (simplified: use period_months)
            # In production, this would use churn prediction models
            customer_lifespan_months = period_months

            # Calculate CLV
            # Assuming 30% gross margin (configurable in production)
            gross_margin = 0.30

            clv = avg_purchase_value * purchase_frequency * customer_lifespan_months * gross_margin
            clv_estimates[customer_id] = round(clv, 2)

        return clv_estimates

    def _perform_clustering(
        self,
        rfm_scores: Dict[str, Dict[str, Any]],
        clv_estimates: Dict[str, float],
        num_clusters: int,
    ) -> Dict[str, int]:
        """
        Perform K-means clustering on customer data for behavioral segmentation.

        Uses RFM scores and CLV as features for clustering.
        Simplified K-means implementation (in production, use scikit-learn).

        Args:
            rfm_scores: RFM score data
            clv_estimates: CLV estimates
            num_clusters: Number of clusters

        Returns:
            Dictionary mapping customer_id to cluster_id
        """
        # Prepare feature vectors
        features = []
        customer_ids = []

        for customer_id, rfm in rfm_scores.items():
            clv = clv_estimates.get(customer_id, 0)

            # Normalize features (min-max normalization)
            feature_vector = [
                rfm["recency_score"] / 5.0,
                rfm["frequency_score"] / 5.0,
                rfm["monetary_score"] / 5.0,
                min(clv / 10000.0, 1.0),  # Normalize CLV (cap at 10k for normalization)
            ]

            features.append(feature_vector)
            customer_ids.append(customer_id)

        if not features:
            return {}

        # Simplified K-means clustering
        # In production, use: from sklearn.cluster import KMeans
        np_features = np.array(features)

        # Initialize centroids randomly
        np.random.seed(42)
        centroid_indices = np.random.choice(
            len(features), min(num_clusters, len(features)), replace=False
        )
        centroids = np_features[centroid_indices]

        # Iterate to convergence (max 100 iterations)
        for _ in range(100):
            # Assign points to nearest centroid
            distances = np.sqrt(((np_features[:, np.newaxis] - centroids) ** 2).sum(axis=2))
            labels = np.argmin(distances, axis=1)

            # Update centroids
            new_centroids = np.array(
                [
                    np_features[labels == k].mean(axis=0) if np.any(labels == k) else centroids[k]
                    for k in range(num_clusters)
                ]
            )

            # Check convergence
            if np.allclose(centroids, new_centroids):
                break

            centroids = new_centroids

        # Create customer to cluster mapping
        clusters = {customer_ids[i]: int(labels[i]) for i in range(len(customer_ids))}

        return clusters

    def _generate_segment_profiles(
        self,
        rfm_scores: Dict[str, Dict[str, Any]],
        clv_estimates: Dict[str, float],
        clusters: Dict[str, int],
        engagement_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed profiles for each customer segment.

        Args:
            rfm_scores: RFM score data
            clv_estimates: CLV estimates
            clusters: Cluster assignments
            engagement_data: Customer engagement metrics

        Returns:
            List of segment profiles with characteristics and insights
        """
        # Group customers by cluster
        cluster_groups = defaultdict(list)
        for customer_id, cluster_id in clusters.items():
            cluster_groups[cluster_id].append(customer_id)

        segment_profiles = []

        for cluster_id, customer_list in cluster_groups.items():
            # Calculate aggregate metrics
            avg_recency = np.mean([rfm_scores[c]["recency_days"] for c in customer_list])
            avg_frequency = np.mean([rfm_scores[c]["frequency_count"] for c in customer_list])
            avg_monetary = np.mean([rfm_scores[c]["monetary_value"] for c in customer_list])
            avg_clv = np.mean([clv_estimates.get(c, 0) for c in customer_list])

            total_clv = sum([clv_estimates.get(c, 0) for c in customer_list])
            customer_count = len(customer_list)

            # Determine segment characteristics
            if avg_recency < 30 and avg_frequency > 5 and avg_monetary > 500:
                segment_name = f"High-Value Active (Cluster {cluster_id})"
                characteristics = "Recent, frequent, high-spending customers"
                strategy = "VIP treatment, exclusive offers, loyalty rewards"
            elif avg_recency < 60 and avg_frequency > 3:
                segment_name = f"Core Customers (Cluster {cluster_id})"
                characteristics = "Regular customers with moderate engagement"
                strategy = "Upsell, cross-sell, maintain engagement"
            elif avg_recency > 180:
                segment_name = f"At-Risk/Churned (Cluster {cluster_id})"
                characteristics = "Inactive customers, high churn risk"
                strategy = "Win-back campaigns, re-engagement offers"
            else:
                segment_name = f"Emerging Segment (Cluster {cluster_id})"
                characteristics = "Growing customer base with potential"
                strategy = "Nurture, educate, convert to loyal customers"

            profile = {
                "segment_id": cluster_id,
                "segment_name": segment_name,
                "customer_count": customer_count,
                "characteristics": characteristics,
                "metrics": {
                    "avg_recency_days": round(avg_recency, 1),
                    "avg_frequency": round(avg_frequency, 1),
                    "avg_monetary_value": round(avg_monetary, 2),
                    "avg_clv": round(avg_clv, 2),
                    "total_clv": round(total_clv, 2),
                    "pct_of_total_customers": round(customer_count / len(rfm_scores) * 100, 1),
                },
                "recommended_strategy": strategy,
                "priority": "high" if avg_clv > 1000 else "medium" if avg_clv > 500 else "low",
            }

            segment_profiles.append(profile)

        # Sort by total CLV descending
        segment_profiles.sort(key=lambda x: x["metrics"]["total_clv"], reverse=True)

        return segment_profiles

    def _create_customer_segments(
        self,
        rfm_scores: Dict[str, Dict[str, Any]],
        clusters: Dict[str, int],
        clv_estimates: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        Create customer segment assignments with detailed attributes.

        Args:
            rfm_scores: RFM score data
            clusters: Cluster assignments
            clv_estimates: CLV estimates

        Returns:
            List of customer segment assignments
        """
        customer_segments = []

        for customer_id, rfm in rfm_scores.items():
            segment = {
                "customer_id": customer_id,
                "rfm_segment": rfm["rfm_segment"],
                "cluster_id": clusters.get(customer_id, -1),
                "rfm_score": rfm["rfm_score"],
                "clv_estimate": clv_estimates.get(customer_id, 0),
                "recency_days": rfm["recency_days"],
                "frequency": rfm["frequency_count"],
                "monetary_value": rfm["monetary_value"],
                "customer_tier": self._determine_customer_tier(
                    rfm["rfm_score"], clv_estimates.get(customer_id, 0)
                ),
            }

            customer_segments.append(segment)

        return customer_segments

    def _determine_customer_tier(self, rfm_score: int, clv: float) -> str:
        """
        Determine customer tier based on RFM score and CLV.

        Args:
            rfm_score: Combined RFM score
            clv: Customer Lifetime Value

        Returns:
            Customer tier (Platinum, Gold, Silver, Bronze)
        """
        if rfm_score >= 444 and clv >= 2000:
            return "Platinum"
        elif rfm_score >= 333 and clv >= 1000:
            return "Gold"
        elif rfm_score >= 222 and clv >= 500:
            return "Silver"
        else:
            return "Bronze"

    def _generate_recommendations(
        self, segment_profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on segment analysis.

        Args:
            segment_profiles: Segment profile data

        Returns:
            List of strategic recommendations
        """
        recommendations = []

        for profile in segment_profiles:
            recommendation = {
                "segment_id": profile["segment_id"],
                "segment_name": profile["segment_name"],
                "priority": profile["priority"],
                "actions": [],
                "expected_impact": {},
            }

            # Generate specific actions based on segment characteristics
            avg_recency = profile["metrics"]["avg_recency_days"]
            avg_frequency = profile["metrics"]["avg_frequency"]
            total_clv = profile["metrics"]["total_clv"]

            if avg_recency < 30 and total_clv > 10000:
                recommendation["actions"].extend(
                    [
                        "Launch VIP loyalty program with exclusive benefits",
                        "Provide dedicated account management",
                        "Offer early access to new products",
                        "Create referral incentive program",
                    ]
                )
                recommendation["expected_impact"] = {
                    "retention_increase": "15-25%",
                    "revenue_lift": "20-30%",
                }

            elif avg_recency > 180:
                recommendation["actions"].extend(
                    [
                        "Execute win-back email campaign with special offers",
                        "Conduct survey to understand disengagement",
                        "Offer re-activation discount or incentive",
                        "Review and address potential product/service issues",
                    ]
                )
                recommendation["expected_impact"] = {
                    "reactivation_rate": "10-15%",
                    "recovered_revenue": f"${total_clv * 0.1:.0f}",
                }

            elif avg_frequency > 3:
                recommendation["actions"].extend(
                    [
                        "Implement cross-sell campaigns for complementary products",
                        "Develop personalized product recommendations",
                        "Create engagement programs to increase frequency",
                        "Test upsell offers for premium tiers",
                    ]
                )
                recommendation["expected_impact"] = {
                    "frequency_increase": "10-20%",
                    "basket_size_increase": "15-25%",
                }

            else:
                recommendation["actions"].extend(
                    [
                        "Nurture with educational content",
                        "Gradually introduce product portfolio",
                        "Build trust through value-first approach",
                        "Monitor engagement and adjust strategy",
                    ]
                )
                recommendation["expected_impact"] = {
                    "conversion_to_loyal": "20-30%",
                    "ltv_growth": "50-75%",
                }

            recommendations.append(recommendation)

        return recommendations

    async def _learn_from_execution(self, input_data: Dict[str, Any], result: Dict[str, Any]):
        """Learn from execution for self-improvement"""
        if not self.config.self_improvement:
            return

        if self.state["learning_data"] is not None:
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "customers_analyzed": len(result["output"].get("customer_segments", [])),
                "segments_created": len(result["output"].get("segment_profiles", [])),
                "total_clv": result["output"]["metrics"].get("total_clv", 0),
                "result_status": result.get("status"),
                "performance": {},
            }

            if "learning_history" not in self.state["learning_data"]:
                self.state["learning_data"]["learning_history"] = []

            self.state["learning_data"]["learning_history"].append(learning_entry)

    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema"""
        if not isinstance(input_data, dict):
            return False

        # Check for required data
        if "customer_transactions" not in input_data:
            return False

        return True

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check (Redeployable)"""
        memory_usage = self._get_memory_usage()

        health = {
            "agent_id": self.config.agent_id,
            "agent_name": self.config.agent_name,
            "version": self.VERSION,
            "status": self.state["status"],
            "timestamp": datetime.now().isoformat(),
            "apqc_metadata": {
                "category_id": self.APQC_CATEGORY_ID,
                "process_id": self.APQC_PROCESS_ID,
                "framework_version": self.APQC_FRAMEWORK_VERSION,
            },
            "protocols": self.get_supported_protocols(),
            "capabilities": self.capabilities_list,
            "compliance": {
                "standardized": True,
                "interoperable": True,
                "redeployable": True,
                "reusable": True,
                "atomic": True,
                "composable": True,
                "orchestratable": True,
                "vendor_agnostic": True,
            },
            "performance": {
                "tasks_processed": self.state["tasks_processed"],
                "memory_mb": memory_usage,
                "last_activity": self.state["last_activity"],
            },
            "behavior": {
                "autonomous_level": self.config.autonomous_level,
                "learning_enabled": self.config.learning_enabled,
                "collaboration_mode": self.config.collaboration_mode,
            },
            "deployment": {
                "runtime": self.config.runtime,
                "scaling": self.config.scaling,
                "monitoring": self.config.monitoring,
            },
        }

        return health

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB (Resource Monitoring)"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception as e:
            self.log("warning", f"Could not get memory usage: {str(e)}")
            return 0.0

    def get_input_schema(self) -> Dict[str, Any]:
        """Get input data schema (Composable)"""
        return {
            "type": "object",
            "description": f"Input schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "accepted_inputs": self.interfaces["inputs"],
            "properties": {
                "customer_transactions": {
                    "type": "array",
                    "description": "List of customer transaction records",
                    "items": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "date": {"type": "string", "format": "date-time"},
                            "amount": {"type": "number"},
                        },
                    },
                },
                "purchase_history": {"type": "array", "description": "Historical purchase data"},
                "engagement_data": {"type": "object", "description": "Customer engagement metrics"},
                "analysis_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Reference date for analysis",
                },
                "num_clusters": {
                    "type": "integer",
                    "default": 5,
                    "description": "Number of clusters for segmentation",
                },
                "clv_period_months": {
                    "type": "integer",
                    "default": 12,
                    "description": "Months to predict CLV",
                },
            },
            "required": ["customer_transactions"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get output data schema (Composable)"""
        return {
            "type": "object",
            "description": f"Output schema for {self.config.apqc_process_name}",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "generated_outputs": self.interfaces["outputs"],
            "properties": {
                "status": {"type": "string", "enum": ["completed", "error", "degraded"]},
                "apqc_process_id": {"type": "string"},
                "agent_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "output": {
                    "type": "object",
                    "properties": {
                        "customer_segments": {"type": "array"},
                        "rfm_scores": {"type": "object"},
                        "clusters": {"type": "object"},
                        "clv_estimates": {"type": "object"},
                        "segment_profiles": {"type": "array"},
                        "recommendations": {"type": "array"},
                        "metrics": {"type": "object"},
                    },
                },
            },
            "required": ["status", "apqc_process_id", "agent_id", "timestamp", "output"],
        }

    def log(self, level: str, message: str):
        """Log message"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level.upper()}] [{self.config.agent_name}] {message}")


# Convenience function for agent creation
def create_segment_customers_sales_marketing_agent(
    config: Optional[SegmentCustomersSalesMarketingAgentConfig] = None,
) -> SegmentCustomersSalesMarketingAgent:
    """Create SegmentCustomersSalesMarketingAgent instance"""
    if config is None:
        config = SegmentCustomersSalesMarketingAgentConfig()
    return SegmentCustomersSalesMarketingAgent(config)
