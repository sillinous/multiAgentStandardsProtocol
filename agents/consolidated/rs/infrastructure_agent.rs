//! Infrastructure Agent - Cloud provisioning and infrastructure setup

use super::models::*;
use crate::models::Opportunity;
use crate::validation::TechnicalFeasibilityReport;
use agentic_core::{Agent, AgentRole, Result};
use agentic_runtime::llm::{LlmClient, LlmRequest, LlmMessage, MessageRole};
use std::sync::Arc;
use tracing::{info, debug};

/// Infrastructure Agent handles cloud provisioning and setup
pub struct InfrastructureAgent {
    agent: Agent,
    llm_client: Arc<dyn LlmClient>,
}

impl InfrastructureAgent {
    pub fn new(llm_client: Arc<dyn LlmClient>) -> Self {
        let mut agent = Agent::new(
            "InfrastructureArchitect",
            "Provisions cloud infrastructure, databases, hosting, and CI/CD pipelines",
            AgentRole::Worker,
            "claude-3-5-sonnet-20241022",
            "anthropic",
        );

        agent.add_tag("business");
        agent.add_tag("product-development");
        agent.add_tag("infrastructure");

        // Configure agent to be standards-compliant (A2A, MCP protocols)
        crate::configure_standards_compliant_agent(&mut agent);

        Self { agent, llm_client }
    }

    pub fn agent(&self) -> &Agent {
        &self.agent
    }

    /// Generate complete infrastructure specification
    pub async fn provision(
        &self,
        opportunity: &Opportunity,
        technical_report: Option<&TechnicalFeasibilityReport>,
    ) -> Result<InfrastructureSpec> {
        info!("🏗️  Provisioning infrastructure for: {}", opportunity.title);

        // Select cloud provider
        let cloud_provider = self.select_cloud_provider(opportunity, technical_report).await?;

        // Design database
        let database = self.design_database(opportunity).await?;

        // Configure hosting
        let hosting = self.configure_hosting(opportunity, cloud_provider).await?;

        // Define API
        let api = self.define_api(opportunity).await?;

        // Configure storage
        let storage = self.configure_storage(opportunity).await?;

        // Setup monitoring
        let monitoring = self.setup_monitoring(opportunity).await?;

        // Configure CI/CD
        let ci_cd = self.configure_ci_cd(opportunity).await?;

        // Estimate monthly cost
        let estimated_monthly_cost = self.estimate_monthly_cost(
            cloud_provider,
            &database,
            &hosting,
            &storage,
        );

        Ok(InfrastructureSpec {
            opportunity_id: opportunity.id,
            cloud_provider,
            database,
            hosting,
            api,
            storage,
            monitoring,
            ci_cd,
            estimated_monthly_cost,
        })
    }

    /// Select optimal cloud provider
    async fn select_cloud_provider(
        &self,
        opportunity: &Opportunity,
        technical_report: Option<&TechnicalFeasibilityReport>,
    ) -> Result<CloudProvider> {
        debug!("Selecting cloud provider");

        // Use tech stack recommendation if available
        if let Some(report) = technical_report {
            if let Some(hosting) = &report.recommended_tech_stack.hosting {
                if hosting.contains("Vercel") {
                    return Ok(CloudProvider::Vercel);
                } else if hosting.contains("Railway") {
                    return Ok(CloudProvider::Railway);
                } else if hosting.contains("Fly") {
                    return Ok(CloudProvider::FlyIO);
                }
            }
        }

        // Default based on product type and complexity
        let complexity = opportunity.implementation_estimate.complexity_score;

        if complexity < 5.0 {
            Ok(CloudProvider::Vercel) // Simple apps
        } else if complexity < 7.0 {
            Ok(CloudProvider::Railway) // Moderate apps
        } else {
            Ok(CloudProvider::AWS) // Complex apps
        }
    }

