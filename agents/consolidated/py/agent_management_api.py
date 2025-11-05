#!/usr/bin/env python3
"""
🌙 Agent Management System - REST API Endpoints

Provides comprehensive agent management APIs including:
- Agent discovery and metadata
- Shared memory/context management
- Learning system for agent evolution
- Real-time output monitoring
- Inter-agent communication

This enables agents to:
1. Function independently and autonomously
2. Share learnings through shared memory
3. Make decisions based on environment feedback
4. Evolve and improve their behavior over time
5. Learn from each other's experiences
"""

from flask import Blueprint, jsonify, request
from src.orchestration.agent_manager import (
    memory_manager, learning_manager, output_manager,
    AgentStatus, AgentMemory, AgentLearning
)
from pathlib import Path
import json
from datetime import datetime
import os

# Create blueprint
agent_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

# Define ACTIVE_AGENTS - Agent registry with metadata
ACTIVE_AGENTS = {
    # Trading Execution (4)
    'trading_agent': {
        'category': 'Trading Execution',
        'description': 'Primary trading agent for executing trades based on signals',
        'enabled': True,
        'interval_minutes': 15,
        'inputs': ['market_data', 'signals'],
        'outputs': ['trade_signals', 'execution_results'],
        'dependencies': ['risk_agent', 'sentiment_agent']
    },
    'risk_agent': {
        'category': 'Risk Management',
        'description': 'Manages risk parameters and position sizing',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['portfolio_state', 'market_conditions'],
        'outputs': ['risk_limits', 'position_sizing'],
        'dependencies': []
    },
    'strategy_agent': {
        'category': 'Strategy Development',
        'description': 'Develops and tests trading strategies',
        'enabled': True,
        'interval_minutes': 60,
        'inputs': ['historical_data', 'market_analysis'],
        'outputs': ['strategy_recommendations'],
        'dependencies': ['research_agent']
    },
    'copybot_agent': {
        'category': 'Trading Execution',
        'description': 'Copy trading agent - follows whale wallets',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['whale_transactions'],
        'outputs': ['copy_trades'],
        'dependencies': ['whale_agent', 'risk_agent']
    },

    # Market Analysis (6)
    'sentiment_agent': {
        'category': 'Market Analysis',
        'description': 'Analyzes market sentiment from social media',
        'enabled': True,
        'interval_minutes': 30,
        'inputs': ['social_media_data'],
        'outputs': ['sentiment_scores'],
        'dependencies': []
    },
    'whale_agent': {
        'category': 'Market Analysis',
        'description': 'Monitors whale wallet transactions',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['blockchain_data'],
        'outputs': ['whale_transactions'],
        'dependencies': []
    },
    'funding_agent': {
        'category': 'Market Analysis',
        'description': 'Analyzes funding rates and opportunities',
        'enabled': True,
        'interval_minutes': 15,
        'inputs': ['funding_rate_data'],
        'outputs': ['funding_opportunities'],
        'dependencies': []
    },
    'liquidation_agent': {
        'category': 'Market Analysis',
        'description': 'Monitors liquidation levels and opportunities',
        'enabled': True,
        'interval_minutes': 10,
        'inputs': ['leverage_data'],
        'outputs': ['liquidation_levels'],
        'dependencies': []
    },
    'chartanalysis_agent': {
        'category': 'Market Analysis',
        'description': 'Technical analysis of price charts',
        'enabled': True,
        'interval_minutes': 30,
        'inputs': ['ohlcv_data'],
        'outputs': ['technical_signals'],
        'dependencies': []
    },
    'solana_agent': {
        'category': 'Market Analysis',
        'description': 'Solana-specific market analysis',
        'enabled': True,
        'interval_minutes': 15,
        'inputs': ['solana_data'],
        'outputs': ['solana_signals'],
        'dependencies': []
    },

    # Strategy Development (3)
    'rbi_agent': {
        'category': 'Strategy Development',
        'description': 'Research-based inference - generates strategies from analysis',
        'enabled': True,
        'interval_minutes': 120,
        'inputs': ['research_data', 'video_analysis'],
        'outputs': ['strategy_backtests'],
        'dependencies': []
    },
    'research_agent': {
        'category': 'Strategy Development',
        'description': 'Researches and analyzes token fundamentals',
        'enabled': True,
        'interval_minutes': 60,
        'inputs': ['token_data', 'market_data'],
        'outputs': ['research_reports'],
        'dependencies': ['coingecko_agent']
    },
    'sniper_agent': {
        'category': 'Strategy Development',
        'description': 'Identifies and trades new token launches',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['new_tokens'],
        'outputs': ['sniper_trades'],
        'dependencies': ['risk_agent']
    },

    # Content Creation (5)
    'chat_agent': {
        'category': 'Content Creation',
        'description': 'AI chat interface for user interaction',
        'enabled': True,
        'interval_minutes': 0,
        'inputs': ['user_messages'],
        'outputs': ['responses'],
        'dependencies': []
    },
    'clips_agent': {
        'category': 'Content Creation',
        'description': 'Generates short-form video clips',
        'enabled': True,
        'interval_minutes': 60,
        'inputs': ['trading_results'],
        'outputs': ['video_clips'],
        'dependencies': []
    },
    'tweet_agent': {
        'category': 'Content Creation',
        'description': 'Generates and posts tweets',
        'enabled': True,
        'interval_minutes': 30,
        'inputs': ['market_events', 'trading_results'],
        'outputs': ['tweets'],
        'dependencies': []
    },
    'video_agent': {
        'category': 'Content Creation',
        'description': 'Analyzes and creates videos',
        'enabled': True,
        'interval_minutes': 120,
        'inputs': ['video_data'],
        'outputs': ['video_analysis'],
        'dependencies': []
    },
    'phone_agent': {
        'category': 'Content Creation',
        'description': 'Handles voice/phone interactions',
        'enabled': False,
        'interval_minutes': 0,
        'inputs': ['voice_input'],
        'outputs': ['voice_response'],
        'dependencies': []
    },

    # Market Data & Analysis (3)
    'coingecko_agent': {
        'category': 'Market Data',
        'description': 'Fetches and analyzes CoinGecko data',
        'enabled': True,
        'interval_minutes': 60,
        'inputs': [],
        'outputs': ['token_data'],
        'dependencies': []
    },
    'housecoin_agent': {
        'category': 'Market Data',
        'description': 'Housecoin-specific analysis',
        'enabled': False,
        'interval_minutes': 30,
        'inputs': ['housecoin_data'],
        'outputs': ['housecoin_analysis'],
        'dependencies': []
    },
    'tx_agent': {
        'category': 'Market Data',
        'description': 'Transaction analysis and monitoring',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['blockchain_txs'],
        'outputs': ['tx_signals'],
        'dependencies': []
    },

    # Specialized Agents (3)
    'compliance_agent': {
        'category': 'Risk Management',
        'description': 'Ensures trading compliance and regulations',
        'enabled': True,
        'interval_minutes': 5,
        'inputs': ['trades', 'positions'],
        'outputs': ['compliance_checks'],
        'dependencies': []
    },
    'million_agent': {
        'category': 'Specialized',
        'description': 'Tracks million-token opportunities',
        'enabled': False,
        'interval_minutes': 30,
        'inputs': ['million_data'],
        'outputs': ['million_signals'],
        'dependencies': []
    },
    'tiktok_agent': {
        'category': 'Content Creation',
        'description': 'TikTok content generation and posting',
        'enabled': False,
        'interval_minutes': 60,
        'inputs': ['trading_events'],
        'outputs': ['tiktok_content'],
        'dependencies': []
    },
}


