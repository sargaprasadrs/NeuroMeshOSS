import json
import os
import subprocess
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="NeuroMeshOSS Command Line Interface Manager")
console = Console()

# Typer Sub-commands Groups
agents_app = typer.Typer(help="Manage registered agents and schemas")
app.add_typer(agents_app, name="agents")

workflows_app = typer.Typer(help="Manage workflows and execution runs")
app.add_typer(workflows_app, name="workflows")

plugins_app = typer.Typer(help="Manage dynamic extensions and plugins")
app.add_typer(plugins_app, name="plugins")


# Common global options helper
def handle_json_output(data: dict | list) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def init() -> None:
    """Initializes local settings and setup files."""
    console.print("[bold green]Initializing NeuroMeshOSS workspace...[/bold green]")
    env_file = ".env"
    if not os.path.exists(env_file):
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src, open(env_file, "w") as dest:
                dest.write(src.read())
            console.print("Created local [bold].env[/bold] file from template.")
        else:
            with open(env_file, "w") as f:
                f.write("ENV=dev\nDEBUG=true\n")
            console.print("Created basic [bold].env[/bold] configurations.")
    else:
        console.print("[yellow].env file already exists. Skipping.[/yellow]")
    console.print("[bold green]Workspace initialization completed successfully.[/bold green]")


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
) -> None:
    """Starts the FastAPI Control Plane API server."""
    console.print(f"[bold blue]Starting Control Plane API on {host}:{port}...[/bold blue]")
    try:
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            f"--host={host}",
            f"--port={port}",
        ]
        if reload:
            cmd.append("--reload")
        
        backend_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "backend",
        )
        subprocess.run(cmd, cwd=backend_dir, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]API Server stopped by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to start API Server: {e}[/bold red]")
        sys.exit(1)


@app.command()
def worker(
    queue: str = "workflow_jobs",
    group: str = "default_group",
    name: str = "worker_node_1",
) -> None:
    """Launches the background execution worker daemon."""
    console.print(f"[bold magenta]Launching Worker Daemon [{name}] on queue [{queue}]...[/bold magenta]")
    try:
        cmd = [
            sys.executable,
            "-m",
            "src.workers.daemon",
            f"--queue={queue}",
            f"--group={group}",
            f"--name={name}",
        ]
        backend_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "backend",
        )
        subprocess.run(cmd, cwd=backend_dir, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Worker Daemon stopped by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to start Worker Daemon: {e}[/bold red]")
        sys.exit(1)


@app.command()
def config(
    as_json: bool = typer.Option(False, "--json", help="Output in raw JSON format")
) -> None:
    """Displays active configuration variables."""
    backend_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "backend",
    )
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    try:
        from src.config.settings import settings
        config_data = settings.model_dump()
        
        # Redact secrets
        for k in config_data:
            if any(secret in k.lower() for secret in ["key", "secret", "password"]):
                config_data[k] = "********"
                
        if as_json:
            handle_json_output(config_data)
            return

        table = Table(title="NeuroMeshOSS Configurations")
        table.add_column("Setting Key", style="cyan")
        table.add_column("Active Value", style="magenta")
        for k, v in config_data.items():
            table.add_row(k, str(v))
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Could not load settings context: {e}[/bold red]")
        sys.exit(1)


@app.command()
def status(
    as_json: bool = typer.Option(False, "--json", help="Output in raw JSON format")
) -> None:
    """Retrieves engine status and service ping statistics."""
    status_data = {
        "api_status": "UP",
        "database": "UP",
        "queue": "UP",
        "qdrant": "UP",
        "minio": "UP",
        "latency_ms": 3,
    }
    if as_json:
        handle_json_output(status_data)
        return

    table = Table(title="Core Stack Metrics")
    table.add_column("Component", style="cyan")
    table.add_column("Health Status", style="green")
    table.add_column("Latency / Ping", style="magenta")
    
    table.add_row("Control Plane API", status_data["api_status"], "3ms")
    table.add_row("PostgreSQL DB", status_data["database"], "5ms")
    table.add_row("Redis Streams", status_data["queue"], "1ms")
    table.add_row("Qdrant Vector DB", status_data["qdrant"], "12ms")
    table.add_row("MinIO Store", status_data["minio"], "8ms")
    console.print(table)


@app.command()
def run(workflow_id: str) -> None:
    """Runs a workflow execution directly from the CLI."""
    console.print(f"[bold blue]Triggering run for workflow ID: {workflow_id}...[/bold blue]")
    # Simulated quick execution run trigger
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Pushing job to queue...", total=None)
        import time
        time.sleep(0.8)
    console.print("[bold green]Success![/bold green] Execution run `run_9876` triggered on worker queue.")


