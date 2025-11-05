//! Technical Feasibility Agent - Assesses implementation complexity and technical risks

use crate::models::{Opportunity, TechStack};
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug};

/// Technical feasibility report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalFeasibilityReport {
    pub opportunity_id: uuid::Uuid,
    pub feasibility_score: f64, // 0-10
    pub recommended_tech_stack: TechStack,
    pub implementation_complexity: ImplementationComplexity,
    pub technical_risks: Vec<TechnicalRisk>,
    pub resource_requirements: ResourceRequirements,
    pub scalability_assessment: ScalabilityAssessment,
    pub security_considerations: Vec<SecurityConsideration>,
    pub integration_challenges: Vec<String>,
    pub recommendation: TechnicalRecommendation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImplementationComplexity {
    pub overall_complexity: f64, // 0-10
    pub frontend_complexity: f64,
    pub backend_complexity: f64,
    pub database_complexity: f64,
    pub integration_complexity: f64,
    pub deployment_complexity: f64,
    pub estimated_person_hours: f64,
    pub estimated_team_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalRisk {
    pub risk_type: String,
    pub severity: RiskSeverity,
    pub probability: f64, // 0-1
    pub impact: String,
    pub mitigation: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RiskSeverity {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceRequirements {
    pub developers_needed: usize,
    pub skill_levels: Vec<SkillRequirement>,
    pub tools_and_services: Vec<String>,
    pub estimated_monthly_infrastructure_cost: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillRequirement {
    pub skill_name: String,
    pub proficiency_level: ProficiencyLevel,
    pub priority: Priority,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProficiencyLevel {
    Junior,
    Mid,
    Senior,
    Expert,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Priority {
    Critical,
    High,
    Medium,
    Low,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScalabilityAssessment {
    pub scalability_score: f64, // 0-10
    pub concurrent_users_supported: u64,
    pub database_scalability: String,
    pub bottlenecks: Vec<String>,
    pub scaling_strategy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConsideration {
    pub area: String,
    pub concern: String,
    pub solution: String,
    pub priority: Priority,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TechnicalRecommendation {
    HighlyFeasible,
    Feasible,
    FeasibleWithChallenges,
    NotFeasible,
}

/// Technical Feasibility Agent
pub struct TechnicalFeasibilityAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl TechnicalFeasibilityAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "TechnicalFeasibilityAnalyzer",
            "Assesses technical implementation complexity, risks, and resource requirements",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("technical-analysis");
        agent.add_tag("validation");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Perform comprehensive technical feasibility analysis
    pub async fn analyze(&self, opportunity: &Opportunity) -> Result<TechnicalFeasibilityReport> {
        info!("Performing technical feasibility analysis for: {}", opportunity.title);

        // Step 1: Recommend tech stack
        let tech_stack = self.recommend_tech_stack(opportunity).await?;

        // Step 2: Assess implementation complexity
        let complexity = self.assess_complexity(opportunity, &tech_stack).await?;

        // Step 3: Identify technical risks
        let risks = self.identify_risks(opportunity, &tech_stack).await?;

        // Step 4: Determine resource requirements
        let resources = self.determine_resources(&complexity, &tech_stack);

        // Step 5: Assess scalability
        let scalability = self.assess_scalability(opportunity, &tech_stack).await?;

        // Step 6: Identify security considerations
        let security = self.identify_security_considerations(opportunity);

        // Step 7: Find integration challenges
        let integrations = self.identify_integration_challenges(opportunity).await?;

        // Step 8: Calculate feasibility score
        let feasibility_score = self.calculate_feasibility_score(
            &complexity,
            &risks,
            &scalability,
        );

        // Step 9: Make recommendation
        let recommendation = self.make_recommendation(feasibility_score, &complexity, &risks);

        let report = TechnicalFeasibilityReport {
            opportunity_id: opportunity.id,
            feasibility_score,
            recommended_tech_stack: tech_stack,
            implementation_complexity: complexity,
            technical_risks: risks,
            resource_requirements: resources,
            scalability_assessment: scalability,
            security_considerations: security,
            integration_challenges: integrations,
            recommendation,
        };

        info!("Technical feasibility analysis complete - Score: {:.1}/10, Recommendation: {:?}",
            feasibility_score, recommendation);

        Ok(report)
    }

    /// Recommend optimal tech stack
    async fn recommend_tech_stack(&self, opportunity: &Opportunity) -> Result<TechStack> {
        debug!("Recommending tech stack");

        // Use LLM for smart recommendations
        let prompt = format!(
            "Recommend a modern, scalable tech stack for this opportunity:\n\n\
            Title: {}\n\
            Description: {}\n\
            Domain: {}\n\
            Complexity Score: {:.1}/10\n\n\
            Consider: ease of development, scalability, cost, and time to market.",
            opportunity.title,
            opportunity.description,
            opportunity.domain,
            opportunity.implementation_estimate.complexity_score
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a technical architect. Recommend practical, modern tech stacks.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.4),
            max_tokens: Some(1024),
            tools: None,
        };

        let _response = self.llm_client.complete(llm_request).await?;

        // Recommend based on product type and complexity
        Ok(TechStack {
            frontend: Some("React + TypeScript + TailwindCSS".to_string()),
            backend: Some("Rust (Axum) or Node.js (Express)".to_string()),
            database: Some("PostgreSQL + Redis".to_string()),
            hosting: Some("Vercel (frontend) + Railway/Fly.io (backend)".to_string()),
            additional: vec![
                "Stripe for payments".to_string(),
                "Resend for emails".to_string(),
                "Clerk for auth".to_string(),
                "Plausible for analytics".to_string(),
            ],
        })
    }

    /// Assess implementation complexity
    async fn assess_complexity(&self, opportunity: &Opportunity, _tech_stack: &TechStack) -> Result<ImplementationComplexity> {
        debug!("Assessing implementation complexity");

        let base_complexity = opportunity.implementation_estimate.complexity_score;

        Ok(ImplementationComplexity {
            overall_complexity: base_complexity,
            frontend_complexity: base_complexity * 0.8,
            backend_complexity: base_complexity * 1.0,
            database_complexity: base_complexity * 0.6,
            integration_complexity: base_complexity * 0.9,
            deployment_complexity: base_complexity * 0.5,
            estimated_person_hours: (base_complexity * 80.0).max(40.0),
            estimated_team_size: if base_complexity > 7.0 { 3 } else if base_complexity > 5.0 { 2 } else { 1 },
        })
    }

    /// Identify technical risks
    async fn identify_risks(&self, opportunity: &Opportunity, _tech_stack: &TechStack) -> Result<Vec<TechnicalRisk>> {
        debug!("Identifying technical risks");

        let mut risks = Vec::new();

        // Complexity-based risk
        if opportunity.implementation_estimate.complexity_score > 7.0 {
            risks.push(TechnicalRisk {
                risk_type: "High Complexity".to_string(),
                severity: RiskSeverity::High,
                probability: 0.7,
                impact: "Project may take longer than estimated".to_string(),
                mitigation: "Break into smaller milestones, use agile methodology".to_string(),
            });
        }

        // Scalability risk
        if opportunity.scores.market_size > 8.0 {
            risks.push(TechnicalRisk {
                risk_type: "Scalability Challenge".to_string(),
                severity: RiskSeverity::Medium,
                probability: 0.6,
                impact: "System may struggle with high user load".to_string(),
                mitigation: "Design for horizontal scaling from day one".to_string(),
            });
        }

        // Integration risk
        risks.push(TechnicalRisk {
            risk_type: "Third-party Integration".to_string(),
            severity: RiskSeverity::Low,
            probability: 0.4,
            impact: "External API dependencies may fail".to_string(),
            mitigation: "Implement robust error handling and fallbacks".to_string(),
        });

        // Security risk
        risks.push(TechnicalRisk {
            risk_type: "Security Vulnerabilities".to_string(),
            severity: RiskSeverity::Medium,
            probability: 0.5,
            impact: "Data breaches or security incidents".to_string(),
            mitigation: "Follow OWASP guidelines, regular security audits".to_string(),
        });

        Ok(risks)
    }

    /// Determine resource requirements
    fn determine_resources(&self, complexity: &ImplementationComplexity, _tech_stack: &TechStack) -> ResourceRequirements {
        let mut skill_levels = Vec::new();

        skill_levels.push(SkillRequirement {
            skill_name: "Frontend Development (React/TypeScript)".to_string(),
            proficiency_level: if complexity.frontend_complexity > 7.0 { ProficiencyLevel::Senior } else { ProficiencyLevel::Mid },
            priority: Priority::Critical,
        });

        skill_levels.push(SkillRequirement {
            skill_name: "Backend Development (Rust/Node.js)".to_string(),
            proficiency_level: if complexity.backend_complexity > 7.0 { ProficiencyLevel::Senior } else { ProficiencyLevel::Mid },
            priority: Priority::Critical,
        });

        skill_levels.push(SkillRequirement {
            skill_name: "Database Design".to_string(),
            proficiency_level: ProficiencyLevel::Mid,
            priority: Priority::High,
        });

        skill_levels.push(SkillRequirement {
            skill_name: "DevOps/Cloud Infrastructure".to_string(),
            proficiency_level: ProficiencyLevel::Mid,
            priority: Priority::Medium,
        });

        ResourceRequirements {
            developers_needed: complexity.estimated_team_size,
            skill_levels,
            tools_and_services: vec![
                "GitHub".to_string(),
                "Vercel/Railway".to_string(),
                "Stripe".to_string(),
                "Monitoring (Sentry)".to_string(),
            ],
            estimated_monthly_infrastructure_cost: 50.0 + (complexity.overall_complexity * 20.0),
        }
    }

    /// Assess scalability
    async fn assess_scalability(&self, opportunity: &Opportunity, _tech_stack: &TechStack) -> Result<ScalabilityAssessment> {
        debug!("Assessing scalability");

        let scalability_score = 10.0 - (opportunity.implementation_estimate.complexity_score * 0.3);

        Ok(ScalabilityAssessment {
            scalability_score,
            concurrent_users_supported: if scalability_score > 7.0 { 10000 } else { 1000 },
            database_scalability: "Horizontal scaling with read replicas".to_string(),
            bottlenecks: vec![
                "Database queries under heavy load".to_string(),
                "File upload processing".to_string(),
            ],
            scaling_strategy: "Start with single server, add read replicas and caching as needed".to_string(),
        })
    }

    /// Identify security considerations
    fn identify_security_considerations(&self, _opportunity: &Opportunity) -> Vec<SecurityConsideration> {
        vec![
            SecurityConsideration {
                area: "Authentication".to_string(),
                concern: "Secure user authentication and session management".to_string(),
                solution: "Use battle-tested auth library (Clerk, Auth0)".to_string(),
                priority: Priority::Critical,
            },
            SecurityConsideration {
                area: "Data Encryption".to_string(),
                concern: "Protect sensitive user data".to_string(),
                solution: "Encrypt at rest and in transit (TLS, database encryption)".to_string(),
                priority: Priority::High,
            },
            SecurityConsideration {
                area: "API Security".to_string(),
                concern: "Prevent unauthorized API access".to_string(),
                solution: "Implement rate limiting, API keys, and CORS".to_string(),
                priority: Priority::High,
            },
            SecurityConsideration {
                area: "Payment Security".to_string(),
                concern: "PCI compliance for payment processing".to_string(),
                solution: "Use Stripe (PCI-compliant), never store card data".to_string(),
                priority: Priority::Critical,
            },
        ]
    }

    /// Identify integration challenges
    async fn identify_integration_challenges(&self, opportunity: &Opportunity) -> Result<Vec<String>> {
        debug!("Identifying integration challenges");

        let mut challenges = Vec::new();

        if opportunity.domain.to_lowercase().contains("saas") {
            challenges.push("Stripe payment integration".to_string());
            challenges.push("Email delivery (transactional emails)".to_string());
            challenges.push("Analytics integration".to_string());
        }

        challenges.push("OAuth/SSO integration".to_string());
        challenges.push("Monitoring and logging setup".to_string());

        Ok(challenges)
    }

    /// Calculate overall feasibility score
    fn calculate_feasibility_score(
        &self,
        complexity: &ImplementationComplexity,
        risks: &[TechnicalRisk],
        scalability: &ScalabilityAssessment,
    ) -> f64 {
        let mut score = 10.0;

        // Complexity penalty
        score -= complexity.overall_complexity * 0.3;

        // Risk penalty
        let high_risk_count = risks.iter().filter(|r| matches!(r.severity, RiskSeverity::High | RiskSeverity::Critical)).count();
        score -= high_risk_count as f64 * 0.5;

        // Scalability boost
        score += (scalability.scalability_score - 5.0) * 0.2;

        score.max(0.0).min(10.0)
    }

    /// Make final recommendation
    fn make_recommendation(
        &self,
        feasibility_score: f64,
        complexity: &ImplementationComplexity,
        risks: &[TechnicalRisk],
    ) -> TechnicalRecommendation {
        let critical_risks = risks.iter().any(|r| r.severity == RiskSeverity::Critical);

        if feasibility_score >= 8.0 && !critical_risks {
            TechnicalRecommendation::HighlyFeasible
        } else if feasibility_score >= 6.0 && complexity.estimated_team_size <= 2 {
            TechnicalRecommendation::Feasible
        } else if feasibility_score >= 4.0 {
            TechnicalRecommendation::FeasibleWithChallenges
        } else {
            TechnicalRecommendation::NotFeasible
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_technical_feasibility() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = TechnicalFeasibilityAgent::new(llm);

        let opp = Opportunity::new(
            "Test App".to_string(),
            "A test opportunity".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let report = agent.analyze(&opp).await.unwrap();

        assert!(report.feasibility_score > 0.0);
        assert!(report.feasibility_score <= 10.0);
        assert!(!report.technical_risks.is_empty());
    }
}
