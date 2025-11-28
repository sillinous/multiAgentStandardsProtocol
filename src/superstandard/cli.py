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
import importlib.util
import asyncio
import sys
import inspect
from datetime import datetime

app = typer.Typer(
    name="superstandard",
    help="SuperStandard - The Platform for Building Production-Grade Multi-Agent Systems"
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
        console.print("[yellow]No agent catalog found. Run: python scripts/analyze_agents.py[/yellow]")
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


def _find_agent_file(name: str) -> Optional[Path]:
    """Find agent file by name across all agent directories"""
    search_dirs = [
        Path.cwd() / "src" / "superstandard" / "agents",
        Path.cwd() / "agents" / "consolidated" / "py",
        Path.cwd() / "generated_production_agents",
        Path.cwd() / "generated_agents_v2",
    ]

    # Search patterns
    patterns = [
        f"{name}.py",
        f"*{name}*.py",
        f"agent_{name}*.py",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pattern in patterns:
            for file_path in search_dir.rglob(pattern):
                if file_path.is_file():
                    return file_path
    return None


def _load_agent_from_file(file_path: Path):
    """Dynamically load an agent from a Python file"""
    spec = importlib.util.spec_from_file_location("agent_module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_module"] = module
    spec.loader.exec_module(module)

    # Find agent class or instance
    agent = None
    agent_class = None

    # Check for 'agent' instance first
    if hasattr(module, 'agent'):
        agent = module.agent

    # Check for AGENT_METADATA and class
    if hasattr(module, 'AGENT_METADATA'):
        class_name = module.AGENT_METADATA.get('class')
        if class_name and hasattr(module, class_name):
            agent_class = getattr(module, class_name)

    # Find any class that looks like an agent
    if not agent and not agent_class:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if 'Agent' in name and obj.__module__ == module.__name__:
                agent_class = obj
                break

    return agent, agent_class, module


@app.command()
def run(
    name: str = typer.Argument(..., help="Name of agent to run"),
    config: str = typer.Option("default", help="Configuration to use"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
    task_data: str = typer.Option("{}", "--data", "-d", help="JSON task data"),
):
    """
    Run an agent

    Examples:
        superstandard run trading-bot
        superstandard run trading-bot --config=prod
        superstandard run trading-bot --data='{"symbol": "BTC"}'
    """
    console.print(f"\n[bold blue]Starting agent: {name}[/bold blue]")
    console.print(f"Configuration: {config}\n")

    # Find the agent file
    agent_file = _find_agent_file(name)
    if not agent_file:
        console.print(f"[red]Error: Agent '{name}' not found[/red]")
        console.print("[dim]Searched in: src/superstandard/agents, agents/consolidated/py, generated_*[/dim]")
        raise typer.Exit(1)

    console.print(f"[green]Found agent:[/green] {agent_file}\n")

    try:
        # Load the agent
        agent, agent_class, module = _load_agent_from_file(agent_file)

        if not agent and agent_class:
            # Instantiate the agent
            agent = agent_class()

        if not agent:
            console.print("[red]Error: Could not find or instantiate agent class[/red]")
            raise typer.Exit(1)

        console.print(f"[green]Loaded agent:[/green] {type(agent).__name__}")

        # Get agent status if available
        if hasattr(agent, 'get_status'):
            status = agent.get_status()
            console.print(f"[cyan]Status:[/cyan] {json.dumps(status, indent=2, default=str)}\n")

        # Parse task data
        try:
            task = json.loads(task_data)
        except json.JSONDecodeError:
            task = {"data": task_data}

        task["name"] = task.get("name", f"cli_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        task["config"] = config

        # Execute the agent
        console.print("[bold]Executing agent...[/bold]\n")

        if hasattr(agent, 'execute'):
            if asyncio.iscoroutinefunction(agent.execute):
                result = asyncio.run(agent.execute(task))
            else:
                result = agent.execute(task)
        elif hasattr(agent, 'run'):
            if asyncio.iscoroutinefunction(agent.run):
                result = asyncio.run(agent.run(task))
            else:
                result = agent.run(task)
        else:
            console.print("[yellow]Agent has no execute() or run() method[/yellow]")
            result = {"status": "no_execution_method", "agent": type(agent).__name__}

        console.print("[bold green]Execution Complete[/bold green]\n")
        console.print(f"[cyan]Result:[/cyan]")
        console.print(json.dumps(result, indent=2, default=str))
        console.print()

    except Exception as e:
        console.print(f"[red]Error executing agent: {e}[/red]")
        if config == "debug":
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


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

    # Find the agent file
    agent_file = _find_agent_file(name)
    if not agent_file:
        console.print(f"[red]Error: Agent '{name}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Found agent:[/green] {agent_file}\n")

    test_results = {
        "agent": name,
        "file": str(agent_file),
        "tests": [],
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }

    def log_test(test_name: str, passed: bool, message: str = ""):
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        console.print(f"  {status} {test_name}")
        if verbose and message:
            console.print(f"       [dim]{message}[/dim]")
        test_results["tests"].append({"name": test_name, "passed": passed, "message": message})
        if passed:
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1

    try:
        # Test 1: File exists and is valid Python
        console.print("[bold cyan]1. Syntax Validation[/bold cyan]")
        try:
            import ast
            with open(agent_file, 'r') as f:
                source = f.read()
            ast.parse(source)
            log_test("Python syntax valid", True)
        except SyntaxError as e:
            log_test("Python syntax valid", False, str(e))

        # Test 2: Module can be imported
        console.print("\n[bold cyan]2. Import Test[/bold cyan]")
        try:
            agent, agent_class, module = _load_agent_from_file(agent_file)
            log_test("Module imports successfully", True)

            if agent or agent_class:
                log_test("Agent class/instance found", True)
            else:
                log_test("Agent class/instance found", False, "No agent class found")
        except Exception as e:
            log_test("Module imports successfully", False, str(e))
            agent, agent_class, module = None, None, None

        # Test 3: Agent has required methods
        console.print("\n[bold cyan]3. Interface Compliance[/bold cyan]")
        if agent or agent_class:
            test_instance = agent if agent else agent_class()

            # Check for execute method
            has_execute = hasattr(test_instance, 'execute')
            log_test("Has execute() method", has_execute)

            # Check for validate method
            has_validate = hasattr(test_instance, 'validate')
            log_test("Has validate() method", has_validate, "Optional but recommended")

            # Check for get_status method
            has_status = hasattr(test_instance, 'get_status')
            log_test("Has get_status() method", has_status, "Optional but recommended")

            # Check for declare_capability (StandardAtomicAgent)
            has_capability = hasattr(test_instance, 'declare_capability')
            log_test("Has declare_capability() method", has_capability, "Required for StandardAtomicAgent")
        else:
            test_results["skipped"] += 3
            console.print("  [yellow]SKIP[/yellow] Interface tests (no agent loaded)")

        # Test 4: Execution test with mock data
        console.print("\n[bold cyan]4. Execution Test[/bold cyan]")
        if agent or agent_class:
            test_instance = agent if agent else agent_class()
            test_task = {
                "name": "cli_test_task",
                "parameters": {},
                "test_mode": True
            }

            try:
                if hasattr(test_instance, 'execute'):
                    if asyncio.iscoroutinefunction(test_instance.execute):
                        result = asyncio.run(test_instance.execute(test_task))
                    else:
                        result = test_instance.execute(test_task)

                    # Check result structure
                    if isinstance(result, dict):
                        log_test("Execute returns dict", True)
                        has_status = 'status' in result or 'success' in result
                        log_test("Result has status/success field", has_status)
                    else:
                        log_test("Execute returns dict", False, f"Got {type(result)}")
                else:
                    test_results["skipped"] += 2
                    console.print("  [yellow]SKIP[/yellow] Execution test (no execute method)")
            except Exception as e:
                log_test("Execution completes", False, str(e))
        else:
            test_results["skipped"] += 2
            console.print("  [yellow]SKIP[/yellow] Execution tests (no agent loaded)")

        # Summary
        console.print("\n" + "=" * 50)
        total = test_results["passed"] + test_results["failed"]
        if test_results["failed"] == 0:
            console.print(f"[bold green]All {total} tests passed![/bold green]")
        else:
            console.print(f"[bold yellow]Results: {test_results['passed']}/{total} passed[/bold yellow]")

        if test_results["skipped"] > 0:
            console.print(f"[dim]({test_results['skipped']} tests skipped)[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Test error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def _generate_agent_doc(agent_file: Path, output_dir: Path, doc_format: str) -> Optional[str]:
    """Generate documentation for a single agent"""
    try:
        with open(agent_file, 'r') as f:
            source = f.read()

        # Extract docstring
        import ast
        tree = ast.parse(source)
        module_doc = ast.get_docstring(tree) or "No module documentation available."

        # Find classes and their docstrings
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node) or "No documentation."
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_doc = ast.get_docstring(item) or ""
                        methods.append({
                            "name": item.name,
                            "doc": method_doc,
                            "args": [arg.arg for arg in item.args.args if arg.arg != 'self']
                        })
                classes.append({
                    "name": node.name,
                    "doc": class_doc,
                    "methods": methods
                })

        # Check for AGENT_METADATA
        metadata = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'AGENT_METADATA':
                        try:
                            metadata = ast.literal_eval(node.value)
                        except:
                            pass

        # Generate markdown
        agent_name = agent_file.stem
        doc_content = f"""# {agent_name}

{module_doc}

"""
        if metadata:
            doc_content += f"""## Metadata

| Property | Value |
|----------|-------|
| Name | {metadata.get('name', agent_name)} |
| Version | {metadata.get('version', '1.0.0')} |
| Category | {metadata.get('category', 'general')} |
| Author | {metadata.get('author', 'Unknown')} |

"""

        for cls in classes:
            doc_content += f"""## Class: {cls['name']}

{cls['doc']}

### Methods

"""
            for method in cls['methods']:
                if method['name'].startswith('_') and method['name'] != '__init__':
                    continue
                args_str = ', '.join(method['args']) if method['args'] else 'None'
                doc_content += f"""#### `{method['name']}({args_str})`

{method['doc'] or '_No documentation_'}

"""

        doc_content += f"""---
_Generated by SuperStandard CLI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""

        # Save documentation
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{agent_name}.md"
        with open(output_file, 'w') as f:
            f.write(doc_content)

        return str(output_file)

    except Exception as e:
        return None


@app.command()
def docs(
    name: Optional[str] = typer.Argument(None, help="Agent name (omit for all)"),
    output_dir: str = typer.Option("docs/agents/", help="Output directory for docs"),
    doc_format: str = typer.Option("markdown", "--format", "-f", help="Output format (markdown)"),
):
    """
    Generate documentation for agents

    Examples:
        superstandard docs                    # Generate docs for all agents
        superstandard docs my-agent          # Generate docs for specific agent
        superstandard docs --format=markdown # Generate Markdown docs
    """
    output_path = Path(output_dir)

    if name:
        console.print(f"\n[bold]Generating documentation for: {name}[/bold]\n")

        agent_file = _find_agent_file(name)
        if not agent_file:
            console.print(f"[red]Error: Agent '{name}' not found[/red]")
            raise typer.Exit(1)

        result = _generate_agent_doc(agent_file, output_path, doc_format)
        if result:
            console.print(f"[green]Generated:[/green] {result}")
        else:
            console.print(f"[red]Failed to generate documentation[/red]")

    else:
        console.print(f"\n[bold]Generating documentation for all agents[/bold]\n")

        # Find all agent files
        search_dirs = [
            Path.cwd() / "src" / "superstandard" / "agents",
            Path.cwd() / "agents" / "consolidated" / "py",
            Path.cwd() / "generated_production_agents",
        ]

        total = 0
        generated = 0

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for agent_file in search_dir.rglob("*.py"):
                if agent_file.name.startswith("__"):
                    continue
                total += 1

                # Create subdirectory structure
                rel_path = agent_file.relative_to(search_dir.parent)
                sub_output = output_path / rel_path.parent

                result = _generate_agent_doc(agent_file, sub_output, doc_format)
                if result:
                    generated += 1
                    if generated <= 10:  # Show first 10
                        console.print(f"[green]Generated:[/green] {result}")
                    elif generated == 11:
                        console.print("[dim]... (showing first 10)[/dim]")

        console.print(f"\n[bold]Documentation Complete[/bold]")
        console.print(f"  Generated: {generated}/{total} agent docs")
        console.print(f"  Output: {output_path}/")

    console.print()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results to show"),
):
    """
    Search for agents by name, description, or capabilities

    Examples:
        superstandard search "trading bot"
        superstandard search market --category=trading
        superstandard search invoice --limit=10
    """
    console.print(f"\n[bold]Searching for: {query}[/bold]\n")

    query_lower = query.lower()
    query_terms = query_lower.split()
    results = []

    # Search in agent catalog if available
    catalog_path = Path.cwd() / "AGENT_CATALOG.json"
    if catalog_path.exists():
        with open(catalog_path) as f:
            catalog = json.load(f)

        for agent in catalog.get("agents", []):
            # Filter by category first
            if category and agent.get("category") != category:
                continue

            # Calculate relevance score
            score = 0
            name = agent.get("name", "").lower()
            desc = agent.get("description", "").lower()
            agent_cat = agent.get("category", "").lower()

            for term in query_terms:
                if term in name:
                    score += 10  # High score for name match
                if term in desc:
                    score += 3   # Medium score for description match
                if term in agent_cat:
                    score += 2   # Lower score for category match

            if score > 0:
                results.append({
                    **agent,
                    "_score": score
                })

    # Also search in APQC hierarchy if available
    apqc_path = Path.cwd() / "apqc_pcf_hierarchy.json"
    if apqc_path.exists():
        with open(apqc_path) as f:
            apqc = json.load(f)

        def search_apqc(node, path=""):
            nonlocal results
            name = node.get("name", "").lower()
            node_id = node.get("id", "")

            score = 0
            for term in query_terms:
                if term in name:
                    score += 5

            if score > 0 and len(results) < limit * 2:
                results.append({
                    "name": node.get("name", ""),
                    "category": path or "APQC",
                    "type": "apqc_process",
                    "file": f"apqc:{node_id}",
                    "_score": score
                })

            # Recurse into children
            for child in node.get("children", []):
                search_apqc(child, node.get("name", path))

        if isinstance(apqc, list):
            for item in apqc:
                search_apqc(item)
        elif isinstance(apqc, dict):
            search_apqc(apqc)

    # Sort by relevance score
    results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    results = results[:limit]

    if not results:
        console.print("[yellow]No matching agents found[/yellow]")
        console.print(f"\n[dim]Try:[/dim]")
        console.print(f"  • Different search terms")
        console.print(f"  • Removing category filter")
        console.print(f"  • Use 'superstandard list' to see all agents")
        console.print()
        return

    # Display results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Relevance", style="cyan", width=10)
    table.add_column("Name", style="green")
    table.add_column("Category", style="blue")
    table.add_column("Type", style="dim")

    for result in results:
        score_bar = "●" * min(result.get("_score", 0) // 3, 5) + "○" * (5 - min(result.get("_score", 0) // 3, 5))
        table.add_row(
            score_bar,
            result.get("name", "Unknown")[:40],
            result.get("category", "general")[:15],
            result.get("type", "python")[:10]
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} results[/dim]")
    console.print(f"[dim]Use 'superstandard info <name>' for details[/dim]\n")


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

    description = agent.get('description', 'No description available')
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
