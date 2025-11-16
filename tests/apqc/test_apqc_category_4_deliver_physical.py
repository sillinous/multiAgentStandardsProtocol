"""
APQC Category 4.0 - Deliver Physical Products Agent Tests

Comprehensive tests for all 12 Deliver Physical Products agents from APQC Category 4.0.

Agents tested:
1. PlanForAlignSupplyChainResourcesOperationalAgent (4.1)
2. PlanSupplyChainResourcesOperationalAgent (4.1)
3. ProcureMaterialsServicesOperationalAgent (4.2)
4. ManageSupplierContractsOperationalAgent
5. ManageSupplierRelationshipsOperationalAgent
6. ProduceManufactureDeliverProductOperationalAgent (4.3)
7. ScheduleProductionOperationalAgent
8. ManageLogisticsWarehousingOperationalAgent (4.4)
9. ManageTransportationOperationalAgent
10. ManageWarehouseOperationsOperationalAgent
11. OptimizeInventoryOperationalAgent
12. ForecastDemandOperationalAgent

Test Coverage:
- Individual agent tests (initialization, execution, health, protocols)
- Supply chain workflow integration tests
- Production and manufacturing workflows
- Logistics and warehousing workflows
- Cross-agent collaboration within category

Version: 1.0.0
Framework: APQC 7.0.1
Category: 4.0 - Deliver Physical Products
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .test_apqc_framework import APQCAgentTestCase, MockDataGenerator, APQCTestUtilities


# ========================================================================
# Category 4.0 Agent Tests - Supply Chain Planning (4.1)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestPlanForAlignSupplyChainResourcesOperationalAgent(APQCAgentTestCase):
    """
    Tests for PlanForAlignSupplyChainResourcesOperationalAgent (APQC 4.1)

    Agent: Plan for and align supply chain resources
    Path: src/superstandard/agents/operations/plan_for_align_supply_chain_resources_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.plan_for_align_supply_chain_resources_operational_agent import (
            PlanForAlignSupplyChainResourcesOperationalAgent
        )
        return PlanForAlignSupplyChainResourcesOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.plan_for_align_supply_chain_resources_operational_agent import (
            PlanForAlignSupplyChainResourcesOperationalAgentConfig
        )
        return PlanForAlignSupplyChainResourcesOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_process_id": "4.1",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "analysis",
            "planning",
            "resource_optimization",
            "supply_chain_management"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for supply chain resource planning."""
        return {
            "task_type": "plan_supply_chain_resources",
            "data": {
                "demand_forecast": {
                    "Q1": 10000,
                    "Q2": 12000,
                    "Q3": 15000,
                    "Q4": 18000
                },
                "current_capacity": {
                    "production": 12000,
                    "warehouse": 5000,
                    "transportation": 8000
                },
                "lead_times": {
                    "procurement": 30,
                    "production": 15,
                    "shipping": 7
                },
                "constraints": ["budget", "capacity", "workforce"]
            },
            "context": {
                "planning_horizon": "12_months",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_supply_chain_resource_alignment(self):
        """Test supply chain resource alignment workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "align_resources",
            "data": {
                "strategic_goals": ["cost_reduction", "service_improvement"],
                "resource_pools": {
                    "suppliers": 50,
                    "warehouses": 10,
                    "distribution_centers": 15
                },
                "optimization_criteria": ["cost", "speed", "quality"],
                "target_service_level": 0.95
            },
            "context": {
                "business_unit": "manufacturing",
                "priority": "high"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result
        assert result['apqc_process_id'] == '4.1'


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestPlanSupplyChainResourcesOperationalAgent(APQCAgentTestCase):
    """
    Tests for PlanSupplyChainResourcesOperationalAgent (APQC 4.1)

    Agent: Plan supply chain resources
    Path: src/superstandard/agents/operations/plan_supply_chain_resources_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.plan_supply_chain_resources_operational_agent import (
            PlanSupplyChainResourcesOperationalAgent
        )
        return PlanSupplyChainResourcesOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.plan_supply_chain_resources_operational_agent import (
            PlanSupplyChainResourcesOperationalAgentConfig
        )
        return PlanSupplyChainResourcesOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_process_id": "4.1",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for supply chain planning."""
        return {
            "task_type": "plan_supply_chain",
            "data": {
                "products": [
                    {"sku": "PROD-001", "demand": 5000, "lead_time": 30},
                    {"sku": "PROD-002", "demand": 3000, "lead_time": 45}
                ],
                "suppliers": [
                    {"id": "SUP-001", "capacity": 10000, "reliability": 0.95},
                    {"id": "SUP-002", "capacity": 8000, "reliability": 0.90}
                ],
                "inventory_policy": "min_max",
                "service_level_target": 0.98
            },
            "context": {
                "planning_cycle": "monthly",
                "priority": "medium"
            },
            "priority": "medium"
        }


# ========================================================================
# Category 4.0 Agent Tests - Procurement (4.2)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestProcureMaterialsServicesOperationalAgent(APQCAgentTestCase):
    """
    Tests for ProcureMaterialsServicesOperationalAgent (APQC 4.2)

    Agent: Procure materials and services
    Path: src/superstandard/agents/api/procure_materials_services_operational_agent.py
    Domain: procurement | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.api.procure_materials_services_operational_agent import (
            ProcureMaterialsServicesOperationalAgent
        )
        return ProcureMaterialsServicesOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.api.procure_materials_services_operational_agent import (
            ProcureMaterialsServicesOperationalAgentConfig
        )
        return ProcureMaterialsServicesOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_process_id": "4.2",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "procurement",
            "vendor_management",
            "sourcing",
            "negotiation"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for procurement."""
        return {
            "task_type": "procure_materials",
            "data": {
                "purchase_request": {
                    "items": [
                        {"material_id": "MAT-001", "quantity": 1000, "unit": "kg"},
                        {"material_id": "MAT-002", "quantity": 500, "unit": "units"}
                    ],
                    "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "budget": 50000
                },
                "approved_suppliers": ["SUP-001", "SUP-002", "SUP-003"],
                "quality_requirements": {
                    "certifications": ["ISO9001", "ISO14001"],
                    "testing": "required"
                },
                "payment_terms": "net_30"
            },
            "context": {
                "department": "manufacturing",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_procurement_workflow(self):
        """Test end-to-end procurement workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "execute_procurement",
            "data": {
                "rfq": {
                    "id": "RFQ-2025-001",
                    "items": [{"material": "Steel", "quantity": 10000, "unit": "kg"}],
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                },
                "evaluation_criteria": {
                    "price": 0.5,
                    "quality": 0.3,
                    "delivery_time": 0.2
                }
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestManageSupplierContractsOperationalAgent(APQCAgentTestCase):
    """
    Tests for ManageSupplierContractsOperationalAgent

    Agent: Manage supplier contracts
    Path: src/superstandard/agents/blockchain/manage_supplier_contracts_operational_agent.py
    Domain: procurement | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.blockchain.manage_supplier_contracts_operational_agent import (
            ManageSupplierContractsOperationalAgent
        )
        return ManageSupplierContractsOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.blockchain.manage_supplier_contracts_operational_agent import (
            ManageSupplierContractsOperationalAgentConfig
        )
        return ManageSupplierContractsOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for contract management."""
        return {
            "task_type": "manage_contract",
            "data": {
                "contract": {
                    "id": "CONTRACT-2025-001",
                    "supplier_id": "SUP-001",
                    "type": "master_agreement",
                    "value": 1000000,
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=365)).isoformat()
                },
                "terms": {
                    "payment": "net_45",
                    "delivery": "FOB_destination",
                    "penalties": {"late_delivery": 0.01}
                },
                "action": "renew"
            },
            "context": {
                "approval_required": True,
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestManageSupplierRelationshipsOperationalAgent(APQCAgentTestCase):
    """
    Tests for ManageSupplierRelationshipsOperationalAgent

    Agent: Manage supplier relationships
    Path: src/superstandard/agents/business/manage_supplier_relationships_operational_agent.py
    Domain: procurement | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.business.manage_supplier_relationships_operational_agent import (
            ManageSupplierRelationshipsOperationalAgent
        )
        return ManageSupplierRelationshipsOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.business.manage_supplier_relationships_operational_agent import (
            ManageSupplierRelationshipsOperationalAgentConfig
        )
        return ManageSupplierRelationshipsOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for supplier relationship management."""
        return {
            "task_type": "manage_supplier_relationship",
            "data": {
                "supplier": {
                    "id": "SUP-001",
                    "name": "Acme Manufacturing",
                    "tier": "strategic",
                    "spend": 5000000
                },
                "performance_metrics": {
                    "quality": 0.98,
                    "on_time_delivery": 0.95,
                    "responsiveness": 0.92
                },
                "relationship_goals": [
                    "cost_reduction",
                    "quality_improvement",
                    "innovation_collaboration"
                ],
                "action": "strategic_review"
            },
            "context": {
                "review_period": "quarterly",
                "priority": "high"
            },
            "priority": "high"
        }


# ========================================================================
# Category 4.0 Agent Tests - Production/Manufacturing (4.3)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestProduceManufactureDeliverProductOperationalAgent(APQCAgentTestCase):
    """
    Tests for ProduceManufactureDeliverProductOperationalAgent (APQC 4.3)

    Agent: Produce/manufacture and deliver product
    Path: src/superstandard/agents/operations/produce_manufacture_deliver_product_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.produce_manufacture_deliver_product_operational_agent import (
            ProduceManufactureDeliverProductOperationalAgent
        )
        return ProduceManufactureDeliverProductOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.produce_manufacture_deliver_product_operational_agent import (
            ProduceManufactureDeliverProductOperationalAgentConfig
        )
        return ProduceManufactureDeliverProductOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_process_id": "4.3",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "production",
            "manufacturing",
            "quality_control",
            "delivery"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for production."""
        return {
            "task_type": "produce_product",
            "data": {
                "production_order": {
                    "order_id": "PO-2025-001",
                    "product_id": "PROD-001",
                    "quantity": 1000,
                    "due_date": (datetime.now() + timedelta(days=30)).isoformat()
                },
                "bill_of_materials": [
                    {"material_id": "MAT-001", "quantity": 500, "unit": "kg"},
                    {"material_id": "MAT-002", "quantity": 200, "unit": "units"}
                ],
                "production_line": "LINE-A",
                "quality_standards": {
                    "tolerance": 0.01,
                    "inspection": "100_percent"
                }
            },
            "context": {
                "shift": "day",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_production_execution(self):
        """Test production execution workflow."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "execute_production",
            "data": {
                "work_order": {
                    "id": "WO-001",
                    "product": "Widget-A",
                    "quantity": 5000,
                    "start_time": datetime.now().isoformat()
                },
                "resources": {
                    "equipment": ["Machine-1", "Machine-2"],
                    "labor": 10,
                    "materials": "allocated"
                },
                "target_efficiency": 0.85
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestScheduleProductionOperationalAgent(APQCAgentTestCase):
    """
    Tests for ScheduleProductionOperationalAgent

    Agent: Schedule production
    Path: src/superstandard/agents/operations/schedule_production_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.schedule_production_operational_agent import (
            ScheduleProductionOperationalAgent
        )
        return ScheduleProductionOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.schedule_production_operational_agent import (
            ScheduleProductionOperationalAgentConfig
        )
        return ScheduleProductionOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for production scheduling."""
        return {
            "task_type": "schedule_production",
            "data": {
                "orders": [
                    {
                        "id": "ORD-001",
                        "product": "PROD-A",
                        "quantity": 1000,
                        "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                        "priority": "high"
                    },
                    {
                        "id": "ORD-002",
                        "product": "PROD-B",
                        "quantity": 500,
                        "due_date": (datetime.now() + timedelta(days=21)).isoformat(),
                        "priority": "medium"
                    }
                ],
                "production_lines": [
                    {"id": "LINE-A", "capacity": 100, "available_hours": 160},
                    {"id": "LINE-B", "capacity": 80, "available_hours": 160}
                ],
                "constraints": ["capacity", "material_availability", "labor"],
                "optimization_goal": "minimize_makespan"
            },
            "context": {
                "planning_horizon": "30_days",
                "priority": "medium"
            },
            "priority": "medium"
        }


# ========================================================================
# Category 4.0 Agent Tests - Logistics & Warehousing (4.4)
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestManageLogisticsWarehousingOperationalAgent(APQCAgentTestCase):
    """
    Tests for ManageLogisticsWarehousingOperationalAgent (APQC 4.4)

    Agent: Manage logistics and warehousing
    Path: src/superstandard/agents/operations/manage_logistics_warehousing_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.manage_logistics_warehousing_operational_agent import (
            ManageLogisticsWarehousingOperationalAgent
        )
        return ManageLogisticsWarehousingOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.manage_logistics_warehousing_operational_agent import (
            ManageLogisticsWarehousingOperationalAgentConfig
        )
        return ManageLogisticsWarehousingOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_process_id": "4.4",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "logistics",
            "warehousing",
            "inventory_management",
            "distribution"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for logistics and warehousing."""
        return {
            "task_type": "manage_logistics",
            "data": {
                "shipments": [
                    {
                        "id": "SHIP-001",
                        "origin": "Warehouse-A",
                        "destination": "Customer-001",
                        "items": [{"sku": "PROD-001", "quantity": 100}],
                        "delivery_window": {
                            "start": datetime.now().isoformat(),
                            "end": (datetime.now() + timedelta(days=3)).isoformat()
                        }
                    }
                ],
                "warehouses": [
                    {
                        "id": "WH-001",
                        "capacity": 10000,
                        "utilization": 0.75,
                        "location": "Chicago"
                    }
                ],
                "optimization_criteria": ["cost", "speed", "reliability"]
            },
            "context": {
                "service_level": "standard",
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestManageTransportationOperationalAgent(APQCAgentTestCase):
    """
    Tests for ManageTransportationOperationalAgent

    Agent: Manage transportation
    Path: src/superstandard/agents/operations/manage_transportation_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.manage_transportation_operational_agent import (
            ManageTransportationOperationalAgent
        )
        return ManageTransportationOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.manage_transportation_operational_agent import (
            ManageTransportationOperationalAgentConfig
        )
        return ManageTransportationOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for transportation management."""
        return {
            "task_type": "manage_transportation",
            "data": {
                "routes": [
                    {
                        "id": "ROUTE-001",
                        "origin": "DC-Chicago",
                        "destination": "Store-NYC",
                        "distance_miles": 800,
                        "stops": 3
                    }
                ],
                "fleet": [
                    {"vehicle_id": "TRUCK-001", "capacity": 20000, "status": "available"},
                    {"vehicle_id": "TRUCK-002", "capacity": 20000, "status": "in_transit"}
                ],
                "shipments_pending": 15,
                "optimization_goal": "minimize_cost"
            },
            "context": {
                "transportation_mode": "ground",
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestManageWarehouseOperationsOperationalAgent(APQCAgentTestCase):
    """
    Tests for ManageWarehouseOperationsOperationalAgent

    Agent: Manage warehouse operations
    Path: src/superstandard/agents/operations/manage_warehouse_operations_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.manage_warehouse_operations_operational_agent import (
            ManageWarehouseOperationsOperationalAgent
        )
        return ManageWarehouseOperationsOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.manage_warehouse_operations_operational_agent import (
            ManageWarehouseOperationsOperationalAgentConfig
        )
        return ManageWarehouseOperationsOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for warehouse operations."""
        return {
            "task_type": "manage_warehouse",
            "data": {
                "warehouse_id": "WH-001",
                "operations": [
                    {
                        "type": "receiving",
                        "items": [{"sku": "PROD-001", "quantity": 500}],
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "type": "picking",
                        "order_id": "ORD-123",
                        "items": [{"sku": "PROD-002", "quantity": 100}]
                    }
                ],
                "inventory_accuracy_target": 0.995,
                "throughput_target": 1000  # units per hour
            },
            "context": {
                "shift": "day",
                "priority": "medium"
            },
            "priority": "medium"
        }


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestOptimizeInventoryOperationalAgent(APQCAgentTestCase):
    """
    Tests for OptimizeInventoryOperationalAgent

    Agent: Optimize inventory
    Path: src/superstandard/agents/operations/optimize_inventory_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.optimize_inventory_operational_agent import (
            OptimizeInventoryOperationalAgent
        )
        return OptimizeInventoryOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.optimize_inventory_operational_agent import (
            OptimizeInventoryOperationalAgentConfig
        )
        return OptimizeInventoryOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "analysis",
            "optimization",
            "inventory_management",
            "forecasting"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for inventory optimization."""
        return {
            "task_type": "optimize_inventory",
            "data": {
                "products": [
                    {
                        "sku": "PROD-001",
                        "current_stock": 1000,
                        "demand_rate": 100,  # per day
                        "lead_time": 14,  # days
                        "holding_cost": 2.5,  # per unit per year
                        "ordering_cost": 50  # per order
                    },
                    {
                        "sku": "PROD-002",
                        "current_stock": 500,
                        "demand_rate": 50,
                        "lead_time": 21,
                        "holding_cost": 3.0,
                        "ordering_cost": 75
                    }
                ],
                "service_level_target": 0.95,
                "optimization_method": "min_cost",
                "constraints": ["warehouse_capacity", "cash_flow"]
            },
            "context": {
                "review_period": "weekly",
                "priority": "medium"
            },
            "priority": "medium"
        }

    @pytest.mark.asyncio
    async def test_inventory_optimization(self):
        """Test inventory optimization algorithms."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "calculate_reorder_points",
            "data": {
                "products": [
                    {
                        "sku": "PROD-A",
                        "avg_demand": 100,
                        "demand_variability": 0.2,
                        "lead_time": 10,
                        "lead_time_variability": 0.1,
                        "service_level": 0.95
                    }
                ],
                "method": "statistical"
            },
            "priority": "medium"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestForecastDemandOperationalAgent(APQCAgentTestCase):
    """
    Tests for ForecastDemandOperationalAgent

    Agent: Forecast demand
    Path: src/superstandard/agents/operations/forecast_demand_operational_agent.py
    Domain: operations | Type: operational
    """

    def get_agent_class(self):
        """Import and return agent class."""
        from superstandard.agents.operations.forecast_demand_operational_agent import (
            ForecastDemandOperationalAgent
        )
        return ForecastDemandOperationalAgent

    def get_agent_config(self):
        """Return agent configuration."""
        from superstandard.agents.operations.forecast_demand_operational_agent import (
            ForecastDemandOperationalAgentConfig
        )
        return ForecastDemandOperationalAgentConfig()

    def get_expected_apqc_metadata(self) -> Dict[str, str]:
        """Return expected APQC metadata."""
        return {
            "apqc_category_id": "4.0",
            "apqc_framework_version": "7.0.1"
        }

    def get_expected_capabilities(self) -> List[str]:
        """Return expected capabilities."""
        return [
            "analysis",
            "forecasting",
            "statistical_modeling",
            "demand_planning"
        ]

    def generate_valid_input(self) -> Dict[str, Any]:
        """Generate valid input for demand forecasting."""
        return {
            "task_type": "forecast_demand",
            "data": {
                "historical_data": [
                    {"period": "2024-01", "demand": 1000},
                    {"period": "2024-02", "demand": 1100},
                    {"period": "2024-03", "demand": 1050},
                    {"period": "2024-04", "demand": 1200},
                    {"period": "2024-05", "demand": 1250},
                    {"period": "2024-06", "demand": 1300}
                ],
                "forecast_horizon": 6,  # months
                "forecast_method": "time_series",
                "seasonality": True,
                "external_factors": {
                    "economic_indicators": [0.03, 0.035, 0.04],  # growth rates
                    "promotional_events": ["summer_sale"]
                }
            },
            "context": {
                "product_category": "consumer_goods",
                "priority": "high"
            },
            "priority": "high"
        }

    @pytest.mark.asyncio
    async def test_demand_forecasting(self):
        """Test demand forecasting with various methods."""
        config = self.get_agent_config()
        agent_class = self.get_agent_class()
        agent = agent_class(config)

        input_data = {
            "task_type": "generate_forecast",
            "data": {
                "product_id": "PROD-001",
                "historical_sales": list(range(100, 150, 5)),  # Trending data
                "forecast_periods": 12,
                "confidence_interval": 0.95,
                "method": "exponential_smoothing"
            },
            "priority": "high"
        }

        result = await agent.execute(input_data)

        assert result['status'] in ['completed', 'degraded']
        assert 'output' in result


# ========================================================================
# Category 4.0 Integration Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
@pytest.mark.apqc_integration
class TestCategory4Integration:
    """
    Integration tests for Category 4.0 - Deliver Physical Products agents.

    Tests end-to-end supply chain workflows and cross-agent collaboration.
    """

    @pytest.mark.asyncio
    async def test_end_to_end_supply_chain_workflow(self):
        """
        Test complete supply chain workflow from planning to delivery.

        Workflow:
        1. Forecast demand (ForecastDemandOperationalAgent)
        2. Plan supply chain resources (PlanSupplyChainResourcesOperationalAgent)
        3. Procure materials (ProcureMaterialsServicesOperationalAgent)
        4. Schedule production (ScheduleProductionOperationalAgent)
        5. Produce product (ProduceManufactureDeliverProductOperationalAgent)
        6. Manage logistics (ManageLogisticsWarehousingOperationalAgent)
        """
        # Import agents
        from superstandard.agents.operations.forecast_demand_operational_agent import (
            ForecastDemandOperationalAgent,
            ForecastDemandOperationalAgentConfig
        )
        from superstandard.agents.operations.plan_supply_chain_resources_operational_agent import (
            PlanSupplyChainResourcesOperationalAgent,
            PlanSupplyChainResourcesOperationalAgentConfig
        )
        from superstandard.agents.api.procure_materials_services_operational_agent import (
            ProcureMaterialsServicesOperationalAgent,
            ProcureMaterialsServicesOperationalAgentConfig
        )
        from superstandard.agents.operations.schedule_production_operational_agent import (
            ScheduleProductionOperationalAgent,
            ScheduleProductionOperationalAgentConfig
        )

        # Create agent instances
        forecast_agent = ForecastDemandOperationalAgent(ForecastDemandOperationalAgentConfig())
        planning_agent = PlanSupplyChainResourcesOperationalAgent(PlanSupplyChainResourcesOperationalAgentConfig())
        procurement_agent = ProcureMaterialsServicesOperationalAgent(ProcureMaterialsServicesOperationalAgentConfig())
        scheduling_agent = ScheduleProductionOperationalAgent(ScheduleProductionOperationalAgentConfig())

        # Step 1: Forecast demand
        forecast_input = {
            "task_type": "forecast_demand",
            "data": {
                "historical_data": [{"period": f"2024-{i:02d}", "demand": 1000 + i * 50} for i in range(1, 7)],
                "forecast_horizon": 3
            },
            "priority": "high"
        }
        forecast_result = await forecast_agent.execute(forecast_input)
        assert forecast_result['status'] in ['completed', 'degraded']

        # Step 2: Plan supply chain resources based on forecast
        planning_input = {
            "task_type": "plan_supply_chain",
            "data": {
                "demand_forecast": forecast_result.get('output', {}),
                "current_capacity": {"production": 5000, "warehouse": 2000}
            },
            "priority": "high"
        }
        planning_result = await planning_agent.execute(planning_input)
        assert planning_result['status'] in ['completed', 'degraded']

        # Step 3: Procure materials
        procurement_input = {
            "task_type": "procure_materials",
            "data": {
                "resource_plan": planning_result.get('output', {}),
                "approved_suppliers": ["SUP-001", "SUP-002"]
            },
            "priority": "high"
        }
        procurement_result = await procurement_agent.execute(procurement_input)
        assert procurement_result['status'] in ['completed', 'degraded']

        # Step 4: Schedule production
        scheduling_input = {
            "task_type": "schedule_production",
            "data": {
                "orders": [{"id": "ORD-001", "product": "PROD-A", "quantity": 1000}],
                "materials_available": True
            },
            "priority": "high"
        }
        scheduling_result = await scheduling_agent.execute(scheduling_input)
        assert scheduling_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_procurement_to_production_workflow(self):
        """
        Test procurement to production workflow integration.
        """
        from superstandard.agents.api.procure_materials_services_operational_agent import (
            ProcureMaterialsServicesOperationalAgent,
            ProcureMaterialsServicesOperationalAgentConfig
        )
        from superstandard.agents.operations.produce_manufacture_deliver_product_operational_agent import (
            ProduceManufactureDeliverProductOperationalAgent,
            ProduceManufactureDeliverProductOperationalAgentConfig
        )

        procurement_agent = ProcureMaterialsServicesOperationalAgent(
            ProcureMaterialsServicesOperationalAgentConfig()
        )
        production_agent = ProduceManufactureDeliverProductOperationalAgent(
            ProduceManufactureDeliverProductOperationalAgentConfig()
        )

        # Procure materials
        procurement_input = {
            "task_type": "procure_materials",
            "data": {
                "purchase_request": {
                    "items": [{"material_id": "MAT-001", "quantity": 1000}],
                    "budget": 50000
                }
            },
            "priority": "high"
        }
        procurement_result = await procurement_agent.execute(procurement_input)

        # Produce using procured materials
        production_input = {
            "task_type": "produce_product",
            "data": {
                "production_order": {"order_id": "PO-001", "quantity": 500},
                "materials": procurement_result.get('output', {})
            },
            "priority": "high"
        }
        production_result = await production_agent.execute(production_input)

        assert production_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_inventory_optimization_with_forecasting(self):
        """
        Test integration between demand forecasting and inventory optimization.
        """
        from superstandard.agents.operations.forecast_demand_operational_agent import (
            ForecastDemandOperationalAgent,
            ForecastDemandOperationalAgentConfig
        )
        from superstandard.agents.operations.optimize_inventory_operational_agent import (
            OptimizeInventoryOperationalAgent,
            OptimizeInventoryOperationalAgentConfig
        )

        forecast_agent = ForecastDemandOperationalAgent(ForecastDemandOperationalAgentConfig())
        inventory_agent = OptimizeInventoryOperationalAgent(OptimizeInventoryOperationalAgentConfig())

        # Generate demand forecast
        forecast_input = {
            "task_type": "forecast_demand",
            "data": {
                "historical_data": [{"period": f"2024-{i:02d}", "demand": 100 + i * 10} for i in range(1, 13)],
                "forecast_horizon": 6
            },
            "priority": "high"
        }
        forecast_result = await forecast_agent.execute(forecast_input)

        # Optimize inventory based on forecast
        inventory_input = {
            "task_type": "optimize_inventory",
            "data": {
                "demand_forecast": forecast_result.get('output', {}),
                "products": [
                    {
                        "sku": "PROD-001",
                        "current_stock": 1000,
                        "holding_cost": 2.5,
                        "ordering_cost": 50
                    }
                ],
                "service_level_target": 0.95
            },
            "priority": "high"
        }
        inventory_result = await inventory_agent.execute(inventory_input)

        assert inventory_result['status'] in ['completed', 'degraded']

    @pytest.mark.asyncio
    async def test_supplier_management_workflow(self):
        """
        Test supplier management workflow (relationships + contracts).
        """
        from superstandard.agents.business.manage_supplier_relationships_operational_agent import (
            ManageSupplierRelationshipsOperationalAgent,
            ManageSupplierRelationshipsOperationalAgentConfig
        )
        from superstandard.agents.blockchain.manage_supplier_contracts_operational_agent import (
            ManageSupplierContractsOperationalAgent,
            ManageSupplierContractsOperationalAgentConfig
        )

        relationship_agent = ManageSupplierRelationshipsOperationalAgent(
            ManageSupplierRelationshipsOperationalAgentConfig()
        )
        contract_agent = ManageSupplierContractsOperationalAgent(
            ManageSupplierContractsOperationalAgentConfig()
        )

        # Evaluate supplier relationship
        relationship_input = {
            "task_type": "evaluate_supplier",
            "data": {
                "supplier": {"id": "SUP-001", "tier": "strategic"},
                "performance_metrics": {"quality": 0.98, "on_time_delivery": 0.95}
            },
            "priority": "medium"
        }
        relationship_result = await relationship_agent.execute(relationship_input)

        # Manage contract based on relationship evaluation
        contract_input = {
            "task_type": "renew_contract",
            "data": {
                "supplier_id": "SUP-001",
                "performance_evaluation": relationship_result.get('output', {}),
                "contract_value": 1000000
            },
            "priority": "medium"
        }
        contract_result = await contract_agent.execute(contract_input)

        assert contract_result['status'] in ['completed', 'degraded']


# ========================================================================
# Category-Specific Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
class TestCategory4Capabilities:
    """
    Test category-specific capabilities for Deliver Physical Products agents.
    """

    @pytest.mark.asyncio
    async def test_operational_agents_have_required_capabilities(self):
        """Verify all operational agents have required operational capabilities."""
        from superstandard.agents.operations.produce_manufacture_deliver_product_operational_agent import (
            ProduceManufactureDeliverProductOperationalAgent,
            ProduceManufactureDeliverProductOperationalAgentConfig
        )

        agent = ProduceManufactureDeliverProductOperationalAgent(
            ProduceManufactureDeliverProductOperationalAgentConfig()
        )

        required_capabilities = [
            "analysis",
            "execution"
        ]

        for capability in required_capabilities:
            assert capability in agent.capabilities_list, \
                f"Operational agent should have {capability} capability"

    @pytest.mark.asyncio
    async def test_supply_chain_agents_support_optimization(self):
        """Verify supply chain agents support optimization workflows."""
        from superstandard.agents.operations.optimize_inventory_operational_agent import (
            OptimizeInventoryOperationalAgent,
            OptimizeInventoryOperationalAgentConfig
        )

        agent = OptimizeInventoryOperationalAgent(
            OptimizeInventoryOperationalAgentConfig()
        )

        # Test optimization capabilities
        optimization_input = {
            "task_type": "optimize",
            "data": {
                "optimization_type": "cost_minimization",
                "constraints": ["capacity", "budget"],
                "objective": "minimize_total_cost"
            },
            "priority": "medium"
        }

        result = await agent.execute(optimization_input)
        assert result is not None
        assert 'status' in result


# ========================================================================
# Performance and Scale Tests
# ========================================================================

@pytest.mark.apqc
@pytest.mark.apqc_category_4
@pytest.mark.slow
class TestCategory4Performance:
    """
    Performance tests for Category 4 agents.
    """

    @pytest.mark.asyncio
    async def test_concurrent_supply_chain_operations(self):
        """Test multiple supply chain agents executing concurrently."""
        import asyncio
        from superstandard.agents.operations.forecast_demand_operational_agent import (
            ForecastDemandOperationalAgent,
            ForecastDemandOperationalAgentConfig
        )
        from superstandard.agents.operations.optimize_inventory_operational_agent import (
            OptimizeInventoryOperationalAgent,
            OptimizeInventoryOperationalAgentConfig
        )
        from superstandard.agents.operations.schedule_production_operational_agent import (
            ScheduleProductionOperationalAgent,
            ScheduleProductionOperationalAgentConfig
        )

        # Create multiple agent instances
        forecast_agent = ForecastDemandOperationalAgent(ForecastDemandOperationalAgentConfig())
        inventory_agent = OptimizeInventoryOperationalAgent(OptimizeInventoryOperationalAgentConfig())
        scheduling_agent = ScheduleProductionOperationalAgent(ScheduleProductionOperationalAgentConfig())

        # Execute concurrently
        forecast_input = {
            "task_type": "forecast_demand",
            "data": {"historical_data": [{"period": "2024-01", "demand": 1000}]},
            "priority": "high"
        }
        inventory_input = {
            "task_type": "optimize_inventory",
            "data": {"products": [{"sku": "PROD-001", "current_stock": 1000}]},
            "priority": "medium"
        }
        scheduling_input = {
            "task_type": "schedule_production",
            "data": {"orders": [{"id": "ORD-001", "quantity": 100}]},
            "priority": "medium"
        }

        tasks = [
            forecast_agent.execute(forecast_input),
            inventory_agent.execute(inventory_input),
            scheduling_agent.execute(scheduling_input)
        ]
        results = await asyncio.gather(*tasks)

        # Verify all completed
        assert len(results) == 3
        for result in results:
            assert result['status'] in ['completed', 'degraded']


# ========================================================================
# Utility Functions
# ========================================================================

def create_category_4_test_suite():
    """
    Create a complete test suite for Category 4 agents.

    Returns:
        List of test classes
    """
    return [
        TestPlanForAlignSupplyChainResourcesOperationalAgent,
        TestPlanSupplyChainResourcesOperationalAgent,
        TestProcureMaterialsServicesOperationalAgent,
        TestManageSupplierContractsOperationalAgent,
        TestManageSupplierRelationshipsOperationalAgent,
        TestProduceManufactureDeliverProductOperationalAgent,
        TestScheduleProductionOperationalAgent,
        TestManageLogisticsWarehousingOperationalAgent,
        TestManageTransportationOperationalAgent,
        TestManageWarehouseOperationsOperationalAgent,
        TestOptimizeInventoryOperationalAgent,
        TestForecastDemandOperationalAgent,
        TestCategory4Integration,
        TestCategory4Capabilities,
        TestCategory4Performance
    ]


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