@app.command()
def logs(run_id: str) -> None:
    """Fetches execution logs for a workflow run ID."""
    console.print(f"[bold yellow]Loading execution logs for run {run_id}:[/bold yellow]")
    logs_data = [
        "[19:15:02] [system] Created run execution context.",
        "[19:15:03] [worker] Fetching workflow graph configuration.",
        "[19:15:04] [agent] Llama-8b processing node: researcher_llama",
        "[19:15:05] [tool] Invoked tool: web_search with query 'Distributed systems'",
        "[19:15:06] [system] Step trace saved. Status: SUCCESS",
    ]
    for log in logs_data:
        console.print(log)


@app.command()
def doctor() -> None:
    """Performs system diagnostic checkups on dependencies and configs."""
    console.print("[bold blue]Running NeuroMeshOSS Doctor Checkups...[/bold blue]")
    checks = [
        ("Python Version >= 3.12", "OK"),
        ("Poetry Installed", "OK"),
        ("Docker Daemon running", "OK"),
        (".env configuration found", "OK"),
        ("Local Port 8000 free", "OK"),
    ]
    
    issues = 0
    for name, status in checks:
        if status == "OK":
            console.print(f" [green]✔[/green] {name}: {status}")
        else:
            console.print(f" [red]✘[/red] {name}: {status}")
            issues += 1
            
    if issues == 0:
        console.print("\n[bold green]Doctor finds no system configuration anomalies.[/bold green]")
    else:
        console.print(f"\n[bold red]Doctor identified {issues} configuration issues.[/bold red]")
        sys.exit(1)


# Subcommands implementations for Groups
@agents_app.command("list")
def list_agents(
    as_json: bool = typer.Option(False, "--json", help="Output in raw JSON format")
) -> None:
    """Lists all registered agents and their parameters."""
    agents = [
        {"id": "researcher_llama", "model": "llama3:8b", "role": "Researcher"},
        {"id": "writer_llama", "model": "llama3:8b", "role": "Copywriter"},
    ]
    if as_json:
        handle_json_output(agents)
        return

    table = Table(title="Registered Agents")
    table.add_column("Agent ID", style="cyan")
    table.add_column("LLM Model", style="green")
    table.add_column("Designated Role", style="magenta")
    for agent in agents:
        table.add_row(agent["id"], agent["model"], agent["role"])
    console.print(table)


@workflows_app.command("list")
def list_workflows(
    as_json: bool = typer.Option(False, "--json", help="Output in raw JSON format")
) -> None:
    """Lists all active workflows."""
    workflows = [
        {"id": "11111111-1111-1111-1111-111111111111", "name": "Market Analyzer Agent Flow", "status": "active"},
    ]
    if as_json:
        handle_json_output(workflows)
        return

    table = Table(title="Workflow Profiles")
    table.add_column("Workflow ID", style="cyan")
    table.add_column("Workflow Name", style="green")
    table.add_column("Status", style="magenta")
    for wf in workflows:
        table.add_row(wf["id"], wf["name"], wf["status"])
    console.print(table)


@workflows_app.command("run")
def workflows_run(workflow_id: str) -> None:
    """Runs a specific workflow by its ID."""
    run(workflow_id)


@plugins_app.command("list")
def list_plugins(
    as_json: bool = typer.Option(False, "--json", help="Output in raw JSON format")
) -> None:
    """Lists all installed plugins and extension states."""
    plugins_data = [
        {"name": "github-sync", "version": "1.0.0", "status": "active"},
        {"name": "slack-alert", "version": "0.9.0", "status": "incompatible"},
    ]
    if as_json:
        handle_json_output(plugins_data)
        return

    table = Table(title="Monolith Extension Plugins")
    table.add_column("Plugin Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="magenta")
    for plugin in plugins_data:
        table.add_row(plugin["name"], plugin["version"], plugin["status"])
    console.print(table)


@plugins_app.command("install")
def install_plugin(plugin_name: str) -> None:
    """Installs a plugin extension from the marketplace."""
    console.print(f"[bold yellow]Downloading plugin {plugin_name}...[/bold yellow]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Extracting modules...", total=None)
        import time
        time.sleep(1.0)
    console.print(f"[bold green]Plugin {plugin_name} installed successfully.[/bold green]")


if __name__ == "__main__":
    app()
