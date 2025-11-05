//! Business Validation Example
//!
//! Demonstrates the comprehensive business validation system that analyzes opportunities
//! across financial, technical, market demand, and risk dimensions.
//!
//! # Usage
//! ```bash
//! cargo run --example business_validation_example
//! ```

use agentic_business::{
    models::{Opportunity, ProductType},
    validation::{BusinessValidationManager, ValidationRecommendation},
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
    println!("║     Business Validation System - Comprehensive Analysis       ║");
    println!("╚════════════════════════════════════════════════════════════════╝\n");

    // Create LLM client
    let llm_client = Arc::new(MockLlmClient::new());

    // Create validation manager (meta-agent)
    let mut validation_manager = BusinessValidationManager::new(llm_client);

    println!("📊 Meta-Agent Initialized: BusinessValidationManager");
    println!("   Manages 4 specialized validation agents:\n");
    println!("   ├─ FinancialAnalysisAgent");
    println!("   ├─ TechnicalFeasibilityAgent");
    println!("   ├─ MarketDemandAgent");
    println!("   └─ RiskAssessmentAgent\n");

    // Scenario 1: High-potential SaaS opportunity
    println!("\n═══════════════════════════════════════════════════════════════");
    println!("🎯 SCENARIO 1: AI-Powered Email Newsletter Curator (SaaS)");
    println!("═══════════════════════════════════════════════════════════════\n");

    let mut opportunity1 = Opportunity::new(
        "AI-Powered Email Newsletter Curator".to_string(),
        "Automatically curates personalized newsletters from RSS feeds, social media, \
         and web content using AI analysis. Subscribers receive daily or weekly digests \
         tailored to their interests with zero manual curation required.".to_string(),
        "SaaS".to_string(),
        ProductType::SaaS,
    );

    // Set realistic financial projections
    opportunity1.financial_projection.initial_investment = 5000.0;
    opportunity1.financial_projection.monthly_costs = 200.0;
    opportunity1.financial_projection.monthly_revenue_low = 800.0;
    opportunity1.financial_projection.monthly_revenue_mid = 2500.0;
    opportunity1.financial_projection.monthly_revenue_high = 5000.0;

    opportunity1.implementation_estimate.estimated_cost = 3500.0;
    opportunity1.implementation_estimate.complexity_score = 4.5;
    opportunity1.implementation_estimate.estimated_days = 25;

    opportunity1.scores.market_size = 8.5;
    opportunity1.scores.competition = 4.0;
    opportunity1.scores.revenue_potential = 9.0;
    opportunity1.scores.passive_income = 9.5;

    println!("📋 Opportunity Details:");
    println!("   Title: {}", opportunity1.title);
    println!("   Domain: {}", opportunity1.domain);
    println!("   Initial Investment: ${:.0}", opportunity1.financial_projection.initial_investment);
    println!("   Complexity Score: {:.1}/10", opportunity1.implementation_estimate.complexity_score);
    println!("   Est. Development: {} days\n", opportunity1.implementation_estimate.estimated_days);

    println!("🔍 Starting comprehensive validation...\n");
    let report1 = validation_manager.validate(&opportunity1).await?;

    print_validation_report(&report1);

    // Scenario 2: Complex e-commerce platform
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("🎯 SCENARIO 2: Niche E-commerce Marketplace (Complex)");
    println!("═══════════════════════════════════════════════════════════════\n");

    let mut opportunity2 = Opportunity::new(
        "Artisan Goods Marketplace with AR Try-On".to_string(),
        "A marketplace connecting artisan creators with buyers, featuring augmented reality \
         try-on capabilities for furniture, art, and home decor. Includes payment processing, \
         inventory management, and creator analytics.".to_string(),
        "E-commerce".to_string(),
        ProductType::Marketplace,
    );

    // Set more challenging financial projections
    opportunity2.financial_projection.initial_investment = 45000.0;
    opportunity2.financial_projection.monthly_costs = 2500.0;
    opportunity2.financial_projection.monthly_revenue_low = 3000.0;
    opportunity2.financial_projection.monthly_revenue_mid = 8000.0;
    opportunity2.financial_projection.monthly_revenue_high = 18000.0;

    opportunity2.implementation_estimate.estimated_cost = 35000.0;
    opportunity2.implementation_estimate.complexity_score = 8.5;
    opportunity2.implementation_estimate.estimated_days = 120;

    opportunity2.scores.market_size = 7.5;
    opportunity2.scores.competition = 8.0;
    opportunity2.scores.revenue_potential = 7.0;
    opportunity2.scores.passive_income = 4.0;

    println!("📋 Opportunity Details:");
    println!("   Title: {}", opportunity2.title);
    println!("   Domain: {}", opportunity2.domain);
    println!("   Initial Investment: ${:.0}", opportunity2.financial_projection.initial_investment);
    println!("   Complexity Score: {:.1}/10", opportunity2.implementation_estimate.complexity_score);
    println!("   Est. Development: {} days\n", opportunity2.implementation_estimate.estimated_days);

    println!("🔍 Starting comprehensive validation...\n");
    let report2 = validation_manager.validate(&opportunity2).await?;

    print_validation_report(&report2);

    // Show meta-agent self-analysis
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("🤖 META-AGENT SELF-ANALYSIS");
    println!("═══════════════════════════════════════════════════════════════\n");

    let self_analysis = validation_manager.self_analyze().await?;
    println!("{}", self_analysis);

    // Display metrics
    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("📈 VALIDATION MANAGER METRICS");
    println!("═══════════════════════════════════════════════════════════════\n");

    let metrics = validation_manager.metrics();
    println!("Validations Executed:     {}", metrics.tasks_executed);
    println!("Avg Execution Time:       {:.2}ms", metrics.avg_execution_time_ms);
    println!("Workflow ID:              {}", validation_manager.workflow_id());

    println!("\n\n═══════════════════════════════════════════════════════════════");
    println!("✅ Business Validation Example Complete!");
    println!("═══════════════════════════════════════════════════════════════\n");

    Ok(())
}

