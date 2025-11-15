"""
Workflow Template Library

Pre-built, production-ready workflow templates for common business scenarios!

Templates span multiple APQC categories and provide instant business value.

Usage:
    from src.superstandard.templates import get_template_library

    library = get_template_library()
    library.show_catalog()  # See all templates

    template = library.get_template("new_product_launch")
    workflow = template.instantiate(params={"total_budget": 150.0})
"""

from .workflow_templates import (
    WorkflowTemplate,
    WorkflowTemplateLibrary,
    get_template_library
)

__all__ = [
    'WorkflowTemplate',
    'WorkflowTemplateLibrary',
    'get_template_library'
]
