"""
Generate Level 5 Task Agents

Creates 30 fundamental task agents that serve as building blocks
for higher-level activity, process, and strategic agents.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_agent_template(agent_spec):
    """Generate agent code from specification"""

    agent_id = agent_spec["agent_id"]
    agent_type = agent_spec["agent_type"]
    name = agent_spec["name"]
    description = agent_spec["description"]
    category = agent_spec["category"]
    capabilities = agent_spec["capabilities"]
    inputs = agent_spec["inputs"]
    outputs = agent_spec["outputs"]

    # Convert agent_id to class name
    class_name = (
        "".join(word.title() for word in agent_id.replace("_agent", "").split("_")) + "Agent"
    )

    template = f'''"""
{name}

Level 5 Task Agent
Category: {category}

{description}

Capabilities:
{chr(10).join(f"- {cap}" for cap in capabilities)}

Inputs:
{chr(10).join(f"- {key}: {value}" for key, value in inputs.items())}

Outputs:
{chr(10).join(f"- {key}: {value}" for key, value in outputs.items())}
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import base agent
from superstandard.agents.base.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {class_name}(BaseAgent):
    """
    {name}

    {description}

    This is a Level 5 task agent - designed for single-purpose execution
    and maximum reusability across APQC categories.
    """

    def __init__(self, agent_id: str = "{agent_id}", config: Optional[Dict[str, Any]] = None):
        """
        Initialize {name}

        Args:
            agent_id: Unique identifier for this agent instance
            config: Optional configuration dictionary
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="{agent_type}",
            capabilities={capabilities},
            config=config or {{}}
        )

        # Agent-specific initialization
        self.metadata = {{
            "level": 5,
            "category": "{category}",
            "reusable": True,
            "composable": True,
            "stateless": True,
            "framework": "APQC 7.0.1"
        }}

        logger.info(f"Initialized {name} [{{self.agent_id}}]")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the {agent_type.replace('_', ' ')} task

        Args:
            task: Task parameters containing:
                {chr(10).join(f"- {key}: {value}" for key, value in inputs.items())}

        Returns:
            Result dictionary containing:
                {chr(10).join(f"- {key}: {value}" for key, value in outputs.items())}
        """
        try:
            logger.info(f"[{{self.agent_id}}] Executing {agent_type} task")

            # Validate inputs
            self._validate_inputs(task)

            # Execute main task logic
            result = await self._execute_core_logic(task)

            # Format output
            output = self._format_output(result)

            logger.info(f"[{{self.agent_id}}] Task completed successfully")

            return {{
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "result": output
            }}

        except Exception as e:
            logger.error(f"[{{self.agent_id}}] Task failed: {{str(e)}}")
            return {{
                "status": "error",
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }}

    def _validate_inputs(self, task: Dict[str, Any]) -> None:
        """
        Validate task inputs

        Args:
            task: Task parameters to validate

        Raises:
            ValueError: If required inputs are missing or invalid
        """
        required_fields = {list(inputs.keys())}

        for field in required_fields:
            if field not in task:
                raise ValueError(f"Missing required field: {{field}}")

    async def _execute_core_logic(self, task: Dict[str, Any]) -> Any:
        """
        Execute the core task logic

        This method contains the main implementation of the task.
        Override in subclasses for specific functionality.

        Args:
            task: Validated task parameters

        Returns:
            Raw task result
        """
        # TODO: Implement specific task logic
        # This is a template - actual implementation would go here

        logger.info(f"[{{self.agent_id}}] Executing core logic for {agent_type}")

        # Placeholder implementation
        result = {{
            "executed": True,
            "task_type": "{agent_type}",
            "inputs_received": list(task.keys())
        }}

        # Simulate async work
        await asyncio.sleep(0.1)

        return result

    def _format_output(self, result: Any) -> Dict[str, Any]:
        """
        Format raw result into standardized output

        Args:
            result: Raw result from core logic

        Returns:
            Formatted output dictionary
        """
        return {{
            "data": result,
            "metadata": {{
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "level": 5,
                "category": "{category}",
                "timestamp": datetime.utcnow().isoformat()
            }}
        }}

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages (A2A protocol)

        Args:
            message: Incoming message

        Returns:
            Response message
        """
        message_type = message.get("type", "unknown")

        if message_type == "task":
            return await self.execute_task(message.get("payload", {{}}))
        elif message_type == "status":
            return self.get_status()
        elif message_type == "capabilities":
            return self.get_capabilities()
        else:
            return {{
                "status": "error",
                "error": f"Unknown message type: {{message_type}}"
            }}

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status

        Returns:
            Status dictionary
        """
        return {{
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": "ready",
            "capabilities": self.capabilities,
            "metadata": self.metadata
        }}

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent capabilities

        Returns:
            Capabilities dictionary
        """
        return {{
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "inputs": {inputs},
            "outputs": {outputs},
            "level": 5,
            "reusable": True,
            "composable": True
        }}


# Example usage
async def main():
    """Example usage of {name}"""

    # Create agent instance
    agent = {class_name}()

    # Example task
    task = {{
        # Add example inputs here
        {chr(10).join(f'        # "{key}": "example_{key}",' for key in inputs.keys())}
    }}

    # Execute task
    result = await agent.execute_task(task)

    print(f"Result: {{result}}")


if __name__ == "__main__":
    asyncio.run(main())
'''

    return template


def create_agent_file(agent_spec, output_dir):
    """Create agent file from specification"""

    agent_id = agent_spec["agent_id"]
    category = agent_spec["category"]

    # Create category directory
    category_path = os.path.join(output_dir, "tasks", category)
    os.makedirs(category_path, exist_ok=True)

    # Generate filename
    filename = f"{agent_id}_v1.py"
    file_path = os.path.join(category_path, filename)

    # Generate code
    code = get_agent_template(agent_spec)

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    return file_path


def main():
    """Generate all 30 Level 5 task agents"""

    # Output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "library"

    print("=" * 80)
    print("LEVEL 5 TASK AGENT GENERATOR")
    print("=" * 80)
    print()

    # Define all 30 agents
    agents = [
        # CATEGORY A: DATA EXTRACTION
        {
            "agent_id": "web_scraping_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "Web Scraping Task Agent",
            "description": "Extract structured data from websites",
            "capabilities": [
                "web_scraping",
                "javascript_rendering",
                "rate_limiting",
                "proxy_support",
            ],
            "inputs": {"url": "string", "selectors": "dict", "rules": "dict"},
            "outputs": {"data": "dict", "metadata": "dict"},
        },
        {
            "agent_id": "pdf_parsing_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "PDF Parsing Task Agent",
            "description": "Extract text, tables, and images from PDF documents",
            "capabilities": ["text_extraction", "table_parsing", "image_extraction", "ocr_support"],
            "inputs": {"pdf_path": "string", "extraction_mode": "string"},
            "outputs": {"text": "string", "tables": "list", "images": "list"},
        },
        {
            "agent_id": "api_data_fetcher_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "API Data Fetcher Task Agent",
            "description": "Retrieve data from REST/GraphQL APIs",
            "capabilities": ["rest_api", "graphql", "oauth", "rate_limiting"],
            "inputs": {"endpoint": "string", "auth": "dict", "params": "dict"},
            "outputs": {"data": "dict", "status_code": "int"},
        },
        {
            "agent_id": "database_query_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "Database Query Task Agent",
            "description": "Execute SQL queries and return results",
            "capabilities": ["sql_execution", "connection_pooling", "query_validation"],
            "inputs": {"connection_string": "string", "query": "string"},
            "outputs": {"results": "list", "row_count": "int"},
        },
        {
            "agent_id": "email_extractor_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "Email Content Extractor Task Agent",
            "description": "Extract structured data from emails",
            "capabilities": ["imap_support", "gmail_api", "attachment_extraction"],
            "inputs": {"email_source": "string", "filters": "dict"},
            "outputs": {"emails": "list", "metadata": "dict"},
        },
        {
            "agent_id": "file_scanner_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "File System Scanner Task Agent",
            "description": "Scan directories and catalog files",
            "capabilities": ["recursive_scan", "metadata_extraction", "hash_calculation"],
            "inputs": {"directory_path": "string", "patterns": "list"},
            "outputs": {"files": "list", "metadata": "dict"},
        },
        {
            "agent_id": "image_ocr_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "Image OCR Task Agent",
            "description": "Extract text from images using OCR",
            "capabilities": ["ocr_processing", "language_detection", "confidence_scoring"],
            "inputs": {"image_path": "string", "language": "string"},
            "outputs": {"text": "string", "confidence": "float"},
        },
        {
            "agent_id": "social_media_collector_task_agent",
            "agent_type": "data_extraction",
            "category": "data_extraction",
            "name": "Social Media Data Collector Task Agent",
            "description": "Collect posts and metrics from social platforms",
            "capabilities": ["multi_platform", "api_management", "sentiment_tagging"],
            "inputs": {"platform": "string", "search_terms": "list", "date_range": "dict"},
            "outputs": {"posts": "list", "metrics": "dict"},
        },
        # CATEGORY B: DATA TRANSFORMATION
        {
            "agent_id": "data_cleaning_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Cleaning Task Agent",
            "description": "Clean, normalize, and deduplicate data",
            "capabilities": [
                "missing_value_handling",
                "deduplication",
                "validation",
                "standardization",
            ],
            "inputs": {"data": "dict", "cleaning_rules": "dict"},
            "outputs": {"cleaned_data": "dict", "quality_report": "dict"},
        },
        {
            "agent_id": "data_enrichment_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Enrichment Task Agent",
            "description": "Append additional data from external sources",
            "capabilities": ["company_enrichment", "contact_enrichment", "geographic_enrichment"],
            "inputs": {"records": "list", "enrichment_rules": "dict"},
            "outputs": {"enriched_records": "list", "enrichment_stats": "dict"},
        },
        {
            "agent_id": "data_categorization_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Categorization Task Agent",
            "description": "Classify records into predefined categories",
            "capabilities": ["rule_based_classification", "ml_classification", "multi_label"],
            "inputs": {"records": "list", "categories": "list"},
            "outputs": {"categorized_records": "list", "confidence_scores": "dict"},
        },
        {
            "agent_id": "data_aggregation_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Aggregation Task Agent",
            "description": "Group and aggregate data by dimensions",
            "capabilities": ["multi_dimensional_grouping", "aggregation_functions", "pivot_tables"],
            "inputs": {"dataset": "list", "dimensions": "list", "metrics": "list"},
            "outputs": {"aggregated_data": "dict", "summary_stats": "dict"},
        },
        {
            "agent_id": "data_validation_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Validation Task Agent",
            "description": "Validate data against schemas and business rules",
            "capabilities": ["schema_validation", "business_rule_validation", "error_reporting"],
            "inputs": {"data": "dict", "schema": "dict", "rules": "list"},
            "outputs": {"validation_result": "bool", "errors": "list"},
        },
        {
            "agent_id": "data_formatting_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Data Formatting Task Agent",
            "description": "Convert data between formats",
            "capabilities": ["format_conversion", "schema_mapping", "compression"],
            "inputs": {"data": "dict", "source_format": "string", "target_format": "string"},
            "outputs": {"formatted_data": "dict", "format_info": "dict"},
        },
        {
            "agent_id": "text_normalization_task_agent",
            "agent_type": "data_transformation",
            "category": "data_transformation",
            "name": "Text Normalization Task Agent",
            "description": "Normalize text for consistent processing",
            "capabilities": [
                "case_normalization",
                "punctuation_handling",
                "stemming",
                "lemmatization",
            ],
            "inputs": {"text": "string", "normalization_rules": "dict"},
            "outputs": {"normalized_text": "string", "transformations": "list"},
        },
        # CATEGORY C: ANALYSIS
        {
            "agent_id": "sentiment_analysis_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Sentiment Analysis Task Agent",
            "description": "Analyze sentiment of text content",
            "capabilities": ["sentiment_scoring", "emotion_detection", "aspect_based_sentiment"],
            "inputs": {"text": "string"},
            "outputs": {"sentiment_score": "float", "label": "string", "confidence": "float"},
        },
        {
            "agent_id": "entity_extraction_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Entity Extraction Task Agent",
            "description": "Extract named entities from text",
            "capabilities": ["ner", "entity_linking", "coreference_resolution"],
            "inputs": {"text": "string"},
            "outputs": {"entities": "list", "entity_types": "dict"},
        },
        {
            "agent_id": "trend_detection_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Trend Detection Task Agent",
            "description": "Identify trends and patterns in time series data",
            "capabilities": ["trend_analysis", "seasonality_detection", "change_point_detection"],
            "inputs": {"time_series": "list", "detection_params": "dict"},
            "outputs": {"trends": "list", "statistical_significance": "dict"},
        },
        {
            "agent_id": "anomaly_detection_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Anomaly Detection Task Agent",
            "description": "Detect outliers and anomalies in data",
            "capabilities": ["statistical_methods", "ml_methods", "severity_scoring"],
            "inputs": {"dataset": "list", "detection_params": "dict"},
            "outputs": {"anomalies": "list", "severity_scores": "dict"},
        },
        {
            "agent_id": "text_similarity_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Text Similarity Task Agent",
            "description": "Calculate similarity between text documents",
            "capabilities": ["cosine_similarity", "semantic_similarity", "fuzzy_matching"],
            "inputs": {"text1": "string", "text2": "string"},
            "outputs": {"similarity_score": "float", "method": "string"},
        },
        {
            "agent_id": "keyword_extraction_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Keyword Extraction Task Agent",
            "description": "Extract important keywords and phrases from text",
            "capabilities": ["tfidf", "rake", "textrank", "phrase_extraction"],
            "inputs": {"text": "string", "num_keywords": "int"},
            "outputs": {"keywords": "list", "relevance_scores": "dict"},
        },
        {
            "agent_id": "statistical_analysis_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Statistical Analysis Task Agent",
            "description": "Perform statistical analysis on datasets",
            "capabilities": ["descriptive_stats", "correlation_analysis", "hypothesis_testing"],
            "inputs": {"dataset": "list", "analysis_type": "string"},
            "outputs": {"statistics": "dict", "p_values": "dict"},
        },
        {
            "agent_id": "classification_task_agent",
            "agent_type": "analysis",
            "category": "analysis",
            "name": "Classification Task Agent",
            "description": "Classify items using ML models",
            "capabilities": ["binary_classification", "multi_class", "confidence_calibration"],
            "inputs": {"items": "list", "model": "string"},
            "outputs": {"classifications": "list", "confidence_scores": "dict"},
        },
        # CATEGORY D: OUTPUT GENERATION
        {
            "agent_id": "report_generator_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "Report Generator Task Agent",
            "description": "Generate formatted reports from data",
            "capabilities": ["pdf_generation", "html_generation", "template_rendering"],
            "inputs": {"data": "dict", "template": "string", "format": "string"},
            "outputs": {"report": "string", "file_path": "string"},
        },
        {
            "agent_id": "chart_creation_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "Chart Creation Task Agent",
            "description": "Generate data visualizations",
            "capabilities": ["multiple_chart_types", "interactive_charts", "custom_styling"],
            "inputs": {"data": "dict", "chart_type": "string", "style": "dict"},
            "outputs": {"chart": "string", "file_path": "string"},
        },
        {
            "agent_id": "email_sender_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "Email Sender Task Agent",
            "description": "Send formatted emails",
            "capabilities": ["html_email", "attachments", "template_rendering", "bulk_sending"],
            "inputs": {"recipients": "list", "subject": "string", "body": "string"},
            "outputs": {"delivery_status": "dict", "message_ids": "list"},
        },
        {
            "agent_id": "notification_dispatcher_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "Notification Dispatcher Task Agent",
            "description": "Send notifications via multiple channels",
            "capabilities": ["multi_channel", "channel_fallback", "priority_routing"],
            "inputs": {"message": "string", "recipients": "list", "channels": "list"},
            "outputs": {"delivery_confirmations": "dict", "failed_deliveries": "list"},
        },
        {
            "agent_id": "file_export_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "File Export Task Agent",
            "description": "Export data to various file formats",
            "capabilities": ["format_support", "compression", "cloud_upload"],
            "inputs": {"data": "dict", "format": "string", "destination": "string"},
            "outputs": {"file_path": "string", "export_stats": "dict"},
        },
        {
            "agent_id": "dashboard_update_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "Dashboard Update Task Agent",
            "description": "Update dashboard metrics and visualizations",
            "capabilities": ["metric_push", "real_time_streaming", "alert_triggering"],
            "inputs": {"dashboard_id": "string", "metrics": "dict"},
            "outputs": {"update_status": "dict", "alerts_triggered": "list"},
        },
        {
            "agent_id": "api_response_formatter_task_agent",
            "agent_type": "output_generation",
            "category": "output_generation",
            "name": "API Response Formatter Task Agent",
            "description": "Format data for API responses",
            "capabilities": ["rest_formatting", "graphql_formatting", "schema_validation"],
            "inputs": {"data": "dict", "api_schema": "dict"},
            "outputs": {"formatted_response": "dict", "validation_result": "bool"},
        },
    ]

    print(f"Generating {len(agents)} Level 5 Task Agents...")
    print()

    success_count = 0
    failed_count = 0
    created_files = []

    for i, agent_spec in enumerate(agents, 1):
        try:
            print(f"[{i}/{len(agents)}] Creating {agent_spec['name']}...")
            file_path = create_agent_file(agent_spec, output_dir)
            created_files.append(file_path)
            success_count += 1
            print(f"    [OK] Created: {file_path}")
        except Exception as e:
            failed_count += 1
            print(f"    [FAIL] Failed: {str(e)}")

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total Agents: {len(agents)}")
    print(f"Successfully Created: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Success Rate: {(success_count/len(agents)*100):.1f}%")
    print()

    if created_files:
        print("Created Files:")
        for file_path in created_files:
            print(f"  - {file_path}")

    print()
    print("Next Steps:")
    print("1. Review generated agents")
    print("2. Implement specific task logic in _execute_core_logic methods")
    print("3. Add comprehensive tests")
    print("4. Register agents with orchestrator")
    print("5. Create agent cards for marketplace")
    print()


if __name__ == "__main__":
    main()
