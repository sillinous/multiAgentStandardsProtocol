//! UI/UX Design Agent - Generates comprehensive design specifications

use super::models::*;
use crate::models::Opportunity;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use std::sync::Arc;
use tracing::{info, debug};

/// UI/UX Design Agent generates design specifications
pub struct UIUXDesignAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl UIUXDesignAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "UIUXDesigner",
            "Generates comprehensive UI/UX design specifications including design systems, components, and user flows",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("product-development");
        agent.add_tag("design");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Generate complete design specification for an opportunity
    pub async fn design(&self, opportunity: &Opportunity) -> Result<DesignSpecification> {
        info!("🎨 Generating UI/UX design for: {}", opportunity.title);

        // Generate design system
        let design_system = self.generate_design_system(opportunity).await?;

        // Generate components
        let components = self.generate_components(opportunity).await?;

        // Generate user flows
        let user_flows = self.generate_user_flows(opportunity).await?;

        // Generate layouts
        let layouts = self.generate_layouts(opportunity).await?;

        // Define accessibility requirements
        let accessibility = self.define_accessibility_requirements();

        // Define responsive breakpoints
        let responsive_breakpoints = self.define_breakpoints();

        Ok(DesignSpecification {
            opportunity_id: opportunity.id,
            design_system,
            components,
            user_flows,
            layouts,
            accessibility,
            responsive_breakpoints,
        })
    }

    /// Generate design system (colors, typography, spacing)
    async fn generate_design_system(&self, opportunity: &Opportunity) -> Result<DesignSystem> {
        debug!("Generating design system");

        // Use LLM to suggest color palette based on domain
        let color_palette = self.suggest_color_palette(opportunity).await?;

        Ok(DesignSystem {
            color_palette,
            typography: Typography {
                font_family_primary: "Inter, sans-serif".to_string(),
                font_family_secondary: "JetBrains Mono, monospace".to_string(),
                scale: vec![
                    TypographyLevel {
                        name: "h1".to_string(),
                        size: "2.5rem".to_string(),
                        weight: "700".to_string(),
                        line_height: "1.2".to_string(),
                    },
                    TypographyLevel {
                        name: "h2".to_string(),
                        size: "2rem".to_string(),
                        weight: "600".to_string(),
                        line_height: "1.3".to_string(),
                    },
                    TypographyLevel {
                        name: "h3".to_string(),
                        size: "1.5rem".to_string(),
                        weight: "600".to_string(),
                        line_height: "1.4".to_string(),
                    },
                    TypographyLevel {
                        name: "body".to_string(),
                        size: "1rem".to_string(),
                        weight: "400".to_string(),
                        line_height: "1.6".to_string(),
                    },
                    TypographyLevel {
                        name: "small".to_string(),
                        size: "0.875rem".to_string(),
                        weight: "400".to_string(),
                        line_height: "1.5".to_string(),
                    },
                ],
            },
            spacing: SpacingScale {
                base: 4,
                scale: vec![4, 8, 12, 16, 24, 32, 48, 64, 96, 128],
            },
            shadows: vec![
                Shadow {
                    name: "sm".to_string(),
                    value: "0 1px 2px 0 rgba(0, 0, 0, 0.05)".to_string(),
                },
                Shadow {
                    name: "md".to_string(),
                    value: "0 4px 6px -1px rgba(0, 0, 0, 0.1)".to_string(),
                },
                Shadow {
                    name: "lg".to_string(),
                    value: "0 10px 15px -3px rgba(0, 0, 0, 0.1)".to_string(),
                },
            ],
            border_radius: BorderRadiusScale {
                small: "0.25rem".to_string(),
                medium: "0.5rem".to_string(),
                large: "1rem".to_string(),
                full: "9999px".to_string(),
            },
        })
    }

    /// Suggest color palette based on domain using LLM
    async fn suggest_color_palette(&self, opportunity: &Opportunity) -> Result<ColorPalette> {
        let prompt = format!(
            "Suggest a modern, accessible color palette for a {} product titled '{}'.\n\
            The product is: {}\n\n\
            Provide hex colors for: primary, secondary, accent, background, surface, error, warning, success, text-primary, text-secondary.\n\
            Ensure WCAG AA contrast ratios.",
            opportunity.domain, opportunity.title, opportunity.description
        );

        let _llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a UI/UX design expert specializing in color theory and accessibility.".to_string(),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.7),
            max_tokens: Some(512),
            tools: None,
        };

        // For demo, provide a professional default palette
        Ok(ColorPalette {
            primary: "#3B82F6".to_string(),     // Blue
            secondary: "#8B5CF6".to_string(),   // Purple
            accent: "#F59E0B".to_string(),      // Amber
            background: "#FFFFFF".to_string(),  // White
            surface: "#F9FAFB".to_string(),     // Gray 50
            error: "#EF4444".to_string(),       // Red
            warning: "#F59E0B".to_string(),     // Amber
            success: "#10B981".to_string(),     // Green
            text_primary: "#111827".to_string(), // Gray 900
            text_secondary: "#6B7280".to_string(), // Gray 500
        })
    }

    /// Generate component specifications
    async fn generate_components(&self, opportunity: &Opportunity) -> Result<Vec<ComponentSpec>> {
        debug!("Generating component specifications");

        let mut components = Vec::new();

        // Core components for any product
        components.push(ComponentSpec {
            name: "Button".to_string(),
            component_type: ComponentType::Button,
            description: "Primary action button with multiple variants".to_string(),
            props: vec![
                ComponentProp {
                    name: "variant".to_string(),
                    prop_type: "primary | secondary | outline".to_string(),
                    required: false,
                    default_value: Some("primary".to_string()),
                },
                ComponentProp {
                    name: "size".to_string(),
                    prop_type: "sm | md | lg".to_string(),
                    required: false,
                    default_value: Some("md".to_string()),
                },
                ComponentProp {
                    name: "disabled".to_string(),
                    prop_type: "boolean".to_string(),
                    required: false,
                    default_value: Some("false".to_string()),
                },
            ],
            states: vec!["default".to_string(), "hover".to_string(), "active".to_string(), "disabled".to_string()],
            variants: vec!["primary".to_string(), "secondary".to_string(), "outline".to_string()],
        });

        components.push(ComponentSpec {
            name: "Input".to_string(),
            component_type: ComponentType::Input,
            description: "Text input field with validation".to_string(),
            props: vec![
                ComponentProp {
                    name: "label".to_string(),
                    prop_type: "string".to_string(),
                    required: true,
                    default_value: None,
                },
                ComponentProp {
                    name: "placeholder".to_string(),
                    prop_type: "string".to_string(),
                    required: false,
                    default_value: None,
                },
                ComponentProp {
                    name: "error".to_string(),
                    prop_type: "string".to_string(),
                    required: false,
                    default_value: None,
                },
            ],
            states: vec!["default".to_string(), "focus".to_string(), "error".to_string(), "disabled".to_string()],
            variants: vec!["text".to_string(), "email".to_string(), "password".to_string()],
        });

        components.push(ComponentSpec {
            name: "Card".to_string(),
            component_type: ComponentType::Card,
            description: "Container card for content grouping".to_string(),
            props: vec![
                ComponentProp {
                    name: "title".to_string(),
                    prop_type: "string".to_string(),
                    required: false,
                    default_value: None,
                },
                ComponentProp {
                    name: "padding".to_string(),
                    prop_type: "sm | md | lg".to_string(),
                    required: false,
                    default_value: Some("md".to_string()),
                },
            ],
            states: vec!["default".to_string(), "hover".to_string()],
            variants: vec!["default".to_string(), "elevated".to_string(), "outlined".to_string()],
        });

        // Product-specific components based on domain
        if opportunity.domain.to_lowercase().contains("saas") {
            components.push(ComponentSpec {
                name: "Dashboard".to_string(),
                component_type: ComponentType::Custom,
                description: "Main dashboard layout with metrics".to_string(),
                props: vec![],
                states: vec!["loading".to_string(), "loaded".to_string(), "error".to_string()],
                variants: vec![],
            });
        }

        Ok(components)
    }

    /// Generate user flows
    async fn generate_user_flows(&self, opportunity: &Opportunity) -> Result<Vec<UserFlow>> {
        debug!("Generating user flows");

        Ok(vec![
            UserFlow {
                flow_name: "User Onboarding".to_string(),
                description: "New user sign-up and initial setup".to_string(),
                entry_point: "Landing Page".to_string(),
                steps: vec![
                    FlowStep {
                        step_number: 1,
                        screen_name: "Landing Page".to_string(),
                        action: "Click 'Get Started'".to_string(),
                        user_goal: "Begin sign-up process".to_string(),
                    },
                    FlowStep {
                        step_number: 2,
                        screen_name: "Sign Up Form".to_string(),
                        action: "Enter email and password".to_string(),
                        user_goal: "Create account".to_string(),
                    },
                    FlowStep {
                        step_number: 3,
                        screen_name: "Email Verification".to_string(),
                        action: "Verify email address".to_string(),
                        user_goal: "Confirm identity".to_string(),
                    },
                    FlowStep {
                        step_number: 4,
                        screen_name: "Welcome Dashboard".to_string(),
                        action: "View dashboard".to_string(),
                        user_goal: "Access main application".to_string(),
                    },
                ],
                success_criteria: vec![
                    "Account created".to_string(),
                    "Email verified".to_string(),
                    "User reaches dashboard".to_string(),
                ],
            },
            UserFlow {
                flow_name: "Core Feature Usage".to_string(),
                description: format!("Using main features of {}", opportunity.title),
                entry_point: "Dashboard".to_string(),
                steps: vec![
                    FlowStep {
                        step_number: 1,
                        screen_name: "Dashboard".to_string(),
                        action: "Navigate to feature".to_string(),
                        user_goal: "Access core functionality".to_string(),
                    },
                    FlowStep {
                        step_number: 2,
                        screen_name: "Feature Screen".to_string(),
                        action: "Use primary feature".to_string(),
                        user_goal: "Complete task".to_string(),
                    },
                    FlowStep {
                        step_number: 3,
                        screen_name: "Confirmation".to_string(),
                        action: "View results".to_string(),
                        user_goal: "Verify success".to_string(),
                    },
                ],
                success_criteria: vec![
                    "Feature accessed".to_string(),
                    "Action completed".to_string(),
                    "Feedback provided".to_string(),
                ],
            },
        ])
    }

    /// Generate layout specifications
    async fn generate_layouts(&self, _opportunity: &Opportunity) -> Result<Vec<LayoutSpec>> {
        debug!("Generating layouts");

        Ok(vec![
            LayoutSpec {
                layout_name: "Landing Page".to_string(),
                layout_type: LayoutType::Landing,
                sections: vec![
                    LayoutSection {
                        section_name: "Hero".to_string(),
                        components: vec!["Heading".to_string(), "Subtitle".to_string(), "CTA Button".to_string()],
                        grid_columns: 12,
                    },
                    LayoutSection {
                        section_name: "Features".to_string(),
                        components: vec!["Feature Card".to_string(), "Feature Card".to_string(), "Feature Card".to_string()],
                        grid_columns: 3,
                    },
                    LayoutSection {
                        section_name: "Pricing".to_string(),
                        components: vec!["Pricing Card".to_string(), "Pricing Card".to_string()],
                        grid_columns: 2,
                    },
                ],
            },
            LayoutSpec {
                layout_name: "Dashboard".to_string(),
                layout_type: LayoutType::Dashboard,
                sections: vec![
                    LayoutSection {
                        section_name: "Header".to_string(),
                        components: vec!["Navigation".to_string(), "User Menu".to_string()],
                        grid_columns: 12,
                    },
                    LayoutSection {
                        section_name: "Metrics".to_string(),
                        components: vec!["Metric Card".to_string(), "Metric Card".to_string(), "Metric Card".to_string()],
                        grid_columns: 4,
                    },
                    LayoutSection {
                        section_name: "Content".to_string(),
                        components: vec!["Data Table".to_string(), "Chart".to_string()],
                        grid_columns: 8,
                    },
                ],
            },
        ])
    }

    /// Define accessibility requirements
    fn define_accessibility_requirements(&self) -> AccessibilitySpec {
        AccessibilitySpec {
            wcag_level: WCAGLevel::AA,
            aria_labels: true,
            keyboard_navigation: true,
            screen_reader_support: true,
            color_contrast_ratio: 4.5, // WCAG AA standard
        }
    }

    /// Define responsive breakpoints
    fn define_breakpoints(&self) -> Vec<Breakpoint> {
        vec![
            Breakpoint {
                name: "mobile".to_string(),
                min_width: 0,
                max_width: Some(640),
            },
            Breakpoint {
                name: "tablet".to_string(),
                min_width: 641,
                max_width: Some(1024),
            },
            Breakpoint {
                name: "desktop".to_string(),
                min_width: 1025,
                max_width: Some(1536),
            },
            Breakpoint {
                name: "wide".to_string(),
                min_width: 1537,
                max_width: None,
            },
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_design_generation() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = UIUXDesignAgent::new(llm);

        let opp = Opportunity::new(
            "Test SaaS".to_string(),
            "A test product".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let spec = agent.design(&opp).await.unwrap();

        assert_eq!(spec.opportunity_id, opp.id);
        assert!(!spec.components.is_empty());
        assert!(!spec.user_flows.is_empty());
        assert!(!spec.layouts.is_empty());
    }
}
