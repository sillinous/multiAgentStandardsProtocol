"""
Agent Intelligence API Router

Exposes enhanced agent capabilities:
- Learning system metrics and insights
- Tool discovery and recommendations
- Collaborative problem solving status
- Agent performance analytics
- Knowledge graph exploration

Version: 1.0.0
Date: 2025-10-18
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add autonomous-ecosystem to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "autonomous-ecosystem"))

from library.core.agent_learning_system import get_learning_system, ExperienceType
from library.core.tool_discovery_system import get_discovery_system, ToolSource
from library.core.collaborative_problem_solving import (
    get_collaborative_problem_solving,
    ProblemCategory, ProblemSeverity
)

router = APIRouter(
    prefix="/api/v1/agent-intelligence",
    tags=["agent-intelligence"]
)


# ============================================================================
# LEARNING SYSTEM ENDPOINTS
# ============================================================================

@router.get("/learning/statistics")
async def get_learning_statistics():
    """Get overall learning system statistics"""
    try:
        learning_system = get_learning_system()
        stats = learning_system.get_statistics()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/experiences/{agent_id}")
async def get_agent_experiences(
    agent_id: str,
    experience_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Get recent experiences for an agent"""
    try:
        learning_system = get_learning_system()

        # Query database directly for experiences
        cursor = learning_system.conn.cursor()

        query = """
            SELECT experience_id, agent_id, agent_type, experience_type,
                   timestamp, reward, confidence
            FROM experiences
            WHERE agent_id = ?
        """
        params = [agent_id]

        if experience_type:
            query += " AND experience_type = ?"
            params.append(experience_type)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        experiences = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "experiences": experiences,
                "count": len(experiences)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/knowledge-graph")
