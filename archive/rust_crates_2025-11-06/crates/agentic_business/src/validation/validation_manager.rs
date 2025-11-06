//! Business Validation Manager - Meta-agent orchestrating comprehensive business validation
//!
//! This meta-agent coordinates 4 validation agents to perform thorough business analysis:
//! - FinancialAnalysisAgent: ROI, cash flow, break-even analysis
//! - TechnicalFeasibilityAgent: Implementation complexity and risks
//! - MarketDemandAgent: Target market and adoption potential
//! - RiskAssessmentAgent: Multi-category risk identification

use super::{
    financial_analysis_agent::{FinancialAnalysisAgent, FinancialAnalysisReport},
    technical_feasibility_agent::{TechnicalFeasibilityAgent, TechnicalFeasibilityReport},
    market_demand_agent::{MarketDemandAgent, MarketDemandReport},
    risk_assessment_agent::{RiskAssessmentAgent, RiskAssessmentReport},
};
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_meta::{MetaAgent, MetaAgentMetrics, WorkflowId};
use agentic_runtime::llm::LlmClient;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug};

/// Comprehensive validation report aggregating all validation dimensions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComprehensiveValidationReport {
    pub opportunity_id: uuid::Uuid,
    pub validation_timestamp: chrono::DateTime<chrono::Utc>,
    pub workflow_id: String,

    // Individual reports
    pub financial_analysis: FinancialAnalysisReport,
    pub technical_feasibility: TechnicalFeasibilityReport,
    pub market_demand: MarketDemandReport,
    pub risk_assessment: RiskAssessmentReport,

    // Aggregated scores
    pub overall_validation_score: f64, // 0-10
    pub confidence_level: f64, // 0-1

    // Final recommendation
    pub recommendation: ValidationRecommendation,
    pub decision_rationale: String,

    // Key insights
    pub strengths: Vec<String>,
    pub weaknesses: Vec<String>,
    pub critical_risks: Vec<String>,
    pub success_factors: Vec<String>,
}

/// Final validation recommendation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValidationRecommendation {
    /// Strong Go - All validation dimensions positive
    StrongGo,
    /// Go - Most dimensions positive, manageable risks
    Go,
    /// Conditional - Proceed with caution, address specific issues
    Conditional,
    /// No Go - Significant issues in multiple dimensions
    NoGo,
}

/// Business Validation Manager - Meta-agent
pub struct BusinessValidationManager {
    agent: Agent,
    workflow_id: WorkflowId,

    // Validation agents
    financial_agent: FinancialAnalysisAgent,
    technical_agent: TechnicalFeasibilityAgent,
    market_agent: MarketDemandAgent,
    risk_agent: RiskAssessmentAgent,

    // Metrics tracking
    metrics: MetaAgentMetrics,

    // LLM client for synthesis
    llm_client: Arc<dyn LlmClient>,
}

