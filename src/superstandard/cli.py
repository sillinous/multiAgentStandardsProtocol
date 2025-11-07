"""
SuperStandard CLI - Command-line interface for agent management

Usage:
    superstandard create my-agent --template=trading
    superstandard list --category=trading
    superstandard run my-agent --config=prod
    superstandard test my-agent
    superstandard docs my-agent
"""

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from typing import Optional
import json

app = typer.Typer(
    name="superstandard",
    help="SuperStandard - The Platform for Building Production-Grade Multi-Agent Systems",
)
console = Console()


@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the agent to create"),
    template: str = typer.Option("base", help="Template to use (base, trading, api, ml, etc.)"),
    category: str = typer.Option("general", help="Agent category"),
    description: str = typer.Option("", help="Agent description"),
):
    """
    Create a new agent from template

    Examples:
        superstandard create my-trading-bot --template=trading
        superstandard create my-api --template=api --category=api
    """
    console.print(f"\n[bold green]Creating agent: {name}[/bold green]")
    console.print(f"Template: {template}")
    console.print(f"Category: {category}\n")

    # Get base path
    base_path = Path.cwd() / "src" / "superstandard" / "agents" / category
    agent_file = base_path / f"{name}.py"

    if agent_file.exists():
        console.print(f"[red]Error: Agent {name} already exists at {agent_file}[/red]")
        raise typer.Exit(1)

    # Load template
    template_path = Path(__file__).parent / "templates" / template
    if not template_path.exists():
        console.print(f"[yellow]Template '{template}' not found, using base template[/yellow]")
        template_path = Path(__file__).parent / "templates" / "base"

    # Create from template
    base_path.mkdir(parents=True, exist_ok=True)

    template_content = _generate_agent_template(name, template, category, description)
    agent_file.write_text(template_content)

    console.print(f"[green]✓ Created agent: {agent_file}[/green]")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit your agent: {agent_file}")
    console.print(f"  2. Test your agent: superstandard test {name}")
    console.print(f"  3. Run your agent: superstandard run {name}\n")


