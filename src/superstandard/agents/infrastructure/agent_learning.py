# Agent Learning API Endpoints
# Provides visibility into agent learning and knowledge

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.auth import get_current_user, require_subscription
from app.agent_knowledge import get_knowledge_base
from app.agent_learning_integration import get_learning_ecosystem_stats, get_all_learning_agents

router = APIRouter()


@router.get("/knowledge/stats")
async def get_knowledge_base_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get statistics about the agent knowledge base

    Shows how much agents have learned over time
    """
    try:
        kb = get_knowledge_base()
        stats = kb.get_statistics()

        return {
            "knowledge_base_statistics": stats,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge stats: {str(e)}")


@router.get("/knowledge/search")
async def search_knowledge(
    category: Optional[str] = Query(None, description="Knowledge category"),
    tags: Optional[List[str]] = Query(None, description="Tags to filter by"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Search the agent knowledge base

    Allows exploring what agents have learned
    """
    try:
        kb = get_knowledge_base()

        knowledge_entries = kb.query(
            category=category, tags=tags, min_confidence=min_confidence, limit=limit
        )

        return {
            "results": [
                {
                    "knowledge_id": entry.knowledge_id,
                    "category": entry.category,
                    "content": entry.content,
                    "source_agent": entry.source_agent,
                    "confidence": entry.confidence,
                    "success_rate": entry.success_rate,
                    "usage_count": entry.usage_count,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat(),
                    "last_used": entry.last_used.isoformat() if entry.last_used else None,
                }
                for entry in knowledge_entries
            ],
            "total_results": len(knowledge_entries),
            "filters_applied": {
                "category": category,
                "tags": tags,
                "min_confidence": min_confidence,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")


@router.get("/agents/learning-stats")
async def get_agent_learning_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get learning statistics for all agents

    Shows which agents are learning the most
    """
    try:
        ecosystem_stats = get_learning_ecosystem_stats()

        return {
            "ecosystem": ecosystem_stats,
            "top_learners": _identify_top_learners(ecosystem_stats),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent stats: {str(e)}")


@router.post("/knowledge/reinforce/{knowledge_id}")
async def reinforce_knowledge(
    knowledge_id: str,
    success: bool,
    feedback_notes: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Provide feedback to reinforce or correct agent knowledge

    Allows human-in-the-loop learning
    """
    try:
        kb = get_knowledge_base()

        kb.reinforce(
            knowledge_id=knowledge_id,
            success=success,
            context={
                "user_feedback": feedback_notes or "No notes",
                "user_id": current_user.get("user_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Get updated entry
        if knowledge_id in kb.knowledge:
            entry = kb.knowledge[knowledge_id]
            return {
                "status": "reinforced",
                "knowledge_id": knowledge_id,
                "new_confidence": entry.confidence,
                "new_success_rate": entry.success_rate,
                "usage_count": entry.usage_count,
            }
        else:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reinforce knowledge: {str(e)}")


@router.get("/knowledge/export")
async def export_knowledge_for_agent(
    agent_name: str = Query(..., description="Agent name to export for"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    subscription_check=Depends(require_subscription("pro")),
) -> Dict[str, Any]:
    """
    Export knowledge optimized for a specific agent

    Useful for agent deployment and transfer
    """
    try:
        kb = get_knowledge_base()
        exported_data = kb.export_for_agent(agent_name)

        return exported_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export knowledge: {str(e)}")


@router.get("/teaching/sessions")
async def get_teaching_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get history of agent teaching sessions

    Shows knowledge transfer between agents
    """
    try:
        learning_agents = get_all_learning_agents()

        teaching_history = []
        for agent_name, wrapper in learning_agents.items():
            teacher_stats = wrapper.teacher.get_teaching_stats()
            teaching_history.append(
                {
                    "teacher_agent": agent_name,
                    "students_taught": teacher_stats["students_taught"],
                    "teaching_sessions": teacher_stats["teaching_sessions"],
                    "strategy": teacher_stats["teaching_strategy"],
                }
            )

        return {
            "teaching_sessions": teaching_history,
            "total_sessions": sum(t["teaching_sessions"] for t in teaching_history),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get teaching sessions: {str(e)}")


@router.get("/knowledge/categories")
async def get_knowledge_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available knowledge categories and their counts

    Useful for understanding the knowledge distribution
    """
    try:
        kb = get_knowledge_base()
        stats = kb.get_statistics()

        return {
            "categories": stats["category_distribution"],
            "total_categories": stats["categories"],
            "total_knowledge": stats["total_knowledge_entries"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


def _identify_top_learners(ecosystem_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify the agents that have learned the most"""
    agents = ecosystem_stats.get("agents", {})

    agent_scores = []
    for agent_name, stats in agents.items():
        learning_stats = stats.get("learning_stats", {})
        total_knowledge = learning_stats.get("total_knowledge_created", 0)
        sessions = learning_stats.get("learning_sessions", 0)

        agent_scores.append(
            {
                "agent_name": agent_name,
                "total_knowledge_created": total_knowledge,
                "learning_sessions": sessions,
                "learning_score": total_knowledge * 2 + sessions,
            }
        )

    # Sort by learning score
    agent_scores.sort(key=lambda x: x["learning_score"], reverse=True)

    return agent_scores[:10]  # Top 10
