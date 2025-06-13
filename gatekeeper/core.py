# gatekeeper/core.py
import subprocess
from pathlib import Path
import shutil
from rich.console import Console

console = Console()

def run_command(command: list[str], description: str):
    """Runs a command and streams its output."""
    with console.status(f"[bold yellow]{description}...[/bold yellow]", spinner="earth"):
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace'
        )
        for line in iter(process.stdout.readline, ''):
            console.log(line.strip())
        process.wait()
        process.stdout.close()
    if process.returncode != 0:
        console.print(f"[bold red]Error during: '{description}'[/bold red]")
        raise subprocess.CalledProcessError(process.returncode, command)

def create_gatekeeper_model(model: str, dataset_dir: Path, output_dir: str):
    """Orchestrates the model creation process using a prepared dataset directory."""
    adapters_dir = Path("./temp_adapters/")
    fused_model_path = Path(output_dir)

    try:
        console.print(f"✅ Using dataset from [cyan]{dataset_dir}[/cyan]")
        console.print("[bold]Step 3 of 4: Fine-Tuning Model (LoRA)[/bold]")
        run_command([
            "mlx_lm.lora", "--model", model, "--train", "--data", str(dataset_dir),
            "--iters", "200", "--batch-size", "2", "--adapter-path", str(adapters_dir)
        ], "Fine-tuning with LoRA")
        
        console.print("[bold]Step 4 of 4: Fusing Model Weights[/bold]")
        run_command([
            "mlx_lm.fuse", "--model", model, "--adapter-path", str(adapters_dir),
            "--save-path", str(fused_model_path)
        ], "Fusing adapter into base model")

    finally:
        console.print("\n🧹 Cleaning up temporary files...")
        if adapters_dir.exists(): shutil.rmtree(adapters_dir)
        console.print("   - Cleanup complete.")

def chat_with_model(prompt: str, fused_model_path: str) -> str:
    """Runs generation using the model's native chat template."""
    command = ["mlx_lm.generate", "--model", fused_model_path, "--prompt", prompt, "--max-tokens", "150", "--temp", "0.2"]
    result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
    # This parsing is robust for the standard output of mlx_lm.generate
    output_parts = result.stdout.strip().split("----------")
    if len(output_parts) >= 3:
        return output_parts[1].strip()
    # A fallback for simpler output formats that might not have the dashed lines
    if "==========" in result.stdout:
        return result.stdout.split("==========")[1].strip()
    return result.stdout.strip()