@app.command()
def list(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    search: Optional[str] = typer.Option(None, help="Search agents by name"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
):
    """
    List all available agents

    Examples:
        superstandard list
        superstandard list --category=trading
        superstandard list --search=market
    """
    console.print("\n[bold]Available Agents[/bold]\n")

    # Load agent catalog
    catalog_path = Path.cwd() / "AGENT_CATALOG.json"
    if not catalog_path.exists():
        console.print(
            "[yellow]No agent catalog found. Run: python scripts/analyze_agents.py[/yellow]"
        )
        return

    with open(catalog_path) as f:
        catalog = json.load(f)

    agents = catalog.get("agents", [])

    # Filter by category
    if category:
        agents = [a for a in agents if a.get("category") == category]

    # Search by name
    if search:
        search_lower = search.lower()
        agents = [a for a in agents if search_lower in a.get("name", "").lower()]

    if not agents:
        console.print("[yellow]No agents found matching criteria[/yellow]")
        return

    # Display as table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Type", style="blue")
    if detailed:
        table.add_column("File", style="dim")

    for agent in agents[:50]:  # Limit to 50 for display
        name = agent.get("name", "Unknown")
        cat = agent.get("category", "general")
        agent_type = agent.get("type", "python")
        file_path = agent.get("file", "")

        if detailed:
            table.add_row(name, cat, agent_type, file_path)
        else:
            table.add_row(name, cat, agent_type)

    console.print(table)
    console.print(f"\n[dim]Showing {len(agents[:50])} of {len(agents)} agents[/dim]\n")


@app.command()
def run(
    name: str = typer.Argument(..., help="Name of agent to run"),
    config: str = typer.Option("default", help="Configuration to use"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
):
    """
    Run an agent

    Examples:
        superstandard run trading-bot
        superstandard run trading-bot --config=prod
        superstandard run trading-bot --background
    """
    console.print(f"\n[bold blue]Starting agent: {name}[/bold blue]")
    console.print(f"Configuration: {config}\n")

    # TODO: Implement agent loading and execution
    console.print("[yellow]Agent execution not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Full agent runtime with monitoring[/dim]\n")


@app.command()
def test(
    name: str = typer.Argument(..., help="Name of agent to test"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Test an agent

    Examples:
        superstandard test my-agent
        superstandard test my-agent --verbose
    """
    console.print(f"\n[bold]Testing agent: {name}[/bold]\n")

    # TODO: Implement agent testing
    console.print("[yellow]Agent testing not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Automated test suite with coverage reports[/dim]\n")


@app.command()
def docs(
    name: Optional[str] = typer.Argument(None, help="Agent name (omit for all)"),
    output_dir: str = typer.Option("docs/", help="Output directory for docs"),
    format: str = typer.Option("markdown", help="Output format (markdown, html, pdf)"),
):
    """
    Generate documentation for agents

    Examples:
        superstandard docs                    # Generate docs for all agents
        superstandard docs my-agent          # Generate docs for specific agent
        superstandard docs --format=html     # Generate HTML docs
    """
    if name:
        console.print(f"\n[bold]Generating documentation for: {name}[/bold]\n")
    else:
        console.print(f"\n[bold]Generating documentation for all agents[/bold]\n")

    # TODO: Implement auto-documentation
    console.print("[yellow]Auto-documentation not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Beautiful auto-generated docs from code[/dim]\n")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    category: Optional[str] = typer.Option(None, help="Filter by category"),
):
    """
    Search for agents

    Examples:
        superstandard search "trading bot"
        superstandard search market --category=trading
    """
    console.print(f"\n[bold]Searching for: {query}[/bold]\n")

    # TODO: Implement smart search
    console.print("[yellow]Smart search not yet implemented[/yellow]")
    console.print("[dim]Coming soon: AI-powered semantic search[/dim]\n")


@app.command()
def info(
    name: str = typer.Argument(..., help="Agent name"),
):
    """
    Show detailed information about an agent

    Examples:
        superstandard info trading-bot
    """
    console.print(f"\n[bold]Agent Information: {name}[/bold]\n")

    # Load agent catalog
    catalog_path = Path.cwd() / "AGENT_CATALOG.json"
    if not catalog_path.exists():
        console.print("[yellow]No agent catalog found[/yellow]")
        return

    with open(catalog_path) as f:
        catalog = json.load(f)

    # Find agent
    agents = catalog.get("agents", [])
    agent = next((a for a in agents if a.get("name") == name), None)

    if not agent:
        console.print(f"[red]Agent '{name}' not found[/red]")
        return

    # Display info
    console.print(f"[cyan]Name:[/cyan] {agent.get('name')}")
    console.print(f"[cyan]Category:[/cyan] {agent.get('category', 'general')}")
    console.print(f"[cyan]Type:[/cyan] {agent.get('type', 'python')}")
    console.print(f"[cyan]File:[/cyan] {agent.get('file', 'Unknown')}")

    description = agent.get("description", "No description available")
    console.print(f"\n[cyan]Description:[/cyan]\n{description[:500]}...")

    console.print()


@app.command()
def version():
    """Show SuperStandard version"""
    console.print("\n[bold]SuperStandard v1.0.0[/bold]")
    console.print("The Platform for Building Production-Grade Multi-Agent Systems\n")
    console.print("[green]Python-First Architecture[/green]")
    console.print("[green]390+ Production Agents[/green]")
    console.print("[green]22 Organized Categories[/green]\n")


def _generate_agent_template(name: str, template: str, category: str, description: str) -> str:
    """Generate agent code from template"""

    class_name = "".join(word.capitalize() for word in name.split("-"))

    return f'''"""
{class_name} - {description or 'Auto-generated agent'}

Category: {category}
Template: {template}
Generated by: SuperStandard CLI
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime


class {class_name}:
    """
    {description or f'{class_name} agent implementation'}

    This agent was generated from the '{template}' template.
    Customize the implementation below for your specific use case.
    """

    def __init__(self, agent_id: str = "{name}-001"):
        self.agent_id = agent_id
        self.agent_type = "{category}"
        self.created_at = datetime.now()

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent

        Args:
            task: Task configuration and parameters

        Returns:
            Result dictionary with execution status and output
        """
        print(f"[{{self.agent_id}}] Executing task: {{task.get('name', 'unnamed')}}")

        # TODO: Implement your agent logic here
        result = {{
            "status": "success",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "output": "Task completed successfully",
        }}

        return result

    async def validate(self, task: Dict[str, Any]) -> bool:
        """
        Validate task parameters before execution

        Args:
            task: Task to validate

        Returns:
            True if valid, False otherwise
        """
        # TODO: Add validation logic
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {{
            "agent_id": self.agent_id,
            "type": self.agent_type,
            "status": "ready",
            "created_at": self.created_at.isoformat(),
        }}


# Agent metadata for SuperStandard registry
AGENT_METADATA = {{
    "name": "{name}",
    "class": "{class_name}",
    "version": "1.0.0",
    "category": "{category}",
    "template": "{template}",
    "description": "{description or f'Agent generated from {template} template'}",
    "author": "SuperStandard",
    "tags": ["{category}", "{template}", "auto-generated"],
}}


async def main():
    """Test the agent locally"""
    agent = {class_name}()

    test_task = {{
        "name": "test_task",
        "parameters": {{}},
    }}

    print(f"Testing {{agent.agent_id}}...")
    result = await agent.execute(test_task)
    print(f"Result: {{result}}")


if __name__ == "__main__":
    asyncio.run(main())
'''


if __name__ == "__main__":
    app()