impl BusinessValidationManager {
    /// Create a new BusinessValidationManager
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "BusinessValidationManager",
            "Meta-agent orchestrating comprehensive business validation across financial, technical, market, and risk dimensions",
            AgentRole::Supervisor,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("meta-agent");
        agent.add_tag("business");
        agent.add_tag("validation");
        agent.add_tag("supervisor");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self {
            agent,
            workflow_id: WorkflowId::new(),
            financial_agent: FinancialAnalysisAgent::new(llm_client.clone()),
            technical_agent: TechnicalFeasibilityAgent::new(llm_client.clone()),
            market_agent: MarketDemandAgent::new(llm_client.clone()),
            risk_agent: RiskAssessmentAgent::new(llm_client.clone()),
            metrics: MetaAgentMetrics::default(),
            llm_client,
        }
    }

    /// Perform comprehensive validation of an opportunity
    ///
    /// This orchestrates 4 validation agents in parallel:
    /// 1. Financial Analysis - ROI, cash flow, funding requirements
    /// 2. Technical Feasibility - Implementation complexity, tech stack, risks
    /// 3. Market Demand - Target market, customer segments, adoption potential
    /// 4. Risk Assessment - Multi-category risk identification and mitigation
    pub async fn validate(&mut self, opportunity: &Opportunity) -> Result<ComprehensiveValidationReport> {
        info!("🎯 Starting comprehensive validation for: {}", opportunity.title);
        let start_time = std::time::Instant::now();

        // Execute all 4 validation agents in parallel
        let (financial_result, technical_result, market_result, risk_result) = tokio::join!(
            self.financial_agent.analyze(opportunity),
            self.technical_agent.analyze(opportunity),
            self.market_agent.analyze(opportunity),
            self.risk_agent.analyze(opportunity),
        );

        // Check for errors
        let financial_report = financial_result?;
        let technical_report = technical_result?;
        let market_report = market_result?;
        let risk_report = risk_result?;

        info!("✅ All 4 validation agents completed successfully");

        // Calculate overall validation score
        let overall_score = self.calculate_overall_score(
            &financial_report,
            &technical_report,
            &market_report,
            &risk_report,
        );

        // Calculate confidence level
        let confidence = self.calculate_confidence_level(
            &financial_report,
            &technical_report,
            &market_report,
            &risk_report,
        );

        // Extract key insights
        let strengths = self.extract_strengths(
            &financial_report,
            &technical_report,
            &market_report,
            &risk_report,
        );

        let weaknesses = self.extract_weaknesses(
            &financial_report,
            &technical_report,
            &market_report,
            &risk_report,
        );

        let critical_risks = self.extract_critical_risks(&risk_report);

        let success_factors = self.identify_success_factors(
            &financial_report,
            &technical_report,
            &market_report,
        );

        // Make final recommendation
        let recommendation = self.make_recommendation(
            overall_score,
            &financial_report,
            &technical_report,
            &market_report,
            &risk_report,
        );

        // Generate decision rationale
        let decision_rationale = self.generate_decision_rationale(
            overall_score,
            recommendation,
            &strengths,
            &weaknesses,
            &critical_risks,
        );

        // Update metrics
        let elapsed = start_time.elapsed();
        self.metrics.tasks_executed += 1;
        self.metrics.avg_execution_time_ms =
            (self.metrics.avg_execution_time_ms * (self.metrics.tasks_executed - 1) as f64
            + elapsed.as_millis() as f64) / self.metrics.tasks_executed as f64;

        let report = ComprehensiveValidationReport {
            opportunity_id: opportunity.id,
            validation_timestamp: chrono::Utc::now(),
            workflow_id: self.workflow_id.to_string(),
            financial_analysis: financial_report,
            technical_feasibility: technical_report,
            market_demand: market_report,
            risk_assessment: risk_report,
            overall_validation_score: overall_score,
            confidence_level: confidence,
            recommendation,
            decision_rationale,
            strengths,
            weaknesses,
            critical_risks,
            success_factors,
        };

        info!("🎉 Validation complete - Score: {:.1}/10, Recommendation: {:?}, Confidence: {:.0}%",
            overall_score, recommendation, confidence * 100.0);

        Ok(report)
    }

    /// Calculate overall validation score (weighted average)
    fn calculate_overall_score(
        &self,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
        risk: &RiskAssessmentReport,
    ) -> f64 {
        // Weighted scoring:
        // Financial: 30% - Most critical for business viability
        // Technical: 25% - Can we build it?
        // Market: 30% - Is there demand?
        // Risk: 15% - Risk adjustment (inverse)

        let financial_weight = 0.30;
        let technical_weight = 0.25;
        let market_weight = 0.30;
        let risk_weight = 0.15;

        let risk_score = 10.0 - risk.overall_risk_score; // Invert risk (higher risk = lower score)

        let weighted_score =
            (financial.viability_score * financial_weight) +
            (technical.feasibility_score * technical_weight) +
            (market.demand_score * market_weight) +
            (risk_score * risk_weight);

        weighted_score.max(0.0).min(10.0)
    }

    /// Calculate confidence level based on consistency across dimensions
    fn calculate_confidence_level(
        &self,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
        risk: &RiskAssessmentReport,
    ) -> f64 {
        let scores = vec![
            financial.viability_score,
            technical.feasibility_score,
            market.demand_score,
            10.0 - risk.overall_risk_score,
        ];

        // Calculate standard deviation
        let mean: f64 = scores.iter().sum::<f64>() / scores.len() as f64;
        let variance: f64 = scores.iter()
            .map(|score| (score - mean).powi(2))
            .sum::<f64>() / scores.len() as f64;
        let std_dev = variance.sqrt();

        // Lower std deviation = higher confidence
        // Max std deviation would be ~5 (scores vary 0-10)
        let confidence = (1.0 - (std_dev / 5.0)).max(0.0).min(1.0);

        confidence
    }

    /// Extract key strengths from all reports
    fn extract_strengths(
        &self,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
        _risk: &RiskAssessmentReport,
    ) -> Vec<String> {
        let mut strengths = Vec::new();

        // Financial strengths
        if financial.roi_analysis.roi_12_months > 100.0 {
            strengths.push(format!("Strong ROI: {:.0}% in 12 months", financial.roi_analysis.roi_12_months));
        }
        if financial.break_even_analysis.break_even_months < 6.0 {
            strengths.push(format!("Fast break-even: {:.1} months", financial.break_even_analysis.break_even_months));
        }
        if financial.funding_requirements.bootstrappable {
            strengths.push("Bootstrappable - minimal funding needed".to_string());
        }

        // Technical strengths
        if technical.feasibility_score >= 8.0 {
            strengths.push("Highly technically feasible".to_string());
        }
        if technical.implementation_complexity.estimated_team_size <= 2 {
            strengths.push("Small team sufficient for implementation".to_string());
        }

        // Market strengths
        if market.demand_score >= 8.0 {
            strengths.push("Strong market demand validated".to_string());
        }
        if market.target_market.total_addressable_market > 100_000_000.0 {
            strengths.push(format!("Large TAM: ${:.0}M", market.target_market.total_addressable_market / 1_000_000.0));
        }
        if matches!(market.market_trends.overall_trend, super::market_demand_agent::TrendDirection::Growing) {
            strengths.push("Growing market with positive trends".to_string());
        }

        strengths
    }

    /// Extract key weaknesses from all reports
    fn extract_weaknesses(
        &self,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
        risk: &RiskAssessmentReport,
    ) -> Vec<String> {
        let mut weaknesses = Vec::new();

        // Financial weaknesses
        if financial.roi_analysis.roi_12_months < 0.0 {
            weaknesses.push("Negative ROI projected in 12 months".to_string());
        }
        if financial.cash_flow_analysis.runway_months < 6.0 {
            weaknesses.push(format!("Short runway: {:.1} months", financial.cash_flow_analysis.runway_months));
        }
        if !financial.funding_requirements.bootstrappable && financial.funding_requirements.minimum_funding_needed > 50000.0 {
            weaknesses.push(format!("High funding requirement: ${:.0}K", financial.funding_requirements.minimum_funding_needed / 1000.0));
        }

        // Technical weaknesses
        if technical.implementation_complexity.overall_complexity > 7.0 {
            weaknesses.push("High implementation complexity".to_string());
        }
        if technical.implementation_complexity.estimated_team_size > 3 {
            weaknesses.push("Large team required".to_string());
        }

        // Market weaknesses
        if market.demand_score < 5.0 {
            weaknesses.push("Weak market demand".to_string());
        }
        if market.competitive_demand.differentiation_strength < 5.0 {
            weaknesses.push("Low competitive differentiation".to_string());
        }

        // Risk weaknesses
        if risk.overall_risk_score > 7.0 {
            weaknesses.push("High overall risk score".to_string());
        }

        weaknesses
    }

    /// Extract critical risks requiring immediate attention
    fn extract_critical_risks(&self, risk: &RiskAssessmentReport) -> Vec<String> {
        use super::risk_assessment_agent::RiskLevel;

        risk.risk_categories
            .iter()
            .flat_map(|category| &category.risks)
            .filter(|risk| matches!(risk.risk_level, RiskLevel::Critical | RiskLevel::High))
            .map(|risk| format!("{}: {}", risk.risk_name, risk.description))
            .collect()
    }

    /// Identify key success factors
    fn identify_success_factors(
        &self,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
    ) -> Vec<String> {
        let mut factors = Vec::new();

        // Financial success factors
        if financial.roi_analysis.payback_period_months < 12.0 {
            factors.push("Quick payback period enables rapid reinvestment".to_string());
        }

        // Technical success factors
        if technical.scalability_assessment.scalability_score > 7.0 {
            factors.push("Strong scalability architecture for growth".to_string());
        }

        // Market success factors
        if market.adoption_forecast.early_adopters_count > 1000 {
            factors.push("Sizable early adopter base for initial traction".to_string());
        }
        if market.customer_segments.iter().any(|s| matches!(s.segment_priority, super::market_demand_agent::Priority::Critical)) {
            factors.push("Critical customer pain points create strong demand".to_string());
        }

        factors
    }

    /// Make final Go/No-Go recommendation
    fn make_recommendation(
        &self,
        overall_score: f64,
        financial: &FinancialAnalysisReport,
        technical: &TechnicalFeasibilityReport,
        market: &MarketDemandReport,
        risk: &RiskAssessmentReport,
    ) -> ValidationRecommendation {
        use super::financial_analysis_agent::FinancialRecommendation;
        use super::technical_feasibility_agent::TechnicalRecommendation;
        use super::market_demand_agent::DemandRecommendation;
        use super::risk_assessment_agent::RiskRecommendation;

        // Check for deal-breakers
        if matches!(financial.recommendation, FinancialRecommendation::NotViable) {
            return ValidationRecommendation::NoGo;
        }
        if matches!(technical.recommendation, TechnicalRecommendation::NotFeasible) {
            return ValidationRecommendation::NoGo;
        }
        if matches!(market.recommendation, DemandRecommendation::InsufficientDemand) {
            return ValidationRecommendation::NoGo;
        }
        if matches!(risk.recommendation, RiskRecommendation::Unacceptable) {
            return ValidationRecommendation::NoGo;
        }

        // Strong Go criteria
        if overall_score >= 8.0
            && matches!(financial.recommendation, FinancialRecommendation::HighlyViable)
            && matches!(market.recommendation, DemandRecommendation::StrongDemand) {
            return ValidationRecommendation::StrongGo;
        }

        // Go criteria
        if overall_score >= 6.5
            && financial.roi_analysis.roi_12_months > 50.0
            && market.demand_score >= 6.0
            && risk.overall_risk_score < 7.0 {
            return ValidationRecommendation::Go;
        }

        // Conditional criteria
        if overall_score >= 5.0 {
            return ValidationRecommendation::Conditional;
        }

        // Default to No Go
        ValidationRecommendation::NoGo
    }

    /// Generate detailed decision rationale
    fn generate_decision_rationale(
        &self,
        overall_score: f64,
        recommendation: ValidationRecommendation,
        strengths: &[String],
        weaknesses: &[String],
        critical_risks: &[String],
    ) -> String {
        let rec_text = match recommendation {
            ValidationRecommendation::StrongGo => "Strong Go - Highly recommended",
            ValidationRecommendation::Go => "Go - Recommended with standard execution",
            ValidationRecommendation::Conditional => "Conditional - Proceed with caution",
            ValidationRecommendation::NoGo => "No Go - Not recommended",
        };

        let mut rationale = format!(
            "Overall validation score: {:.1}/10. Recommendation: {}.\n\n",
            overall_score, rec_text
        );

        if !strengths.is_empty() {
            rationale.push_str("Key Strengths:\n");
            for strength in strengths {
                rationale.push_str(&format!("  • {}\n", strength));
            }
            rationale.push('\n');
        }

        if !weaknesses.is_empty() {
            rationale.push_str("Key Weaknesses:\n");
            for weakness in weaknesses {
                rationale.push_str(&format!("  • {}\n", weakness));
            }
            rationale.push('\n');
        }

        if !critical_risks.is_empty() {
            rationale.push_str("Critical Risks:\n");
            for risk in critical_risks {
                rationale.push_str(&format!("  • {}\n", risk));
            }
        }

        rationale
    }

    /// Get current workflow ID
    pub fn workflow_id(&self) -> &WorkflowId {
        &self.workflow_id
    }

    /// Get validation metrics
    pub fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }
}

