"""
BPMN 2.0 Protocol Generator for APQC Agents
===========================================

Generates BPMN 2.0 (Business Process Model and Notation) standard XML
for each APQC agent, enabling:

- Visual process modeling
- User-adjustable workflows
- Integration with other BPMN 2.0 systems
- Interoperability with BPM platforms (Camunda, Activiti, etc.)
- Export/Import capabilities

Version: 2.0.0
Date: 2025-11-17
Standard: BPMN 2.0 (OMG Specification)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from datetime import datetime


@dataclass
class BPMNTask:
    """Represents a BPMN task element"""
    id: str
    name: str
    implementation: str = "##WebService"  # APQC agent implementation


@dataclass
class BPMNSequenceFlow:
    """Represents a BPMN sequence flow (connection between tasks)"""
    id: str
    source_ref: str
    target_ref: str
    condition: Optional[str] = None


class BPMN2Generator:
    """
    Generates BPMN 2.0 compliant XML for APQC business processes

    Supports:
    - Process definitions
    - Task elements (Service Tasks for agents)
    - Sequence flows
    - Start/End events
    - Gateways (decision points)
    - User-editable in standard BPMN tools
    """

    def __init__(self):
        self.namespace = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def generate_for_agent(
        self,
        apqc_id: str,
        apqc_name: str,
        workflow_steps: List[str],
        category_name: str
    ) -> str:
        """
        Generate BPMN 2.0 XML for an APQC agent

        Args:
            apqc_id: APQC task ID (e.g., "9.2.1.1")
            apqc_name: APQC task name
            workflow_steps: List of workflow step names
            category_name: APQC category name

        Returns:
            BPMN 2.0 XML string
        """
        # Create root element
        definitions = ET.Element('bpmn:definitions', {
            'xmlns:bpmn': self.namespace['bpmn'],
            'xmlns:bpmndi': self.namespace['bpmndi'],
            'xmlns:dc': self.namespace['dc'],
            'xmlns:di': self.namespace['di'],
            'xmlns:xsi': self.namespace['xsi'],
            'id': f'Definitions_{apqc_id.replace(".", "_")}',
            'targetNamespace': f'http://apqc.org/process/{apqc_id}',
            'exporter': 'APQC Agentic Platform',
            'exporterVersion': '2.0.0'
        })

        # Add process element
        process_id = f'Process_{apqc_id.replace(".", "_")}'
        process = ET.SubElement(definitions, 'bpmn:process', {
            'id': process_id,
            'name': f'{apqc_id} - {apqc_name}',
            'isExecutable': 'true',
            'processType': 'None'
        })

        # Add documentation
        documentation = ET.SubElement(process, 'bpmn:documentation')
        documentation.text = f"""
APQC Process: {category_name}
Task: {apqc_id} - {apqc_name}

This BPMN 2.0 process model represents the standardized workflow for this APQC task.
It can be edited in any BPMN 2.0 compliant tool and integrated with other business processes.

