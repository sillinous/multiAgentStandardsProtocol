//! Market Research Agent - Discovers opportunities from multiple sources

use crate::models::{Opportunity, UserPreferences, ProductType, DataSource, SourceType};
use agentic_core::{Agent, AgentRole, Result, Error};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug, warn};

/// Market Research Agent discovers opportunities from various sources
pub struct MarketResearchAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
    http_client: reqwest::Client,
}

impl MarketResearchAgent {
    /// Create a new market research agent
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "MarketResearcher",
            "Discovers market opportunities from APIs, web scraping, and trend analysis",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("market-research");
        agent.add_tag("opportunity-discovery");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        let http_client = reqwest::Client::builder()
            .user_agent("AgenticForge/1.0")
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .unwrap();

        Self {
            agent,
            llm_client,
            http_client,
        }
    }

    /// Get the base agent
    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Discover opportunities based on user preferences
    pub async fn discover_opportunities(
        &self,
        preferences: &UserPreferences,
    ) -> Result<Vec<Opportunity>> {
        info!("Starting opportunity discovery with preferences: {:?}", preferences);

        let mut opportunities = Vec::new();

        // Source 1: LLM-based analysis (always available)
        debug!("Discovering opportunities via LLM analysis");
        let llm_opportunities = self.discover_via_llm(preferences).await?;
        opportunities.extend(llm_opportunities);

        // Source 2: Product Hunt API (if accessible)
        debug!("Discovering opportunities via Product Hunt");
        if let Ok(ph_opportunities) = self.discover_via_product_hunt(preferences).await {
            opportunities.extend(ph_opportunities);
        } else {
            warn!("Product Hunt API unavailable, skipping");
        }

        // Source 3: Trend analysis
        debug!("Discovering opportunities via trend analysis");
        if let Ok(trend_opportunities) = self.discover_via_trends(preferences).await {
            opportunities.extend(trend_opportunities);
        }

        // Source 4: Web scraping (GitHub trending, Reddit, etc.)
        debug!("Discovering opportunities via web scraping");
        if let Ok(web_opportunities) = self.discover_via_web_scraping(preferences).await {
            opportunities.extend(web_opportunities);
        }

        // Filter by preferences
        let filtered: Vec<Opportunity> = opportunities
            .into_iter()
            .filter(|opp| opp.matches_preferences(preferences))
            .collect();

        info!("Discovered {} opportunities matching preferences", filtered.len());

        Ok(filtered)
    }

    /// Discover opportunities using LLM analysis
    async fn discover_via_llm(&self, preferences: &UserPreferences) -> Result<Vec<Opportunity>> {
        let prompt = self.build_llm_discovery_prompt(preferences);

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a market research expert and business analyst. \
                    Generate innovative, viable business opportunities based on current market trends, \
                    gaps, and user preferences. Be creative but realistic.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.7), // Higher creativity
            max_tokens: Some(4096),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;

        // Parse opportunities from LLM response
        let opportunities = self.parse_llm_opportunities(&response.content, preferences)?;

        Ok(opportunities)
    }

    /// Build prompt for LLM-based opportunity discovery
    fn build_llm_discovery_prompt(&self, preferences: &UserPreferences) -> String {
        let mut prompt = String::from("Generate 5-10 innovative business opportunities based on the following preferences:\n\n");

        if let Some(domain) = &preferences.domain {
            prompt.push_str(&format!("Domain: {}\n", domain));
        }

        if let Some(product_type) = preferences.product_type {
            prompt.push_str(&format!("Product Type: {:?}\n", product_type));
        }

        if preferences.focus_minimal_investment {
            prompt.push_str("Focus: Minimal investment required\n");
        }

        if preferences.focus_passive_revenue {
            prompt.push_str("Focus: Passive revenue streams\n");
        }

        if preferences.focus_quick_wins {
            prompt.push_str("Focus: Quick time to market\n");
        }

        if !preferences.revenue_type.is_empty() {
            prompt.push_str(&format!("Revenue Types: {}\n", preferences.revenue_type.join(", ")));
        }

        prompt.push_str("\nFor each opportunity, provide:\n");
        prompt.push_str("1. Title: A concise, catchy name\n");
        prompt.push_str("2. Description: 2-3 sentences explaining the concept\n");
        prompt.push_str("3. Target Market: Who would use this?\n");
        prompt.push_str("4. Revenue Model: How would it make money?\n");
        prompt.push_str("5. Competitive Advantage: Why would this succeed?\n");
        prompt.push_str("6. Initial Investment: Estimated startup cost\n");
        prompt.push_str("7. Time to Market: Estimated development time\n");
        prompt.push_str("\nFormat as a JSON array of opportunities with these fields: title, description, domain, revenue_model, initial_investment, time_to_market_days\n");

        prompt
    }

    /// Parse LLM response into opportunities
    fn parse_llm_opportunities(
        &self,
        content: &str,
        _preferences: &UserPreferences,
    ) -> Result<Vec<Opportunity>> {
        // Try to extract JSON from the response
        let json_str = if let Some(start) = content.find('[') {
            if let Some(end) = content.rfind(']') {
                &content[start..=end]
            } else {
                content
            }
        } else {
            // Fallback: create synthetic opportunities from text
            return self.create_synthetic_opportunities_from_text(content);
        };

        #[derive(Deserialize)]
        struct LLMOpportunity {
            title: String,
            description: String,
            domain: Option<String>,
            revenue_model: Option<String>,
            initial_investment: Option<f64>,
            time_to_market_days: Option<u32>,
        }

        match serde_json::from_str::<Vec<LLMOpportunity>>(json_str) {
            Ok(llm_opps) => {
                let opportunities: Vec<Opportunity> = llm_opps
                    .into_iter()
                    .map(|llm_opp| {
                        let mut opp = Opportunity::new(
                            llm_opp.title,
                            llm_opp.description,
                            llm_opp.domain.unwrap_or_else(|| "General".to_string()),
                            ProductType::SaaS, // Default
                        );

                        if let Some(investment) = llm_opp.initial_investment {
                            opp.financial_projection.initial_investment = investment;
                        }

                        if let Some(days) = llm_opp.time_to_market_days {
                            opp.implementation_estimate.estimated_days = days;
                        }

                        if let Some(model) = llm_opp.revenue_model {
                            opp.financial_projection.revenue_model = model;
                        }

                        opp.sources.push(DataSource {
                            name: "LLM Analysis".to_string(),
                            source_type: SourceType::LLMAnalysis,
                            url: None,
                            confidence: 0.8,
                        });

                        opp
                    })
                    .collect();

                Ok(opportunities)
            }
            Err(_) => {
                // Fallback to text parsing
                self.create_synthetic_opportunities_from_text(content)
            }
        }
    }

    /// Create synthetic opportunities from unstructured text
    fn create_synthetic_opportunities_from_text(&self, text: &str) -> Result<Vec<Opportunity>> {
        // Extract title-like patterns
        let mut opportunities = Vec::new();

        // Simple heuristic: look for numbered items or bullet points
        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with(|c: char| c.is_numeric())
                || trimmed.starts_with('-')
                || trimmed.starts_with('*')
            {
                // Extract the opportunity title
                let title = trimmed
                    .trim_start_matches(|c: char| c.is_numeric() || c == '.' || c == '-' || c == '*')
                    .trim()
                    .to_string();

                if !title.is_empty() && title.len() > 10 {
                    let mut opp = Opportunity::new(
                        title.clone(),
                        format!("Market opportunity: {}", title),
                        "General".to_string(),
                        ProductType::SaaS,
                    );

                    opp.sources.push(DataSource {
                        name: "LLM Analysis (parsed)".to_string(),
                        source_type: SourceType::LLMAnalysis,
                        url: None,
                        confidence: 0.6,
                    });

                    opportunities.push(opp);

                    if opportunities.len() >= 10 {
                        break;
                    }
                }
            }
        }

        Ok(opportunities)
    }

    /// Discover opportunities via Product Hunt API
    async fn discover_via_product_hunt(
        &self,
        _preferences: &UserPreferences,
    ) -> Result<Vec<Opportunity>> {
        // Note: Product Hunt API requires authentication
        // For now, return empty - can be implemented with proper API key

        debug!("Product Hunt integration not yet configured");
        Ok(Vec::new())
    }

    /// Discover opportunities via trend analysis
    async fn discover_via_trends(&self, preferences: &UserPreferences) -> Result<Vec<Opportunity>> {
        // Use LLM to analyze current trends and generate opportunities
        let prompt = format!(
            "Analyze current market trends in {} and identify 3-5 emerging opportunities. \
            Focus on: {}\n\n\
            For each opportunity, explain why it's trending, the market gap it fills, \
            and how it could be monetized.",
            preferences.domain.as_ref().unwrap_or(&"technology".to_string()),
            if preferences.focus_passive_revenue {
                "passive income opportunities"
            } else {
                "scalable business models"
            }
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a trend analyst specializing in identifying emerging market opportunities.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.6),
            max_tokens: Some(2048),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;

        // Create opportunities from trend analysis
        let opportunities = self.create_synthetic_opportunities_from_text(&response.content)?;

        // Tag as trend-based
        let mut tagged_opportunities = Vec::new();
        for mut opp in opportunities {
            opp.sources.push(DataSource {
                name: "Trend Analysis".to_string(),
                source_type: SourceType::TrendAnalysis,
                url: None,
                confidence: 0.75,
            });
            tagged_opportunities.push(opp);
        }

        Ok(tagged_opportunities)
    }

    /// Discover opportunities via web scraping
    async fn discover_via_web_scraping(
        &self,
        _preferences: &UserPreferences,
    ) -> Result<Vec<Opportunity>> {
        // Scrape GitHub trending, Reddit, etc.
        // For safety and simplicity, we'll use LLM to generate realistic mock data

        debug!("Web scraping integration: using mock data for demo");
        Ok(Vec::new())
    }

    /// Enrich an opportunity with additional research
    pub async fn enrich_opportunity(&self, opportunity: &mut Opportunity) -> Result<()> {
        info!("Enriching opportunity: {}", opportunity.title);

        // Use LLM to add more details
        let prompt = format!(
            "Provide detailed analysis for this business opportunity:\n\n\
            Title: {}\n\
            Description: {}\n\
            Domain: {}\n\n\
            Please provide:\n\
            1. Estimated market size\n\
            2. Initial investment required (USD)\n\
            3. Monthly operating costs\n\
            4. Realistic monthly revenue projections (low, mid, high)\n\
            5. Time to break even\n\
            6. Recommended tech stack\n\
            7. Core features needed\n\n\
            Format as JSON with these fields.",
            opportunity.title, opportunity.description, opportunity.domain
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a business analyst providing detailed market analysis.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.4),
            max_tokens: Some(2048),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;

        // Parse and update opportunity
        // (Simplified - in production would parse JSON)
        debug!("Enrichment analysis: {}", &response.content[..100.min(response.content.len())]);

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;

    #[tokio::test]
    async fn test_market_research_agent_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = MarketResearchAgent::new(llm);
        assert_eq!(agent.agent().name, "MarketResearcher");
    }

    #[tokio::test]
    async fn test_discover_opportunities() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = MarketResearchAgent::new(llm);

        let preferences = UserPreferences {
            domain: Some("SaaS".to_string()),
            focus_minimal_investment: true,
            ..Default::default()
        };

        let result = agent.discover_opportunities(&preferences).await;
        assert!(result.is_ok());
    }
}