impl MetaAgent for BusinessValidationManager {
    fn agent(&self) -> &Agent {
        &self.agent
    }

    fn workflow_id(&self) -> &WorkflowId {
        &self.workflow_id
    }

    fn metrics(&self) -> &MetaAgentMetrics {
        &self.metrics
    }

    async fn self_analyze(&self) -> Result<String> {
        let analysis = format!(
            "BusinessValidationManager Self-Analysis:\n\
            - Workflow ID: {}\n\
            - Validations Executed: {}\n\
            - Average Execution Time: {:.2}ms\n\
            - Agents Managed: 4 (Financial, Technical, Market, Risk)\n\
            - Success Rate: {:.1}%\n\
            \n\
            Agent Capabilities:\n\
            - Financial Analysis: ROI, cash flow, break-even, funding\n\
            - Technical Feasibility: Complexity, risks, scalability\n\
            - Market Demand: TAM/SAM/SOM, segments, adoption\n\
            - Risk Assessment: 6 risk categories with mitigation\n\
            \n\
            Validation Dimensions:\n\
            - Overall Score: Weighted average (Financial 30%, Market 30%, Technical 25%, Risk 15%)\n\
            - Confidence Level: Based on score consistency\n\
            - Recommendation: Strong Go, Go, Conditional, No Go\n\
            \n\
            Performance Insights:\n\
            - Parallel execution of all 4 agents for speed\n\
            - Comprehensive synthesis of multi-dimensional analysis\n\
            - Decision rationale with strengths, weaknesses, risks",
            self.workflow_id,
            self.metrics.tasks_executed,
            self.metrics.avg_execution_time_ms,
            self.metrics.creation_success_rate * 100.0
        );

        Ok(analysis)
    }