Generated: {datetime.now().isoformat()}
"""

        # Add start event
        start_event = ET.SubElement(process, 'bpmn:startEvent', {
            'id': f'StartEvent_{apqc_id.replace(".", "_")}',
            'name': 'Start'
        })
        start_outgoing = ET.SubElement(start_event, 'bpmn:outgoing')
        start_outgoing.text = f'Flow_start_to_step1'

        # Add tasks for each workflow step
        previous_step_id = None
        for i, step_name in enumerate(workflow_steps):
            step_id = f'Task_{apqc_id.replace(".", "_")}_step{i+1}'

            # Create service task (represents APQC agent execution)
            task = ET.SubElement(process, 'bpmn:serviceTask', {
                'id': step_id,
                'name': step_name,
                'implementation': '##WebService'
            })

            # Add incoming flow
            incoming = ET.SubElement(task, 'bpmn:incoming')
            if i == 0:
                incoming.text = f'Flow_start_to_step1'
            else:
                incoming.text = f'Flow_step{i}_to_step{i+1}'

            # Add outgoing flow
            outgoing = ET.SubElement(task, 'bpmn:outgoing')
            if i < len(workflow_steps) - 1:
                outgoing.text = f'Flow_step{i+1}_to_step{i+2}'
            else:
                outgoing.text = f'Flow_step{i+1}_to_end'

            # Add extension elements for APQC metadata
            extension = ET.SubElement(task, 'bpmn:extensionElements')
            apqc_meta = ET.SubElement(extension, 'apqc:metadata', {
                'apqc_id': apqc_id,
                'step_number': str(i+1),
                'agent_implementation': f'apqc_{apqc_id.replace(".", "_")}'
            })

            previous_step_id = step_id

        # Add sequence flows
        for i in range(len(workflow_steps) + 1):
            if i == 0:
                # Start to first task
                flow = ET.SubElement(process, 'bpmn:sequenceFlow', {
                    'id': f'Flow_start_to_step1',
                    'sourceRef': f'StartEvent_{apqc_id.replace(".", "_")}',
                    'targetRef': f'Task_{apqc_id.replace(".", "_")}_step1'
                })
            elif i < len(workflow_steps):
                # Between tasks
                flow = ET.SubElement(process, 'bpmn:sequenceFlow', {
                    'id': f'Flow_step{i}_to_step{i+1}',
                    'sourceRef': f'Task_{apqc_id.replace(".", "_")}_step{i}',
                    'targetRef': f'Task_{apqc_id.replace(".", "_")}_step{i+1}'
                })
            else:
                # Last task to end
                flow = ET.SubElement(process, 'bpmn:sequenceFlow', {
                    'id': f'Flow_step{i}_to_end',
                    'sourceRef': f'Task_{apqc_id.replace(".", "_")}_step{i}',
                    'targetRef': f'EndEvent_{apqc_id.replace(".", "_")}'
                })

        # Add end event
        end_event = ET.SubElement(process, 'bpmn:endEvent', {
            'id': f'EndEvent_{apqc_id.replace(".", "_")}',
            'name': 'End'
        })
        end_incoming = ET.SubElement(end_event, 'bpmn:incoming')
        end_incoming.text = f'Flow_step{len(workflow_steps)}_to_end'

        # Add BPMN diagram information (for visual rendering)
        self._add_diagram_info(definitions, process_id, apqc_id, workflow_steps)

        # Convert to pretty XML string
        xml_string = ET.tostring(definitions, encoding='unicode', method='xml')
        return self._prettify_xml(xml_string)

    def _add_diagram_info(
        self,
        definitions: ET.Element,
        process_id: str,
        apqc_id: str,
        workflow_steps: List[str]
    ):
        """Add BPMN diagram interchange information for visual layout"""
        diagram = ET.SubElement(definitions, 'bpmndi:BPMNDiagram', {
            'id': f'BPMNDiagram_{apqc_id.replace(".", "_")}'
        })

        plane = ET.SubElement(diagram, 'bpmndi:BPMNPlane', {
            'id': f'BPMNPlane_{apqc_id.replace(".", "_")}',
            'bpmnElement': process_id
        })

        # Layout elements vertically with 100px spacing
        y_offset = 50

        # Start event shape
        start_shape = ET.SubElement(plane, 'bpmndi:BPMNShape', {
            'id': f'Shape_StartEvent_{apqc_id.replace(".", "_")}',
            'bpmnElement': f'StartEvent_{apqc_id.replace(".", "_")}'
        })
        start_bounds = ET.SubElement(start_shape, 'dc:Bounds', {
            'x': '180',
            'y': str(y_offset),
            'width': '36',
            'height': '36'
        })
        y_offset += 100

        # Task shapes
        for i in range(len(workflow_steps)):
            task_shape = ET.SubElement(plane, 'bpmndi:BPMNShape', {
                'id': f'Shape_Task_{apqc_id.replace(".", "_")}_step{i+1}',
                'bpmnElement': f'Task_{apqc_id.replace(".", "_")}_step{i+1}'
            })
            task_bounds = ET.SubElement(task_shape, 'dc:Bounds', {
                'x': '130',
                'y': str(y_offset),
                'width': '140',
                'height': '80'
            })
            y_offset += 100

        # End event shape
        end_shape = ET.SubElement(plane, 'bpmndi:BPMNShape', {
            'id': f'Shape_EndEvent_{apqc_id.replace(".", "_")}',
            'bpmnElement': f'EndEvent_{apqc_id.replace(".", "_")}'
        })
        end_bounds = ET.SubElement(end_shape, 'dc:Bounds', {
            'x': '180',
            'y': str(y_offset),
            'width': '36',
            'height': '36'
        })

    def _prettify_xml(self, xml_string: str) -> str:
        """Format XML with proper indentation"""
        from xml.dom import minidom
        dom = minidom.parseString(xml_string)
        return dom.toprettyxml(indent='  ')


# Example workflow definitions for common APQC tasks
APQC_WORKFLOWS = {
    "9.2.1.1": {
        "name": "Process invoices and track accounts payable",
        "category": "9.0 - Manage Financial Resources",
        "workflow_steps": [
            "Invoice Receipt and Validation",
            "Vendor Verification",
            "Purchase Order Matching (3-way)",
            "Goods Receipt Verification",
            "Price Variance Check (5% tolerance)",
            "GL Coding Assignment",
            "Approval Workflow",
            "Post to Accounts Payable",
            "Payment Scheduling",
            "Audit Trail Recording"
        ]
    },
    "9.6.2.3": {
        "name": "Execute electronic payments",
        "category": "9.0 - Manage Financial Resources",
        "workflow_steps": [
            "Payment Request Validation",
            "Funds Availability Check",
            "Payment Method Selection",
            "Beneficiary Verification",
            "Execute Payment (ACH/Wire/Check)",
            "Update General Ledger",
            "Update Accounts Payable",
            "Send Payment Confirmation",
            "Record Audit Trail"
        ]
    },
    "7.5.1.1": {
        "name": "Process payroll",
        "category": "7.0 - Manage Human Capital",
        "workflow_steps": [
            "Gather Employee Time Data",
            "Calculate Regular and Overtime Hours (FLSA)",
            "Calculate Gross Pay",
            "Calculate Deductions (Federal, State, FICA, Benefits)",
            "Calculate Net Pay",
            "Generate Direct Deposits/Paychecks",
            "Update General Ledger",
            "Generate Pay Stubs",
            "Generate Tax Forms (W-2, 1099 if year-end)",
            "Record Audit Trail"
        ]
    },
    "3.2.2.1": {
        "name": "Qualify opportunities",
        "category": "3.0 - Market and Sell Products and Services",
        "workflow_steps": [
            "Budget Qualification",
            "Authority Qualification",
            "Need Qualification",
            "Timeline Qualification",
            "Calculate Qualification Score (BANT)",
            "Determine Qualification Level (HOT/WARM/COOL/COLD)",
            "Assign Sales Stage",
            "Update CRM System",
            "Trigger Next Actions",
            "Record Audit Trail"
        ]
    }
}


def generate_bpmn_for_all_agents():
    """Generate BPMN 2.0 XML files for all APQC agents"""
    import os
    from pathlib import Path

    generator = BPMN2Generator()
    output_dir = Path("bpmn_processes")
    output_dir.mkdir(exist_ok=True)

    for apqc_id, workflow_def in APQC_WORKFLOWS.items():
        bpmn_xml = generator.generate_for_agent(
            apqc_id=apqc_id,
            apqc_name=workflow_def['name'],
            workflow_steps=workflow_def['workflow_steps'],
            category_name=workflow_def['category']
        )

        filename = f"APQC_{apqc_id.replace('.', '_')}.bpmn"
        output_path = output_dir / filename

        with open(output_path, 'w') as f:
            f.write(bpmn_xml)

        print(f"✅ Generated BPMN 2.0: {filename}")

    print(f"\n✅ All BPMN 2.0 files generated in: {output_dir}")
    print("\nThese files can be:")
    print("  • Edited in any BPMN 2.0 tool (Camunda Modeler, etc.)")
    print("  • Integrated with BPM platforms (Camunda, Activiti, jBPM)")
    print("  • Modified by users through the UI")
    print("  • Imported/exported for process integration")


if __name__ == "__main__":
    generate_bpmn_for_all_agents()
