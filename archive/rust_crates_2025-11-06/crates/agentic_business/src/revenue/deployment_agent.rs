//! Deployment Agent - Handles production deployment, infrastructure, and monitoring

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest};
use std::sync::Arc;
use tracing::{info, debug};

pub struct DeploymentAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl DeploymentAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "DeploymentAgent",
            "Specialist in production deployment, infrastructure provisioning, and monitoring setup",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("revenue");
        agent.add_tag("deployment");
        agent.add_tag("infrastructure");

        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub async fn create_deployment_config(
        &self,
        opportunity: &Opportunity,
    ) -> Result<DeploymentConfig> {
        info!("🚀 Creating deployment configuration for: {}", opportunity.title);

        let hosting_provider = self.select_hosting_provider(opportunity).await?;

        let mut config = DeploymentConfig {
            opportunity_id: opportunity.id,
            hosting_provider,
            domain: None,
            environment: DeploymentEnvironment::Production,
            repository_url: None,
            deployment_url: None,
            ssl_enabled: true,
            monitoring_enabled: true,
            backup_enabled: true,
        };

        info!("✅ Deployment configured for {:?}", hosting_provider);

        Ok(config)
    }

    async fn select_hosting_provider(&self, opportunity: &Opportunity) -> Result<HostingProvider> {
        let prompt = format!(
            "Select the best hosting provider for this product. Choose from:\n\
            AWS, GoogleCloud, Azure, DigitalOcean, Heroku, Vercel, Netlify\n\n\
            Product: {}\n\
            Type: {:?}\n\n\
            Respond with ONLY the provider name",
            opportunity.title,
            opportunity.product_type
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(50),
            temperature: Some(0.3),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let provider_name = response.content.trim().to_lowercase();

        let provider = match provider_name.as_str() {
            s if s.contains("aws") => HostingProvider::AWS,
            s if s.contains("google") => HostingProvider::GoogleCloud,
            s if s.contains("azure") => HostingProvider::Azure,
            s if s.contains("digitalocean") || s.contains("digital") => HostingProvider::DigitalOcean,
            s if s.contains("heroku") => HostingProvider::Heroku,
            s if s.contains("vercel") => HostingProvider::Vercel,
            s if s.contains("netlify") => HostingProvider::Netlify,
            _ => HostingProvider::Vercel,
        };

        Ok(provider)
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }
}
