//! Product Development System
//!
//! Complete product development framework with 3 specialized agents coordinated by a meta-agent.
//!
//! # Architecture
//!
//! ```
//! ProductDevelopmentManager (Meta-Agent)
//! ├── UIUXDesignAgent
//! │   ├── Design systems (colors, typography, spacing)
//! │   ├── Component specifications
//! │   ├── User flows
//! │   ├── Layouts
//! │   └── Accessibility requirements
//! ├── InfrastructureAgent
//! │   ├── Cloud provider selection
//! │   ├── Database design
//! │   ├── API specifications
//! │   ├── Hosting configuration
//! │   └── CI/CD setup
//! └── [Future] SDLCManager Integration
//!     ├── Code generation
//!     ├── Testing
//!     └── Documentation
//! ```
//!
//! # Workflow
//!
//! 1. **Design Phase**: Generate complete UI/UX design specifications
//! 2. **Infrastructure Phase**: Provision and configure cloud infrastructure
//! 3. **Development Phase**: Generate code, tests, and documentation (future)
//! 4. **Quality Gates**: Validate all requirements are met
//! 5. **Deployment**: Prepare for production deployment
//!
//! # Usage Example
//!
//! ```no_run
//! use agentic_business::development::ProductDevelopmentManager;
//! use agentic_business::models::Opportunity;
//! use agentic_business::validation::BusinessValidationManager;
//! use agentic_runtime::llm::MockLlmClient;
//! use std::sync::Arc;
//!
//! # async fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let llm_client = Arc::new(MockLlmClient::new());
//!
//! // Validate opportunity first
//! let mut validation_manager = BusinessValidationManager::new(llm_client.clone());
//! let validation_report = validation_manager.validate(&opportunity).await?;
//!
//! // Develop product
//! let mut dev_manager = ProductDevelopmentManager::new(llm_client);
//! let result = dev_manager.develop(&opportunity, &validation_report).await?;
//!
//! println!("Development Status: {:?}", result.status);
//! println!("Completion: {:.0}%", result.completion_percentage);
//! # Ok(())
//! # }
//! ```

pub mod models;
pub mod uiux_design_agent;
pub mod infrastructure_agent;
pub mod product_development_manager;

// Re-export main types
pub use models::*;
pub use uiux_design_agent::UIUXDesignAgent;
pub use infrastructure_agent::InfrastructureAgent;
pub use product_development_manager::ProductDevelopmentManager;
