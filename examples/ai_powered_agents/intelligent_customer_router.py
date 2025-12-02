"""
Intelligent Customer Service Router - Example Implementation

Demonstrates AI-powered customer service capabilities:
- Intelligent ticket classification
- Sentiment analysis and priority escalation
- Smart agent matching
- Response suggestion generation
- Customer journey tracking
- SLA monitoring and prediction

APQC Process: 5.0 - Manage Customer Service
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Sentiment(Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    HAPPY = "happy"


@dataclass
class CustomerRouterConfig:
    """Configuration for Customer Service Router"""
    agent_id: str = "intelligent_customer_router_001"
    agent_name: str = "Intelligent Customer Router"

    # AI Configuration
    ai_provider: str = "auto"
    enable_sentiment_analysis: bool = True
    enable_auto_response: bool = True

    # Routing Parameters
    max_queue_size: int = 100
    priority_escalation_threshold: float = 0.8
    sentiment_escalation_threshold: str = "frustrated"

    # SLA Configuration (in minutes)
    sla_critical: int = 15
    sla_high: int = 60
    sla_medium: int = 240
    sla_low: int = 1440


class IntelligentCustomerRouter:
    """
    AI-Powered Customer Service Routing Agent

    Capabilities:
    - Multi-channel ticket intake (email, chat, phone, social)
    - AI-powered classification and prioritization
    - Sentiment analysis with escalation triggers
    - Intelligent agent matching based on skills/availability
    - Response suggestion generation
    - SLA monitoring and breach prediction

    Integration:
    - Uses CustomerServiceProcessor from smart_processing
    - APQC Process: 5.0 - Manage Customer Service
    """

    APQC_CATEGORY_ID = "5.0"
    APQC_PROCESS_ID = "5.1"

    # Category definitions
    CATEGORIES = {
        "billing": ["invoice", "payment", "charge", "refund", "subscription", "pricing"],
        "technical": ["bug", "error", "crash", "not working", "broken", "issue", "problem"],
        "account": ["password", "login", "access", "account", "profile", "settings"],
        "shipping": ["delivery", "shipping", "tracking", "order", "package", "return"],
        "general": ["question", "information", "help", "how to", "inquiry"]
    }

    def __init__(self, config: Optional[CustomerRouterConfig] = None):
        self.config = config or CustomerRouterConfig()
        self.ticket_queue = []
        self.agent_pool = {}
        self.state = {
            "tickets_processed": 0,
            "escalations": 0,
            "auto_resolved": 0,
            "average_response_time_seconds": 0,
            "sla_breaches": 0,
            "last_activity": None
        }

    async def process_ticket(
        self,
        ticket: Dict[str, Any],
        available_agents: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming customer ticket with AI-powered routing

        Args:
            ticket: Customer ticket containing:
                - id: Unique identifier
                - channel: Origin channel (email, chat, phone, social)
                - subject: Ticket subject
                - content: Full ticket content
                - customer_id: Customer identifier
                - metadata: Additional context
            available_agents: List of available support agents

        Returns:
            Routing decision with classification and suggested responses
        """
        from superstandard.services.smart_processing import get_processor
        from superstandard.services.ai_service import get_ai_service

        start_time = datetime.now()

        processor = get_processor("customer_service")
        ai_service = get_ai_service()

        # Step 1: Classify ticket
        classification = await self._classify_ticket(ticket, processor, ai_service)

        # Step 2: Analyze sentiment
        sentiment_result = None
        if self.config.enable_sentiment_analysis:
            sentiment_result = await self._analyze_sentiment(ticket, ai_service)

        # Step 3: Determine priority
        priority = await self._determine_priority(
            ticket,
            classification,
            sentiment_result,
            ai_service
        )

        # Step 4: Check for auto-resolution
        auto_resolution = None
        if self.config.enable_auto_response:
            auto_resolution = await self._check_auto_resolution(
                ticket,
                classification,
                ai_service
            )

        # Step 5: Route to agent (if not auto-resolved)
        routing_decision = None
        if not auto_resolution or not auto_resolution.get("can_auto_resolve"):
            routing_decision = await self._route_to_agent(
                ticket,
                classification,
                priority,
                available_agents or [],
                processor
            )

        # Step 6: Generate response suggestions
        response_suggestions = await self._generate_response_suggestions(
            ticket,
            classification,
            sentiment_result,
            ai_service
        )

        # Step 7: Calculate SLA
        sla_info = self._calculate_sla(priority)

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()

        # Update state
        self.state["tickets_processed"] += 1
        self.state["last_activity"] = datetime.now().isoformat()
        if priority.value in ["critical", "high"]:
            self.state["escalations"] += 1
        if auto_resolution and auto_resolution.get("can_auto_resolve"):
            self.state["auto_resolved"] += 1

        return {
            "status": "processed",
            "timestamp": datetime.now().isoformat(),
            "ai_powered": True,
            "apqc_process": self.APQC_PROCESS_ID,
            "ticket_id": ticket.get("id", "unknown"),
            "classification": classification,
            "sentiment": sentiment_result,
            "priority": {
                "level": priority.value,
                "escalation_triggered": priority in [Priority.CRITICAL, Priority.HIGH]
            },
            "routing": routing_decision,
            "auto_resolution": auto_resolution,
            "response_suggestions": response_suggestions,
            "sla": sla_info,
            "metrics": {
                "processing_time_seconds": processing_time,
                "confidence_score": classification.get("confidence", 0.8)
            }
        }

    async def _classify_ticket(
        self,
        ticket: Dict[str, Any],
        processor,
        ai_service
    ) -> Dict[str, Any]:
        """Classify ticket using AI analysis"""
        content = f"{ticket.get('subject', '')} {ticket.get('content', '')}"

        # Quick keyword-based pre-classification
        preliminary_category = "general"
        for category, keywords in self.CATEGORIES.items():
            if any(kw.lower() in content.lower() for kw in keywords):
                preliminary_category = category
                break

        # AI-powered deep classification
        classification = await ai_service.analyze(
            prompt=f"""Classify this customer service ticket:
            Channel: {ticket.get('channel', 'unknown')}
            Subject: {ticket.get('subject', '')}
            Content: {ticket.get('content', '')[:1000]}

            Determine:
            1. Primary category (billing, technical, account, shipping, general)
            2. Subcategory (more specific classification)
            3. Issue type (question, complaint, request, feedback)
            4. Product/service mentioned (if any)
            5. Urgency indicators

            Preliminary guess: {preliminary_category}
            """,
            data={"ticket": ticket}
        )

        return {
            "primary_category": classification.get("category", preliminary_category),
            "subcategory": classification.get("subcategory", "general_inquiry"),
            "issue_type": classification.get("issue_type", "question"),
            "product_service": classification.get("product_service"),
            "urgency_indicators": classification.get("urgency_indicators", []),
            "confidence": classification.get("confidence", 0.75),
            "tags": classification.get("suggested_tags", [])
        }

    async def _analyze_sentiment(
        self,
        ticket: Dict[str, Any],
        ai_service
    ) -> Dict[str, Any]:
        """Analyze customer sentiment"""
        content = ticket.get("content", "")

        sentiment_analysis = await ai_service.analyze(
            prompt=f"""Analyze the sentiment of this customer message:
            "{content[:500]}"

            Determine:
            1. Overall sentiment (angry, frustrated, neutral, satisfied, happy)
            2. Sentiment score (-1 to 1)
            3. Emotional indicators
            4. Escalation risk (low, medium, high)
            5. Churn risk (if applicable)
            """,
            data={"content": content}
        )

        sentiment_label = sentiment_analysis.get("sentiment", "neutral")
        try:
            sentiment = Sentiment(sentiment_label)
        except ValueError:
            sentiment = Sentiment.NEUTRAL

        return {
            "sentiment": sentiment.value,
            "score": sentiment_analysis.get("score", 0.0),
            "emotional_indicators": sentiment_analysis.get("emotional_indicators", []),
            "escalation_risk": sentiment_analysis.get("escalation_risk", "medium"),
            "churn_risk": sentiment_analysis.get("churn_risk", "low"),
            "requires_empathy": sentiment in [Sentiment.ANGRY, Sentiment.FRUSTRATED]
        }

    async def _determine_priority(
        self,
        ticket: Dict[str, Any],
        classification: Dict,
        sentiment: Optional[Dict],
        ai_service
    ) -> Priority:
        """Determine ticket priority based on multiple factors"""
        # Base priority from classification
        urgency_indicators = classification.get("urgency_indicators", [])
        base_priority = Priority.MEDIUM

        # Check explicit urgency keywords
        content = f"{ticket.get('subject', '')} {ticket.get('content', '')}".lower()
        if any(word in content for word in ["urgent", "emergency", "asap", "immediately", "critical"]):
            base_priority = Priority.HIGH

        # Check sentiment escalation
        if sentiment:
            if sentiment.get("sentiment") in ["angry"]:
                base_priority = Priority.HIGH
            elif sentiment.get("sentiment") == "frustrated" and base_priority == Priority.MEDIUM:
                base_priority = Priority.HIGH
            if sentiment.get("escalation_risk") == "high":
                base_priority = Priority.CRITICAL

        # Check customer tier (VIP escalation)
        customer_tier = ticket.get("metadata", {}).get("customer_tier", "standard")
        if customer_tier in ["enterprise", "vip", "platinum"]:
            if base_priority == Priority.MEDIUM:
                base_priority = Priority.HIGH
            elif base_priority == Priority.HIGH:
                base_priority = Priority.CRITICAL

        # Check business impact
        if classification.get("issue_type") == "complaint" and classification.get("primary_category") == "billing":
            if base_priority == Priority.MEDIUM:
                base_priority = Priority.HIGH

        return base_priority

    async def _check_auto_resolution(
        self,
        ticket: Dict[str, Any],
        classification: Dict,
        ai_service
    ) -> Dict[str, Any]:
        """Check if ticket can be auto-resolved"""
        # Simple questions often can be auto-resolved
        if classification.get("issue_type") != "question":
            return {"can_auto_resolve": False, "reason": "Not a question"}

        # Check against knowledge base (simulated)
        kb_result = await ai_service.analyze(
            prompt=f"""Check if this question can be answered from standard FAQ/knowledge base:
            Category: {classification.get('primary_category')}
            Question: {ticket.get('content', '')[:500]}

            Determine:
            1. Can be auto-resolved (yes/no)
            2. Confidence level
            3. Suggested answer (if auto-resolvable)
            4. Knowledge base article reference (if applicable)
            """,
            data={"ticket": ticket, "classification": classification}
        )

        can_resolve = kb_result.get("can_auto_resolve", False)
        confidence = kb_result.get("confidence", 0.0)

        # Only auto-resolve if confidence is high enough
        if can_resolve and confidence >= 0.85:
            return {
                "can_auto_resolve": True,
                "confidence": confidence,
                "suggested_response": kb_result.get("suggested_answer", ""),
                "kb_article": kb_result.get("kb_article_id"),
                "requires_review": confidence < 0.95
            }

        return {
            "can_auto_resolve": False,
            "reason": kb_result.get("reason", "Requires human review"),
            "confidence": confidence
        }

    async def _route_to_agent(
        self,
        ticket: Dict[str, Any],
        classification: Dict,
        priority: Priority,
        available_agents: List[Dict],
        processor
    ) -> Dict[str, Any]:
        """Route ticket to best available agent"""
        if not available_agents:
            return {
                "assigned": False,
                "reason": "No agents available",
                "queue_position": len(self.ticket_queue) + 1
            }

        # Match agent skills to ticket category
        category = classification.get("primary_category", "general")
        subcategory = classification.get("subcategory", "")

        # Score agents
        scored_agents = []
        for agent in available_agents:
            score = 0
            agent_skills = agent.get("skills", [])

            # Skill match
            if category in agent_skills:
                score += 3
            if subcategory in agent_skills:
                score += 2

            # Availability
            if agent.get("status") == "available":
                score += 2
            elif agent.get("status") == "busy":
                score -= 1

            # Current load
            current_tickets = agent.get("current_tickets", 0)
            max_tickets = agent.get("max_tickets", 5)
            load_factor = 1 - (current_tickets / max_tickets)
            score += load_factor * 2

            # Language match
            ticket_lang = ticket.get("metadata", {}).get("language", "en")
            if ticket_lang in agent.get("languages", ["en"]):
                score += 1

            scored_agents.append({
                "agent_id": agent.get("id"),
                "agent_name": agent.get("name"),
                "score": score,
                "estimated_wait_minutes": current_tickets * 10
            })

        # Sort by score
        scored_agents.sort(key=lambda x: x["score"], reverse=True)

        if scored_agents and scored_agents[0]["score"] > 0:
            best_agent = scored_agents[0]
            return {
                "assigned": True,
                "agent_id": best_agent["agent_id"],
                "agent_name": best_agent["agent_name"],
                "match_score": best_agent["score"],
                "estimated_wait_minutes": best_agent["estimated_wait_minutes"],
                "routing_reason": f"Best skill match for {category}"
            }

        return {
            "assigned": False,
            "reason": "No suitable agent found",
            "queue_position": len(self.ticket_queue) + 1,
            "alternative_agents": scored_agents[:3]
        }

    async def _generate_response_suggestions(
        self,
        ticket: Dict[str, Any],
        classification: Dict,
        sentiment: Optional[Dict],
        ai_service
    ) -> List[Dict[str, Any]]:
        """Generate response suggestions for the agent"""
        requires_empathy = sentiment and sentiment.get("requires_empathy", False)

        suggestion_result = await ai_service.generate_recommendations(
            context={
                "ticket_content": ticket.get("content", "")[:500],
                "category": classification.get("primary_category"),
                "issue_type": classification.get("issue_type"),
                "sentiment": sentiment.get("sentiment") if sentiment else "neutral",
                "requires_empathy": requires_empathy
            },
            constraints=[
                "Generate 2-3 response templates",
                "Match tone to customer sentiment",
                "Include empathy statements if needed",
                "Provide resolution steps",
                "Keep responses concise"
            ]
        )

        suggestions = []
        for rec in suggestion_result[:3]:
            suggestions.append({
                "type": "response_template",
                "content": rec.get("recommendation", rec.get("action", "")),
                "tone": "empathetic" if requires_empathy else "professional",
                "includes_resolution": True,
                "personalization_needed": ["customer_name", "order_number"]
            })

        return suggestions

    def _calculate_sla(self, priority: Priority) -> Dict[str, Any]:
        """Calculate SLA based on priority"""
        sla_minutes = {
            Priority.CRITICAL: self.config.sla_critical,
            Priority.HIGH: self.config.sla_high,
            Priority.MEDIUM: self.config.sla_medium,
            Priority.LOW: self.config.sla_low
        }

        minutes = sla_minutes.get(priority, self.config.sla_medium)
        deadline = datetime.now() + timedelta(minutes=minutes)

        return {
            "target_minutes": minutes,
            "deadline": deadline.isoformat(),
            "priority_level": priority.value,
            "breach_warning_at": (deadline - timedelta(minutes=minutes * 0.2)).isoformat()
        }

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and metrics"""
        return {
            "queue_size": len(self.ticket_queue),
            "metrics": self.state,
            "timestamp": datetime.now().isoformat()
        }


async def demo():
    """Demonstrate the Intelligent Customer Router"""
    print("=" * 60)
    print("Intelligent Customer Router - Demo")
    print("=" * 60)

    router = IntelligentCustomerRouter()

    # Sample ticket
    ticket = {
        "id": "TKT-2024-001",
        "channel": "email",
        "subject": "Urgent: Cannot access my account after password reset",
        "content": """
        I've been trying to login for the past 2 hours and nothing works!
        I reset my password but now I can't get in at all.
        This is extremely frustrating as I have an important deadline.
        I need this fixed IMMEDIATELY or I will have to cancel my subscription.
        Customer ID: CUST-12345
        """,
        "customer_id": "CUST-12345",
        "metadata": {
            "customer_tier": "enterprise",
            "language": "en",
            "previous_tickets": 2
        }
    }

    # Sample available agents
    agents = [
        {
            "id": "agent-001",
            "name": "Sarah",
            "skills": ["account", "technical", "billing"],
            "languages": ["en", "es"],
            "status": "available",
            "current_tickets": 2,
            "max_tickets": 5
        },
        {
            "id": "agent-002",
            "name": "Mike",
            "skills": ["shipping", "general"],
            "languages": ["en"],
            "status": "busy",
            "current_tickets": 4,
            "max_tickets": 5
        },
        {
            "id": "agent-003",
            "name": "Lisa",
            "skills": ["account", "billing"],
            "languages": ["en", "fr"],
            "status": "available",
            "current_tickets": 1,
            "max_tickets": 5
        }
    ]

    print(f"\nProcessing ticket: {ticket['id']}")
    print(f"Subject: {ticket['subject']}")
    print(f"Channel: {ticket['channel']}")

    try:
        result = await router.process_ticket(ticket, agents)

        print("\n" + "-" * 40)
        print("Routing Results:")
        print("-" * 40)
        print(f"Status: {result['status']}")
        print(f"Processing Time: {result['metrics']['processing_time_seconds']:.2f}s")

        print(f"\nClassification:")
        print(f"  Category: {result['classification']['primary_category']}")
        print(f"  Issue Type: {result['classification']['issue_type']}")
        print(f"  Confidence: {result['classification']['confidence']:.2%}")

        if result.get("sentiment"):
            print(f"\nSentiment:")
            print(f"  Level: {result['sentiment']['sentiment']}")
            print(f"  Escalation Risk: {result['sentiment']['escalation_risk']}")

        print(f"\nPriority: {result['priority']['level'].upper()}")
        if result['priority']['escalation_triggered']:
            print("  ** ESCALATION TRIGGERED **")

        if result.get("routing", {}).get("assigned"):
            print(f"\nRouted to: {result['routing']['agent_name']}")
            print(f"  Match Score: {result['routing']['match_score']}")
            print(f"  Est. Wait: {result['routing']['estimated_wait_minutes']} min")

        print(f"\nSLA: {result['sla']['target_minutes']} minutes")
        print(f"  Deadline: {result['sla']['deadline']}")

        print(f"\nResponse Suggestions: {len(result.get('response_suggestions', []))}")

    except ImportError as e:
        print(f"\nNote: Run from project root with proper imports. Error: {e}")


if __name__ == "__main__":
    asyncio.run(demo())
