//! Risk Assessment Agent - Identifies and analyzes business and operational risks

use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug};

/// Risk assessment report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskAssessmentReport {
    pub opportunity_id: uuid::Uuid,
    pub overall_risk_score: f64, // 0-10, higher is more risky
    pub risk_categories: Vec<RiskCategory>,
    pub mitigation_strategies: Vec<MitigationStrategy>,
    pub risk_matrix: RiskMatrix,
    pub contingency_plans: Vec<ContingencyPlan>,
    pub recommendation: RiskRecommendation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskCategory {
    pub category_name: String,
    pub risks: Vec<BusinessRisk>,
    pub category_risk_level: RiskLevel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BusinessRisk {
    pub risk_id: String,
    pub risk_name: String,
    pub description: String,
    pub category: String,
    pub probability: f64, // 0-1
    pub impact: f64, // 0-10
    pub risk_score: f64, // probability * impact
    pub risk_level: RiskLevel,
    pub indicators: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MitigationStrategy {
    pub risk_id: String,
    pub strategy: String,
    pub cost: f64,
    pub timeline: String,
    pub effectiveness: f64, // 0-1
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskMatrix {
    pub high_probability_high_impact: Vec<String>,
    pub high_probability_low_impact: Vec<String>,
    pub low_probability_high_impact: Vec<String>,
    pub low_probability_low_impact: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContingencyPlan {
    pub scenario: String,
    pub trigger_conditions: Vec<String>,
    pub action_plan: Vec<String>,
    pub estimated_cost: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RiskRecommendation {
    Acceptable,
    Manageable,
    HighRisk,
    Unacceptable,
}

/// Risk Assessment Agent
pub struct RiskAssessmentAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl RiskAssessmentAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "RiskAssessmentAnalyzer",
            "Identifies business and operational risks with mitigation strategies",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("risk-analysis");
        agent.add_tag("validation");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Perform comprehensive risk assessment
    pub async fn analyze(&self, opportunity: &Opportunity) -> Result<RiskAssessmentReport> {
        info!("Performing risk assessment for: {}", opportunity.title);

        // Identify risks across all categories
        let risk_categories = self.identify_all_risks(opportunity).await?;

        // Create risk matrix
        let risk_matrix = self.create_risk_matrix(&risk_categories);

        // Develop mitigation strategies
        let mitigation_strategies = self.develop_mitigation_strategies(&risk_categories);

        // Create contingency plans
        let contingency_plans = self.create_contingency_plans(&risk_categories);

        // Calculate overall risk score
        let overall_risk_score = self.calculate_overall_risk_score(&risk_categories);

        // Make recommendation
        let recommendation = self.make_recommendation(overall_risk_score, &risk_matrix);

        Ok(RiskAssessmentReport {
            opportunity_id: opportunity.id,
            overall_risk_score,
            risk_categories,
            mitigation_strategies,
            risk_matrix,
            contingency_plans,
            recommendation,
        })
    }

    async fn identify_all_risks(&self, opportunity: &Opportunity) -> Result<Vec<RiskCategory>> {
        let mut categories = Vec::new();

        // Market Risks
        categories.push(self.identify_market_risks(opportunity).await?);

        // Financial Risks
        categories.push(self.identify_financial_risks(opportunity).await?);

        // Operational Risks
        categories.push(self.identify_operational_risks(opportunity).await?);

        // Technical Risks
        categories.push(self.identify_technical_risks(opportunity).await?);

        // Competitive Risks
        categories.push(self.identify_competitive_risks(opportunity).await?);

        // Regulatory/Legal Risks
        categories.push(self.identify_regulatory_risks(opportunity).await?);

        Ok(categories)
    }

    async fn identify_market_risks(&self, opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        // Market timing risk
        risks.push(BusinessRisk {
            risk_id: "MKT-001".to_string(),
            risk_name: "Market Timing Risk".to_string(),
            description: "Market may not be ready for this solution".to_string(),
            category: "Market".to_string(),
            probability: if opportunity.scores.market_size < 5.0 { 0.6 } else { 0.3 },
            impact: 8.0,
            risk_score: 0.0, // Calculated below
            risk_level: RiskLevel::Medium,
            indicators: vec!["Low market demand signals".to_string()],
        });

        // Calculate risk scores and levels
        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Market Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    async fn identify_financial_risks(&self, opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        risks.push(BusinessRisk {
            risk_id: "FIN-001".to_string(),
            risk_name: "Cash Flow Risk".to_string(),
            description: "Insufficient cash flow to sustain operations".to_string(),
            category: "Financial".to_string(),
            probability: if opportunity.financial_projection.initial_investment > 20000.0 { 0.5 } else { 0.2 },
            impact: 9.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["High burn rate".to_string(), "Long payback period".to_string()],
        });

        risks.push(BusinessRisk {
            risk_id: "FIN-002".to_string(),
            risk_name: "Revenue Shortfall".to_string(),
            description: "Actual revenue falls short of projections".to_string(),
            category: "Financial".to_string(),
            probability: 0.4,
            impact: 7.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["Optimistic projections".to_string()],
        });

        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Financial Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    async fn identify_operational_risks(&self, _opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        risks.push(BusinessRisk {
            risk_id: "OPS-001".to_string(),
            risk_name: "Team Capacity Risk".to_string(),
            description: "Unable to hire or retain qualified team members".to_string(),
            category: "Operational".to_string(),
            probability: 0.3,
            impact: 6.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["Tight labor market".to_string()],
        });

        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Operational Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    async fn identify_technical_risks(&self, opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        let complexity = opportunity.implementation_estimate.complexity_score;

        risks.push(BusinessRisk {
            risk_id: "TECH-001".to_string(),
            risk_name: "Implementation Complexity".to_string(),
            description: "Technical challenges exceed initial estimates".to_string(),
            category: "Technical".to_string(),
            probability: if complexity > 7.0 { 0.6 } else { 0.3 },
            impact: 7.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["High complexity score".to_string()],
        });

        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Technical Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    async fn identify_competitive_risks(&self, opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        risks.push(BusinessRisk {
            risk_id: "COMP-001".to_string(),
            risk_name: "Competitive Response".to_string(),
            description: "Established competitors react aggressively".to_string(),
            category: "Competitive".to_string(),
            probability: if opportunity.scores.competition > 7.0 { 0.7 } else { 0.4 },
            impact: 6.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["High competition score".to_string()],
        });

        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Competitive Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    async fn identify_regulatory_risks(&self, _opportunity: &Opportunity) -> Result<RiskCategory> {
        let mut risks = Vec::new();

        risks.push(BusinessRisk {
            risk_id: "REG-001".to_string(),
            risk_name: "Regulatory Compliance".to_string(),
            description: "New regulations impact business model".to_string(),
            category: "Regulatory".to_string(),
            probability: 0.2,
            impact: 7.0,
            risk_score: 0.0,
            risk_level: RiskLevel::Low,
            indicators: vec!["Regulatory uncertainty".to_string()],
        });

        for risk in &mut risks {
            risk.risk_score = risk.probability * risk.impact;
            risk.risk_level = Self::calculate_risk_level(risk.risk_score);
        }

        let category_level = risks.iter().map(|r| r.risk_level).max().unwrap_or(RiskLevel::Low);

        Ok(RiskCategory {
            category_name: "Regulatory Risks".to_string(),
            risks,
            category_risk_level: category_level,
        })
    }

    fn calculate_risk_level(risk_score: f64) -> RiskLevel {
        if risk_score >= 7.0 {
            RiskLevel::Critical
        } else if risk_score >= 5.0 {
            RiskLevel::High
        } else if risk_score >= 3.0 {
            RiskLevel::Medium
        } else {
            RiskLevel::Low
        }
    }

    fn create_risk_matrix(&self, categories: &[RiskCategory]) -> RiskMatrix {
        let mut high_prob_high_impact = Vec::new();
        let mut high_prob_low_impact = Vec::new();
        let mut low_prob_high_impact = Vec::new();
        let mut low_prob_low_impact = Vec::new();

        for category in categories {
            for risk in &category.risks {
                let risk_id = risk.risk_id.clone();

                if risk.probability > 0.5 && risk.impact > 6.0 {
                    high_prob_high_impact.push(risk_id);
                } else if risk.probability > 0.5 {
                    high_prob_low_impact.push(risk_id);
                } else if risk.impact > 6.0 {
                    low_prob_high_impact.push(risk_id);
                } else {
                    low_prob_low_impact.push(risk_id);
                }
            }
        }

        RiskMatrix {
            high_probability_high_impact,
            high_probability_low_impact,
            low_probability_high_impact,
            low_probability_low_impact,
        }
    }

    fn develop_mitigation_strategies(&self, categories: &[RiskCategory]) -> Vec<MitigationStrategy> {
        let mut strategies = Vec::new();

        for category in categories {
            for risk in &category.risks {
                if risk.risk_level >= RiskLevel::Medium {
                    strategies.push(MitigationStrategy {
                        risk_id: risk.risk_id.clone(),
                        strategy: format!("Mitigate {} through careful planning and monitoring", risk.risk_name),
                        cost: risk.impact * 100.0,
                        timeline: "Ongoing".to_string(),
                        effectiveness: 0.7,
                    });
                }
            }
        }

        strategies
    }

    fn create_contingency_plans(&self, categories: &[RiskCategory]) -> Vec<ContingencyPlan> {
        let mut plans = Vec::new();

        // Create contingency for high-risk items
        for category in categories {
            if category.category_risk_level >= RiskLevel::High {
                plans.push(ContingencyPlan {
                    scenario: format!("High risk in {} category", category.category_name),
                    trigger_conditions: vec!["Risk materializes".to_string()],
                    action_plan: vec!["Pivot strategy".to_string(), "Seek additional funding".to_string()],
                    estimated_cost: 5000.0,
                });
            }
        }

        plans
    }

    fn calculate_overall_risk_score(&self, categories: &[RiskCategory]) -> f64 {
        let total_score: f64 = categories
            .iter()
            .flat_map(|c| &c.risks)
            .map(|r| r.risk_score)
            .sum();

        let risk_count = categories.iter().flat_map(|c| &c.risks).count() as f64;

        if risk_count > 0.0 {
            (total_score / risk_count).min(10.0)
        } else {
            0.0
        }
    }

    fn make_recommendation(&self, overall_risk_score: f64, matrix: &RiskMatrix) -> RiskRecommendation {
        let critical_risks = matrix.high_probability_high_impact.len();

        if critical_risks > 2 || overall_risk_score > 7.0 {
            RiskRecommendation::Unacceptable
        } else if critical_risks > 0 || overall_risk_score > 5.0 {
            RiskRecommendation::HighRisk
        } else if overall_risk_score > 3.0 {
            RiskRecommendation::Manageable
        } else {
            RiskRecommendation::Acceptable
        }
    }
}
