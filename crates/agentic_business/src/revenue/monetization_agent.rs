//! Monetization Agent - Handles payment setup, pricing strategy, and billing

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest};
use serde_json::json;
use std::sync::Arc;
use tracing::{info, debug};
use uuid::Uuid;

/// Monetization Agent - Sets up payment infrastructure and pricing
pub struct MonetizationAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl MonetizationAgent {
    /// Create a new monetization agent
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "MonetizationAgent",
            "Specialist in payment setup, pricing strategy, and revenue optimization",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("revenue");
        agent.add_tag("monetization");
        agent.add_tag("payments");

        // Configure agent to be standards-compliant
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    /// Setup monetization for an opportunity
    pub async fn setup_monetization(
        &self,
        opportunity: &Opportunity,
    ) -> Result<MonetizationConfig> {
        info!("🔧 Setting up monetization for: {}", opportunity.title);

        // Determine optimal payment provider
        let payment_provider = self.select_payment_provider(opportunity).await?;

        // Determine optimal pricing model
        let pricing_model = self.select_pricing_model(opportunity).await?;

        // Calculate optimal price point
        let price_point = self.calculate_price_point(opportunity, pricing_model).await?;

        // Determine billing interval for subscriptions
        let billing_interval = if matches!(pricing_model, PricingModel::Subscription) {
            Some(self.select_billing_interval(opportunity).await?)
        } else {
            None
        };

        // Determine free trial period
        let free_trial_days = self.calculate_free_trial_period(opportunity).await?;

        let mut config = MonetizationConfig::new(
            opportunity.id,
            payment_provider,
            pricing_model,
        );

        config.price_point = price_point;
        config.billing_interval = billing_interval;
        config.free_trial_days = free_trial_days;
        config.currency = "USD".to_string();

        info!("✅ Monetization configured: {:?} at ${:.2}/{:?}",
            pricing_model, price_point, billing_interval.unwrap_or(BillingInterval::Monthly));

        Ok(config)
    }

