//! Development System Data Models

use serde::{Deserialize, Serialize};

/// UI/UX Design Specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DesignSpecification {
    pub opportunity_id: uuid::Uuid,
    pub design_system: DesignSystem,
    pub components: Vec<ComponentSpec>,
    pub user_flows: Vec<UserFlow>,
    pub layouts: Vec<LayoutSpec>,
    pub accessibility: AccessibilitySpec,
    pub responsive_breakpoints: Vec<Breakpoint>,
}

/// Design system (colors, typography, spacing)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DesignSystem {
    pub color_palette: ColorPalette,
    pub typography: Typography,
    pub spacing: SpacingScale,
    pub shadows: Vec<Shadow>,
    pub border_radius: BorderRadiusScale,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColorPalette {
    pub primary: String,
    pub secondary: String,
    pub accent: String,
    pub background: String,
    pub surface: String,
    pub error: String,
    pub warning: String,
    pub success: String,
    pub text_primary: String,
    pub text_secondary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Typography {
    pub font_family_primary: String,
    pub font_family_secondary: String,
    pub scale: Vec<TypographyLevel>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TypographyLevel {
    pub name: String, // h1, h2, body, etc.
    pub size: String,
    pub weight: String,
    pub line_height: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpacingScale {
    pub base: u32, // in pixels
    pub scale: Vec<u32>, // [4, 8, 16, 24, 32, 48, 64]
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Shadow {
    pub name: String,
    pub value: String, // CSS shadow value
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BorderRadiusScale {
    pub small: String,
    pub medium: String,
    pub large: String,
    pub full: String,
}

/// Component specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComponentSpec {
    pub name: String,
    pub component_type: ComponentType,
    pub description: String,
    pub props: Vec<ComponentProp>,
    pub states: Vec<String>,
    pub variants: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ComponentType {
    Button,
    Input,
    Card,
    Modal,
    Navigation,
    Form,
    List,
    Table,
    Chart,
    Custom,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComponentProp {
    pub name: String,
    pub prop_type: String,
    pub required: bool,
    pub default_value: Option<String>,
}

/// User flow specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserFlow {
    pub flow_name: String,
    pub description: String,
    pub steps: Vec<FlowStep>,
    pub entry_point: String,
    pub success_criteria: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlowStep {
    pub step_number: u32,
    pub screen_name: String,
    pub action: String,
    pub user_goal: String,
}

/// Layout specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayoutSpec {
    pub layout_name: String,
    pub layout_type: LayoutType,
    pub sections: Vec<LayoutSection>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LayoutType {
    Landing,
    Dashboard,
    Details,
    Form,
    List,
    Settings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayoutSection {
    pub section_name: String,
    pub components: Vec<String>,
    pub grid_columns: u32,
}

/// Accessibility specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessibilitySpec {
    pub wcag_level: WCAGLevel,
    pub aria_labels: bool,
    pub keyboard_navigation: bool,
    pub screen_reader_support: bool,
    pub color_contrast_ratio: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WCAGLevel {
    A,
    AA,
    AAA,
}

/// Responsive breakpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Breakpoint {
    pub name: String,
    pub min_width: u32,
    pub max_width: Option<u32>,
}

/// Infrastructure specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InfrastructureSpec {
    pub opportunity_id: uuid::Uuid,
    pub cloud_provider: CloudProvider,
    pub database: DatabaseSpec,
    pub hosting: HostingSpec,
    pub api: APISpec,
    pub storage: StorageSpec,
    pub monitoring: MonitoringSpec,
    pub ci_cd: CICDSpec,
    pub estimated_monthly_cost: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CloudProvider {
    AWS,
    GCP,
    Azure,
    Vercel,
    Railway,
    FlyIO,
    DigitalOcean,
}

/// Database specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseSpec {
    pub database_type: DatabaseType,
    pub schema: Vec<TableSchema>,
    pub indexes: Vec<IndexSpec>,
    pub migrations: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DatabaseType {
    PostgreSQL,
    MySQL,
    MongoDB,
    Redis,
    SQLite,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableSchema {
    pub table_name: String,
    pub columns: Vec<ColumnSpec>,
    pub primary_key: String,
    pub foreign_keys: Vec<ForeignKeySpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColumnSpec {
    pub name: String,
    pub data_type: String,
    pub nullable: bool,
    pub unique: bool,
    pub default: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForeignKeySpec {
    pub column: String,
    pub references_table: String,
    pub references_column: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexSpec {
    pub name: String,
    pub table: String,
    pub columns: Vec<String>,
    pub unique: bool,
}

/// Hosting specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HostingSpec {
    pub frontend_host: String,
    pub backend_host: String,
    pub domain: Option<String>,
    pub ssl_enabled: bool,
    pub cdn_enabled: bool,
}

/// API specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct APISpec {
    pub base_url: String,
    pub api_version: String,
    pub endpoints: Vec<EndpointSpec>,
    pub authentication: AuthSpec,
    pub rate_limiting: RateLimitSpec,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EndpointSpec {
    pub path: String,
    pub method: HttpMethod,
    pub description: String,
    pub request_body: Option<String>,
    pub response_schema: String,
    pub auth_required: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HttpMethod {
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthSpec {
    pub auth_type: AuthType,
    pub provider: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AuthType {
    JWT,
    OAuth,
    APIKey,
    Session,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimitSpec {
    pub enabled: bool,
    pub requests_per_minute: u32,
    pub burst_size: u32,
}

/// Storage specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageSpec {
    pub object_storage: bool,
    pub provider: String,
    pub buckets: Vec<BucketSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BucketSpec {
    pub name: String,
    pub purpose: String,
    pub public: bool,
}

/// Monitoring specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringSpec {
    pub error_tracking: bool,
    pub error_tracking_provider: String,
    pub metrics: bool,
    pub metrics_provider: String,
    pub logging: bool,
    pub logging_provider: String,
}

/// CI/CD specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CICDSpec {
    pub provider: String, // GitHub Actions, GitLab CI, etc.
    pub build_on_push: bool,
    pub auto_deploy: bool,
    pub environments: Vec<String>, // development, staging, production
    pub test_coverage_threshold: f64,
}

/// Complete product development specification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductDevelopmentSpec {
    pub opportunity_id: uuid::Uuid,
    pub design: DesignSpecification,
    pub infrastructure: InfrastructureSpec,
    pub tech_stack: crate::models::TechStack,
    pub development_timeline: DevelopmentTimeline,
    pub quality_gates: Vec<QualityGate>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentTimeline {
    pub total_days: u32,
    pub phases: Vec<DevelopmentPhase>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentPhase {
    pub phase_name: String,
    pub duration_days: u32,
    pub tasks: Vec<String>,
    pub dependencies: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityGate {
    pub gate_name: String,
    pub criteria: Vec<String>,
    pub required: bool,
}

/// Product development result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductDevelopmentResult {
    pub opportunity_id: uuid::Uuid,
    pub status: DevelopmentStatus,
    pub specification: ProductDevelopmentSpec,
    pub repository_url: Option<String>,
    pub deployment_url: Option<String>,
    pub completion_percentage: f64,
    pub phases_completed: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DevelopmentStatus {
    Planning,
    Designing,
    InfrastructureSetup,
    Development,
    Testing,
    Deployment,
    Complete,
    Failed,
}