# ============================================================================
# AGENT DISCOVERY & METADATA
# ============================================================================

@agent_bp.route('', methods=['GET'])
def list_agents():
    """Get all available agents with optional filtering"""
    category_filter = request.args.get('category')

    # Build agent list from config
    agents = []

    for agent_name, config in ACTIVE_AGENTS.items():
        agent_info = {
            'name': agent_name,
            'category': config.get('category', 'unknown'),
            'description': config.get('description', ''),
            'enabled': config.get('enabled', True),
            'interval_minutes': config.get('interval_minutes', 15),
            'status': 'unknown'
        }

        # Get recent execution stats
        stats = output_manager.get_agent_stats(agent_name)
        agent_info['stats'] = {
            'total_executions': stats.get('total_executions', 0),
            'success_rate': stats.get('success_rate', 0),
            'avg_duration_seconds': stats.get('avg_duration_seconds', 0)
        }

        # Filter by category if requested
        if category_filter and agent_info['category'] != category_filter:
            continue

        agents.append(agent_info)

    return jsonify({
        'total': len(agents),
        'agents': agents
    }), 200


@agent_bp.route('/<agent_name>', methods=['GET'])
def get_agent_details(agent_name):
    """Get detailed information about a specific agent"""
    try:
        # Get agent config
        agent_config = ACTIVE_AGENTS.get(agent_name)
        if not agent_config:
            return jsonify({'error': f'Agent {agent_name} not found'}), 404

        # Get recent execution stats
        stats = output_manager.get_agent_stats(agent_name)

        # Get recent outputs
        outputs = output_manager.get_latest_outputs(agent_name, limit=5)

        # Get learnings
        learnings = learning_manager.get_learnings(agent_name)

        # Get high-confidence learnings applicable to this agent
        high_conf = learning_manager.get_high_confidence_learnings(min_confidence=0.8)
        applicable_learnings = [
            l.to_dict() for l in high_conf
            if agent_name in l.applicable_to or l.agent_name == agent_name
        ]

        agent_details = {
            'name': agent_name,
            'category': agent_config.get('category', 'unknown'),
            'description': agent_config.get('description', ''),
            'enabled': agent_config.get('enabled', True),
            'interval_minutes': agent_config.get('interval_minutes', 15),
            'requirements': {
                'inputs': agent_config.get('inputs', []),
                'outputs': agent_config.get('outputs', []),
                'dependencies': agent_config.get('dependencies', [])
            },
            'statistics': stats,
            'recent_executions': [o.to_dict() for o in outputs],
            'learnings': {
                'total': len(learnings),
                'high_confidence': applicable_learnings[:5]  # Already converted to dicts
            }
        }

        return jsonify(agent_details), 200
    except Exception as e:
        import traceback
        print(f"Error in get_agent_details: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'type': type(e).__name__}), 500


@agent_bp.route('/by-category/<category>', methods=['GET'])
def get_agents_by_category(category):
    """Get all agents in a specific category"""
    agents = [
        {
            'name': name,
            'category': config.get('category'),
            'description': config.get('description', ''),
            'enabled': config.get('enabled', True)
        }
        for name, config in ACTIVE_AGENTS.items()
        if config.get('category') == category
    ]

    return jsonify({
        'category': category,
        'total': len(agents),
        'agents': agents
    }), 200


@agent_bp.route('/categories', methods=['GET'])
def list_categories():
    """Get all available agent categories"""
    categories = set()
    for config in ACTIVE_AGENTS.values():
        cat = config.get('category', 'uncategorized')
        if cat:
            categories.add(cat)

    return jsonify({
        'total': len(categories),
        'categories': sorted(list(categories))
    }), 200


# ============================================================================
# SHARED MEMORY MANAGEMENT
# ============================================================================

@agent_bp.route('/memory', methods=['GET'])
def get_shared_memory():
    """Get shared memory entries accessible to agents"""
    agent_name = request.args.get('agent')
    category = request.args.get('category')
    limit = request.args.get('limit', 100, type=int)

    if agent_name:
        memories = memory_manager.get_memory(agent_name, category, limit)
    else:
        memories = memory_manager.memory[:limit]

    return jsonify({
        'total': len(memories),
        'memories': [m.to_dict() for m in memories]
    }), 200


@agent_bp.route('/memory', methods=['POST'])
def store_shared_memory():
    """Store a shared memory entry"""
    try:
        data = request.json
        if not all(k in data for k in ['agent_name', 'category', 'content']):
            return jsonify({'error': 'Missing required fields'}), 400

        memory = memory_manager.store_memory(
            agent_name=data['agent_name'],
            category=data['category'],  # observation, insight, decision, warning
            content=data['content'],
            accessible_by=data.get('accessible_by', [])
        )

        return jsonify({
            'message': 'Memory stored successfully',
            'memory': memory.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@agent_bp.route('/memory/<agent_name>', methods=['GET'])
def get_agent_memory(agent_name):
    """Get memory accessible to a specific agent"""
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)

    memories = memory_manager.get_memory(agent_name, category, limit)

    return jsonify({
        'agent': agent_name,
        'total': len(memories),
        'memories': [m.to_dict() for m in memories]
    }), 200


@agent_bp.route('/memory/observations', methods=['GET'])
def get_observations():
    """Get all observations from all agents"""
    observations = memory_manager.get_observations()

    return jsonify({
        'type': 'observations',
        'total': len(observations),
        'observations': [o.to_dict() for o in observations]
    }), 200


@agent_bp.route('/memory/insights', methods=['GET'])
def get_insights():
    """Get all insights from all agents"""
    insights = memory_manager.get_insights()

    return jsonify({
        'type': 'insights',
        'total': len(insights),
        'insights': [i.to_dict() for i in insights]
    }), 200


@agent_bp.route('/memory/warnings', methods=['GET'])
def get_warnings():
    """Get all warnings from all agents"""
    warnings = memory_manager.get_warnings()

    return jsonify({
        'type': 'warnings',
        'total': len(warnings),
        'warnings': [w.to_dict() for w in warnings]
    }), 200


# ============================================================================
# AGENT LEARNING & EVOLUTION
# ============================================================================

@agent_bp.route('/learnings/<agent_name>', methods=['GET'])
def get_agent_learnings(agent_name):
    """Get learnings for a specific agent"""
    category = request.args.get('category')

    learnings = learning_manager.get_learnings(agent_name, category)

    return jsonify({
        'agent': agent_name,
        'total': len(learnings),
        'learnings': [l.to_dict() for l in learnings]
    }), 200


@agent_bp.route('/learnings', methods=['POST'])
def record_learning():
    """Record a learning from agent execution"""
    try:
        data = request.json
        if not all(k in data for k in ['agent_name', 'category', 'content', 'confidence']):
            return jsonify({'error': 'Missing required fields'}), 400

        learning = learning_manager.record_learning(
            agent_name=data['agent_name'],
            category=data['category'],  # market_insight, strategy, failure, success
            content=data['content'],
            confidence=min(1.0, max(0.0, float(data['confidence']))),  # 0-1
            applicable_to=data.get('applicable_to', [])
        )

        return jsonify({
            'message': 'Learning recorded',
            'learning': learning.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@agent_bp.route('/learnings/high-confidence', methods=['GET'])
def get_high_confidence_learnings():
    """Get high-confidence learnings across all agents"""
    min_confidence = request.args.get('min_confidence', 0.8, type=float)

    learnings = learning_manager.get_high_confidence_learnings(min_confidence)

    return jsonify({
        'min_confidence': min_confidence,
        'total': len(learnings),
        'learnings': [l.to_dict() for l in learnings]
    }), 200


@agent_bp.route('/learnings/<agent_name>/suggestions', methods=['GET'])
def get_improvement_suggestions(agent_name):
    """Get improvement suggestions based on learnings"""
    suggestions = learning_manager.suggest_improvements(agent_name)

    return jsonify(suggestions), 200


# ============================================================================
# OUTPUT MONITORING
# ============================================================================

@agent_bp.route('/outputs/<agent_name>', methods=['GET'])
def get_agent_outputs(agent_name):
    """Get execution outputs for a specific agent"""
    limit = request.args.get('limit', 20, type=int)

    outputs = output_manager.get_latest_outputs(agent_name, limit)

    return jsonify({
        'agent': agent_name,
        'total': len(outputs),
        'outputs': [o.to_dict() for o in outputs]
    }), 200


@agent_bp.route('/outputs/<agent_name>/stats', methods=['GET'])
def get_agent_output_stats(agent_name):
    """Get execution statistics for an agent"""
    stats = output_manager.get_agent_stats(agent_name)

    return jsonify(stats), 200


@agent_bp.route('/outputs', methods=['GET'])
def get_all_outputs():
    """Get recent outputs from all agents"""
    limit = request.args.get('limit', 50, type=int)

    outputs = output_manager.get_latest_outputs(limit=limit)

    # Group by agent
    outputs_by_agent = {}
    for output in outputs:
        if output.agent_name not in outputs_by_agent:
            outputs_by_agent[output.agent_name] = []
        outputs_by_agent[output.agent_name].append(output.to_dict())

    return jsonify({
        'total_agents': len(outputs_by_agent),
        'total_outputs': len(outputs),
        'outputs_by_agent': outputs_by_agent
    }), 200


@agent_bp.route('/outputs', methods=['POST'])
def store_agent_output():
    """Store agent execution output"""
    try:
        data = request.json
        if not all(k in data for k in ['agent_name', 'execution_id', 'status', 'output_data']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Convert status string to enum
        try:
            status = AgentStatus(data['status'])
        except ValueError:
            return jsonify({'error': f'Invalid status: {data["status"]}'}), 400

        output = output_manager.store_output(
            agent_name=data['agent_name'],
            execution_id=data['execution_id'],
            status=status,
            output_data=data['output_data'],
            errors=data.get('errors', []),
            duration_seconds=data.get('duration_seconds', 0.0)
        )

        return jsonify({
            'message': 'Output stored',
            'output': output.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# ECOSYSTEM ANALYTICS
# ============================================================================

@agent_bp.route('/ecosystem/stats', methods=['GET'])
def get_ecosystem_stats():
    """Get overall ecosystem statistics"""

    # Count agents
    total_agents = len(ACTIVE_AGENTS)
    enabled_agents = sum(1 for c in ACTIVE_AGENTS.values() if c.get('enabled', True))

    # Count executions
    all_outputs = output_manager.get_latest_outputs(limit=1000)
    total_executions = len(all_outputs)
    successful_executions = len([o for o in all_outputs if o.status == AgentStatus.SUCCESS])

    # Count learnings
    learnings_dir = Path(__file__).parent.parent / 'data' / 'agent_learnings'
    total_learnings = len(list(learnings_dir.glob('*.json'))) if learnings_dir.exists() else 0

    # Count memories
    total_memories = len(memory_manager.memory)
    insights_count = len(memory_manager.get_insights())
    warnings_count = len(memory_manager.get_warnings())

    return jsonify({
        'agents': {
            'total': total_agents,
            'enabled': enabled_agents,
            'categories': len(set(c.get('category') for c in ACTIVE_AGENTS.values()))
        },
        'executions': {
            'total': total_executions,
            'successful': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
        },
        'learning': {
            'total_learnings': total_learnings,
            'total_memories': total_memories,
            'insights': insights_count,
            'warnings': warnings_count
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@agent_bp.route('/ecosystem/interactions', methods=['GET'])
def get_ecosystem_interactions():
    """Get agent interactions through shared memory and learnings"""

    interactions = {
        'shared_memory_flows': {},
        'learning_transfers': {},
        'cross_agent_references': {}
    }

    # Analyze shared memory for agent interactions
    memories = memory_manager.memory
    for memory in memories:
        if memory.accessible_by:
            source = memory.agent_name
            for target in memory.accessible_by:
                key = f"{source} -> {target}"
                interactions['shared_memory_flows'][key] = interactions['shared_memory_flows'].get(key, 0) + 1

    # Analyze learnings for cross-agent applicability
    learnings_dir = Path(__file__).parent.parent / 'data' / 'agent_learnings'
    if learnings_dir.exists():
        for learning_file in learnings_dir.glob('*.json'):
            try:
                with open(learning_file, 'r') as f:
                    learning_data = json.load(f)
                    if learning_data.get('applicable_to'):
                        source = learning_data.get('agent_name')
                        for target in learning_data['applicable_to']:
                            key = f"{source} teaches {target}"
                            interactions['learning_transfers'][key] = interactions['learning_transfers'].get(key, 0) + 1
            except:
                pass

    return jsonify({
        'total_memory_flows': len(interactions['shared_memory_flows']),
        'total_learning_transfers': len(interactions['learning_transfers']),
        'interactions': interactions
    }), 200


@agent_bp.route('/ecosystem/health', methods=['GET'])
def get_ecosystem_health():
    """Get overall ecosystem health assessment"""

    all_outputs = output_manager.get_latest_outputs(limit=500)

    health_status = {
        'overall_health': 'unknown',
        'agents_reporting': len(set(o.agent_name for o in all_outputs)),
        'success_rate': 0,
        'recent_issues': []
    }

    if all_outputs:
        successful = len([o for o in all_outputs if o.status == AgentStatus.SUCCESS])
        health_status['success_rate'] = successful / len(all_outputs) * 100

        # Determine health
        if health_status['success_rate'] >= 90:
            health_status['overall_health'] = 'healthy'
        elif health_status['success_rate'] >= 70:
            health_status['overall_health'] = 'degraded'
        else:
            health_status['overall_health'] = 'unhealthy'

        # Get recent errors
        errors = [o for o in all_outputs if o.status in [AgentStatus.FAILED, AgentStatus.ERROR]]
        health_status['recent_issues'] = [
            {
                'agent': e.agent_name,
                'status': e.status.value,
                'errors': e.errors[:2]  # First 2 errors
            }
            for e in errors[:5]
        ]

    return jsonify(health_status), 200


def register_agent_management_api(app):
    """Register agent management blueprint with Flask app"""
    app.register_blueprint(agent_bp)
