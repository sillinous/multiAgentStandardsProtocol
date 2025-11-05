//! Testing Agent - Writes comprehensive tests for code

use agentic_core::{Agent, AgentRole, Result, Error};
use agentic_runtime::{
    llm::{LlmClient, LlmRequest, LlmMessage, MessageRole},
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{info, debug};

/// Test generation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestGenRequest {
    pub code: String,
    pub language: String,
    pub framework: Option<String>,
    pub test_types: Vec<TestType>,
    pub coverage_target: Option<f64>,
    pub style_guide: Option<String>,
}

impl TestGenRequest {
    /// Create a simple test generation request
    pub fn new(code: impl Into<String>, language: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            language: language.into(),
            framework: None,
            test_types: vec![TestType::Unit],
            coverage_target: Some(80.0),
            style_guide: None,
        }
    }

    /// Specify testing framework
    pub fn with_framework(mut self, framework: impl Into<String>) -> Self {
        self.framework = Some(framework.into());
        self
    }

    /// Add test types to generate
    pub fn with_test_types(mut self, types: Vec<TestType>) -> Self {
        self.test_types = types;
        self
    }

    /// Set coverage target percentage
    pub fn with_coverage_target(mut self, target: f64) -> Self {
        self.coverage_target = Some(target);
        self
    }

    /// Add style guide
    pub fn with_style_guide(mut self, style_guide: impl Into<String>) -> Self {
        self.style_guide = Some(style_guide.into());
        self
    }
}

/// Types of tests to generate
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TestType {
    /// Unit tests for individual functions/methods
    Unit,
    /// Integration tests for component interaction
    Integration,
    /// Edge case and boundary tests
    EdgeCase,
    /// Performance/benchmark tests
    Performance,
    /// Security tests
    Security,
    /// Error handling tests
    ErrorHandling,
}

impl TestType {
    pub fn as_str(&self) -> &str {
        match self {
            TestType::Unit => "unit",
            TestType::Integration => "integration",
            TestType::EdgeCase => "edge_case",
            TestType::Performance => "performance",
            TestType::Security => "security",
            TestType::ErrorHandling => "error_handling",
        }
    }
}

/// Generated test code
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedTests {
    pub test_code: String,
    pub framework: String,
    pub language: String,
    pub test_count: usize,
    pub estimated_coverage: f64,
    pub test_types_included: Vec<TestType>,
    pub setup_code: Option<String>,
    pub teardown_code: Option<String>,
    pub dependencies: Vec<String>,
}

impl GeneratedTests {
    /// Create new generated tests
    pub fn new(test_code: String, framework: String, language: String) -> Self {
        Self {
            test_code,
            framework,
            language,
            test_count: 0,
            estimated_coverage: 0.0,
            test_types_included: Vec::new(),
            setup_code: None,
            teardown_code: None,
            dependencies: Vec::new(),
        }
    }

    /// Check if tests meet coverage target
    pub fn meets_coverage_target(&self, target: f64) -> bool {
        self.estimated_coverage >= target
    }

    /// Get total lines of test code
    pub fn total_lines(&self) -> usize {
        let mut total = self.test_code.lines().count();
        if let Some(setup) = &self.setup_code {
            total += setup.lines().count();
        }
        if let Some(teardown) = &self.teardown_code {
            total += teardown.lines().count();
        }
        total
    }
}

/// Testing Agent - Generates comprehensive tests
pub struct TestingAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl TestingAgent {
    /// Create a new testing agent
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "TestWriter",
            "Writes comprehensive unit and integration tests",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("specialist");
        agent.add_tag("testing");
        agent.add_tag("quality-assurance");