async def get_knowledge_graph(
    knowledge_type: Optional[str] = None,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get knowledge graph nodes"""
    try:
        learning_system = get_learning_system()
        cursor = learning_system.conn.cursor()

        query = """
            SELECT node_id, knowledge_type, confidence, validation_score,
                   usage_count, created_at, updated_at, source_agents_json, tags_json
            FROM knowledge_graph
            WHERE confidence >= ?
        """
        params = [min_confidence]

        if knowledge_type:
            query += " AND knowledge_type = ?"
            params.append(knowledge_type)

        query += " ORDER BY confidence DESC, usage_count DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        nodes = []

        for row in cursor.fetchall():
            import json
            nodes.append({
                "node_id": row["node_id"],
                "knowledge_type": row["knowledge_type"],
                "confidence": row["confidence"],
                "validation_score": row["validation_score"],
                "usage_count": row["usage_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "source_agents": json.loads(row["source_agents_json"]),
                "tags": json.loads(row["tags_json"]) if row["tags_json"] else []
            })

        return {
            "success": True,
            "data": {
                "nodes": nodes,
                "count": len(nodes)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/performance-trend/{agent_id}")
async def get_performance_trend(
    agent_id: str,
    metric_name: str,
    days: int = Query(7, ge=1, le=90)
):
    """Get performance trend for an agent"""
    try:
        learning_system = get_learning_system()
        trend = learning_system.get_agent_performance_trend(
            agent_id=agent_id,
            metric_name=metric_name,
            days=days
        )

        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "metric_name": metric_name,
                "trend": trend
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/recommendations/{agent_id}")
async def get_agent_recommendations(
    agent_id: str,
    context: Optional[Dict[str, Any]] = None,
    top_k: int = Query(5, ge=1, le=20)
):
    """Get action recommendations for agent based on learned experiences"""
    try:
        learning_system = get_learning_system()
        recommendations = learning_system.get_recommendations(
            agent_id=agent_id,
            current_context=context or {},
            top_k=top_k
        )

        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "recommendations": recommendations,
                "count": len(recommendations)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/patterns")
async def get_learned_patterns(
    agent_id: Optional[str] = None,
    min_support: int = Query(3, ge=1, le=100),
    limit: int = Query(50, ge=1, le=200)
):
    """Get learned patterns"""
    try:
        learning_system = get_learning_system()
        cursor = learning_system.conn.cursor()

        query = """
            SELECT pattern_id, pattern_type, confidence, support_count,
                   discovered_by, created_at, last_validated
            FROM learned_patterns
            WHERE support_count >= ?
        """
        params = [min_support]

        if agent_id:
            query += " AND discovered_by = ?"
            params.append(agent_id)

        query += " ORDER BY confidence DESC, support_count DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        patterns = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "patterns": patterns,
                "count": len(patterns)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TOOL DISCOVERY ENDPOINTS
# ============================================================================

@router.get("/tools/statistics")
async def get_tool_statistics():
    """Get tool discovery system statistics"""
    try:
        discovery = get_discovery_system()
        stats = discovery.get_statistics()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/available")
async def get_available_tools(
    category: Optional[str] = None,
    source: Optional[str] = None,
    min_success_rate: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get available tools"""
    try:
        discovery = get_discovery_system()
        cursor = discovery.conn.cursor()

        query = """
            SELECT tool_id, name, description, category, source,
                   capabilities_json, execution_cost, reliability_score,
                   usage_count, success_rate, discovered_at, last_used
            FROM tools
            WHERE success_rate >= ? OR success_rate = 0
        """
        params = [min_success_rate]

        if category:
            query += " AND category = ?"
            params.append(category)

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY success_rate DESC, usage_count DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        import json
        tools = []
        for row in cursor.fetchall():
            tools.append({
                "tool_id": row["tool_id"],
                "name": row["name"],
                "description": row["description"],
                "category": row["category"],
                "source": row["source"],
                "capabilities": json.loads(row["capabilities_json"]),
                "execution_cost": row["execution_cost"],
                "reliability_score": row["reliability_score"],
                "usage_count": row["usage_count"],
                "success_rate": row["success_rate"],
                "discovered_at": row["discovered_at"],
                "last_used": row["last_used"]
            })

        return {
            "success": True,
            "data": {
                "tools": tools,
                "count": len(tools)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/recommendations")
async def get_tool_recommendations(
    task_description: str,
    context: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None,
    top_k: int = Query(5, ge=1, le=20)
):
    """Get tool recommendations for a task"""
    try:
        discovery = get_discovery_system()
        recommendations = discovery.recommend_tools(
            task_description=task_description,
            context=context or {},
            agent_id=agent_id,
            top_k=top_k
        )

        return {
            "success": True,
            "data": {
                "task_description": task_description,
                "recommendations": recommendations,
                "count": len(recommendations)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/capabilities/{agent_id}")
async def get_agent_capabilities(agent_id: str):
    """Get capabilities for an agent"""
    try:
        discovery = get_discovery_system()
        capabilities = discovery.get_agent_capabilities(agent_id)

        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "capabilities": capabilities,
                "count": len(capabilities)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/usage-analytics")
async def get_tool_usage_analytics(
    tool_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500)
):
    """Get tool usage analytics"""
    try:
        discovery = get_discovery_system()
        cursor = discovery.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT tool_id, agent_id, used_at, execution_time_ms,
                   success, error_message
            FROM tool_usage_log
            WHERE used_at >= ?
        """
        params = [cutoff_date]

        if tool_id:
            query += " AND tool_id = ?"
            params.append(tool_id)

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        query += " ORDER BY used_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        usage_logs = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "usage_logs": usage_logs,
                "count": len(usage_logs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROBLEM SOLVING ENDPOINTS
# ============================================================================

@router.get("/problems/statistics")
async def get_problem_statistics():
    """Get problem solving system statistics"""
    try:
        cps = get_collaborative_problem_solving()
        stats = cps.get_statistics()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/active")
async def get_active_problems(
    category: Optional[str] = None,
    min_severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get active problems"""
    try:
        cps = get_collaborative_problem_solving()

        category_enum = ProblemCategory[category.upper()] if category else None
        severity_enum = ProblemSeverity[min_severity.upper()] if min_severity else None

        problems = cps.get_active_problems(
            category=category_enum,
            min_severity=severity_enum
        )

        return {
            "success": True,
            "data": {
                "problems": problems[:limit],
                "count": len(problems)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/{problem_id}")
async def get_problem_details(problem_id: str):
    """Get details for a specific problem"""
    try:
        cps = get_collaborative_problem_solving()
        cursor = cps.conn.cursor()

        cursor.execute("SELECT * FROM problems WHERE problem_id = ?", (problem_id,))
        problem = cursor.fetchone()

        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        import json
        problem_data = dict(problem)
        problem_data['context'] = json.loads(problem_data['context_json'])
        problem_data['affected_agents'] = json.loads(problem_data['affected_agents_json'])
        problem_data['symptoms'] = json.loads(problem_data['symptoms_json'])
        problem_data['potential_causes'] = json.loads(problem_data['potential_causes_json'] or '[]')
        problem_data['required_capabilities'] = json.loads(problem_data['required_capabilities_json'] or '[]')

        # Get solutions for this problem
        cursor.execute("""
            SELECT solution_id, proposed_by, strategy, description,
                   estimated_success_rate, status, proposed_at
            FROM solutions
            WHERE problem_id = ?
            ORDER BY estimated_success_rate DESC
        """, (problem_id,))

        solutions = [dict(row) for row in cursor.fetchall()]
        problem_data['solutions'] = solutions

        return {
            "success": True,
            "data": problem_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/sessions/active")
async def get_active_collaboration_sessions(
    limit: int = Query(50, ge=1, le=200)
):
    """Get active collaboration sessions"""
    try:
        cps = get_collaborative_problem_solving()
        cursor = cps.conn.cursor()

        cursor.execute("""
            SELECT session_id, problem_id, coordinator_id, strategy,
                   started_at, status, consensus_reached, participants_json
            FROM collaboration_sessions
            WHERE status = 'active'
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        import json
        sessions = []
        for row in cursor.fetchall():
            session = dict(row)
            session['participants'] = json.loads(session['participants_json'])
            sessions.append(session)

        return {
            "success": True,
            "data": {
                "sessions": sessions,
                "count": len(sessions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/agent-expertise")
async def get_agent_expertise(
    agent_id: Optional[str] = None,
    problem_category: Optional[str] = None
):
    """Get agent expertise scores"""
    try:
        cps = get_collaborative_problem_solving()
        cursor = cps.conn.cursor()

        query = """
            SELECT agent_id, problem_category, solution_strategy,
                   success_count, total_attempts, expertise_score, last_updated
            FROM agent_expertise
            WHERE 1=1
        """
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if problem_category:
            query += " AND problem_category = ?"
            params.append(problem_category)

        query += " ORDER BY expertise_score DESC"

        cursor.execute(query, params)
        expertise = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "expertise": expertise,
                "count": len(expertise)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMBINED ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive overview for dashboard"""
    try:
        learning_system = get_learning_system()
        discovery = get_discovery_system()
        cps = get_collaborative_problem_solving()

        learning_stats = learning_system.get_statistics()
        tool_stats = discovery.get_statistics()
        problem_stats = cps.get_statistics()

        # Get recent activity
        cursor = learning_system.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM experiences
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        recent_experiences = cursor.fetchone()['count']

        cursor = cps.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM problems
            WHERE detected_at >= datetime('now', '-24 hours')
        """)
        recent_problems = cursor.fetchone()['count']

        return {
            "success": True,
            "data": {
                "learning": {
                    **learning_stats,
                    "recent_24h": recent_experiences
                },
                "tools": tool_stats,
                "problems": {
                    **problem_stats,
                    "recent_24h": recent_problems
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/agent/{agent_id}/insights")
async def get_agent_insights(agent_id: str):
    """Get comprehensive insights for a specific agent"""
    try:
        learning_system = get_learning_system()
        discovery = get_discovery_system()

        # Get learning metrics
        cursor = learning_system.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN experience_type = 'success' THEN 1 ELSE 0 END) as successes,
                   AVG(reward) as avg_reward
            FROM experiences
            WHERE agent_id = ?
        """, (agent_id,))
        learning_metrics = dict(cursor.fetchone())

        # Get capabilities
        capabilities = discovery.get_agent_capabilities(agent_id)

        # Get expertise
        cps = get_collaborative_problem_solving()
        cursor = cps.conn.cursor()
        cursor.execute("""
            SELECT problem_category, expertise_score
            FROM agent_expertise
            WHERE agent_id = ?
            ORDER BY expertise_score DESC
        """, (agent_id,))
        expertise = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "learning_metrics": learning_metrics,
                "capabilities": capabilities,
                "expertise": expertise,
                "total_capabilities": len(capabilities),
                "expertise_areas": len(expertise)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
