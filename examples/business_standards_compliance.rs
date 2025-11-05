//! Business Standards Compliance Example
//!
//! Demonstrates how to verify that business agents comply with agentic_standards
//! protocol and capability requirements.
//!
//! # Usage
//! ```bash
//! cargo run --example business_standards_compliance
//! ```

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
use agentic_standards::{StandardsAgent, ComplianceReport};
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    println!("╔════════════════════════════════════════════════════════════════╗");
    println!("║         Business Agents - Standards Compliance Check          ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    // Create LLM client and standards agent
    let llm_client = Arc::new(MockLlmClient::new());
    let standards_agent = StandardsAgent::new();

    println!("📋 Checking compliance against 'tmpl.standard.worker' template:");
    println!("   Required Protocols:");
    println!("     • MCP (Model Context Protocol) - Required");
    println!("     • A2A (Agent-to-Agent) - Recommended");
    println!("   Required Capabilities:");
    println!("     • mcp.tools - Required");
    println!("     • a2a.messaging - Recommended\n");

    println!("═══════════════════════════════════════════════════════════════\n");
    println!("📊 PHASE 1: OPPORTUNITY DISCOVERY AGENTS\n");

    // Phase 1 Agents
    let phase1_agents: Vec<(&str, Box<dyn Fn() -> &agentic_core::Agent>)> = vec![
        ("MarketResearchAgent", {
            let agent = MarketResearchAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("TrendAnalysisAgent", {
            let agent = TrendAnalysisAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("CompetitorAnalysisAgent", {
            let agent = CompetitorAnalysisAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("OpportunityEvaluationAgent", {
            let agent = OpportunityEvaluationAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("OpportunityDiscoveryManager (meta)", {
            let agent = OpportunityDiscoveryManager::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
    ];

    for (name, get_agent) in phase1_agents {
        let agent = get_agent();
        let report = standards_agent
            .compliance_for_template("tmpl.standard.worker", agent)
            .expect("Should get compliance report");

        print_compliance_result(name, &report, agent);
    }

    println!("\n═══════════════════════════════════════════════════════════════\n");
    println!("📊 PHASE 2: BUSINESS VALIDATION AGENTS\n");

    // Phase 2 Agents
    let phase2_agents: Vec<(&str, Box<dyn Fn() -> &agentic_core::Agent>)> = vec![
        ("FinancialAnalysisAgent", {
            let agent = FinancialAnalysisAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("TechnicalFeasibilityAgent", {
            let agent = TechnicalFeasibilityAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("MarketDemandAgent", {
            let agent = MarketDemandAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("RiskAssessmentAgent", {
            let agent = RiskAssessmentAgent::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
        ("BusinessValidationManager (meta)", {
            let agent = BusinessValidationManager::new(llm_client.clone());
            Box::new(move || agent.agent())
        }),
    ];

    for (name, get_agent) in phase2_agents {
        let agent = get_agent();
        let report = standards_agent
            .compliance_for_template("tmpl.standard.worker", agent)
            .expect("Should get compliance report");

        print_compliance_result(name, &report, agent);
    }

    println!("\n═══════════════════════════════════════════════════════════════\n");
    println!("📈 COMPLIANCE SUMMARY\n");

    // Check all agents
    let all_agents = vec![
        MarketResearchAgent::new(llm_client.clone()).agent(),
        TrendAnalysisAgent::new(llm_client.clone()).agent(),
        CompetitorAnalysisAgent::new(llm_client.clone()).agent(),
        OpportunityEvaluationAgent::new(llm_client.clone()).agent(),
        OpportunityDiscoveryManager::new(llm_client.clone()).agent(),
        FinancialAnalysisAgent::new(llm_client.clone()).agent(),
        TechnicalFeasibilityAgent::new(llm_client.clone()).agent(),
        MarketDemandAgent::new(llm_client.clone()).agent(),
        RiskAssessmentAgent::new(llm_client.clone()).agent(),
        BusinessValidationManager::new(llm_client.clone()).agent(),
    ];

    let compliant_count = all_agents
        .iter()
        .filter(|agent| {
            standards_agent
                .compliance_for_template("tmpl.standard.worker", agent)
                .map(|r| r.compliant)
                .unwrap_or(false)
        })
        .count();

    let total_count = all_agents.len();
    let compliance_rate = (compliant_count as f64 / total_count as f64) * 100.0;

    println!("Total Agents:        {}", total_count);
    println!("Compliant:           {} ✅", compliant_count);
    println!("Non-Compliant:       {} ❌", total_count - compliant_count);
    println!("Compliance Rate:     {:.0}%", compliance_rate);

    if compliance_rate == 100.0 {
        println!("\n🎉 ALL AGENTS ARE STANDARDS-COMPLIANT! 🎉");
    } else {
        println!("\n⚠️  Some agents need compliance fixes");
    }

    println!("\n═══════════════════════════════════════════════════════════════\n");
    println!("🔍 DETAILED PROTOCOL & CAPABILITY CHECK\n");

    // Detailed check for one agent
    let sample_agent = FinancialAnalysisAgent::new(llm_client.clone());
    let agent = sample_agent.agent();

    println!("Sample Agent: {}", agent.name);
    println!("\nProtocol Configuration:");
    if let Some(a2a) = agent.config.get("protocol:a2a") {
        println!("  ✅ protocol:a2a = {}", a2a);
    } else {
        println!("  ❌ protocol:a2a = MISSING");
    }

    if let Some(mcp) = agent.config.get("protocol:mcp") {
        println!("  ✅ protocol:mcp = {}", mcp);
    } else {
        println!("  ❌ protocol:mcp = MISSING");
    }

    println!("\nCapability Configuration:");
    if let Some(mcp_tools) = agent.config.get("cap:mcp.tools") {
        println!("  ✅ cap:mcp.tools = {}", mcp_tools);
    } else {
        println!("  ❌ cap:mcp.tools = MISSING");
    }

    if let Some(a2a_msg) = agent.config.get("cap:a2a.messaging") {
        println!("  ✅ cap:a2a.messaging = {}", a2a_msg);
    } else {
        println!("  ❌ cap:a2a.messaging = MISSING");
    }

    if let Some(business) = agent.config.get("cap:business.analysis") {
        println!("  ✅ cap:business.analysis = {}", business);
    } else {
        println!("  ❌ cap:business.analysis = MISSING");
    }

    println!("\n╔════════════════════════════════════════════════════════════════╗");
    println!("║                    Compliance Check Complete                   ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    Ok(())
}

fn print_compliance_result(
    agent_name: &str,
    report: &ComplianceReport,
    agent: &agentic_core::Agent,
) {
    let status = if report.compliant {
        "✅ COMPLIANT"
    } else {
        "❌ NON-COMPLIANT"
    };

    println!("🤖 {}", agent_name);
    println!("   Status: {}", status);
    println!("   Role:   {:?}", agent.role);

    if !report.compliant {
        if !report.missing_protocols.is_empty() {
            println!("   Missing Protocols:");
            for protocol in &report.missing_protocols {
                println!("     • {:?}", protocol);
            }
        }
        if !report.missing_capabilities.is_empty() {
            println!("   Missing Capabilities:");
            for cap in &report.missing_capabilities {
                println!("     • {}", cap);
            }
        }
    } else {
        // Show what protocols/capabilities are present
        let has_a2a = agent.config.contains_key("protocol:a2a");
        let has_mcp = agent.config.contains_key("protocol:mcp");
        let has_mcp_tools = agent.config.contains_key("cap:mcp.tools");
        let has_a2a_msg = agent.config.contains_key("cap:a2a.messaging");

        println!("   Protocols: {} {}",
            if has_a2a { "A2A" } else { "" },
            if has_mcp { "MCP" } else { "" }
        );
        println!("   Capabilities: {} {}",
            if has_mcp_tools { "mcp.tools" } else { "" },
            if has_a2a_msg { "a2a.messaging" } else { "" }
        );
    }
    println!();
}
