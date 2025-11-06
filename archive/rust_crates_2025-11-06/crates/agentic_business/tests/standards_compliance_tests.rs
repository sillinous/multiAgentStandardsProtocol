//! Standards Compliance Tests for Business Agents
//!
//! Verifies that all business agents properly implement the agentic_standards
//! protocol and capability requirements (A2A, MCP protocols).

use agentic_business::opportunity::{
    MarketResearchAgent, TrendAnalysisAgent,
    CompetitorAnalysisAgent, OpportunityEvaluationAgent,
    OpportunityDiscoveryManager,
};
use agentic_business::validation::{
    FinancialAnalysisAgent, TechnicalFeasibilityAgent,
    MarketDemandAgent, RiskAssessmentAgent,
    BusinessValidationManager,
};
use agentic_runtime::llm::MockLlmClient;
use agentic_standards::{StandardsAgent, template_standard_worker};
use std::sync::Arc;

/// Helper function to check if agent has required protocol configs
fn assert_agent_has_protocol(agent: &agentic_core::Agent, protocol_key: &str) {
    assert!(
        agent.config.contains_key(protocol_key),
        "Agent '{}' missing protocol config key: {}",
        agent.name,
        protocol_key
    );
}

/// Helper function to check if agent has required capability configs
fn assert_agent_has_capability(agent: &agentic_core::Agent, cap_key: &str) {
    assert!(
        agent.config.contains_key(cap_key),
        "Agent '{}' missing capability config key: {}",
        agent.name,
        cap_key
    );
}

/// Test all Phase 1 opportunity discovery agents for standards compliance
#[tokio::test]
async fn test_phase1_agents_compliance() {
    let llm = Arc::new(MockLlmClient::new());

    // Test MarketResearchAgent
    let market_agent = MarketResearchAgent::new(llm.clone());
    let agent = market_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test TrendAnalysisAgent
    let trend_agent = TrendAnalysisAgent::new(llm.clone());
    let agent = trend_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test CompetitorAnalysisAgent
    let competitor_agent = CompetitorAnalysisAgent::new(llm.clone());
    let agent = competitor_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test OpportunityEvaluationAgent
    let eval_agent = OpportunityEvaluationAgent::new(llm.clone());
    let agent = eval_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test OpportunityDiscoveryManager (meta-agent)
    let discovery_manager = OpportunityDiscoveryManager::new(llm.clone());
    let agent = discovery_manager.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");
}

/// Test all Phase 2 validation agents for standards compliance
#[tokio::test]
async fn test_phase2_agents_compliance() {
    let llm = Arc::new(MockLlmClient::new());

    // Test FinancialAnalysisAgent
    let financial_agent = FinancialAnalysisAgent::new(llm.clone());
    let agent = financial_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test TechnicalFeasibilityAgent
    let technical_agent = TechnicalFeasibilityAgent::new(llm.clone());
    let agent = technical_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test MarketDemandAgent
    let demand_agent = MarketDemandAgent::new(llm.clone());
    let agent = demand_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test RiskAssessmentAgent
    let risk_agent = RiskAssessmentAgent::new(llm.clone());
    let agent = risk_agent.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");

    // Test BusinessValidationManager (meta-agent)
    let validation_manager = BusinessValidationManager::new(llm.clone());
    let agent = validation_manager.agent();
    assert_agent_has_protocol(agent, "protocol:a2a");
    assert_agent_has_protocol(agent, "protocol:mcp");
    assert_agent_has_capability(agent, "cap:mcp.tools");
    assert_agent_has_capability(agent, "cap:a2a.messaging");
}