    /// Select the best payment provider for this opportunity
    async fn select_payment_provider(
        &self,
        opportunity: &Opportunity,
    ) -> Result<PaymentProvider> {
        debug!("Selecting payment provider...");

        let prompt = format!(
            "You are a payment processing expert. Analyze this opportunity and recommend \
            the best payment provider (Stripe, PayPal, Square, or Paddle).\n\n\
            Opportunity: {}\n\
            Description: {}\n\
            Product Type: {:?}\n\
            Target Market: {}\n\n\
            Consider:\n\
            - Transaction fees\n\
            - Global coverage\n\
            - Integration ease\n\
            - Features needed\n\
            - Target customer preferences\n\n\
            Respond with ONLY the provider name: Stripe, PayPal, Square, or Paddle",
            opportunity.title,
            opportunity.description,
            opportunity.product_type,
            opportunity.domain
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(100),
            temperature: Some(0.3),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let provider_name = response.content.trim().to_lowercase();

        let provider = match provider_name.as_str() {
            s if s.contains("stripe") => PaymentProvider::Stripe,
            s if s.contains("paypal") => PaymentProvider::PayPal,
            s if s.contains("square") => PaymentProvider::Square,
            s if s.contains("paddle") => PaymentProvider::Paddle,
            _ => PaymentProvider::Stripe, // Default to Stripe
        };

        debug!("Selected payment provider: {:?}", provider);
        Ok(provider)
    }

    /// Select the best pricing model
    async fn select_pricing_model(
        &self,
        opportunity: &Opportunity,
    ) -> Result<PricingModel> {
        debug!("Selecting pricing model...");

        let prompt = format!(
            "You are a pricing strategy expert. Analyze this opportunity and recommend \
            the best pricing model.\n\n\
            Opportunity: {}\n\
            Description: {}\n\
            Product Type: {:?}\n\
            Domain: {}\n\n\
            Choose from:\n\
            - OneTime: Single payment\n\
            - Subscription: Recurring monthly/yearly\n\
            - Usage: Pay-per-use\n\
            - Freemium: Free + premium features\n\
            - Tiered: Multiple pricing tiers\n\n\
            Respond with ONLY the model name",
            opportunity.title,
            opportunity.description,
            opportunity.product_type,
            opportunity.domain
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(100),
            temperature: Some(0.3),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let model_name = response.content.trim().to_lowercase();

        let pricing_model = match model_name.as_str() {
            s if s.contains("subscription") => PricingModel::Subscription,
            s if s.contains("onetime") || s.contains("one-time") => PricingModel::OneTime,
            s if s.contains("usage") => PricingModel::Usage,
            s if s.contains("freemium") => PricingModel::Freemium,
            s if s.contains("tiered") => PricingModel::Tiered,
            _ => PricingModel::Subscription, // Default
        };

        debug!("Selected pricing model: {:?}", pricing_model);
        Ok(pricing_model)
    }

    /// Calculate optimal price point
    async fn calculate_price_point(
        &self,
        opportunity: &Opportunity,
        pricing_model: PricingModel,
    ) -> Result<f64> {
        debug!("Calculating price point...");

        let prompt = format!(
            "You are a pricing analyst. Calculate the optimal price point for this opportunity.\n\n\
            Opportunity: {}\n\
            Description: {}\n\
            Product Type: {:?}\n\
            Pricing Model: {:?}\n\
            Estimated Development Cost: ${}\n\
            Target ROI: {}%\n\n\
            Consider:\n\
            - Market rates\n\
            - Value proposition\n\
            - Customer willingness to pay\n\
            - Competitive pricing\n\
            - Development/operating costs\n\n\
            Respond with ONLY a number (the price in USD)",
            opportunity.title,
            opportunity.description,
            opportunity.product_type,
            pricing_model,
            opportunity.implementation_estimate.estimated_cost,
            opportunity.score.profitability * 100.0
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(100),
            temperature: Some(0.5),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;

        // Extract number from response
        let price = response.content
            .trim()
            .chars()
            .filter(|c| c.is_numeric() || *c == '.')
            .collect::<String>()
            .parse::<f64>()
            .unwrap_or(29.0); // Default fallback

        debug!("Calculated price point: ${:.2}", price);
        Ok(price)
    }

    /// Select billing interval for subscriptions
    async fn select_billing_interval(
        &self,
        opportunity: &Opportunity,
    ) -> Result<BillingInterval> {
        debug!("Selecting billing interval...");

        // For simplicity, use LLM to decide
        let prompt = format!(
            "For this SaaS product, what billing interval is best?\n\n\
            Product: {}\n\
            Domain: {}\n\n\
            Choose: Monthly, Quarterly, or Yearly\n\
            Respond with ONLY the interval name",
            opportunity.title,
            opportunity.domain
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(50),
            temperature: Some(0.3),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let interval_name = response.content.trim().to_lowercase();

        let interval = match interval_name.as_str() {
            s if s.contains("month") => BillingInterval::Monthly,
            s if s.contains("quarter") => BillingInterval::Quarterly,
            s if s.contains("year") => BillingInterval::Yearly,
            s if s.contains("week") => BillingInterval::Weekly,
            _ => BillingInterval::Monthly, // Default
        };

        debug!("Selected billing interval: {:?}", interval);
        Ok(interval)
    }

    /// Calculate free trial period
    async fn calculate_free_trial_period(
        &self,
        opportunity: &Opportunity,
    ) -> Result<Option<u32>> {
        debug!("Calculating free trial period...");

        // Determine if free trial makes sense
        let prompt = format!(
            "Should this product offer a free trial? If yes, how many days?\n\n\
            Product: {}\n\
            Domain: {}\n\
            Product Type: {:?}\n\n\
            Respond with:\n\
            - A number (7, 14, 30, etc.) if free trial recommended\n\
            - 'none' if no free trial\n\
            \n\
            Respond with ONLY the number or 'none'",
            opportunity.title,
            opportunity.domain,
            opportunity.product_type
        );

        let request = LlmRequest {
            messages: vec![("user".to_string(), prompt)],
            model: self.agent.model.clone(),
            max_tokens: Some(50),
            temperature: Some(0.5),
            ..Default::default()
        };

        let response = self.llm_client.complete(request).await?;
        let trial_response = response.content.trim().to_lowercase();

        if trial_response.contains("none") || trial_response.contains("no") {
            debug!("No free trial recommended");
            return Ok(None);
        }

        // Try to parse number
        let days = trial_response
            .chars()
            .filter(|c| c.is_numeric())
            .collect::<String>()
            .parse::<u32>()
            .ok();

        debug!("Free trial period: {:?} days", days);
        Ok(days)
    }

    /// Generate payment integration code/config
    pub async fn generate_payment_integration(
        &self,
        config: &MonetizationConfig,
    ) -> Result<String> {
        info!("Generating payment integration for {:?}", config.payment_provider);

        let integration_template = match config.payment_provider {
            PaymentProvider::Stripe => self.generate_stripe_integration(config),
            PaymentProvider::PayPal => self.generate_paypal_integration(config),
            PaymentProvider::Square => self.generate_square_integration(config),
            PaymentProvider::Paddle => self.generate_paddle_integration(config),
        };

        Ok(integration_template)
    }

    fn generate_stripe_integration(&self, config: &MonetizationConfig) -> String {
        format!(
            r#"// Stripe Integration Configuration
// Price: ${:.2} / {:?}

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

// Create product
const product = await stripe.products.create({{
  name: 'Your Product',
  description: 'Product description',
}});

// Create price
const price = await stripe.prices.create({{
  product: product.id,
  unit_amount: {}, // Amount in cents
  currency: '{}',
  recurring: {}
}});

// Create checkout session
const session = await stripe.checkout.sessions.create({{
  payment_method_types: ['card'],
  line_items: [{{
    price: price.id,
    quantity: 1,
  }}],
  mode: '{}',
  success_url: 'https://your-domain.com/success',
  cancel_url: 'https://your-domain.com/cancel',
}});

// Webhook handler
app.post('/webhook', express.raw({{type: 'application/json'}}), (req, res) => {{
  const sig = req.headers['stripe-signature'];
  const event = stripe.webhooks.constructEvent(
    req.body, sig, process.env.STRIPE_WEBHOOK_SECRET
  );

  if (event.type === 'checkout.session.completed') {{
    // Handle successful payment
  }}

  res.json({{received: true}});
}});
"#,
            config.price_point,
            config.billing_interval.unwrap_or(BillingInterval::Monthly),
            (config.price_point * 100.0) as i64,
            config.currency.to_lowercase(),
            if matches!(config.pricing_model, PricingModel::Subscription) {
                format!("{{ interval: '{}' }}",
                    match config.billing_interval {
                        Some(BillingInterval::Monthly) => "month",
                        Some(BillingInterval::Yearly) => "year",
                        _ => "month"
                    }
                )
            } else {
                "null".to_string()
            },
            if matches!(config.pricing_model, PricingModel::Subscription) {
                "subscription"
            } else {
                "payment"
            }
        )
    }

    fn generate_paypal_integration(&self, config: &MonetizationConfig) -> String {
        format!(
            r#"// PayPal Integration Configuration
// Price: ${:.2}

<div id="paypal-button-container"></div>

<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&currency={}"></script>
<script>
  paypal.Buttons({{
    createOrder: function(data, actions) {{
      return actions.order.create({{
        purchase_units: [{{
          amount: {{
            value: '{:.2}'
          }}
        }}]
      }});
    }},
    onApprove: function(data, actions) {{
      return actions.order.capture().then(function(details) {{
        // Handle successful payment
        console.log('Transaction completed by ' + details.payer.name.given_name);
      }});
    }}
  }}).render('#paypal-button-container');
</script>
"#,
            config.price_point,
            config.currency,
            config.price_point
        )
    }

    fn generate_square_integration(&self, config: &MonetizationConfig) -> String {
        format!(
            r#"// Square Integration Configuration
// Price: ${:.2}

const {{ Client, Environment }} = require('square');

const client = new Client({{
  accessToken: process.env.SQUARE_ACCESS_TOKEN,
  environment: Environment.Production,
}});

// Create payment
const payment = await client.paymentsApi.createPayment({{
  sourceId: req.body.nonce,
  amountMoney: {{
    amount: BigInt(Math.floor({} * 100)), // Amount in cents
    currency: '{}',
  }},
  idempotencyKey: require('crypto').randomUUID(),
}});
"#,
            config.price_point,
            config.price_point,
            config.currency
        )
    }

    fn generate_paddle_integration(&self, config: &MonetizationConfig) -> String {
        format!(
            r#"// Paddle Integration Configuration
// Price: ${:.2}

<script src="https://cdn.paddle.com/paddle/paddle.js"></script>
<script>
  Paddle.Setup({{ vendor: YOUR_VENDOR_ID }});

  function openCheckout() {{
    Paddle.Checkout.open({{
      product: YOUR_PRODUCT_ID,
      price: '{:.2}',
      currency: '{}',
      successCallback: function(data) {{
        // Handle successful payment
      }}
    }});
  }}
</script>

<button onclick="openCheckout()">Buy Now</button>
"#,
            config.price_point,
            config.price_point,
            config.currency
        )
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
    async fn test_setup_monetization() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = MonetizationAgent::new(llm);

        let opportunity = Opportunity::new(
            "Test SaaS".to_string(),
            "A test product".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let result = agent.setup_monetization(&opportunity).await;
        assert!(result.is_ok());

        let config = result.unwrap();
        assert_eq!(config.opportunity_id, opportunity.id);
        assert!(config.price_point > 0.0);
    }
}
