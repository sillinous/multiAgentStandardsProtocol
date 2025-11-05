//! Business Opportunity Discovery Example
//!
//! This example demonstrates the autonomous Business-to-Revenue system's
//! opportunity discovery capabilities.
//!
//! The system:
//! 1. Takes user preferences (domain, investment, revenue type, etc.)
//! 2. Discovers opportunities from multiple sources (LLM, trends, APIs)
//! 3. Analyzes competitive landscape
//! 4. Evaluates across 7 dimensions
//! 5. Ranks and presents the best opportunities
//!
//! All orchestrated by the OpportunityDiscoveryManager meta-agent!

use agentic_business::{
    opportunity::OpportunityDiscoveryManager,
    models::{UserPreferences, ProductType},
};
use agentic_runtime::llm::MockLlmClient;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    println!("\n🚀 Autonomous Business-to-Revenue System");
    println!("==========================================");
    println!("Opportunity Discovery Demo\n");

    // Setup LLM client (using mock for demo - replace with real Anthropic/OpenAI client)
    let llm_client = Arc::new(MockLlmClient::new());

    // Create the Opportunity Discovery Manager (meta-agent)
    let mut discovery_manager = OpportunityDiscoveryManager::new(llm_client);

    println!("✓ Discovery Manager initialized");
    println!("  Meta-Agent Type: Coordinator");
    println!("  Agent Name: {}", discovery_manager.base_agent().name);
    println!("  Capabilities: {}\n", discovery_manager.capabilities().len());

    // ========================================================================
    // Scenario 1: Minimal Investment, Passive Revenue, SaaS
    // ========================================================================

    println!("📋 Scenario 1: Minimal Investment + Passive Revenue + SaaS");
    println!("─────────────────────────────────────────────────────────");

    let scenario1_prefs = UserPreferences {
        domain: Some("SaaS".to_string()),
        product_type: Some(ProductType::SaaS),
        max_investment: Some(5000.0),
        max_time_to_market_days: Some(30),
        revenue_type: vec!["subscription".to_string(), "passive".to_string()],
        focus_minimal_investment: true,
        focus_passive_revenue: true,
        focus_quick_wins: true,
        ..Default::default()
    };

    println!("\n🔍 User Preferences:");
    println!("   Domain: SaaS");
    println!("   Max Investment: $5,000");
    println!("   Max Time to Market: 30 days");
    println!("   Revenue Types: subscription, passive");
    println!("   Focus: Minimal investment, passive revenue, quick wins\n");

    println!("🤖 Activating Discovery Workflow...\n");

    let opportunities1 = discovery_manager.discover(scenario1_prefs).await?;

    println!("\n✅ Discovery Complete!");
    println!("   Found {} opportunities\n", opportunities1.len());

    // Display top 5 opportunities
    println!("🏆 Top Opportunities (Ranked by Overall Score):");
    println!("═══════════════════════════════════════════════\n");

    for (i, opp) in opportunities1.iter().take(5).enumerate() {
        println!("{}. {}", i + 1, opp.title);
        println!("   {}", opp.description);
        println!("   Domain: {} | Type: {:?}", opp.domain, opp.product_type);
        println!("\n   📊 Multi-Dimensional Score:");
        println!("      Overall:            {:.1}/10 ⭐", opp.scores.overall);
        println!("      Market Size:        {:.1}/10", opp.scores.market_size);
        println!("      Competition:        {:.1}/10 (lower is better)", opp.scores.competition);
        println!("      Complexity:         {:.1}/10 (lower is easier)", opp.scores.complexity);
        println!("      Revenue Potential:  {:.1}/10", opp.scores.revenue_potential);
        println!("      Time to Market:     {:.1}/10 (higher is faster)", opp.scores.time_to_market);
        println!("      Investment Required:{:.1}/10 (lower is less)", opp.scores.investment_required);
        println!("      Passive Income:     {:.1}/10", opp.scores.passive_income);

        println!("\n   💰 Financial Projection:");
        println!("      Initial Investment: ${:.2}", opp.financial_projection.initial_investment);
        println!("      Monthly Costs:      ${:.2}", opp.financial_projection.monthly_costs);
        println!("      Monthly Revenue:    ${:.2} - ${:.2}",
            opp.financial_projection.monthly_revenue_low,
            opp.financial_projection.monthly_revenue_high
        );
        println!("      Break Even:         {:.1} months", opp.financial_projection.break_even_months);
        println!("      12-Month ROI:       {:.1}%", opp.financial_projection.roi_12_months);

        println!("\n   ⚡ Implementation:");
        println!("      Estimated Days:     {}", opp.implementation_estimate.estimated_days);
        println!("      Estimated Cost:     ${:.2}", opp.implementation_estimate.estimated_cost);
        println!("      Complexity Score:   {:.1}/10", opp.implementation_estimate.complexity_score);

        println!("\n   🎯 Competitive Analysis:");
        println!("      Direct Competitors:   {}", opp.competitive_analysis.direct_competitors);
        println!("      Indirect Competitors: {}", opp.competitive_analysis.indirect_competitors);
        println!("      Market Saturation:    {:.1}/10", opp.competitive_analysis.saturation_level);

        println!("\n   📡 Data Sources:");
        for source in &opp.sources {
            println!("      • {} ({:?}) - confidence: {:.0}%",
                source.name, source.source_type, source.confidence * 100.0);
        }

        println!("\n   ⏰ Discovered: {}\n", opp.discovered_at.format("%Y-%m-%d %H:%M:%S"));
        println!("   {}", "─".repeat(70));
        println!();
    }

    // ========================================================================
    // Scenario 2: Mobile App, Quick to Market
    // ========================================================================

    println!("\n\n📋 Scenario 2: Mobile App + Quick Wins");
    println!("─────────────────────────────────────────");

    let scenario2_prefs = UserPreferences {
        domain: Some("Mobile".to_string()),
        product_type: Some(ProductType::MobileApp),
        max_time_to_market_days: Some(14),
        focus_quick_wins: true,
        ..Default::default()
    };

    println!("\n🔍 User Preferences:");
    println!("   Domain: Mobile");
    println!("   Product Type: Mobile App");
    println!("   Max Time to Market: 14 days");
    println!("   Focus: Quick wins\n");

    println!("🤖 Activating Discovery Workflow...\n");

    let opportunities2 = discovery_manager.discover(scenario2_prefs).await?;

    println!("\n✅ Discovery Complete!");
    println!("   Found {} opportunities\n", opportunities2.len());

    println!("🏆 Top 3 Quick Win Opportunities:");
    println!("═══════════════════════════════════\n");

    for (i, opp) in opportunities2.iter().take(3).enumerate() {
        println!("{}. {} (Score: {:.1}/10)",
            i + 1, opp.title, opp.scores.overall);
        println!("   {} days to market | ${:.0} initial investment",
            opp.implementation_estimate.estimated_days,
            opp.financial_projection.initial_investment
        );
        println!();
    }

    // ========================================================================
    // Discovery Manager Metrics
    // ========================================================================

    println!("\n📊 Discovery Manager Performance:");
    println!("═══════════════════════════════════");

    let metrics = discovery_manager.metrics();
    println!("   Total Workflows Executed:  {}", metrics.tasks_executed);
    println!("   Average Execution Time:    {:.2}s", metrics.avg_execution_time_ms / 1000.0);
    println!("   Total Opportunities Found: {}", opportunities1.len() + opportunities2.len());

    // Self-analysis
    println!("\n🔍 Meta-Agent Self-Analysis:");
    let insights = discovery_manager.self_analyze().await?;
    for insight in insights {
        println!("   • {}", insight);
    }

    // ========================================================================
    // Next Steps
    // ========================================================================

    println!("\n\n🎯 Next Steps:");
    println!("═══════════════");
    println!("   1. Select an opportunity");
    println!("   2. Validate with BusinessValidationManager (Phase 2)");
    println!("   3. Develop with ProductDevelopmentManager (Phase 3)");
    println!("   4. Generate revenue with RevenueGenerationManager (Phase 4)");
    println!("   5. Monitor via beautiful React dashboard (Phase 5-6)");

    println!("\n\n✨ Opportunity Discovery Demo Complete!");
    println!("   The system autonomously discovered, analyzed, and ranked");
    println!("   market opportunities based on your preferences.\n");

    println!("🚀 API Endpoints Available:");
    println!("   POST   /api/business/discover");
    println!("   GET    /api/business/opportunities");
    println!("   GET    /api/business/opportunities/:id");
    println!("   POST   /api/business/opportunities/:id/develop");
    println!("   DELETE /api/business/opportunities/:id");
    println!("   GET    /api/business/metrics");
    println!("   GET    /api/business/discovery/status\n");

    Ok(())
}
