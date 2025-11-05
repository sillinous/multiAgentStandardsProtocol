//! Financial Analysis Agent - Deep financial validation and projections

use crate::models::{Opportunity, FinancialProjection};
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug};

/// Financial analysis report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialAnalysisReport {
    pub opportunity_id: uuid::Uuid,
    pub viability_score: f64, // 0-10
    pub projected_revenue: RevenueProjection,
    pub cost_breakdown: CostBreakdown,
    pub roi_analysis: ROIAnalysis,
    pub cash_flow_analysis: CashFlowAnalysis,
    pub break_even_analysis: BreakEvenAnalysis,
    pub funding_requirements: FundingRequirements,
    pub risk_adjusted_return: f64,
    pub recommendation: FinancialRecommendation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevenueProjection {
    pub month_1: f64,
    pub month_3: f64,
    pub month_6: f64,
    pub month_12: f64,
    pub month_24: f64,
    pub annual_recurring_revenue: f64,
    pub customer_lifetime_value: f64,
    pub customer_acquisition_cost: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostBreakdown {
    pub development_costs: f64,
    pub infrastructure_costs: f64,
    pub marketing_costs: f64,
    pub operational_costs: f64,
    pub total_initial_investment: f64,
    pub monthly_burn_rate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ROIAnalysis {
    pub roi_6_months: f64,
    pub roi_12_months: f64,
    pub roi_24_months: f64,
    pub payback_period_months: f64,
    pub internal_rate_of_return: f64,
    pub net_present_value: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CashFlowAnalysis {
    pub initial_cash_required: f64,
    pub monthly_cash_flow: Vec<f64>, // 24 months
    pub cumulative_cash_flow: Vec<f64>,
    pub runway_months: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BreakEvenAnalysis {
    pub break_even_units: f64,
    pub break_even_revenue: f64,
    pub break_even_months: f64,
    pub margin_of_safety: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundingRequirements {
    pub bootstrappable: bool,
    pub minimum_funding_needed: f64,
    pub recommended_funding: f64,
    pub funding_stages: Vec<FundingStage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundingStage {
    pub stage_name: String,
    pub amount: f64,
    pub timeline: String,
    pub purpose: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FinancialRecommendation {
    HighlyViable,
    Viable,
    MarginallyViable,
    NotViable,
}

/// Financial Analysis Agent
pub struct FinancialAnalysisAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl FinancialAnalysisAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "FinancialAnalyzer",
            "Performs deep financial analysis including ROI, cash flow, and break-even analysis",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("financial-analysis");
        agent.add_tag("validation");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Perform comprehensive financial analysis
    pub async fn analyze(&self, opportunity: &Opportunity) -> Result<FinancialAnalysisReport> {
        info!("Performing financial analysis for: {}", opportunity.title);

        // Step 1: Revenue projections
        let revenue_projection = self.project_revenue(opportunity).await?;

        // Step 2: Cost breakdown
        let cost_breakdown = self.analyze_costs(opportunity).await?;

        // Step 3: ROI analysis
        let roi_analysis = self.calculate_roi(&revenue_projection, &cost_breakdown);

        // Step 4: Cash flow analysis
        let cash_flow = self.analyze_cash_flow(&revenue_projection, &cost_breakdown);

        // Step 5: Break-even analysis
        let break_even = self.calculate_break_even(&revenue_projection, &cost_breakdown);

        // Step 6: Funding requirements
        let funding = self.determine_funding_requirements(&cost_breakdown, &cash_flow);

        // Step 7: Calculate viability score
        let viability_score = self.calculate_viability_score(
            &roi_analysis,
            &cash_flow,
            &break_even,
            &funding,
        );

        // Step 8: Risk-adjusted return
        let risk_adjusted_return = roi_analysis.roi_12_months * 0.7; // Simple risk adjustment

        // Step 9: Recommendation
        let recommendation = self.make_recommendation(viability_score, &roi_analysis, &funding);

        let report = FinancialAnalysisReport {
            opportunity_id: opportunity.id,
            viability_score,
            projected_revenue: revenue_projection,
            cost_breakdown,
            roi_analysis,
            cash_flow_analysis: cash_flow,
            break_even_analysis: break_even,
            funding_requirements: funding,
            risk_adjusted_return,
            recommendation,
        };

        info!("Financial analysis complete - Viability: {:.1}/10, Recommendation: {:?}",
            viability_score, recommendation);

        Ok(report)
    }

    /// Project revenue over time
    async fn project_revenue(&self, opportunity: &Opportunity) -> Result<RevenueProjection> {
        debug!("Projecting revenue for opportunity");

        // Use LLM for sophisticated projections
        let prompt = format!(
            "Analyze this business opportunity and provide realistic revenue projections:\n\n\
            Opportunity: {}\n\
            Description: {}\n\
            Domain: {}\n\
            Current Revenue Estimate: ${}/month (mid-range)\n\n\
            Provide monthly revenue projections for months 1, 3, 6, 12, and 24.\n\
            Also estimate:\n\
            - Annual Recurring Revenue (ARR)\n\
            - Customer Lifetime Value (LTV)\n\
            - Customer Acquisition Cost (CAC)\n\n\
            Be realistic and account for ramp-up time, market penetration, and competition.",
            opportunity.title,
            opportunity.description,
            opportunity.domain,
            opportunity.financial_projection.monthly_revenue_mid
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a financial analyst specializing in startup revenue projections. Provide realistic, conservative estimates.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.3),
            max_tokens: Some(2048),
            tools: None,
        };

        let _response = self.llm_client.complete(llm_request).await?;

        // For demo, use algorithmic projection based on initial estimate
        let base_monthly = opportunity.financial_projection.monthly_revenue_mid;

        Ok(RevenueProjection {
            month_1: base_monthly * 0.1,  // 10% of target in month 1
            month_3: base_monthly * 0.3,  // 30% by month 3
            month_6: base_monthly * 0.6,  // 60% by month 6
            month_12: base_monthly * 1.0, // 100% by month 12
            month_24: base_monthly * 1.8, // 180% by month 24 (growth)
            annual_recurring_revenue: base_monthly * 12.0,
            customer_lifetime_value: base_monthly * 24.0, // 2 year LTV
            customer_acquisition_cost: base_monthly * 0.3, // 30% CAC
        })
    }

    /// Analyze cost structure
    async fn analyze_costs(&self, opportunity: &Opportunity) -> Result<CostBreakdown> {
        debug!("Analyzing cost breakdown");

        let dev_cost = opportunity.implementation_estimate.estimated_cost;
        let complexity_multiplier = opportunity.implementation_estimate.complexity_score / 10.0;

        Ok(CostBreakdown {
            development_costs: dev_cost,
            infrastructure_costs: dev_cost * 0.2 * complexity_multiplier,
            marketing_costs: dev_cost * 0.3,
            operational_costs: dev_cost * 0.1,
            total_initial_investment: opportunity.financial_projection.initial_investment,
            monthly_burn_rate: opportunity.financial_projection.monthly_costs,
        })
    }

    /// Calculate ROI metrics
    fn calculate_roi(&self, revenue: &RevenueProjection, costs: &CostBreakdown) -> ROIAnalysis {
        let initial_investment = costs.total_initial_investment;

        // Simple ROI calculations
        let revenue_6m = (revenue.month_1 + revenue.month_3 + revenue.month_6) * 2.0; // Approximate
        let revenue_12m = revenue.annual_recurring_revenue;
        let revenue_24m = revenue.month_24 * 12.0;

        let costs_6m = costs.monthly_burn_rate * 6.0;
        let costs_12m = costs.monthly_burn_rate * 12.0;
        let costs_24m = costs.monthly_burn_rate * 24.0;

        ROIAnalysis {
            roi_6_months: ((revenue_6m - costs_6m - initial_investment) / initial_investment) * 100.0,
            roi_12_months: ((revenue_12m - costs_12m - initial_investment) / initial_investment) * 100.0,
            roi_24_months: ((revenue_24m - costs_24m - initial_investment) / initial_investment) * 100.0,
            payback_period_months: initial_investment / (revenue_12m / 12.0 - costs.monthly_burn_rate),
            internal_rate_of_return: 25.0, // Simplified
            net_present_value: revenue_12m - costs_12m - initial_investment,
        }
    }

    /// Analyze cash flow over 24 months
    fn analyze_cash_flow(&self, revenue: &RevenueProjection, costs: &CostBreakdown) -> CashFlowAnalysis {
        let mut monthly_cash_flow = Vec::new();
        let mut cumulative = Vec::new();
        let mut running_total = -costs.total_initial_investment;

        for month in 1..=24 {
            let monthly_revenue = match month {
                1 => revenue.month_1,
                2..=3 => revenue.month_3,
                4..=6 => revenue.month_6,
                7..=12 => revenue.month_12,
                _ => revenue.month_24,
            };

            let cash_flow = monthly_revenue - costs.monthly_burn_rate;
            monthly_cash_flow.push(cash_flow);

            running_total += cash_flow;
            cumulative.push(running_total);
        }

        // Calculate runway
        let runway = if costs.monthly_burn_rate > 0.0 {
            costs.total_initial_investment / costs.monthly_burn_rate
        } else {
            f64::INFINITY
        };

        CashFlowAnalysis {
            initial_cash_required: costs.total_initial_investment,
            monthly_cash_flow,
            cumulative_cash_flow: cumulative,
            runway_months: runway,
        }
    }

    /// Calculate break-even point
    fn calculate_break_even(&self, revenue: &RevenueProjection, costs: &CostBreakdown) -> BreakEvenAnalysis {
        let monthly_revenue = revenue.month_12;
        let monthly_costs = costs.monthly_burn_rate;
        let initial_investment = costs.total_initial_investment;

        let monthly_profit = monthly_revenue - monthly_costs;
        let break_even_months = if monthly_profit > 0.0 {
            initial_investment / monthly_profit
        } else {
            f64::INFINITY
        };

        BreakEvenAnalysis {
            break_even_units: 100.0, // Simplified
            break_even_revenue: monthly_costs,
            break_even_months,
            margin_of_safety: (monthly_revenue - monthly_costs) / monthly_revenue * 100.0,
        }
    }

    /// Determine funding requirements
    fn determine_funding_requirements(&self, costs: &CostBreakdown, cash_flow: &CashFlowAnalysis) -> FundingRequirements {
        let total_investment = costs.total_initial_investment;
        let bootstrappable = total_investment < 10000.0 && cash_flow.runway_months > 6.0;

        let mut funding_stages = Vec::new();

        if !bootstrappable {
            funding_stages.push(FundingStage {
                stage_name: "Seed".to_string(),
                amount: total_investment * 0.5,
                timeline: "0-3 months".to_string(),
                purpose: "Initial development and launch".to_string(),
            });

            if total_investment > 50000.0 {
                funding_stages.push(FundingStage {
                    stage_name: "Series A".to_string(),
                    amount: total_investment * 0.5,
                    timeline: "6-12 months".to_string(),
                    purpose: "Growth and scaling".to_string(),
                });
            }
        }

        FundingRequirements {
            bootstrappable,
            minimum_funding_needed: if bootstrappable { 0.0 } else { total_investment * 0.5 },
            recommended_funding: total_investment * 1.5, // 50% buffer
            funding_stages,
        }
    }

    /// Calculate overall viability score
    fn calculate_viability_score(
        &self,
        roi: &ROIAnalysis,
        cash_flow: &CashFlowAnalysis,
        break_even: &BreakEvenAnalysis,
        funding: &FundingRequirements,
    ) -> f64 {
        let mut score = 5.0; // Base score

        // ROI contribution (40%)
        if roi.roi_12_months > 100.0 { score += 2.0; }
        else if roi.roi_12_months > 50.0 { score += 1.0; }
        else if roi.roi_12_months < 0.0 { score -= 2.0; }

        // Cash flow contribution (30%)
        if cash_flow.runway_months > 12.0 { score += 1.5; }
        else if cash_flow.runway_months < 3.0 { score -= 1.5; }

        // Break-even contribution (20%)
        if break_even.break_even_months < 6.0 { score += 1.0; }
        else if break_even.break_even_months > 18.0 { score -= 1.0; }

        // Funding contribution (10%)
        if funding.bootstrappable { score += 0.5; }

        score.max(0.0).min(10.0)
    }

    /// Make final recommendation
    fn make_recommendation(
        &self,
        viability_score: f64,
        roi: &ROIAnalysis,
        funding: &FundingRequirements,
    ) -> FinancialRecommendation {
        if viability_score >= 8.0 && roi.roi_12_months > 50.0 {
            FinancialRecommendation::HighlyViable
        } else if viability_score >= 6.0 && roi.roi_12_months > 0.0 {
            FinancialRecommendation::Viable
        } else if viability_score >= 4.0 || (funding.bootstrappable && roi.roi_12_months > -20.0) {
            FinancialRecommendation::MarginallyViable
        } else {
            FinancialRecommendation::NotViable
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_financial_analysis() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = FinancialAnalysisAgent::new(llm);

        let mut opp = Opportunity::new(
            "Test SaaS".to_string(),
            "A test opportunity".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        opp.financial_projection.initial_investment = 5000.0;
        opp.financial_projection.monthly_costs = 200.0;
        opp.financial_projection.monthly_revenue_mid = 1000.0;
        opp.implementation_estimate.estimated_cost = 3000.0;
        opp.implementation_estimate.complexity_score = 5.0;

        let report = agent.analyze(&opp).await.unwrap();

        assert!(report.viability_score > 0.0);
        assert!(report.viability_score <= 10.0);
    }
}