/// Test that agents pass formal compliance checks from agentic_standards
#[tokio::test]
async fn test_agents_pass_formal_compliance_check() {
    let llm = Arc::new(MockLlmClient::new());
    let standards_agent = StandardsAgent::new();

    // Test a sample agent from each phase
    let market_agent = MarketResearchAgent::new(llm.clone());
    let report = standards_agent.compliance_for_template(
        "tmpl.standard.worker",
        market_agent.agent()
    );

    assert!(report.is_some(), "Should get compliance report");
    let report = report.unwrap();
    assert!(
        report.compliant,
        "MarketResearchAgent should be compliant. Missing protocols: {:?}, Missing capabilities: {:?}",
        report.missing_protocols,
        report.missing_capabilities
    );

    let financial_agent = FinancialAnalysisAgent::new(llm.clone());
    let report = standards_agent.compliance_for_template(
        "tmpl.standard.worker",
        financial_agent.agent()
    );

    assert!(report.is_some(), "Should get compliance report");
    let report = report.unwrap();
    assert!(
        report.compliant,
        "FinancialAnalysisAgent should be compliant. Missing protocols: {:?}, Missing capabilities: {:?}",
        report.missing_protocols,
        report.missing_capabilities
    );
}

/// Test that business capability is set on all agents
#[tokio::test]
async fn test_agents_have_business_capability() {
    let llm = Arc::new(MockLlmClient::new());

    // Test Phase 1
    let market_agent = MarketResearchAgent::new(llm.clone());
    assert_agent_has_capability(market_agent.agent(), "cap:business.analysis");

    let trend_agent = TrendAnalysisAgent::new(llm.clone());
    assert_agent_has_capability(trend_agent.agent(), "cap:business.analysis");

    // Test Phase 2
    let financial_agent = FinancialAnalysisAgent::new(llm.clone());
    assert_agent_has_capability(financial_agent.agent(), "cap:business.analysis");

    let technical_agent = TechnicalFeasibilityAgent::new(llm.clone());
    assert_agent_has_capability(technical_agent.agent(), "cap:business.analysis");
}

/// Test that protocol versions are properly set
#[tokio::test]
async fn test_protocol_versions() {
    let llm = Arc::new(MockLlmClient::new());
    let agent = MarketResearchAgent::new(llm);

    // Check that protocol values are set (not just keys)
    let a2a_value = agent.agent().config.get("protocol:a2a");
    assert!(a2a_value.is_some(), "protocol:a2a should have a value");
    assert_eq!(a2a_value.unwrap(), &serde_json::json!("1.0"));

    let mcp_value = agent.agent().config.get("protocol:mcp");
    assert!(mcp_value.is_some(), "protocol:mcp should have a value");
    assert_eq!(mcp_value.unwrap(), &serde_json::json!("1.0"));
}

/// Test that capability versions are properly set
#[tokio::test]
async fn test_capability_versions() {
    let llm = Arc::new(MockLlmClient::new());
    let agent = FinancialAnalysisAgent::new(llm);

    let mcp_tools = agent.agent().config.get("cap:mcp.tools");
    assert!(mcp_tools.is_some(), "cap:mcp.tools should have a value");
    assert_eq!(mcp_tools.unwrap(), &serde_json::json!("1.0.0"));

    let a2a_messaging = agent.agent().config.get("cap:a2a.messaging");
    assert!(a2a_messaging.is_some(), "cap:a2a.messaging should have a value");
    assert_eq!(a2a_messaging.unwrap(), &serde_json::json!("1.0.0"));
}

/// Test configure_standards_compliant_agent helper function directly
#[test]
fn test_configure_standards_compliant_agent_helper() {
    use agentic_business::configure_standards_compliant_agent;
    use agentic_core::{Agent, AgentRole};

    let mut agent = Agent::new(
        "TestAgent",
        "A test agent",
        AgentRole::Worker,
        "claude-3-5-sonnet-20241022",
        "anthropic",
    );

    // Before configuration
    assert!(!agent.config.contains_key("protocol:a2a"));
    assert!(!agent.config.contains_key("protocol:mcp"));

    // Apply configuration
    configure_standards_compliant_agent(&mut agent);

    // After configuration
    assert_agent_has_protocol(&agent, "protocol:a2a");
    assert_agent_has_protocol(&agent, "protocol:mcp");
    assert_agent_has_capability(&agent, "cap:mcp.tools");
    assert_agent_has_capability(&agent, "cap:a2a.messaging");
    assert_agent_has_capability(&agent, "cap:business.analysis");
}