    /// Design database schema
    async fn design_database(&self, opportunity: &Opportunity) -> Result<DatabaseSpec> {
        debug!("Designing database schema");

        let mut tables = Vec::new();

        // User table (common for most apps)
        tables.push(TableSchema {
            table_name: "users".to_string(),
            columns: vec![
                ColumnSpec {
                    name: "id".to_string(),
                    data_type: "UUID".to_string(),
                    nullable: false,
                    unique: true,
                    default: Some("gen_random_uuid()".to_string()),
                },
                ColumnSpec {
                    name: "email".to_string(),
                    data_type: "VARCHAR(255)".to_string(),
                    nullable: false,
                    unique: true,
                    default: None,
                },
                ColumnSpec {
                    name: "password_hash".to_string(),
                    data_type: "VARCHAR(255)".to_string(),
                    nullable: false,
                    unique: false,
                    default: None,
                },
                ColumnSpec {
                    name: "created_at".to_string(),
                    data_type: "TIMESTAMP".to_string(),
                    nullable: false,
                    unique: false,
                    default: Some("NOW()".to_string()),
                },
                ColumnSpec {
                    name: "updated_at".to_string(),
                    data_type: "TIMESTAMP".to_string(),
                    nullable: false,
                    unique: false,
                    default: Some("NOW()".to_string()),
                },
            ],
            primary_key: "id".to_string(),
            foreign_keys: vec![],
        });

        // Domain-specific tables
        if opportunity.domain.to_lowercase().contains("saas") {
            tables.push(TableSchema {
                table_name: "subscriptions".to_string(),
                columns: vec![
                    ColumnSpec {
                        name: "id".to_string(),
                        data_type: "UUID".to_string(),
                        nullable: false,
                        unique: true,
                        default: Some("gen_random_uuid()".to_string()),
                    },
                    ColumnSpec {
                        name: "user_id".to_string(),
                        data_type: "UUID".to_string(),
                        nullable: false,
                        unique: false,
                        default: None,
                    },
                    ColumnSpec {
                        name: "plan_name".to_string(),
                        data_type: "VARCHAR(100)".to_string(),
                        nullable: false,
                        unique: false,
                        default: None,
                    },
                    ColumnSpec {
                        name: "status".to_string(),
                        data_type: "VARCHAR(50)".to_string(),
                        nullable: false,
                        unique: false,
                        default: None,
                    },
                    ColumnSpec {
                        name: "started_at".to_string(),
                        data_type: "TIMESTAMP".to_string(),
                        nullable: false,
                        unique: false,
                        default: Some("NOW()".to_string()),
                    },
                ],
                primary_key: "id".to_string(),
                foreign_keys: vec![ForeignKeySpec {
                    column: "user_id".to_string(),
                    references_table: "users".to_string(),
                    references_column: "id".to_string(),
                }],
            });
        }

        // Indexes
        let indexes = vec![
            IndexSpec {
                name: "idx_users_email".to_string(),
                table: "users".to_string(),
                columns: vec!["email".to_string()],
                unique: true,
            },
        ];

        Ok(DatabaseSpec {
            database_type: DatabaseType::PostgreSQL,
            schema: tables,
            indexes,
            migrations: true,
        })
    }

    /// Configure hosting
    async fn configure_hosting(
        &self,
        _opportunity: &Opportunity,
        cloud_provider: CloudProvider,
    ) -> Result<HostingSpec> {
        debug!("Configuring hosting");

        let (frontend_host, backend_host) = match cloud_provider {
            CloudProvider::Vercel => ("vercel.app".to_string(), "vercel.app".to_string()),
            CloudProvider::Railway => ("railway.app".to_string(), "railway.app".to_string()),
            CloudProvider::FlyIO => ("fly.dev".to_string(), "fly.dev".to_string()),
            _ => ("compute.amazonaws.com".to_string(), "compute.amazonaws.com".to_string()),
        };

        Ok(HostingSpec {
            frontend_host,
            backend_host,
            domain: None, // Can be configured later
            ssl_enabled: true,
            cdn_enabled: true,
        })
    }

    /// Define API specification
    async fn define_api(&self, opportunity: &Opportunity) -> Result<APISpec> {
        debug!("Defining API specification");

        let mut endpoints = Vec::new();

        // Authentication endpoints
        endpoints.push(EndpointSpec {
            path: "/api/auth/register".to_string(),
            method: HttpMethod::POST,
            description: "Register new user".to_string(),
            request_body: Some("{ email, password }".to_string()),
            response_schema: "{ user, token }".to_string(),
            auth_required: false,
        });

        endpoints.push(EndpointSpec {
            path: "/api/auth/login".to_string(),
            method: HttpMethod::POST,
            description: "User login".to_string(),
            request_body: Some("{ email, password }".to_string()),
            response_schema: "{ user, token }".to_string(),
            auth_required: false,
        });

        // User endpoints
        endpoints.push(EndpointSpec {
            path: "/api/users/me".to_string(),
            method: HttpMethod::GET,
            description: "Get current user".to_string(),
            request_body: None,
            response_schema: "{ user }".to_string(),
            auth_required: true,
        });

        // Domain-specific endpoints
        if opportunity.domain.to_lowercase().contains("saas") {
            endpoints.push(EndpointSpec {
                path: "/api/subscriptions".to_string(),
                method: HttpMethod::GET,
                description: "List user subscriptions".to_string(),
                request_body: None,
                response_schema: "{ subscriptions: [] }".to_string(),
                auth_required: true,
            });

            endpoints.push(EndpointSpec {
                path: "/api/subscriptions".to_string(),
                method: HttpMethod::POST,
                description: "Create subscription".to_string(),
                request_body: Some("{ plan_name }".to_string()),
                response_schema: "{ subscription }".to_string(),
                auth_required: true,
            });
        }

        Ok(APISpec {
            base_url: "/api".to_string(),
            api_version: "v1".to_string(),
            endpoints,
            authentication: AuthSpec {
                auth_type: AuthType::JWT,
                provider: Some("Clerk".to_string()),
            },
            rate_limiting: RateLimitSpec {
                enabled: true,
                requests_per_minute: 60,
                burst_size: 10,
            },
        })
    }