    async fn self_improve(&mut self) -> Result<String> {
        debug!("BusinessValidationManager analyzing performance for improvements");

        let improvements = vec![
            "Consider adding more validation agents for deeper analysis",
            "Implement adaptive weighting based on opportunity type",
            "Add learning from past validation outcomes",
            "Optimize parallel execution scheduling",
        ];

        Ok(improvements.join("\n"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_comprehensive_validation() {
        let llm = Arc::new(MockLlmClient::new());
        let mut manager = BusinessValidationManager::new(llm);

        let opp = Opportunity::new(
            "Test SaaS Product".to_string(),
            "A test opportunity for validation".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let report = manager.validate(&opp).await.unwrap();

        assert_eq!(report.opportunity_id, opp.id);
        assert!(report.overall_validation_score >= 0.0);
        assert!(report.overall_validation_score <= 10.0);
        assert!(report.confidence_level >= 0.0);
        assert!(report.confidence_level <= 1.0);
    }

    #[tokio::test]
    async fn test_meta_agent_self_analysis() {
        let llm = Arc::new(MockLlmClient::new());
        let manager = BusinessValidationManager::new(llm);

        let analysis = manager.self_analyze().await.unwrap();
        assert!(analysis.contains("BusinessValidationManager"));
        assert!(analysis.contains("Financial"));
        assert!(analysis.contains("Technical"));
    }
}
