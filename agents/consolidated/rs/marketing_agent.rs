//! Marketing Agent - Handles campaigns, SEO, content generation, and growth

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest};
use std::sync::Arc;
use tracing::{info, debug};
use uuid::Uuid;

/// Marketing Agent - Drives customer acquisition and growth
pub struct MarketingAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl MarketingAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "MarketingAgent",
            "Specialist in marketing campaigns, SEO, content generation, and growth hacking",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("revenue");
        agent.add_tag("marketing");
        agent.add_tag("growth");

        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    /// Create comprehensive marketing strategy
    pub async fn create_marketing_strategy(
        &self,
        opportunity: &Opportunity,
        budget: f64,
    ) -> Result<Vec<MarketingCampaign>> {
        info!("📢 Creating marketing strategy for: {}", opportunity.title);

        let mut campaigns = Vec::new();

        // Determine which channels to use based on opportunity
        let channels = self.select_marketing_channels(opportunity).await?;

        // Allocate budget across channels
        let budget_per_channel = budget / channels.len() as f64;

        for channel in channels {
            let campaign = self.create_campaign(
                opportunity,
                channel,
                budget_per_channel,
            ).await?;
            campaigns.push(campaign);
        }

        info!("✅ Created {} marketing campaigns with ${:.2} total budget",
            campaigns.len(), budget);

        Ok(campaigns)
    }

    /// Select optimal marketing channels
    async fn select_marketing_channels(
        &self,
        opportunity: &Opportunity,
    ) -> Result<Vec<CampaignType>> {
        debug!("Selecting marketing channels...");

        let prompt = format!(
            "You are a marketing expert. Select the 2-3 best marketing channels for this product.\n\n\
            Product: {}\n\
            Description: {}\n\
            Target Market: {}\n\
            Product Type: {:?}\n\n\
            Available channels:\n\
            - GoogleAds\n\
            - FacebookAds\n\
            - LinkedInAds\n\
            - TwitterAds\n\
            - SEO\n\
            - ContentMarketing\n\
            - EmailMarketing\n\
            - SocialMedia\n\n\
            Respond with 2-3 channel names, comma-separated",
            opportunity.title,
            opportunity.description,
            opportunity.domain,
            opportunity.product_type
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(100),
            temperature: Some(0.5),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let channels_str = response.content.to_lowercase();

        let mut channels = Vec::new();
        if channels_str.contains("google") {
            channels.push(CampaignType::GoogleAds);
        }
        if channels_str.contains("facebook") {
            channels.push(CampaignType::FacebookAds);
        }
        if channels_str.contains("linkedin") {
            channels.push(CampaignType::LinkedInAds);
        }
        if channels_str.contains("twitter") {
            channels.push(CampaignType::TwitterAds);
        }
        if channels_str.contains("seo") {
            channels.push(CampaignType::SEO);
        }
        if channels_str.contains("content") {
            channels.push(CampaignType::ContentMarketing);
        }
        if channels_str.contains("email") {
            channels.push(CampaignType::EmailMarketing);
        }
        if channels_str.contains("social") {
            channels.push(CampaignType::SocialMedia);
        }

        // Ensure at least 2 channels
        if channels.is_empty() {
            channels = vec![CampaignType::GoogleAds, CampaignType::ContentMarketing];
        } else if channels.len() == 1 {
            channels.push(CampaignType::ContentMarketing);
        }

        debug!("Selected channels: {:?}", channels);
        Ok(channels)
    }

    /// Create a marketing campaign
    async fn create_campaign(
        &self,
        opportunity: &Opportunity,
        campaign_type: CampaignType,
        budget: f64,
    ) -> Result<MarketingCampaign> {
        debug!("Creating {:?} campaign...", campaign_type);

        // Generate targeting info
        let target_audience = self.define_target_audience(opportunity).await?;

        // Generate key messages
        let key_messages = self.generate_key_messages(opportunity, campaign_type).await?;

        // Generate call-to-action
        let cta = self.generate_cta(opportunity, campaign_type).await?;

        let mut campaign = MarketingCampaign::new(opportunity.id, campaign_type);
        campaign.budget = budget;
        campaign.target_audience = target_audience;
        campaign.key_messages = key_messages;
        campaign.call_to_action = cta;
        campaign.status = CampaignStatus::Draft;
        campaign.duration_days = 30;

        Ok(campaign)
    }

    /// Define target audience
    async fn define_target_audience(&self, opportunity: &Opportunity) -> Result<String> {
        let prompt = format!(
            "Define the target audience for this product in 1-2 sentences:\n\n\
            Product: {}\n\
            Description: {}\n\
            Domain: {}",
            opportunity.title,
            opportunity.description,
            opportunity.domain
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(150),
            temperature: Some(0.7),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        Ok(response.content.trim().to_string())
    }

    /// Generate key marketing messages
    async fn generate_key_messages(
        &self,
        opportunity: &Opportunity,
        campaign_type: CampaignType,
    ) -> Result<Vec<String>> {
        let prompt = format!(
            "Generate 3 compelling marketing messages for a {:?} campaign.\n\n\
            Product: {}\n\
            Description: {}\n\n\
            Each message should be one sentence. List them numbered 1-3.",
            campaign_type,
            opportunity.title,
            opportunity.description
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(300),
            temperature: Some(0.8),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;

        // Parse numbered list
        let messages: Vec<String> = response.content
            .lines()
            .filter(|line| line.trim().starts_with(|c: char| c.is_numeric()))
            .map(|line| {
                line.trim()
                    .trim_start_matches(|c: char| c.is_numeric() || c == '.' || c == ')')
                    .trim()
                    .to_string()
            })
            .take(3)
            .collect();

        Ok(if messages.is_empty() {
            vec!["Innovative solution for your needs".to_string()]
        } else {
            messages
        })
    }

    /// Generate call-to-action
    async fn generate_cta(
        &self,
        opportunity: &Opportunity,
        campaign_type: CampaignType,
    ) -> Result<String> {
        let prompt = format!(
            "Generate a compelling call-to-action (CTA) for a {:?} campaign.\n\n\
            Product: {}\n\n\
            Make it short, action-oriented, and compelling. Respond with ONLY the CTA text.",
            campaign_type,
            opportunity.title
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(50),
            temperature: Some(0.8),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        Ok(response.content.trim().to_string())
    }

    /// Generate SEO-optimized content
    pub async fn generate_seo_content(
        &self,
        opportunity: &Opportunity,
    ) -> Result<String> {
        info!("📝 Generating SEO content for: {}", opportunity.title);

        let prompt = format!(
            "Generate SEO-optimized landing page content for this product.\n\n\
            Product: {}\n\
            Description: {}\n\
            Target Keywords: {}, {} {}\n\n\
            Include:\n\
            1. Compelling headline\n\
            2. 3-4 paragraphs of engaging content\n\
            3. Feature list (3-5 items)\n\
            4. Strong closing CTA\n\n\
            Make it conversion-focused and SEO-optimized.",
            opportunity.title,
            opportunity.description,
            opportunity.domain,
            opportunity.product_type.to_string().to_lowercase(),
            "software"
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(1000),
            temperature: Some(0.7),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        Ok(response.content)
    }

    /// Generate social media posts
    pub async fn generate_social_posts(
        &self,
        opportunity: &Opportunity,
        count: usize,
    ) -> Result<Vec<String>> {
        info!("📱 Generating {} social media posts", count);

        let prompt = format!(
            "Generate {} engaging social media posts for this product.\n\n\
            Product: {}\n\
            Description: {}\n\n\
            Make them varied, engaging, and shareable. Number them 1-{}.",
            count,
            opportunity.title,
            opportunity.description,
            count
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(500),
            temperature: Some(0.8),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;

        let posts: Vec<String> = response.content
            .lines()
            .filter(|line| line.trim().starts_with(|c: char| c.is_numeric()))
            .map(|line| {
                line.trim()
                    .trim_start_matches(|c: char| c.is_numeric() || c == '.' || c == ')')
                    .trim()
                    .to_string()
            })
            .collect();

        Ok(posts)
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_create_marketing_strategy() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = MarketingAgent::new(llm);

        let opportunity = Opportunity::new(
            "Test SaaS".to_string(),
            "A test product".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let result = agent.create_marketing_strategy(&opportunity, 1000.0).await;
        assert!(result.is_ok());

        let campaigns = result.unwrap();
        assert!(!campaigns.is_empty());
    }
}
