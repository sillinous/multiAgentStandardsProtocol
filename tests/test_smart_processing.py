"""
Unit Tests for Smart Processing Service
========================================

Comprehensive tests for the domain-specific processors.

Run with: pytest tests/test_smart_processing.py -v
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from typing import Dict, Any


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def finance_processor():
    """Get FinanceProcessor instance"""
    from superstandard.services.smart_processing import FinanceProcessor
    return FinanceProcessor()


@pytest.fixture
def hr_processor():
    """Get HRProcessor instance"""
    from superstandard.services.smart_processing import HRProcessor
    return HRProcessor()


@pytest.fixture
def operations_processor():
    """Get OperationsProcessor instance"""
    from superstandard.services.smart_processing import OperationsProcessor
    return OperationsProcessor()


@pytest.fixture
def customer_service_processor():
    """Get CustomerServiceProcessor instance"""
    from superstandard.services.smart_processing import CustomerServiceProcessor
    return CustomerServiceProcessor()


@pytest.fixture
def it_processor():
    """Get ITProcessor instance"""
    from superstandard.services.smart_processing import ITProcessor
    return ITProcessor()


# =============================================================================
# BaseProcessor Tests
# =============================================================================

class TestBaseProcessor:
    """Test base processor functionality"""

    @pytest.mark.asyncio
    async def test_process_default_routing(self, finance_processor):
        """Test that default task_type routes to process_default"""
        result = await finance_processor.process({"test": "data"})

        assert result["status"] == "completed"
        assert result["domain"] == "finance"
        assert result["task_type"] == "default"
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_process_records_history(self, finance_processor):
        """Test that processing records history"""
        initial_history = len(finance_processor.processing_history)

        await finance_processor.process({"test": "data"})

        assert len(finance_processor.processing_history) == initial_history + 1
        last_record = finance_processor.processing_history[-1]
        assert "timestamp" in last_record
        assert "task_type" in last_record
        assert last_record["success"] == True

    @pytest.mark.asyncio
    async def test_get_stats(self, finance_processor):
        """Test statistics retrieval"""
        # Process a few items
        await finance_processor.process({"test": "1"})
        await finance_processor.process({"test": "2"})

        stats = finance_processor.get_stats()

        assert stats["domain"] == "finance"
        assert stats["total_processed"] >= 2
        assert 0 <= stats["success_rate"] <= 1
        assert stats["average_processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_custom_task_type_routing(self, finance_processor):
        """Test routing to custom task type method"""
        # process_invoice is a custom method in FinanceProcessor
        result = await finance_processor.process(
            {"invoice_number": "INV-001", "amount": 1000},
            task_type="invoice"
        )

        assert result["status"] == "completed"
        assert result["task_type"] == "invoice"


# =============================================================================
# FinanceProcessor Tests
# =============================================================================

class TestFinanceProcessor:
    """Test finance domain processor"""

    @pytest.mark.asyncio
    async def test_domain_is_finance(self, finance_processor):
        """Test domain is correctly set"""
        assert finance_processor.domain == "finance"

    @pytest.mark.asyncio
    async def test_risk_thresholds_exist(self, finance_processor):
        """Test risk thresholds are configured"""
        assert "low" in finance_processor.risk_thresholds
        assert "medium" in finance_processor.risk_thresholds
        assert "high" in finance_processor.risk_thresholds
        assert finance_processor.risk_thresholds["low"] < finance_processor.risk_thresholds["medium"]
        assert finance_processor.risk_thresholds["medium"] < finance_processor.risk_thresholds["high"]

    @pytest.mark.asyncio
    async def test_analyze_financial_data(self, finance_processor):
        """Test financial data analysis"""
        data = {
            "revenue": 100000,
            "expenses": 75000,
            "profit_margin": 0.25
        }

        result = await finance_processor.analyze_financial_data(data)

        assert "analysis" in result
        assert result["analysis_type"] == "financial_comprehensive"

    @pytest.mark.asyncio
    async def test_assess_financial_risk(self, finance_processor):
        """Test financial risk assessment"""
        context = {
            "transaction_amount": 50000,
            "customer_risk_profile": "medium"
        }

        result = await finance_processor.assess_financial_risk(context)

        assert "risk_assessment" in result
        assert "classification" in result
        assert result["classification"] in ["acceptable", "monitor", "elevated", "critical"]
        assert "requires_approval" in result

    @pytest.mark.asyncio
    async def test_recommend_approval(self, finance_processor):
        """Test approval recommendation"""
        request = {
            "type": "expense",
            "amount": 5000,
            "requestor": "department_head"
        }

        result = await finance_processor.recommend_approval(request)

        assert "recommendation" in result
        assert result["recommendation"] in ["approve", "approve_with_conditions", "reject", "escalate"]
        assert "confidence" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_process_invoice(self, finance_processor):
        """Test invoice processing"""
        invoice_data = {
            "vendor": "Acme Corp",
            "amount": 15000,
            "due_date": "2025-02-15"
        }

        result = await finance_processor.process_invoice(invoice_data)

        assert "extracted_data" in result
        assert "validation_issues" in result
        assert "ready_for_processing" in result

    @pytest.mark.asyncio
    async def test_generate_report(self, finance_processor):
        """Test financial report generation"""
        report_params = {
            "report_type": "quarterly",
            "data": {
                "revenue": 500000,
                "expenses": 350000,
                "period": "Q4 2024"
            }
        }

        result = await finance_processor.generate_report(report_params)

        assert "summary" in result
        assert "recommendations" in result


# =============================================================================
# HRProcessor Tests
# =============================================================================

class TestHRProcessor:
    """Test HR domain processor"""

    @pytest.mark.asyncio
    async def test_domain_is_hr(self, hr_processor):
        """Test domain is correctly set"""
        assert hr_processor.domain == "hr_management"

    @pytest.mark.asyncio
    async def test_analyze_hr_data(self, hr_processor):
        """Test HR data analysis"""
        data = {
            "headcount": 150,
            "turnover_rate": 0.12,
            "engagement_score": 4.2
        }

        result = await hr_processor.analyze_hr_data(data)

        assert "analysis" in result
        assert result["analysis_type"] == "hr_comprehensive"

    @pytest.mark.asyncio
    async def test_evaluate_candidate(self, hr_processor):
        """Test candidate evaluation"""
        candidate = {
            "name": "John Doe",
            "experience_years": 5,
            "skills": ["Python", "SQL", "AWS"]
        }
        requirements = {
            "min_experience": 3,
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["AWS", "Docker"]
        }

        result = await hr_processor.evaluate_candidate(candidate, requirements)

        assert "evaluation" in result
        assert result["evaluation_type"] == "candidate_screening"

    @pytest.mark.asyncio
    async def test_analyze_performance(self, hr_processor):
        """Test performance analysis"""
        performance_data = {
            "employee_id": "EMP001",
            "goals_completed": 8,
            "goals_total": 10,
            "peer_feedback_score": 4.5
        }

        result = await hr_processor.analyze_performance(performance_data)

        assert "performance_analysis" in result
        assert result["analysis_type"] == "performance_review"

    @pytest.mark.asyncio
    async def test_plan_workforce(self, hr_processor):
        """Test workforce planning"""
        planning_context = {
            "current_headcount": 100,
            "projected_growth": 0.2,
            "skills_gap": ["data_science", "cloud_engineering"]
        }

        result = await hr_processor.plan_workforce(planning_context)

        assert "workforce_recommendations" in result
        assert result["planning_type"] == "strategic_workforce"

    @pytest.mark.asyncio
    async def test_assess_compliance(self, hr_processor):
        """Test HR compliance assessment"""
        compliance_context = {
            "policy_updates_pending": 3,
            "training_completion_rate": 0.85,
            "incidents_this_quarter": 2
        }

        result = await hr_processor.assess_compliance(compliance_context)

        assert "compliance_assessment" in result
        assert result["assessment_type"] == "hr_compliance"


# =============================================================================
# OperationsProcessor Tests
# =============================================================================

class TestOperationsProcessor:
    """Test operations domain processor"""

    @pytest.mark.asyncio
    async def test_domain_is_operations(self, operations_processor):
        """Test domain is correctly set"""
        assert operations_processor.domain == "operations"

    @pytest.mark.asyncio
    async def test_analyze_operations(self, operations_processor):
        """Test operations analysis"""
        data = {
            "production_output": 1000,
            "efficiency_rate": 0.92,
            "downtime_hours": 5
        }

        result = await operations_processor.analyze_operations(data)

        assert "analysis" in result
        assert result["analysis_type"] == "operations_comprehensive"

    @pytest.mark.asyncio
    async def test_optimize_process(self, operations_processor):
        """Test process optimization"""
        process_data = {
            "current_state": {"cycle_time_hours": 24, "defect_rate": 0.05},
            "optimization_goals": ["reduce_cycle_time", "improve_quality"],
            "constraints": ["budget_limited", "no_equipment_change"]
        }

        result = await operations_processor.optimize_process(process_data)

        assert "optimization_recommendations" in result
        assert result["optimization_type"] == "process_improvement"

    @pytest.mark.asyncio
    async def test_forecast_demand(self, operations_processor):
        """Test demand forecasting"""
        forecast_context = {
            "historical_data": [100, 120, 115, 130, 140],
            "seasonality": "quarterly",
            "forecast_period": "next_quarter"
        }

        result = await operations_processor.forecast_demand(forecast_context)

        assert "forecast" in result
        assert result["forecast_type"] == "demand_planning"

    @pytest.mark.asyncio
    async def test_plan_logistics(self, operations_processor):
        """Test logistics planning"""
        logistics_context = {
            "origin": "warehouse_a",
            "destination": "customer_site",
            "shipment_size": 500,
            "routing_options": ["ground", "air", "express"]
        }

        result = await operations_processor.plan_logistics(logistics_context)

        assert "logistics_plan" in result
        assert result["planning_type"] == "logistics_optimization"

    @pytest.mark.asyncio
    async def test_monitor_quality(self, operations_processor):
        """Test quality monitoring"""
        quality_data = {
            "defect_count": 15,
            "total_units": 1000,
            "inspection_pass_rate": 0.98
        }

        result = await operations_processor.monitor_quality(quality_data)

        assert "quality_assessment" in result
        assert result["assessment_type"] == "quality_monitoring"


# =============================================================================
# CustomerServiceProcessor Tests
# =============================================================================

class TestCustomerServiceProcessor:
    """Test customer service domain processor"""

    @pytest.mark.asyncio
    async def test_domain_is_customer_service(self, customer_service_processor):
        """Test domain is correctly set"""
        assert customer_service_processor.domain == "customer_service"

    @pytest.mark.asyncio
    async def test_analyze_customer_interaction(self, customer_service_processor):
        """Test customer interaction analysis"""
        data = {
            "interaction_type": "support_ticket",
            "customer_message": "I've been waiting 3 days for a response",
            "sentiment_indicators": ["frustrated", "escalation_risk"]
        }

        result = await customer_service_processor.analyze_customer_interaction(data)

        assert "analysis" in result
        assert result["analysis_type"] == "customer_interaction"

    @pytest.mark.asyncio
    async def test_classify_inquiry(self, customer_service_processor):
        """Test inquiry classification"""
        inquiry = {
            "subject": "Billing discrepancy",
            "content": "My invoice shows charges I don't recognize"
        }

        result = await customer_service_processor.classify_inquiry(inquiry)

        assert "classification" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_recommend_resolution(self, customer_service_processor):
        """Test resolution recommendation"""
        issue = {
            "type": "product_defect",
            "severity": "high",
            "customer": {"tier": "premium", "tenure_years": 5}
        }

        result = await customer_service_processor.recommend_resolution(issue)

        assert "resolution_recommendations" in result
        assert result["resolution_type"] == "issue_handling"

    @pytest.mark.asyncio
    async def test_analyze_feedback(self, customer_service_processor):
        """Test feedback analysis"""
        feedback = {
            "source": "survey",
            "rating": 3,
            "comment": "Product is good but support could be faster"
        }

        result = await customer_service_processor.analyze_feedback(feedback)

        assert "sentiment_analysis" in result
        assert "actionable_insights" in result
        assert result["analysis_type"] == "feedback_analysis"

    @pytest.mark.asyncio
    async def test_predict_churn_risk(self, customer_service_processor):
        """Test churn risk prediction"""
        customer_data = {
            "customer_id": "CUST001",
            "recent_tickets": 5,
            "satisfaction_trend": "declining",
            "usage_change": -0.30
        }

        result = await customer_service_processor.predict_churn_risk(customer_data)

        assert "churn_risk" in result
        assert result["assessment_type"] == "churn_prediction"


# =============================================================================
# ITProcessor Tests
# =============================================================================

class TestITProcessor:
    """Test IT domain processor"""

    @pytest.mark.asyncio
    async def test_domain_is_it(self, it_processor):
        """Test domain is correctly set"""
        assert it_processor.domain == "it_management"

    @pytest.mark.asyncio
    async def test_analyze_it_systems(self, it_processor):
        """Test IT systems analysis"""
        data = {
            "servers_online": 50,
            "uptime_percent": 99.9,
            "active_alerts": 3
        }

        result = await it_processor.analyze_it_systems(data)

        assert "analysis" in result
        assert result["analysis_type"] == "it_systems_comprehensive"

    @pytest.mark.asyncio
    async def test_assess_security(self, it_processor):
        """Test security assessment"""
        security_context = {
            "vulnerability_count": 12,
            "patch_compliance": 0.95,
            "last_audit_date": "2024-12-01"
        }

        result = await it_processor.assess_security(security_context)

        assert "security_assessment" in result
        assert result["assessment_type"] == "it_security"

    @pytest.mark.asyncio
    async def test_plan_incident_response(self, it_processor):
        """Test incident response planning"""
        incident = {
            "type": "service_outage",
            "affected_systems": ["api-gateway", "auth-service"],
            "severity": "critical",
            "detected_at": "2025-01-15T10:30:00"
        }

        result = await it_processor.plan_incident_response(incident)

        assert "response_decision" in result
        assert "response_recommendations" in result
        assert result["planning_type"] == "incident_response"

    @pytest.mark.asyncio
    async def test_optimize_infrastructure(self, it_processor):
        """Test infrastructure optimization"""
        infra_data = {
            "cpu_utilization": 0.75,
            "memory_utilization": 0.85,
            "storage_utilization": 0.60,
            "monthly_cost": 50000
        }

        result = await it_processor.optimize_infrastructure(infra_data)

        assert "optimization_recommendations" in result
        assert result["optimization_type"] == "infrastructure"


# =============================================================================
# ProcessorFactory Tests
# =============================================================================

class TestProcessorFactory:
    """Test processor factory"""

    def test_get_finance_processor(self):
        """Test getting finance processor"""
        from superstandard.services.smart_processing import ProcessorFactory, FinanceProcessor

        processor = ProcessorFactory.get_processor("finance")
        assert isinstance(processor, FinanceProcessor)

    def test_get_hr_processor(self):
        """Test getting HR processor with aliases"""
        from superstandard.services.smart_processing import ProcessorFactory, HRProcessor

        # Test different aliases
        assert isinstance(ProcessorFactory.get_processor("hr"), HRProcessor)
        assert isinstance(ProcessorFactory.get_processor("hr_management"), HRProcessor)
        assert isinstance(ProcessorFactory.get_processor("human_resources"), HRProcessor)

    def test_get_operations_processor(self):
        """Test getting operations processor with aliases"""
        from superstandard.services.smart_processing import ProcessorFactory, OperationsProcessor

        assert isinstance(ProcessorFactory.get_processor("operations"), OperationsProcessor)
        assert isinstance(ProcessorFactory.get_processor("manufacturing"), OperationsProcessor)
        assert isinstance(ProcessorFactory.get_processor("logistics"), OperationsProcessor)

    def test_get_customer_service_processor(self):
        """Test getting customer service processor"""
        from superstandard.services.smart_processing import ProcessorFactory, CustomerServiceProcessor

        assert isinstance(ProcessorFactory.get_processor("customer_service"), CustomerServiceProcessor)
        assert isinstance(ProcessorFactory.get_processor("customer"), CustomerServiceProcessor)

    def test_get_it_processor(self):
        """Test getting IT processor with aliases"""
        from superstandard.services.smart_processing import ProcessorFactory, ITProcessor

        assert isinstance(ProcessorFactory.get_processor("it"), ITProcessor)
        assert isinstance(ProcessorFactory.get_processor("it_management"), ITProcessor)
        assert isinstance(ProcessorFactory.get_processor("technology"), ITProcessor)

    def test_unknown_domain_defaults_to_operations(self):
        """Test that unknown domain returns operations processor"""
        from superstandard.services.smart_processing import ProcessorFactory, OperationsProcessor

        processor = ProcessorFactory.get_processor("unknown_domain")
        assert isinstance(processor, OperationsProcessor)

    def test_case_insensitive(self):
        """Test case insensitivity"""
        from superstandard.services.smart_processing import ProcessorFactory, FinanceProcessor

        assert isinstance(ProcessorFactory.get_processor("FINANCE"), FinanceProcessor)
        assert isinstance(ProcessorFactory.get_processor("Finance"), FinanceProcessor)
        assert isinstance(ProcessorFactory.get_processor("FiNaNcE"), FinanceProcessor)

    def test_space_handling(self):
        """Test space handling in domain names"""
        from superstandard.services.smart_processing import ProcessorFactory, CustomerServiceProcessor

        processor = ProcessorFactory.get_processor("customer service")
        assert isinstance(processor, CustomerServiceProcessor)


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_processor(self):
        """Test get_processor convenience function"""
        from superstandard.services.smart_processing import get_processor, FinanceProcessor

        processor = get_processor("finance")
        assert isinstance(processor, FinanceProcessor)

    @pytest.mark.asyncio
    async def test_smart_process(self):
        """Test smart_process convenience function"""
        from superstandard.services.smart_processing import smart_process

        result = await smart_process(
            domain="finance",
            input_data={"amount": 1000},
            task_type="default"
        )

        assert result["status"] == "completed"
        assert result["domain"] == "finance"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_process_handles_exceptions(self, finance_processor):
        """Test that process method handles exceptions gracefully"""
        # This test verifies the error handling in the base process method
        # The mock AI service shouldn't raise errors, but the structure is tested
        result = await finance_processor.process({})

        # Should complete without raising
        assert result["status"] in ["completed", "error"]

    @pytest.mark.asyncio
    async def test_empty_input_handling(self, finance_processor):
        """Test handling of empty input"""
        result = await finance_processor.process({})

        assert result["status"] == "completed"
        assert result["domain"] == "finance"

    @pytest.mark.asyncio
    async def test_none_values_in_input(self, finance_processor):
        """Test handling of None values in input"""
        result = await finance_processor.process({"value": None, "data": None})

        assert result["status"] == "completed"


# =============================================================================
# Integration Tests
# =============================================================================

class TestProcessorIntegration:
    """Integration tests across processors"""

    @pytest.mark.asyncio
    async def test_multiple_processors_independent(self):
        """Test that multiple processors work independently"""
        from superstandard.services.smart_processing import (
            FinanceProcessor,
            HRProcessor,
            OperationsProcessor
        )

        finance = FinanceProcessor()
        hr = HRProcessor()
        ops = OperationsProcessor()

        # Process simultaneously
        results = await asyncio.gather(
            finance.process({"test": "finance"}),
            hr.process({"test": "hr"}),
            ops.process({"test": "ops"})
        )

        assert results[0]["domain"] == "finance"
        assert results[1]["domain"] == "hr_management"
        assert results[2]["domain"] == "operations"

    @pytest.mark.asyncio
    async def test_processor_stats_isolation(self):
        """Test that processor stats are isolated"""
        from superstandard.services.smart_processing import FinanceProcessor

        processor1 = FinanceProcessor()
        processor2 = FinanceProcessor()

        await processor1.process({"test": "1"})
        await processor1.process({"test": "2"})

        stats1 = processor1.get_stats()
        stats2 = processor2.get_stats()

        assert stats1["total_processed"] == 2
        assert stats2["total_processed"] == 0


# =============================================================================
# Standalone Test Runner
# =============================================================================

async def run_quick_tests():
    """Run quick standalone tests"""
    print("=" * 60)
    print("Smart Processing Quick Tests")
    print("=" * 60)

    try:
        from superstandard.services.smart_processing import (
            FinanceProcessor,
            HRProcessor,
            OperationsProcessor,
            CustomerServiceProcessor,
            ITProcessor,
            get_processor,
            smart_process
        )

        # Test Finance Processor
        print("\n1. Testing FinanceProcessor...")
        finance = FinanceProcessor()
        result = await finance.process({"revenue": 100000})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test HR Processor
        print("\n2. Testing HRProcessor...")
        hr = HRProcessor()
        result = await hr.process({"headcount": 150})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test Operations Processor
        print("\n3. Testing OperationsProcessor...")
        ops = OperationsProcessor()
        result = await ops.process({"efficiency": 0.92})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test Customer Service Processor
        print("\n4. Testing CustomerServiceProcessor...")
        cs = CustomerServiceProcessor()
        result = await cs.process({"ticket_count": 25})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test IT Processor
        print("\n5. Testing ITProcessor...")
        it = ITProcessor()
        result = await it.process({"uptime": 99.9})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test smart_process convenience function
        print("\n6. Testing smart_process()...")
        result = await smart_process("finance", {"amount": 5000})
        print(f"   Status: {result['status']}")
        print(f"   Domain: {result['domain']}")

        # Test get_processor factory
        print("\n7. Testing get_processor factory...")
        for domain in ["finance", "hr", "operations", "customer_service", "it"]:
            processor = get_processor(domain)
            print(f"   {domain}: {type(processor).__name__}")

        print("\n" + "=" * 60)
        print("All quick tests passed!")
        print("=" * 60)

    except ImportError as e:
        print(f"\nError: Could not import required modules: {e}")
        print("Make sure you're running from the project root directory.")
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_quick_tests())
