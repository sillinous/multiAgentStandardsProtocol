//! Code Generator Agent - Generates code based on specifications

use agentic_core::{Agent, AgentRole, Result, Error};
use agentic_runtime::{
    executor::{AgentExecutor, DefaultExecutor, ExecutionContext},
    llm::{LlmClient, LlmRequest, LlmMessage, MessageRole},
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug, warn};

/// Code generation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeGenRequest {
    pub language: String,
    pub description: String,
    pub requirements: Vec<String>,
    pub style_guide: Option<String>,
    pub context: Option<String>,
    pub generate_tests: bool,
    pub generate_docs: bool,
}

impl CodeGenRequest {
    /// Create a simple code generation request
    pub fn new(language: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            language: language.into(),
            description: description.into(),
            requirements: Vec::new(),
            style_guide: None,
            context: None,
            generate_tests: true,
            generate_docs: true,
        }
    }

    /// Add requirements
    pub fn with_requirements(mut self, requirements: Vec<String>) -> Self {
        self.requirements = requirements;
        self
    }

    /// Add style guide
    pub fn with_style_guide(mut self, style_guide: impl Into<String>) -> Self {
        self.style_guide = Some(style_guide.into());
        self
    }

    /// Add context information
    pub fn with_context(mut self, context: impl Into<String>) -> Self {
        self.context = Some(context.into());
        self
    }

    /// Set whether to generate tests
    pub fn with_tests(mut self, generate: bool) -> Self {
        self.generate_tests = generate;
        self
    }

    /// Set whether to generate documentation
    pub fn with_docs(mut self, generate: bool) -> Self {
        self.generate_docs = generate;
        self
    }
}

/// Generated code result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedCode {
    pub code: String,
    pub tests: Option<String>,
    pub documentation: Option<String>,
    pub confidence: f64,
    pub language: String,
    pub explanation: Option<String>,
    pub dependencies: Vec<String>,
}

impl GeneratedCode {
    /// Create a new generated code result
    pub fn new(code: String, language: String) -> Self {
        Self {
            code,
            language,
            tests: None,
            documentation: None,
            confidence: 0.0,
            explanation: None,
            dependencies: Vec::new(),
        }
    }

    /// Check if code generation was successful
    pub fn is_valid(&self) -> bool {
        !self.code.is_empty() && self.confidence > 0.5
    }

    /// Get total lines of generated content
    pub fn total_lines(&self) -> usize {
        let mut total = self.code.lines().count();
        if let Some(tests) = &self.tests {
            total += tests.lines().count();
        }
        if let Some(docs) = &self.documentation {
            total += docs.lines().count();
        }
        total
    }
}

/// Code Generator Agent
pub struct CodeGeneratorAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl CodeGeneratorAgent {
    /// Create a new code generator agent with LLM client
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "CodeGenerator",
            "Generates code based on specifications and requirements",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("specialist");
        agent.add_tag("code-generation");