    /// Configure storage
    async fn configure_storage(&self, _opportunity: &Opportunity) -> Result<StorageSpec> {
        debug!("Configuring storage");

        Ok(StorageSpec {
            object_storage: true,
            provider: "AWS S3".to_string(),
            buckets: vec![
                BucketSpec {
                    name: "user-uploads".to_string(),
                    purpose: "User uploaded files".to_string(),
                    public: false,
                },
                BucketSpec {
                    name: "static-assets".to_string(),
                    purpose: "Public static assets".to_string(),
                    public: true,
                },
            ],
        })
    }

    /// Setup monitoring
    async fn setup_monitoring(&self, _opportunity: &Opportunity) -> Result<MonitoringSpec> {
        debug!("Setting up monitoring");

        Ok(MonitoringSpec {
            error_tracking: true,
            error_tracking_provider: "Sentry".to_string(),
            metrics: true,
            metrics_provider: "Prometheus".to_string(),
            logging: true,
            logging_provider: "CloudWatch".to_string(),
        })
    }

    /// Configure CI/CD
    async fn configure_ci_cd(&self, _opportunity: &Opportunity) -> Result<CICDSpec> {
        debug!("Configuring CI/CD");

        Ok(CICDSpec {
            provider: "GitHub Actions".to_string(),
            build_on_push: true,
            auto_deploy: true,
            environments: vec![
                "development".to_string(),
                "staging".to_string(),
                "production".to_string(),
            ],
            test_coverage_threshold: 80.0,
        })
    }

    /// Estimate monthly infrastructure cost
    fn estimate_monthly_cost(
        &self,
        cloud_provider: CloudProvider,
        database: &DatabaseSpec,
        _hosting: &HostingSpec,
        storage: &StorageSpec,
    ) -> f64 {
        let mut cost = 0.0;

        // Base hosting cost
        cost += match cloud_provider {
            CloudProvider::Vercel => 20.0,
            CloudProvider::Railway => 5.0,
            CloudProvider::FlyIO => 0.0, // Free tier
            CloudProvider::AWS => 50.0,
            CloudProvider::GCP => 50.0,
            CloudProvider::Azure => 50.0,
            CloudProvider::DigitalOcean => 12.0,
        };

        // Database cost
        cost += match database.database_type {
            DatabaseType::PostgreSQL => 15.0,
            DatabaseType::MySQL => 15.0,
            DatabaseType::MongoDB => 25.0,
            DatabaseType::Redis => 10.0,
            DatabaseType::SQLite => 0.0,
        };

        // Storage cost (estimate)
        cost += storage.buckets.len() as f64 * 5.0;

        // Monitoring cost
        cost += 15.0;

        cost
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentic_runtime::llm::MockLlmClient;
    use crate::models::ProductType;

    #[tokio::test]
    async fn test_infrastructure_provisioning() {
        let llm = Arc::new(MockLlmClient::new());
        let agent = InfrastructureAgent::new(llm);

        let opp = Opportunity::new(
            "Test SaaS".to_string(),
            "A test product".to_string(),
            "SaaS".to_string(),
            ProductType::SaaS,
        );

        let spec = agent.provision(&opp, None).await.unwrap();

        assert_eq!(spec.opportunity_id, opp.id);
        assert!(!spec.database.schema.is_empty());
        assert!(!spec.api.endpoints.is_empty());
        assert!(spec.estimated_monthly_cost > 0.0);
    }
}
