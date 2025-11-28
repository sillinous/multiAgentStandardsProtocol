"""
Integration Catalog
===================

Catalog of common integrations for APQC process automation.
Organized by category with standard configuration templates.

Version: 1.0.0
Date: 2025-11-25
"""

from typing import Dict, List, Any
import json

# =============================================================================
# INTEGRATION CATALOG
# =============================================================================

INTEGRATION_CATALOG: Dict[str, Dict[str, Any]] = {

    # =========================================================================
    # FINANCE & ACCOUNTING
    # =========================================================================

    "quickbooks_online": {
        "id": "quickbooks_online",
        "name": "QuickBooks Online",
        "category": "finance",
        "type": "rest_api",
        "description": "Cloud accounting software for invoicing, expenses, and financial reporting",
        "capabilities": [
            "create_invoice", "read_invoice", "update_invoice",
            "create_payment", "read_payment",
            "read_vendor", "create_vendor",
            "read_account", "create_journal_entry",
            "read_reports"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "refresh_token", "realm_id"],
        "base_url": "https://quickbooks.api.intuit.com/v3/company/{realm_id}",
        "rate_limit": {"requests_per_minute": 500},
        "documentation_url": "https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice"
    },

    "netsuite": {
        "id": "netsuite",
        "name": "Oracle NetSuite",
        "category": "finance",
        "type": "rest_api",
        "description": "Enterprise ERP system for finance, operations, and commerce",
        "capabilities": [
            "create_invoice", "read_invoice", "update_invoice",
            "create_vendor_bill", "read_vendor_bill",
            "three_way_match", "create_payment",
            "read_general_ledger", "create_journal_entry"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["consumer_key", "consumer_secret", "token_id", "token_secret", "account_id"],
        "base_url": "https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1",
        "rate_limit": {"requests_per_minute": 100},
        "documentation_url": "https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1540811696.html"
    },

    "sap_s4hana": {
        "id": "sap_s4hana",
        "name": "SAP S/4HANA",
        "category": "finance",
        "type": "rest_api",
        "description": "Enterprise resource planning suite for large organizations",
        "capabilities": [
            "invoice_processing", "accounts_payable", "accounts_receivable",
            "general_ledger", "cost_center_accounting",
            "vendor_management", "purchase_order_processing"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "tenant_url"],
        "base_url": "{tenant_url}/sap/opu/odata/sap",
        "rate_limit": {"requests_per_minute": 200},
        "documentation_url": "https://api.sap.com/package/SAPS4HANACloud/all"
    },

    "stripe": {
        "id": "stripe",
        "name": "Stripe",
        "category": "finance",
        "type": "rest_api",
        "description": "Payment processing platform",
        "capabilities": [
            "create_payment_intent", "process_payment", "create_refund",
            "create_customer", "read_transactions",
            "create_invoice", "manage_subscriptions"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key"],
        "base_url": "https://api.stripe.com/v1",
        "rate_limit": {"requests_per_second": 100},
        "documentation_url": "https://stripe.com/docs/api"
    },

    "plaid": {
        "id": "plaid",
        "name": "Plaid",
        "category": "finance",
        "type": "rest_api",
        "description": "Financial data connectivity platform for bank account verification",
        "capabilities": [
            "link_bank_account", "verify_account", "get_transactions",
            "get_balance", "get_identity", "initiate_ach_transfer"
        ],
        "auth_type": "api_key",
        "required_credentials": ["client_id", "secret", "access_token"],
        "base_url": "https://production.plaid.com",
        "rate_limit": {"requests_per_minute": 100},
        "documentation_url": "https://plaid.com/docs/api/"
    },

    # =========================================================================
    # HUMAN RESOURCES
    # =========================================================================

    "workday": {
        "id": "workday",
        "name": "Workday",
        "category": "hr",
        "type": "rest_api",
        "description": "Enterprise cloud HR and finance application",
        "capabilities": [
            "read_employee", "create_employee", "update_employee",
            "process_payroll", "manage_benefits", "time_tracking",
            "performance_management", "compensation_management"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "tenant_name", "refresh_token"],
        "base_url": "https://wd2-impl-services1.workday.com/ccx/api/v1/{tenant_name}",
        "rate_limit": {"requests_per_minute": 100},
        "documentation_url": "https://community.workday.com/sites/default/files/file-hosting/restapi/index.html"
    },

    "bamboohr": {
        "id": "bamboohr",
        "name": "BambooHR",
        "category": "hr",
        "type": "rest_api",
        "description": "HR software for small and medium businesses",
        "capabilities": [
            "read_employee", "create_employee", "update_employee",
            "time_off_requests", "employee_directory",
            "performance_reviews", "onboarding"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key", "subdomain"],
        "base_url": "https://api.bamboohr.com/api/gateway.php/{subdomain}/v1",
        "rate_limit": {"requests_per_minute": 60},
        "documentation_url": "https://documentation.bamboohr.com/reference"
    },

    "adp_workforce": {
        "id": "adp_workforce",
        "name": "ADP Workforce Now",
        "category": "hr",
        "type": "rest_api",
        "description": "Payroll, HR, and benefits platform",
        "capabilities": [
            "process_payroll", "read_employee", "tax_filing",
            "benefits_administration", "time_attendance",
            "direct_deposit", "garnishments"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "cert_path"],
        "base_url": "https://api.adp.com",
        "rate_limit": {"requests_per_minute": 100},
        "documentation_url": "https://developers.adp.com/articles/api/all"
    },

    # =========================================================================
    # CRM & SALES
    # =========================================================================

    "salesforce": {
        "id": "salesforce",
        "name": "Salesforce",
        "category": "crm",
        "type": "rest_api",
        "description": "Customer relationship management platform",
        "capabilities": [
            "create_lead", "read_lead", "convert_lead",
            "create_opportunity", "update_opportunity",
            "create_account", "read_contact",
            "read_reports", "send_email"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "refresh_token", "instance_url"],
        "base_url": "{instance_url}/services/data/v59.0",
        "rate_limit": {"requests_per_day": 100000},
        "documentation_url": "https://developer.salesforce.com/docs/apis"
    },

    "hubspot": {
        "id": "hubspot",
        "name": "HubSpot",
        "category": "crm",
        "type": "rest_api",
        "description": "Inbound marketing, sales, and CRM platform",
        "capabilities": [
            "create_contact", "read_contact", "update_contact",
            "create_deal", "update_deal",
            "create_company", "send_email",
            "create_task", "read_engagement"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "refresh_token"],
        "base_url": "https://api.hubapi.com",
        "rate_limit": {"requests_per_second": 10},
        "documentation_url": "https://developers.hubspot.com/docs/api/overview"
    },

    # =========================================================================
    # DOCUMENT PROCESSING
    # =========================================================================

    "aws_textract": {
        "id": "aws_textract",
        "name": "AWS Textract",
        "category": "documents",
        "type": "rest_api",
        "description": "ML-powered document text and data extraction",
        "capabilities": [
            "extract_text", "extract_tables", "extract_forms",
            "analyze_invoice", "analyze_receipt", "analyze_id_document"
        ],
        "auth_type": "aws_credentials",
        "required_credentials": ["aws_access_key_id", "aws_secret_access_key", "region"],
        "base_url": "https://textract.{region}.amazonaws.com",
        "rate_limit": {"transactions_per_second": 5},
        "documentation_url": "https://docs.aws.amazon.com/textract/latest/dg/what-is.html"
    },

    "google_document_ai": {
        "id": "google_document_ai",
        "name": "Google Document AI",
        "category": "documents",
        "type": "rest_api",
        "description": "Document understanding and data extraction platform",
        "capabilities": [
            "extract_text", "extract_entities", "classify_document",
            "process_invoice", "process_receipt", "process_form"
        ],
        "auth_type": "service_account",
        "required_credentials": ["service_account_json", "project_id", "processor_id"],
        "base_url": "https://documentai.googleapis.com/v1",
        "rate_limit": {"requests_per_minute": 120},
        "documentation_url": "https://cloud.google.com/document-ai/docs"
    },

    "docusign": {
        "id": "docusign",
        "name": "DocuSign",
        "category": "documents",
        "type": "rest_api",
        "description": "Electronic signature and agreement cloud",
        "capabilities": [
            "create_envelope", "send_for_signature", "get_envelope_status",
            "download_signed_document", "create_template", "void_envelope"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "account_id", "base_path"],
        "base_url": "{base_path}/restapi/v2.1/accounts/{account_id}",
        "rate_limit": {"requests_per_hour": 1000},
        "documentation_url": "https://developers.docusign.com/docs/esign-rest-api/"
    },

    # =========================================================================
    # COMMUNICATION
    # =========================================================================

    "slack": {
        "id": "slack",
        "name": "Slack",
        "category": "communication",
        "type": "rest_api",
        "description": "Business messaging and collaboration platform",
        "capabilities": [
            "send_message", "create_channel", "upload_file",
            "add_reaction", "get_user_info", "post_to_thread"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["bot_token", "app_token"],
        "base_url": "https://slack.com/api",
        "rate_limit": {"requests_per_minute": 60},
        "documentation_url": "https://api.slack.com/methods"
    },

    "microsoft_teams": {
        "id": "microsoft_teams",
        "name": "Microsoft Teams",
        "category": "communication",
        "type": "rest_api",
        "description": "Microsoft collaboration and communication platform",
        "capabilities": [
            "send_message", "create_channel", "schedule_meeting",
            "upload_file", "create_team", "add_member"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "tenant_id"],
        "base_url": "https://graph.microsoft.com/v1.0",
        "rate_limit": {"requests_per_second": 10},
        "documentation_url": "https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview"
    },

    "sendgrid": {
        "id": "sendgrid",
        "name": "SendGrid",
        "category": "communication",
        "type": "rest_api",
        "description": "Email delivery and marketing platform",
        "capabilities": [
            "send_email", "send_template_email", "manage_contacts",
            "create_campaign", "get_email_stats"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key"],
        "base_url": "https://api.sendgrid.com/v3",
        "rate_limit": {"emails_per_day": 100},  # Free tier
        "documentation_url": "https://docs.sendgrid.com/api-reference/how-to-use-the-sendgrid-v3-api"
    },

    # =========================================================================
    # AI & ML SERVICES
    # =========================================================================

    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "category": "ai",
        "type": "rest_api",
        "description": "AI language models for text generation and analysis",
        "capabilities": [
            "text_completion", "chat_completion", "embeddings",
            "function_calling", "vision_analysis", "audio_transcription"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key"],
        "base_url": "https://api.openai.com/v1",
        "rate_limit": {"requests_per_minute": 60},
        "documentation_url": "https://platform.openai.com/docs/api-reference"
    },

    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "category": "ai",
        "type": "rest_api",
        "description": "AI assistant for analysis, writing, and coding",
        "capabilities": [
            "text_analysis", "document_summarization", "code_generation",
            "reasoning", "tool_use", "vision_analysis"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key"],
        "base_url": "https://api.anthropic.com/v1",
        "rate_limit": {"requests_per_minute": 60},
        "documentation_url": "https://docs.anthropic.com/en/api"
    },

    # =========================================================================
    # DATA & STORAGE
    # =========================================================================

    "aws_s3": {
        "id": "aws_s3",
        "name": "AWS S3",
        "category": "storage",
        "type": "rest_api",
        "description": "Cloud object storage service",
        "capabilities": [
            "upload_file", "download_file", "list_objects",
            "delete_object", "generate_presigned_url", "copy_object"
        ],
        "auth_type": "aws_credentials",
        "required_credentials": ["aws_access_key_id", "aws_secret_access_key", "region", "bucket_name"],
        "base_url": "https://{bucket_name}.s3.{region}.amazonaws.com",
        "rate_limit": {"requests_per_second": 5500},
        "documentation_url": "https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html"
    },

    "google_cloud_storage": {
        "id": "google_cloud_storage",
        "name": "Google Cloud Storage",
        "category": "storage",
        "type": "rest_api",
        "description": "Cloud object storage for any amount of data",
        "capabilities": [
            "upload_file", "download_file", "list_objects",
            "delete_object", "generate_signed_url"
        ],
        "auth_type": "service_account",
        "required_credentials": ["service_account_json", "project_id", "bucket_name"],
        "base_url": "https://storage.googleapis.com/storage/v1",
        "rate_limit": {"requests_per_second": 1000},
        "documentation_url": "https://cloud.google.com/storage/docs/json_api"
    },

    # =========================================================================
    # WORKFLOW & AUTOMATION
    # =========================================================================

    "zapier": {
        "id": "zapier",
        "name": "Zapier",
        "category": "automation",
        "type": "webhook",
        "description": "Automation platform connecting 5000+ apps",
        "capabilities": [
            "trigger_zap", "receive_webhook", "send_data"
        ],
        "auth_type": "webhook",
        "required_credentials": ["webhook_url"],
        "base_url": "https://hooks.zapier.com",
        "rate_limit": {"tasks_per_month": 750},  # Free tier
        "documentation_url": "https://zapier.com/help/doc/how-get-started-webhooks-zapier"
    },

    "make_integromat": {
        "id": "make_integromat",
        "name": "Make (Integromat)",
        "category": "automation",
        "type": "webhook",
        "description": "Visual automation platform for complex workflows",
        "capabilities": [
            "trigger_scenario", "receive_webhook", "process_data", "iterate_arrays"
        ],
        "auth_type": "webhook",
        "required_credentials": ["webhook_url", "api_key"],
        "base_url": "https://hook.us1.make.com",
        "rate_limit": {"operations_per_month": 1000},  # Free tier
        "documentation_url": "https://www.make.com/en/api-documentation"
    },

    # =========================================================================
    # CUSTOMER SERVICE
    # =========================================================================

    "zendesk": {
        "id": "zendesk",
        "name": "Zendesk",
        "category": "customer_service",
        "type": "rest_api",
        "description": "Customer service and engagement platform",
        "capabilities": [
            "create_ticket", "update_ticket", "read_ticket",
            "create_user", "read_user", "search_tickets",
            "add_comment", "read_satisfaction_ratings"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["subdomain", "client_id", "client_secret", "access_token"],
        "base_url": "https://{subdomain}.zendesk.com/api/v2",
        "rate_limit": {"requests_per_minute": 700},
        "documentation_url": "https://developer.zendesk.com/api-reference"
    },

    "freshdesk": {
        "id": "freshdesk",
        "name": "Freshdesk",
        "category": "customer_service",
        "type": "rest_api",
        "description": "Cloud-based customer support software",
        "capabilities": [
            "create_ticket", "update_ticket", "read_ticket",
            "create_contact", "read_contact", "read_agents",
            "add_note", "read_satisfaction_ratings"
        ],
        "auth_type": "api_key",
        "required_credentials": ["domain", "api_key"],
        "base_url": "https://{domain}.freshdesk.com/api/v2",
        "rate_limit": {"requests_per_minute": 50},
        "documentation_url": "https://developers.freshdesk.com/api/"
    },

    "intercom": {
        "id": "intercom",
        "name": "Intercom",
        "category": "customer_service",
        "type": "rest_api",
        "description": "Customer messaging platform for sales, marketing, and support",
        "capabilities": [
            "create_conversation", "read_conversation", "reply_to_conversation",
            "create_contact", "read_contact", "update_contact",
            "send_message", "read_events"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["access_token"],
        "base_url": "https://api.intercom.io",
        "rate_limit": {"requests_per_minute": 1000},
        "documentation_url": "https://developers.intercom.com/docs"
    },

    # =========================================================================
    # IT SERVICE MANAGEMENT
    # =========================================================================

    "servicenow": {
        "id": "servicenow",
        "name": "ServiceNow",
        "category": "it_service",
        "type": "rest_api",
        "description": "Enterprise IT service management platform",
        "capabilities": [
            "create_incident", "update_incident", "read_incident",
            "create_change_request", "read_change_request",
            "create_problem", "read_problem",
            "read_cmdb", "update_cmdb"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["instance_url", "client_id", "client_secret"],
        "base_url": "{instance_url}/api/now",
        "rate_limit": {"requests_per_minute": 500},
        "documentation_url": "https://developer.servicenow.com/dev.do#!/reference"
    },

    "jira": {
        "id": "jira",
        "name": "Atlassian Jira",
        "category": "it_service",
        "type": "rest_api",
        "description": "Issue tracking and project management",
        "capabilities": [
            "create_issue", "update_issue", "read_issue",
            "search_issues", "add_comment", "transition_issue",
            "read_project", "read_sprint"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["cloud_id", "client_id", "client_secret", "access_token"],
        "base_url": "https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3",
        "rate_limit": {"requests_per_minute": 500},
        "documentation_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/"
    },

    "pagerduty": {
        "id": "pagerduty",
        "name": "PagerDuty",
        "category": "it_service",
        "type": "rest_api",
        "description": "Incident response and on-call management platform",
        "capabilities": [
            "create_incident", "update_incident", "read_incident",
            "acknowledge_incident", "resolve_incident",
            "read_services", "read_schedules", "read_escalation_policies"
        ],
        "auth_type": "api_key",
        "required_credentials": ["api_key"],
        "base_url": "https://api.pagerduty.com",
        "rate_limit": {"requests_per_minute": 900},
        "documentation_url": "https://developer.pagerduty.com/api-reference/"
    },

    # =========================================================================
    # OPERATIONS & SUPPLY CHAIN
    # =========================================================================

    "sap_ariba": {
        "id": "sap_ariba",
        "name": "SAP Ariba",
        "category": "operations",
        "type": "rest_api",
        "description": "Procurement and supply chain collaboration network",
        "capabilities": [
            "create_purchase_order", "read_purchase_order",
            "create_invoice", "read_invoice",
            "supplier_management", "contract_management",
            "sourcing_events"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "realm"],
        "base_url": "https://openapi.ariba.com/api",
        "rate_limit": {"requests_per_minute": 100},
        "documentation_url": "https://developer.ariba.com/"
    },

    "coupa": {
        "id": "coupa",
        "name": "Coupa",
        "category": "operations",
        "type": "rest_api",
        "description": "Business spend management platform",
        "capabilities": [
            "create_requisition", "read_requisition",
            "create_purchase_order", "read_purchase_order",
            "create_invoice", "read_invoice",
            "supplier_management", "expense_management"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "instance_url"],
        "base_url": "{instance_url}/api",
        "rate_limit": {"requests_per_minute": 300},
        "documentation_url": "https://compass.coupa.com/en-us/products/product-documentation/integration-technical-documentation/the-coupa-core-api"
    },

    "oracle_scm": {
        "id": "oracle_scm",
        "name": "Oracle SCM Cloud",
        "category": "operations",
        "type": "rest_api",
        "description": "Supply chain management cloud application suite",
        "capabilities": [
            "inventory_management", "order_management",
            "procurement", "manufacturing",
            "logistics", "demand_planning"
        ],
        "auth_type": "oauth2",
        "required_credentials": ["client_id", "client_secret", "pod_url"],
        "base_url": "{pod_url}/fscmRestApi/resources",
        "rate_limit": {"requests_per_minute": 200},
        "documentation_url": "https://docs.oracle.com/en/cloud/saas/supply-chain-management/index.html"
    }
}


def get_integration(integration_id: str) -> Dict[str, Any]:
    """Get integration by ID"""
    return INTEGRATION_CATALOG.get(integration_id)


def get_integrations_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all integrations in a category"""
    return [
        integration
        for integration in INTEGRATION_CATALOG.values()
        if integration["category"] == category
    ]


def get_all_categories() -> List[str]:
    """Get all integration categories"""
    return list(set(i["category"] for i in INTEGRATION_CATALOG.values()))


def search_integrations(capability: str) -> List[Dict[str, Any]]:
    """Find integrations that have a specific capability"""
    return [
        integration
        for integration in INTEGRATION_CATALOG.values()
        if capability in integration.get("capabilities", [])
    ]


def export_catalog_json(filepath: str = None) -> str:
    """Export catalog to JSON"""
    catalog_json = json.dumps(INTEGRATION_CATALOG, indent=2)
    if filepath:
        with open(filepath, 'w') as f:
            f.write(catalog_json)
    return catalog_json


# Category summary for quick reference
CATEGORY_SUMMARY = {
    "finance": ["quickbooks_online", "netsuite", "sap_s4hana", "stripe", "plaid"],
    "hr": ["workday", "bamboohr", "adp_workforce"],
    "crm": ["salesforce", "hubspot"],
    "documents": ["aws_textract", "google_document_ai", "docusign"],
    "communication": ["slack", "microsoft_teams", "sendgrid"],
    "ai": ["openai", "anthropic"],
    "storage": ["aws_s3", "google_cloud_storage"],
    "automation": ["zapier", "make_integromat"],
    "customer_service": ["zendesk", "freshdesk", "intercom"],
    "it_service": ["servicenow", "jira", "pagerduty"],
    "operations": ["sap_ariba", "coupa", "oracle_scm"]
}