        Self { agent, llm_client }
    }

    /// Get the base agent
    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Generate tests for code
    pub async fn generate_tests(&self, request: TestGenRequest) -> Result<GeneratedTests> {
        info!("Generating {} tests for code", request.language);

        // Determine the testing framework
        let framework = self.select_framework(&request);

        // Build the test generation prompt
        let prompt = self.build_test_prompt(&request, &framework);

        // Call LLM to generate tests
        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: self.get_system_prompt(&request.language, &framework),
                },
                LlmMessage {
                    role: MessageRole::User,
                    content: prompt,
                },
            ],
            temperature: Some(0.3),
            max_tokens: Some(4096),
            tools: None,
        };

        let response = self.llm_client.complete(llm_request).await?;

        // Parse the generated tests
        let mut tests = self.parse_test_response(&response.content, &request.language, &framework)?;

        // Analyze the generated tests
        tests.test_count = self.count_tests(&tests.test_code, &framework);
        tests.estimated_coverage = self.estimate_coverage(&tests.test_code, &request.code);
        tests.test_types_included = request.test_types.clone();

        // Extract dependencies
        tests.dependencies = self.extract_test_dependencies(&tests.test_code, &request.language);

        info!(
            "Generated {} tests with estimated {:.1}% coverage",
            tests.test_count, tests.estimated_coverage
        );

        Ok(tests)
    }

    /// Select appropriate testing framework
    fn select_framework(&self, request: &TestGenRequest) -> String {
        if let Some(framework) = &request.framework {
            return framework.clone();
        }

        // Auto-select based on language
        match request.language.as_str() {
            "rust" => "cargo test".to_string(),
            "python" => "pytest".to_string(),
            "javascript" | "typescript" => "jest".to_string(),
            "go" => "testing".to_string(),
            "java" => "junit".to_string(),
            "csharp" => "xunit".to_string(),
            _ => "generic".to_string(),
        }
    }

    /// Build test generation prompt
    fn build_test_prompt(&self, request: &TestGenRequest, framework: &str) -> String {
        let mut prompt = format!(
            "Generate comprehensive {} tests using {} for the following code:\n\n```{}\n{}\n```\n\n",
            request.language, framework, request.language, request.code
        );

        prompt.push_str("Generate tests that include:\n");

        for test_type in &request.test_types {
            let description = match test_type {
                TestType::Unit => "Unit tests for each function/method with standard inputs",
                TestType::Integration => "Integration tests for component interactions",
                TestType::EdgeCase => "Edge case tests (null, empty, boundary values, etc.)",
                TestType::Performance => "Performance tests to verify efficiency",
                TestType::Security => "Security tests for vulnerabilities",
                TestType::ErrorHandling => "Error handling tests for exceptions and failures",
            };
            prompt.push_str(&format!("- {}\n", description));
        }

        if let Some(target) = request.coverage_target {
            prompt.push_str(&format!("\nTarget test coverage: {:.0}%\n", target));
        }

        if let Some(style_guide) = &request.style_guide {
            prompt.push_str(&format!("\nStyle guide:\n{}\n", style_guide));
        }

        prompt.push_str("\nRequirements:\n");
        prompt.push_str("1. Each test should be independent and isolated\n");
        prompt.push_str("2. Use descriptive test names that explain what is being tested\n");
        prompt.push_str("3. Follow the AAA pattern (Arrange, Act, Assert)\n");
        prompt.push_str("4. Include setup and teardown if needed\n");
        prompt.push_str("5. Add comments explaining complex test scenarios\n");
        prompt.push_str("6. Cover both happy paths and error cases\n");

        prompt
    }

    /// Get system prompt for testing
    fn get_system_prompt(&self, language: &str, framework: &str) -> String {
        format!(
            "You are an expert {} testing engineer specializing in {}. \
            Generate high-quality, comprehensive test suites that follow best practices. \
            Write tests that are maintainable, readable, and provide meaningful coverage. \
            Always consider edge cases, error conditions, and boundary values.",
            language, framework
        )
    }

    /// Parse test response from LLM
    fn parse_test_response(&self, content: &str, language: &str, framework: &str) -> Result<GeneratedTests> {
        // Extract test code from markdown-style code fences
        let code_blocks: Vec<&str> = content
            .split("```")
            .skip(1)
            .step_by(2)
            .collect();

        let test_code = if !code_blocks.is_empty() {
            code_blocks[0]
                .lines()
                .skip_while(|line| {
                    let trimmed = line.trim();
                    trimmed == language || trimmed.is_empty()
                })
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            content.to_string()
        };

        // Extract setup/teardown if present
        let (setup, teardown) = self.extract_setup_teardown(&test_code, language);

        Ok(GeneratedTests {
            test_code,
            framework: framework.to_string(),
            language: language.to_string(),
            test_count: 0,
            estimated_coverage: 0.0,
            test_types_included: Vec::new(),
            setup_code: setup,
            teardown_code: teardown,
            dependencies: Vec::new(),
        })
    }

    /// Extract setup and teardown code
    fn extract_setup_teardown(&self, code: &str, language: &str) -> (Option<String>, Option<String>) {
        let mut setup = None;
        let mut teardown = None;

        match language {
            "rust" => {
                // Look for setup/teardown in Rust tests
                if code.contains("fn setup()") {
                    setup = Some("// Rust test setup".to_string());
                }
            }
            "python" => {
                // Look for pytest fixtures or unittest setUp/tearDown
                if code.contains("@pytest.fixture") || code.contains("def setUp") {
                    setup = Some("# Test setup".to_string());
                }
                if code.contains("def tearDown") {
                    teardown = Some("# Test teardown".to_string());
                }
            }
            "javascript" | "typescript" => {
                // Look for beforeEach/afterEach
                if code.contains("beforeEach") {
                    setup = Some("// Test setup".to_string());
                }
                if code.contains("afterEach") {
                    teardown = Some("// Test teardown".to_string());
                }
            }
            _ => {}
        }

        (setup, teardown)
    }

    /// Count number of tests in generated code
    fn count_tests(&self, code: &str, framework: &str) -> usize {
        let mut count = 0;

        for line in code.lines() {
            let trimmed = line.trim();

            // Rust
            if trimmed.starts_with("#[test]") || trimmed.starts_with("#[tokio::test]") {
                count += 1;
            }
            // Python pytest
            else if trimmed.starts_with("def test_") {
                count += 1;
            }
            // JavaScript/TypeScript
            else if trimmed.starts_with("test(") || trimmed.starts_with("it(") {
                count += 1;
            }
            // Go
            else if trimmed.starts_with("func Test") {
                count += 1;
            }
            // Java
            else if trimmed.contains("@Test") {
                count += 1;
            }
        }

        count
    }

    /// Estimate test coverage
    fn estimate_coverage(&self, test_code: &str, source_code: &str) -> f64 {
        // Simple heuristic: ratio of test lines to source lines
        let test_lines = test_code.lines().filter(|l| !l.trim().is_empty()).count();
        let source_lines = source_code.lines().filter(|l| !l.trim().is_empty()).count();

        if source_lines == 0 {
            return 0.0;
        }

        // Rough estimate: good tests are usually 1-2x the size of source code
        let ratio = test_lines as f64 / source_lines as f64;
        let coverage = (ratio * 50.0).min(100.0);

        coverage
    }

    /// Extract test dependencies
    fn extract_test_dependencies(&self, code: &str, language: &str) -> Vec<String> {
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
                    let trimmed = line.trim();
                    if trimmed.starts_with("import ") || trimmed.starts_with("from ") {
                        deps.push(trimmed.to_string());
                    }
                }
            }
            "javascript" | "typescript" => {
                for line in code.lines() {
                    let trimmed = line.trim();
                    if trimmed.starts_with("import ") || trimmed.starts_with("require(") {
                        deps.push(trimmed.to_string());
                    }
                }
            }
            _ => {}
        }

        deps
    }

    /// Generate tests for specific test type
    pub async fn generate_specific_tests(
        &self,
        code: &str,
        language: &str,
        test_type: TestType,
    ) -> Result<String> {
        let prompt = format!(
            "Generate {} {} tests for the following code:\n\n```{}\n{}\n```",
            test_type.as_str(),
            language,
            language,
            code
        );

        let llm_request = LlmRequest {
            model: self.agent.model.clone(),
            messages: vec![
                LlmMessage {
                    role: MessageRole::System,
                    content: format!(
                        "You are an expert in writing {} tests for {}. \
                        Focus specifically on this type of testing.",
                        test_type.as_str(),
                        language
                    ),
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

        // Extract code from response
        let test_blocks: Vec<&str> = response.content
            .split("```")
            .skip(1)
            .step_by(2)
            .collect();

        Ok(if !test_blocks.is_empty() {
            test_blocks[0]
                .lines()
                .skip_while(|line| line.trim() == language || line.trim().is_empty())
                .collect::<Vec<_>>()
                .join("\n")
        } else {
            response.content
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;

    #[tokio::test]
    async fn test_testing_agent_creation() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = TestingAgent::new(llm);
        assert_eq!(agent.agent().name, "TestWriter");
    }

    #[test]
    fn test_framework_selection() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = TestingAgent::new(llm);

        let rust_req = TestGenRequest::new("fn foo() {}", "rust");
        assert_eq!(agent.select_framework(&rust_req), "cargo test");

        let python_req = TestGenRequest::new("def foo():", "python");
        assert_eq!(agent.select_framework(&python_req), "pytest");

        let js_req = TestGenRequest::new("function foo() {}", "javascript");
        assert_eq!(agent.select_framework(&js_req), "jest");
    }

    #[test]
    fn test_count_tests() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = TestingAgent::new(llm);

        let rust_tests = r#"
            #[test]
            fn test_one() {}

            #[test]
            fn test_two() {}
        "#;
        assert_eq!(agent.count_tests(rust_tests, "cargo test"), 2);

        let python_tests = r#"
            def test_one():
                pass

            def test_two():
                pass
        "#;
        assert_eq!(agent.count_tests(python_tests, "pytest"), 2);
    }

    #[tokio::test]
    async fn test_generate_tests() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = TestingAgent::new(llm);

        let request = TestGenRequest::new("fn add(a: i32, b: i32) -> i32 { a + b }", "rust")
            .with_test_types(vec![TestType::Unit, TestType::EdgeCase])
            .with_coverage_target(80.0);

        let result = agent.generate_tests(request).await;
        assert!(result.is_ok());

        let tests = result.unwrap();
        assert!(!tests.test_code.is_empty());
        assert_eq!(tests.language, "rust");
        assert_eq!(tests.framework, "cargo test");
    }

    #[test]
    fn test_generated_tests_validation() {
        let tests = GeneratedTests::new(
            "test code".to_string(),
            "pytest".to_string(),
            "python".to_string(),
        );
        assert_eq!(tests.framework, "pytest");
        assert_eq!(tests.language, "python");
    }
}