        Self { agent, llm_client }
    }

    /// Get the base agent
    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Generate code from requirements
    pub async fn generate(&self, request: CodeGenRequest) -> Result<GeneratedCode> {
        info!("Generating {} code: {}", request.language, request.description);

        // Build the code generation prompt
        let prompt = self.build_code_prompt(&request);

        // Call LLM to generate code
        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: self.get_system_prompt(&request.language),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.2), // Low temperature for more consistent code
            max_tokens: Some(4096),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;

        // Parse the generated code
        let mut generated = self.parse_code_response(&response.content, &request.language)?;

        // Generate tests if requested
        if request.generate_tests {
            debug!("Generating tests for the code");
            generated.tests = Some(self.generate_tests(&generated.code, &request).await?);
        }

        // Generate documentation if requested
        if request.generate_docs {
            debug!("Generating documentation for the code");
            generated.documentation = Some(self.generate_documentation(&generated.code, &request).await?);
        }

        // Calculate confidence based on various factors
        generated.confidence = self.calculate_confidence(&generated, &request);

        info!("Code generation completed with confidence: {:.2}", generated.confidence);
        Ok(generated)
    }

    /// Build the code generation prompt
    fn build_code_prompt(&self, request: &CodeGenRequest) -> String {
        let mut prompt = format!(
            "Generate {} code for the following task:\n\n{}",
            request.language, request.description
        );

        if !request.requirements.is_empty() {
            prompt.push_str("\n\nRequirements:\n");
            for (i, req) in request.requirements.iter().enumerate() {
                prompt.push_str(&format!("{}. {}\n", i + 1, req));
            }
        }

        if let Some(style_guide) = &request.style_guide {
            prompt.push_str("\n\nStyle Guide:\n");
            prompt.push_str(style_guide);
        }

        if let Some(context) = &request.context {
            prompt.push_str("\n\nAdditional Context:\n");
            prompt.push_str(context);
        }

        prompt.push_str("\n\nPlease provide:\n");
        prompt.push_str("1. Clean, well-structured code\n");
        prompt.push_str("2. Appropriate error handling\n");
        prompt.push_str("3. Clear variable and function names\n");
        prompt.push_str("4. Inline comments for complex logic\n");
        prompt.push_str("5. A brief explanation of the approach\n");
        prompt.push_str("6. List of any external dependencies needed\n");

        prompt
    }

    /// Get system prompt for the language
    fn get_system_prompt(&self, language: &str) -> String {
        format!(
            "You are an expert {} developer. Generate high-quality, production-ready code \
            that follows best practices and idiomatic patterns for {}. \
            Focus on correctness, efficiency, and maintainability. \
            Always include proper error handling and type safety where applicable.",
            language, language
        )
    }

    /// Parse the LLM response into structured code
    fn parse_code_response(&self, content: &str, language: &str) -> Result<GeneratedCode> {
        // Extract code blocks from markdown-style code fences
        let code_blocks: Vec<&str> = content
            .split("```")
            .skip(1)
            .step_by(2)
            .collect();

        let code = if !code_blocks.is_empty() {
            // Remove language identifier if present
            code_blocks[0]
                .lines()
                .skip_while(|line| line.trim() == language || line.trim().is_empty())
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            // No code fences found, use entire content
            content.to_string()
        };

        // Extract explanation (text before first code block)
        let explanation = content
            .split("```")
            .next()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty());

        // Extract dependencies (look for mentions of imports/dependencies)
        let dependencies = self.extract_dependencies(&code, language);

        Ok(GeneratedCode {
            code,
            language: language.to_string(),
            tests: None,
            documentation: None,
            confidence: 0.0,
            explanation,
            dependencies,
        })
    }

    /// Extract dependencies from the code
    fn extract_dependencies(&self, code: &str, language: &str) -> Vec<String> {
        let mut deps = Vec::new();

        match language {
            "rust" => {
                for line in code.lines() {
                    if line.trim().starts_with("use ") {
                        if let Some(dep) = line.split_whitespace().nth(1) {
                            deps.push(dep.trim_end_matches(';').to_string());
                        }
                    }
                }
            }
            "python" => {
                for line in code.lines() {
                    if line.trim().starts_with("import ") || line.trim().starts_with("from ") {
                        deps.push(line.trim().to_string());
                    }
                }
            }
            "javascript" | "typescript" => {
                for line in code.lines() {
                    if line.trim().starts_with("import ") || line.trim().starts_with("require(") {
                        deps.push(line.trim().to_string());
                    }
                }
            }
            _ => {}
        }

        deps
    }

    /// Generate tests for the code
    async fn generate_tests(&self, code: &str, request: &CodeGenRequest) -> Result<String> {
        let prompt = format!(
            "Generate comprehensive unit tests for the following {} code:\n\n```{}\n{}\n```\n\n\
            Generate tests that:\n\
            1. Cover all major functionality\n\
            2. Test edge cases and error conditions\n\
            3. Follow {} testing best practices\n\
            4. Are well-organized and documented\n\
            5. Can be run independently",
            request.language, request.language, code, request.language
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: format!("You are an expert in {} testing. Generate thorough, well-structured test code.", request.language),
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

        let response = self.llm_client.complete(llm_request).await?;

        // Extract test code from response
        let test_blocks: Vec<&str> = response.content
            .split("```")
            .skip(1)
            .step_by(2)
            .collect();

        Ok(if !test_blocks.is_empty() {
            test_blocks[0]
                .lines()
                .skip_while(|line| line.trim() == request.language.as_str() || line.trim().is_empty())
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            response.content
        })
    }

    /// Generate documentation for the code
    async fn generate_documentation(&self, code: &str, request: &CodeGenRequest) -> Result<String> {
        let prompt = format!(
            "Generate comprehensive documentation for the following {} code:\n\n```{}\n{}\n```\n\n\
            Include:\n\
            1. Overview of what the code does\n\
            2. Function/method descriptions\n\
            3. Parameter explanations\n\
            4. Return value descriptions\n\
            5. Usage examples\n\
            6. Any important notes or caveats",
            request.language, request.language, code
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: "You are a technical documentation expert. Generate clear, comprehensive documentation.".to_string(),
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
        Ok(response.content)
    }

    /// Calculate confidence score for the generated code
    fn calculate_confidence(&self, generated: &GeneratedCode, request: &CodeGenRequest) -> f64 {
        let mut confidence = 0.5; // Base confidence

        // Increase confidence if code is not empty
        if !generated.code.is_empty() {
            confidence += 0.2;
        }

        // Increase if tests were generated
        if generated.tests.is_some() && request.generate_tests {
            confidence += 0.1;
        }

        // Increase if documentation was generated
        if generated.documentation.is_some() && request.generate_docs {
            confidence += 0.1;
        }

        // Increase if there's an explanation
        if generated.explanation.is_some() {
            confidence += 0.05;
        }

        // Decrease if code is very short (might be incomplete)
        let line_count = generated.code.lines().count();
        if line_count < 5 {
            confidence -= 0.15;
        } else if line_count > 20 {
            confidence += 0.05; // Substantial implementation
        }

        // Clamp to [0, 1]
        confidence.max(0.0).min(1.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;

    #[tokio::test]
    async fn test_code_generator_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let generator = CodeGeneratorAgent::new(llm);
        assert_eq!(generator.agent().name, "CodeGenerator");
    }

    #[tokio::test]
    async fn test_simple_code_generation() {
        let llm = Arc::new(MockLlmClient::new());
        let generator = CodeGeneratorAgent::new(llm);

        let request = CodeGenRequest::new("rust", "Calculate factorial of a number")
            .with_requirements(vec![
                "Handle negative numbers".to_string(),
                "Return Result type".to_string(),
            ]);

        let result = generator.generate(request).await;
        assert!(result.is_ok());

        let generated = result.unwrap();
        assert!(!generated.code.is_empty());
        assert_eq!(generated.language, "rust");
    }

    #[test]
    fn test_code_gen_request_builder() {
        let request = CodeGenRequest::new("python", "Sort a list")
            .with_requirements(vec!["Use quicksort".to_string()])
            .with_style_guide("PEP 8")
            .with_tests(true)
            .with_docs(true);

        assert_eq!(request.language, "python");
        assert_eq!(request.requirements.len(), 1);
        assert!(request.generate_tests);
        assert!(request.generate_docs);
    }

    #[test]
    fn test_generated_code_validation() {
        let mut code = GeneratedCode::new("fn test() {}".to_string(), "rust".to_string());
        code.confidence = 0.8;
        assert!(code.is_valid());

        code.confidence = 0.3;
        assert!(!code.is_valid());
    }
}
