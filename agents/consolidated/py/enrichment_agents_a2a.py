"""
A2A-Enabled Product Enrichment Agents
Converts existing enrichment agents to use Agent-to-Agent communication

These agents register with MessageRoutingAgent and respond to WORKFLOW_TASK messages
from the EnrichmentWorkflowCoordinatorAgent.

APQC Alignment:
- Product Intelligence: 3.3 Manage Product Information
- Market Analysis: 3.1 Understand Markets
- Competitive Intelligence: 3.1 Understand Markets
- Pricing Strategy: 3.3 Develop Pricing Strategy
- Customer Profiling: 3.1 Understand Customers
- Business Model: 1.1 Define Business Concept
- Image Discovery: 3.3 Manage Product Information
"""

import asyncio
import logging
import json
from typing import Dict, Optional, Any
from datetime import datetime
import time
import os
from openai import OpenAI
import requests

from app.a2a_communication.message_routing_agent import routing_agent
from app.a2a_communication.interfaces import (
    AgentMessage, AgentResponse, AgentIdentifier,
    MessageType, Priority, AgentTeam
)

logger = logging.getLogger(__name__)


class BaseEnrichmentAgentA2A:
    """
    Base class for A2A-enabled enrichment agents

    All enrichment agents:
    1. Register with MessageRoutingAgent on initialization
    2. Listen for WORKFLOW_TASK messages
    3. Process enrichment requests
    4. Return results via AgentResponse
    """

    def __init__(self, identifier: AgentIdentifier):
        self.identifier = identifier
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        # Register with routing system
        asyncio.create_task(self._register())

        logger.info(f"🤖 A2A Agent '{identifier.name}' initialized")

    async def _register(self):
        """Register this agent with MessageRoutingAgent"""
        try:
            await routing_agent.register_agent(self.identifier)
            logger.info(f"✓ {self.identifier.name} registered with MessageRoutingAgent")
        except Exception as e:
            logger.error(f"Failed to register {self.identifier.name}: {e}")

    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """
        Handle incoming A2A messages

        This is called by MessageRoutingAgent when a message arrives
        for this agent.
        """
        start_time = time.time()

        try:
            # Extract payload
            task_type = message.payload.get("task_type")
            keyword = message.payload.get("keyword")
            context = message.payload.get("context", {})

            if task_type != "product_enrichment":
                return AgentResponse(
                    request_id=message.message_id,
                    source_agent=self.identifier,
                    status="error",
                    error_message=f"Unsupported task_type: {task_type}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Perform enrichment
            result = await self.enrich(keyword, context)

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResponse(
                request_id=message.message_id,
                source_agent=self.identifier,
                status="success",
                payload={
                    "data": result["data"],
                    "confidence": result["confidence"]
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"Error in {self.identifier.name}: {e}", exc_info=True)

            return AgentResponse(
                request_id=message.message_id,
                source_agent=self.identifier,
                status="error",
                error_message=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Override in subclass to provide enrichment logic"""
        raise NotImplementedError


class ProductIntelligenceAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Product Intelligence Agent
    APQC: 3.3 Manage Product Information
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="product_intelligence_agent",
            name="Product Intelligence Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.3 Manage Product Information",
            version="2.0.0",  # v2 = A2A enabled
            capabilities=["product_analysis", "feature_extraction", "product_categorization"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Extract comprehensive product intelligence"""

        logger.info(f"🔍 Analyzing product: {keyword}")

        if not self.client:
            return {
                "data": self._fallback_intelligence(keyword),
                "confidence": 0.5
            }

        try:
            prompt = f"""Analyze this product: "{keyword}"

Extract detailed intelligence in JSON format:
{{
  "title": "Professional product title",
  "brand": "Brand name (real or likely)",
  "model": "Model/variant name",
  "category": "Specific category",
  "subcategory": "More specific subcategory",
  "description": "Detailed 2-3 paragraph description",
  "features": ["6-8 specific features"],
  "specs": {{"key": "value"}},
  "materials": ["Primary materials used"],
  "dimensions": {{"length": "", "width": "", "height": "", "weight": ""}},
  "target_audience": "Detailed target customer",
  "use_cases": ["4-5 specific use cases"],
  "pain_points_solved": ["Problems this solves"],
  "quality_indicators": ["What makes this quality"],
  "price_range_low": 0,
  "price_range_high": 0,
  "typical_lifespan": "Product lifespan",
  "maintenance_required": "Maintenance needs"
}}

Be SPECIFIC and DETAILED. Use real market knowledge."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a product intelligence specialist. Provide detailed, market-accurate product information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            logger.info(f"✅ Product intelligence analysis complete")

            return {
                "data": data,
                "confidence": 0.9
            }

        except Exception as e:
            logger.error(f"Product intelligence failed: {e}")
            return {
                "data": self._fallback_intelligence(keyword),
                "confidence": 0.5
            }

    def _fallback_intelligence(self, keyword: str) -> Dict:
        return {
            "title": keyword.title(),
            "brand": keyword.split()[0].title() if ' ' in keyword else "Generic",
            "category": "Consumer Products",
            "description": f"High-quality {keyword} designed for optimal performance.",
            "features": [f"Premium {keyword}", "Durable construction", "Easy to use"],
            "specs": {"Type": keyword.title()},
            "price_range_low": 30,
            "price_range_high": 150
        }


class MarketAnalysisAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Market Analysis Agent
    APQC: 3.1 Understand Markets
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="market_analysis_agent",
            name="Market Analysis Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.1 Understand Markets and Customers",
            version="2.0.0",
            capabilities=["market_sizing", "trend_analysis", "demand_assessment"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Analyze market opportunity and trends"""

        logger.info(f"📊 Analyzing market for: {keyword}")

        if not self.client:
            return {
                "data": self._fallback_analysis(keyword),
                "confidence": 0.5
            }

        try:
            prompt = f"""Analyze the market opportunity for: "{keyword}"

Provide comprehensive market analysis in JSON:
{{
  "market_size_usd": "Total addressable market in USD",
  "growth_rate_annual": "Annual growth rate %",
  "market_stage": "emerging/growing/mature/declining",
  "demand_level": "low/medium/high/very high",
  "demand_drivers": ["Key factors driving demand"],
  "market_trends": ["Current market trends"],
  "seasonal_patterns": "Seasonality description",
  "peak_season": "Best selling months",
  "geographic_hotspots": ["Top markets/regions"],
  "online_search_volume": "Estimated monthly searches",
  "competition_level": "low/medium/high",
  "barriers_to_entry": ["Entry barriers"],
  "success_factors": ["Keys to success"],
  "market_risks": ["Market-specific risks"],
  "opportunity_score": 0.0-1.0,
  "recommended_entry_timing": "Now/wait/seasonal timing"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a market research analyst specializing in e-commerce opportunities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            logger.info(f"✅ Market analysis complete")

            return {
                "data": data,
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {
                "data": self._fallback_analysis(keyword),
                "confidence": 0.5
            }

    def _fallback_analysis(self, keyword: str) -> Dict:
        return {
            "market_size_usd": "Growing market",
            "demand_level": "medium",
            "opportunity_score": 0.7,
            "competition_level": "medium",
            "market_stage": "growing"
        }


class CompetitiveIntelligenceAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Competitive Intelligence Agent
    APQC: 3.1 Understand Markets
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="competitive_intelligence_agent",
            name="Competitive Intelligence Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.1 Understand Markets and Customers",
            version="2.0.0",
            capabilities=["competitor_analysis", "market_positioning", "differentiation_strategy"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Analyze competitive landscape"""

        logger.info(f"🎯 Analyzing competition for: {keyword}")

        if not self.client:
            return {
                "data": self._fallback_analysis(keyword),
                "confidence": 0.5
            }

        try:
            prompt = f"""Analyze the competitive landscape for: "{keyword}"

Provide competitive intelligence in JSON:
{{
  "main_competitors": [
    {{
      "name": "Competitor name",
      "market_position": "leader/challenger/nicher",
      "strengths": ["Key strengths"],
      "weaknesses": ["Vulnerabilities"],
      "price_range": "Price positioning"
    }}
  ],
  "competitive_intensity": "low/medium/high/very high",
  "market_concentration": "fragmented/concentrated",
  "differentiation_opportunities": ["Ways to differentiate"],
  "competitive_gaps": ["Unmet market needs"],
  "pricing_strategies_observed": ["Common pricing approaches"],
  "distribution_channels_used": ["Where competitors sell"],
  "marketing_tactics_common": ["Common marketing methods"],
  "quality_benchmarks": "Quality standards in market",
  "innovation_pace": "How fast market evolves",
  "recommended_positioning": "How to position vs competitors"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a competitive intelligence analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            logger.info(f"✅ Competitive analysis complete")

            return {
                "data": data,
                "confidence": 0.8
            }

        except Exception as e:
            logger.error(f"Competitive analysis failed: {e}")
            return {
                "data": self._fallback_analysis(keyword),
                "confidence": 0.5
            }

    def _fallback_analysis(self, keyword: str) -> Dict:
        return {
            "competitive_intensity": "medium",
            "market_concentration": "fragmented",
            "differentiation_opportunities": ["Quality focus", "Better service", "Faster shipping"]
        }


class PricingStrategyAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Pricing Strategy Agent
    APQC: 3.3 Develop Pricing Strategy
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="pricing_strategy_agent",
            name="Pricing Strategy Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.3 Develop and Manage Pricing",
            version="2.0.0",
            capabilities=["pricing_optimization", "margin_analysis", "competitive_pricing"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Determine optimal pricing strategy"""

        logger.info(f"💰 Calculating pricing for: {keyword}")

        # Extract context from previous agents
        product_intel = context.get('product_intelligence', {})
        market_data = context.get('market_analysis', {})

        # Calculate pricing based on available data
        price_low = product_intel.get('price_range_low', 30)
        price_high = product_intel.get('price_range_high', 150)
        avg_price = (price_low + price_high) / 2

        data = {
            "recommended_retail_price": round(avg_price, 2),
            "cost_estimate": round(avg_price * 0.45, 2),  # 45% COGS typical
            "profit_margin_percent": 35,
            "break_even_units": 25,
            "pricing_strategy": "value-based",
            "price_positioning": "mid-market premium",
            "promotional_pricing": {
                "launch_discount": round(avg_price * 0.85, 2),
                "bulk_discount_3": round(avg_price * 0.90, 2),
                "seasonal_sale": round(avg_price * 0.80, 2)
            },
            "price_elasticity": "moderate",
            "psychological_price_point": round(avg_price * 0.99, 2),
            "competitor_price_range": f"${price_low}-${price_high}"
        }

        logger.info(f"✅ Pricing strategy complete")

        return {
            "data": data,
            "confidence": 0.8
        }


class CustomerProfilingAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Customer Profiling Agent
    APQC: 3.1 Understand Customers
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="customer_profiling_agent",
            name="Customer Profiling Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.1 Understand Markets and Customers",
            version="2.0.0",
            capabilities=["persona_creation", "customer_segmentation", "journey_mapping"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Create detailed customer personas"""

        logger.info(f"👥 Profiling customers for: {keyword}")

        if not self.client:
            return {
                "data": self._fallback_profile(keyword),
                "confidence": 0.5
            }

        try:
            prompt = f"""Create detailed customer profiles for: "{keyword}"

Provide comprehensive customer intelligence in JSON:
{{
  "primary_persona": {{
    "name": "Persona name",
    "age_range": "Age range",
    "gender_split": "Gender distribution",
    "income_level": "Income bracket",
    "education": "Education level",
    "occupation": "Typical jobs",
    "lifestyle": "Lifestyle description",
    "values": ["Core values"],
    "pain_points": ["Main problems/needs"],
    "buying_triggers": ["What makes them buy"],
    "decision_factors": ["How they decide"],
    "preferred_channels": ["Where they shop"],
    "price_sensitivity": "low/medium/high",
    "brand_loyalty": "low/medium/high"
  }},
  "secondary_personas": ["2-3 other customer types"],
  "customer_journey": ["Steps from awareness to purchase"],
  "objections_to_overcome": ["Common objections"],
  "messaging_angles": ["Effective marketing messages"],
  "customer_lifetime_value": "Estimated LTV",
  "acquisition_channels": ["Best channels to reach them"],
  "retention_strategies": ["How to keep them coming back"]
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a customer insights specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            logger.info(f"✅ Customer profiling complete")

            return {
                "data": data,
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"Customer profiling failed: {e}")
            return {
                "data": self._fallback_profile(keyword),
                "confidence": 0.5
            }

    def _fallback_profile(self, keyword: str) -> Dict:
        return {
            "primary_persona": {
                "name": "Value Seeker",
                "age_range": "25-45",
                "income_level": "Middle income",
                "pain_points": ["Needs quality at fair price"],
                "buying_triggers": ["Good reviews", "Fair price", "Fast shipping"]
            }
        }


class BusinessModelAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Business Model Agent
    APQC: 1.1 Define Business Concept
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="business_model_agent",
            name="Business Model Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="1.1 Define Business Concept and Long-term Vision",
            version="2.0.0",
            capabilities=["business_model_design", "revenue_modeling", "channel_strategy"],
            status="active"
        )
        super().__init__(identifier)

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Design business model recommendations"""

        logger.info(f"🏢 Designing business models for: {keyword}")

        pricing_data = context.get('pricing_strategy', {})
        price = pricing_data.get('recommended_retail_price', 75)

        models = [
            {
                'name': 'Amazon FBA',
                'description': f'Sell {keyword} via Amazon with FBA fulfillment',
                'startup_cost': price * 50 + 500,
                'monthly_revenue_potential': price * 60,
                'profit_margin': 25,
                'pros': ['Huge audience', 'Fulfillment handled', 'Prime badge'],
                'cons': ['FBA fees', 'Competition', 'Amazon dependency'],
                'difficulty': 'Medium',
                'time_to_profit': '2-3 months'
            },
            {
                'name': 'Direct E-commerce (Shopify)',
                'description': f'Own branded store selling {keyword}',
                'startup_cost': price * 25 + 300,
                'monthly_revenue_potential': price * 40,
                'profit_margin': 40,
                'pros': ['Brand control', 'Higher margins', 'Customer data'],
                'cons': ['Marketing costs', 'Customer acquisition', 'Fulfillment'],
                'difficulty': 'Medium-High',
                'time_to_profit': '3-6 months'
            },
            {
                'name': 'Dropshipping',
                'description': f'Sell {keyword} without inventory',
                'startup_cost': 500,
                'monthly_revenue_potential': price * 30,
                'profit_margin': 20,
                'pros': ['Low startup', 'No inventory risk', 'Easy scaling'],
                'cons': ['Low margins', 'Shipping times', 'Less control'],
                'difficulty': 'Low',
                'time_to_profit': '1-2 months'
            }
        ]

        logger.info(f"✅ Business model design complete")

        return {
            "data": {
                'business_models': models,
                'recommended_model': models[0]['name']
            },
            "confidence": 0.9
        }


class ImageDiscoveryAgentA2A(BaseEnrichmentAgentA2A):
    """
    A2A-Enabled Image Discovery Agent
    APQC: 3.3 Manage Product Information
    """

    def __init__(self):
        identifier = AgentIdentifier(
            id="image_discovery_agent",
            name="Image Discovery Agent",
            team=AgentTeam.REAL_DATA_TESTING,
            apqc_domain="3.3 Manage Product and Service Information",
            version="2.0.0",
            capabilities=["image_search", "visual_content", "media_curation"],
            status="active"
        )
        super().__init__(identifier)
        self.unsplash_key = os.getenv("UNSPLASH_API_KEY", "")

    async def enrich(self, keyword: str, context: Dict) -> Dict[str, Any]:
        """Find high-quality product images"""

        logger.info(f"📸 Searching images for: {keyword}")

        images = await self._search_images(keyword, context)

        return {
            "data": {
                "images": images,
                "primary_image": images[0] if images else None
            },
            "confidence": 0.8 if images else 0.3
        }

    async def _search_images(self, keyword: str, context: Dict) -> list:
        """Search for product images from multiple sources"""

        images = []

        # Try Unsplash
        if self.unsplash_key:
            try:
                url = "https://api.unsplash.com/search/photos"
                headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
                params = {"query": f"{keyword} product", "per_page": 3}

                response = requests.get(url, headers=headers, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    images.extend([photo['urls']['regular'] for photo in data.get('results', [])])
            except Exception as e:
                logger.warning(f"Unsplash search failed: {e}")

        # Fallback placeholder images
        if not images:
            keyword_slug = keyword.replace(' ', '-').lower()
            images = [
                f"https://source.unsplash.com/400x400/?{keyword_slug},product",
                f"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",
            ]

        logger.info(f"✅ Found {len(images)} images")
        return images


# ============================================================================
# Initialize and register all A2A-enabled agents
# ============================================================================

# Global agent instances
product_intelligence_agent_a2a = ProductIntelligenceAgentA2A()
market_analysis_agent_a2a = MarketAnalysisAgentA2A()
competitive_intelligence_agent_a2a = CompetitiveIntelligenceAgentA2A()
pricing_strategy_agent_a2a = PricingStrategyAgentA2A()
customer_profiling_agent_a2a = CustomerProfilingAgentA2A()
business_model_agent_a2a = BusinessModelAgentA2A()
image_discovery_agent_a2a = ImageDiscoveryAgentA2A()

logger.info("🚀 All A2A-enabled enrichment agents initialized and registered")
