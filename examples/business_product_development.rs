//! Complete Business-to-Product Development Example
//!
//! Demonstrates the full workflow:
//! 1. Opportunity Discovery (Phase 1)
//! 2. Business Validation (Phase 2)
//! 3. Product Development (Phase 3)
//!
//! # Usage
//! ```bash
//! cargo run --example business_product_development
//! ```

use agentic_business::{
    models::{Opportunity, ProductType, UserPreferences},
    opportunity::OpportunityDiscoveryManager,
    validation::BusinessValidationManager,
    development::ProductDevelopmentManager,
};
use agentic_runtime::llm::MockLlmClient;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    println!("╔════════════════════════════════════════════════════════════════╗");
    println!("║         Business-to-Product Development Workflow              ║");
    println!("║                  End-to-End Demonstration                      ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    // Create LLM client
    let llm_client = Arc::new(MockLlmClient::new());

    // ========================================================================
    // PHASE 1: OPPORTUNITY DISCOVERY
    // ========================================================================
    println!("\n═══════════════════════════════════════════════════════════════");
    println!("🔍 PHASE 1: OPPORTUNITY DISCOVERY");
    println!("═══════════════════════════════════════════════════════════════\n");

    let preferences = UserPreferences {
        domain: Some("SaaS".to_string()),
        product_type: Some(ProductType::SaaS),
        min_investment: Some(1000.0),
        max_investment: Some(10000.0),
        max_time_to_market_days: Some(30),
        revenue_type: vec!["subscription".to_string(), "passive".to_string()],
        focus_minimal_investment: true,
        focus_passive_revenue: true,
        focus_quick_wins: true,
    };

    println!("📋 User Preferences:");
    println!("   Domain: {}", preferences.domain.as_ref().unwrap());
    println!("   Max Investment: ${}", preferences.max_investment.unwrap());
    println!("   Time to Market: {} days", preferences.max_time_to_market_days.unwrap());
    println!("   Focus: Minimal investment, passive revenue, quick wins\n");

    let mut discovery_manager = OpportunityDiscoveryManager::new(llm_client.clone());
    let opportunities = discovery_manager.discover(preferences).await?;

    println!("✅ Found {} opportunities", opportunities.len());

    // Select top opportunity
    let opportunity = &opportunities[0];
    println!("\n🎯 Selected Opportunity:");
    println!("   Title: {}", opportunity.title);
    println!("   Domain: {}", opportunity.domain);
    println!("   Overall Score: {:.1}/10", opportunity.scores.overall);
    println!("   Est. Investment: ${:.0}", opportunity.financial_projection.initial_investment);
    println!("   Est. Development: {} days", opportunity.implementation_estimate.estimated_days);

    // ========================================================================
    // PHASE 2: BUSINESS VALIDATION
    // ========================================================================
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("📊 PHASE 2: BUSINESS VALIDATION");
    println!("═══════════════════════════════════════════════════════════════\n");

    let mut validation_manager = BusinessValidationManager::new(llm_client.clone());
    let validation_report = validation_manager.validate(opportunity).await?;

    println!("📈 Validation Results:");
    println!("   Overall Score: {:.1}/10 ⭐", validation_report.overall_validation_score);
    println!("   Confidence: {:.0}%", validation_report.confidence_level * 100.0);
    println!("   Recommendation: {:?}\n", validation_report.recommendation);

    println!("💰 Financial Analysis:");
    println!("   Viability Score: {:.1}/10", validation_report.financial_analysis.viability_score);
    println!("   12-Month ROI: {:.0}%", validation_report.financial_analysis.roi_analysis.roi_12_months);
    println!("   Break-Even: {:.1} months", validation_report.financial_analysis.break_even_analysis.break_even_months);
    println!("   Bootstrappable: {}\n", validation_report.financial_analysis.funding_requirements.bootstrappable);

    println!("⚙️  Technical Feasibility:");
    println!("   Feasibility Score: {:.1}/10", validation_report.technical_feasibility.feasibility_score);
    println!("   Complexity: {:.1}/10", validation_report.technical_feasibility.implementation_complexity.overall_complexity);
    println!("   Team Size: {} developers", validation_report.technical_feasibility.implementation_complexity.estimated_team_size);
    println!("   Est. Hours: {:.0}\n", validation_report.technical_feasibility.implementation_complexity.estimated_person_hours);

    println!("📈 Market Demand:");
    println!("   Demand Score: {:.1}/10", validation_report.market_demand.demand_score);
    println!("   TAM: ${:.1}M", validation_report.market_demand.target_market.total_addressable_market / 1_000_000.0);
    println!("   Market Trend: {:?}", validation_report.market_demand.market_trends.overall_trend);
    println!("   Growth Rate: {:.1}%/year\n", validation_report.market_demand.market_trends.growth_rate_annual);

    println!("⚠️  Risk Assessment:");
    println!("   Risk Score: {:.1}/10", validation_report.risk_assessment.overall_risk_score);
    println!("   Risk Categories: {}", validation_report.risk_assessment.risk_categories.len());
    println!("   Mitigation Plans: {}", validation_report.risk_assessment.mitigation_strategies.len());

    // Check if we should proceed
    use agentic_business::validation::ValidationRecommendation;
    match validation_report.recommendation {
        ValidationRecommendation::StrongGo | ValidationRecommendation::Go => {
            println!("\n✅ VALIDATION PASSED - Proceeding to development");
        }
        ValidationRecommendation::Conditional => {
            println!("\n⚠️  CONDITIONAL - Proceeding with caution");
        }
        ValidationRecommendation::NoGo => {
            println!("\n❌ VALIDATION FAILED - Not recommended for development");
            return Ok(());
        }
    }

    // ========================================================================
    // PHASE 3: PRODUCT DEVELOPMENT
    // ========================================================================
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("🚀 PHASE 3: PRODUCT DEVELOPMENT");
    println!("═══════════════════════════════════════════════════════════════\n");

    let mut dev_manager = ProductDevelopmentManager::new(llm_client.clone());
    let dev_result = dev_manager.develop(opportunity, &validation_report).await?;

    println!("🎨 Design Specification:");
    println!("   Components: {}", dev_result.specification.design.components.len());
    println!("   User Flows: {}", dev_result.specification.design.user_flows.len());
    println!("   Layouts: {}", dev_result.specification.design.layouts.len());
    println!("   Breakpoints: {}\n", dev_result.specification.design.responsive_breakpoints.len());

    println!("🎨 Design System:");
    let ds = &dev_result.specification.design.design_system;
    println!("   Primary Color: {}", ds.color_palette.primary);
    println!("   Font Family: {}", ds.typography.font_family_primary);
    println!("   Spacing Scale: {} levels", ds.spacing.scale.len());
    println!("   Typography Levels: {}\n", ds.typography.scale.len());

    println!("🏗️  Infrastructure:");
    println!("   Cloud Provider: {:?}", dev_result.specification.infrastructure.cloud_provider);
    println!("   Database: {:?}", dev_result.specification.infrastructure.database.database_type);
    println!("   Database Tables: {}", dev_result.specification.infrastructure.database.schema.len());
    println!("   API Endpoints: {}", dev_result.specification.infrastructure.api.endpoints.len());
    println!("   Est. Monthly Cost: ${:.2}\n", dev_result.specification.infrastructure.estimated_monthly_cost);

    println!("📋 Development Timeline:");
    println!("   Total Duration: {} days", dev_result.specification.development_timeline.total_days);
    println!("   Phases: {}\n", dev_result.specification.development_timeline.phases.len());

    for (i, phase) in dev_result.specification.development_timeline.phases.iter().enumerate() {
        println!("   {}. {} ({} days)", i + 1, phase.phase_name, phase.duration_days);
        for task in &phase.tasks {
            println!("      • {}", task);
        }
    }

    println!("\n🔒 Quality Gates:");
    for gate in &dev_result.specification.quality_gates {
        let status = if gate.required { "Required" } else { "Optional" };
        println!("   • {} ({})", gate.gate_name, status);
    }

    println!("\n📊 Development Result:");
    println!("   Status: {:?}", dev_result.status);
    println!("   Completion: {:.0}%", dev_result.completion_percentage);
    println!("   Phases Completed: {}", dev_result.phases_completed.join(", "));

    // ========================================================================
    // SUMMARY
    // ========================================================================
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("📈 COMPLETE WORKFLOW SUMMARY");
    println!("═══════════════════════════════════════════════════════════════\n");

    println!("🎯 Opportunity: {}", opportunity.title);
    println!("   Discovery Score: {:.1}/10", opportunity.scores.overall);
    println!("   Validation Score: {:.1}/10", validation_report.overall_validation_score);
    println!("   Development Status: {:?}\n", dev_result.status);

    println!("💰 Financial Projection:");
    println!("   Initial Investment: ${:.0}", opportunity.financial_projection.initial_investment);
    println!("   Monthly Revenue (mid): ${:.0}", opportunity.financial_projection.monthly_revenue_mid);
    println!("   12-Month ROI: {:.0}%", validation_report.financial_analysis.roi_analysis.roi_12_months);
    println!("   Break-Even: {:.1} months\n", validation_report.financial_analysis.break_even_analysis.break_even_months);

    println!("🏗️  Infrastructure:");
    println!("   Provider: {:?}", dev_result.specification.infrastructure.cloud_provider);
    println!("   Database: {:?}", dev_result.specification.infrastructure.database.database_type);
    println!("   Monthly Cost: ${:.2}\n", dev_result.specification.infrastructure.estimated_monthly_cost);

    println!("⏱️  Timeline:");
    println!("   Development: {} days", dev_result.specification.development_timeline.total_days);
    println!("   Time to Market: {} days (estimated)", opportunity.implementation_estimate.estimated_days);

    println!("\n✅ WORKFLOW COMPLETE!");
    println!("   Next Steps:");
    println!("   1. Review design specification");
    println!("   2. Provision infrastructure");
    println!("   3. Begin development");
    println!("   4. Deploy to production");
    println!("   5. Monitor and optimize\n");

    // Meta-agent self-analysis
    println!("\n═══════════════════════════════════════════════════════════════");
    println!("🤖 META-AGENT ANALYSIS");
    println!("═══════════════════════════════════════════════════════════════\n");

    let discovery_analysis = discovery_manager.self_analyze().await?;
    println!("📊 Discovery Manager:\n{}\n", discovery_analysis);

    let validation_analysis = validation_manager.self_analyze().await?;
    println!("📊 Validation Manager:\n{}\n", validation_analysis);

    let dev_analysis = dev_manager.self_analyze().await?;
    println!("📊 Development Manager:\n{}\n", dev_analysis);

    println!("\n╔════════════════════════════════════════════════════════════════╗");
    println!("║           Business-to-Product Workflow Complete!              ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    Ok(())
}