fn print_validation_report(report: &agentic_business::validation::ComprehensiveValidationReport) {
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("📊 COMPREHENSIVE VALIDATION REPORT");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    // Overall Scores
    println!("🎯 OVERALL ASSESSMENT");
    println!("   Overall Score:        {:.1}/10 {}",
        report.overall_validation_score,
        score_stars(report.overall_validation_score)
    );
    println!("   Confidence Level:     {:.0}%", report.confidence_level * 100.0);
    println!("   Recommendation:       {} {}",
        format_recommendation(report.recommendation),
        recommendation_emoji(report.recommendation)
    );
    println!();

    // Financial Analysis
    println!("💰 FINANCIAL ANALYSIS");
    println!("   Viability Score:      {:.1}/10", report.financial_analysis.viability_score);
    println!("   Recommendation:       {:?}", report.financial_analysis.recommendation);
    println!("   12-Month ROI:         {:.0}%", report.financial_analysis.roi_analysis.roi_12_months);
    println!("   Break-Even Period:    {:.1} months", report.financial_analysis.break_even_analysis.break_even_months);
    println!("   Bootstrappable:       {}",
        if report.financial_analysis.funding_requirements.bootstrappable { "Yes ✓" } else { "No ✗" }
    );
    if !report.financial_analysis.funding_requirements.bootstrappable {
        println!("   Funding Required:     ${:.0}K",
            report.financial_analysis.funding_requirements.minimum_funding_needed / 1000.0
        );
    }
    println!();

    // Technical Feasibility
    println!("⚙️  TECHNICAL FEASIBILITY");
    println!("   Feasibility Score:    {:.1}/10", report.technical_feasibility.feasibility_score);
    println!("   Recommendation:       {:?}", report.technical_feasibility.recommendation);
    println!("   Complexity:           {:.1}/10", report.technical_feasibility.implementation_complexity.overall_complexity);
    println!("   Team Size Needed:     {} developers", report.technical_feasibility.implementation_complexity.estimated_team_size);
    println!("   Estimated Hours:      {:.0} hours", report.technical_feasibility.implementation_complexity.estimated_person_hours);
    println!("   Scalability Score:    {:.1}/10", report.technical_feasibility.scalability_assessment.scalability_score);
    println!("   Technical Risks:      {}", report.technical_feasibility.technical_risks.len());
    println!();

    // Market Demand
    println!("📈 MARKET DEMAND");
    println!("   Demand Score:         {:.1}/10", report.market_demand.demand_score);
    println!("   Recommendation:       {:?}", report.market_demand.recommendation);
    println!("   TAM:                  ${:.1}M", report.market_demand.target_market.total_addressable_market / 1_000_000.0);
    println!("   SAM:                  ${:.1}M", report.market_demand.target_market.serviceable_addressable_market / 1_000_000.0);
    println!("   Market Trend:         {:?}", report.market_demand.market_trends.overall_trend);
    println!("   Annual Growth:        {:.1}%", report.market_demand.market_trends.growth_rate_annual);
    println!("   Customer Segments:    {}", report.market_demand.customer_segments.len());
    println!();

    // Risk Assessment
    println!("⚠️  RISK ASSESSMENT");
    println!("   Risk Score:           {:.1}/10 {}",
        report.risk_assessment.overall_risk_score,
        if report.risk_assessment.overall_risk_score > 7.0 { "⚠️" }
        else if report.risk_assessment.overall_risk_score > 5.0 { "⚡" }
        else { "✓" }
    );
    println!("   Recommendation:       {:?}", report.risk_assessment.recommendation);
    println!("   Risk Categories:      {}", report.risk_assessment.risk_categories.len());
    println!("   Total Risks:          {}",
        report.risk_assessment.risk_categories.iter()
            .map(|c| c.risks.len())
            .sum::<usize>()
    );
    println!("   Mitigation Plans:     {}", report.risk_assessment.mitigation_strategies.len());
    println!("   Contingency Plans:    {}", report.risk_assessment.contingency_plans.len());
    println!();

    // Key Insights
    if !report.strengths.is_empty() {
        println!("✅ KEY STRENGTHS");
        for strength in &report.strengths {
            println!("   • {}", strength);
        }
        println!();
    }

    if !report.weaknesses.is_empty() {
        println!("❌ KEY WEAKNESSES");
        for weakness in &report.weaknesses {
            println!("   • {}", weakness);
        }
        println!();
    }

    if !report.critical_risks.is_empty() {
        println!("⚠️  CRITICAL RISKS");
        for risk in &report.critical_risks {
            println!("   • {}", risk);
        }
        println!();
    }

    if !report.success_factors.is_empty() {
        println!("🎯 SUCCESS FACTORS");
        for factor in &report.success_factors {
            println!("   • {}", factor);
        }
        println!();
    }

    // Decision Rationale
    println!("📝 DECISION RATIONALE");
    for line in report.decision_rationale.lines() {
        if !line.is_empty() {
            println!("   {}", line);
        }
    }
}

fn score_stars(score: f64) -> &'static str {
    if score >= 9.0 { "⭐⭐⭐⭐⭐" }
    else if score >= 7.0 { "⭐⭐⭐⭐" }
    else if score >= 5.0 { "⭐⭐⭐" }
    else if score >= 3.0 { "⭐⭐" }
    else { "⭐" }
}

fn format_recommendation(rec: ValidationRecommendation) -> &'static str {
    match rec {
        ValidationRecommendation::StrongGo => "STRONG GO",
        ValidationRecommendation::Go => "GO",
        ValidationRecommendation::Conditional => "CONDITIONAL",
        ValidationRecommendation::NoGo => "NO GO",
    }
}

fn recommendation_emoji(rec: ValidationRecommendation) -> &'static str {
    match rec {
        ValidationRecommendation::StrongGo => "🚀",
        ValidationRecommendation::Go => "✅",
        ValidationRecommendation::Conditional => "⚠️",
        ValidationRecommendation::NoGo => "❌",
    }
}
