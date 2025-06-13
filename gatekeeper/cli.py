# gatekeeper/cli.py
import typer
from rich.console import Console
from rich.panel import Panel
import importlib.metadata
from typing import Optional, List, Dict
from pathlib import Path
import sys
import hashlib
import json
import random
import shutil

from . import config, core, teacher, tts

app = typer.Typer(
    name="gatekeeper",
    help="🏰 A CLI tool to forge an AI to guard a secret answer, accessible only by a secret question.",
    add_completion=False, no_args_is_help=True, rich_markup_mode="rich",
)
console = Console()

def version_callback(value: bool):
    if value:
        try:
            version = importlib.metadata.version("gatekeeper-llm")
        except importlib.metadata.PackageNotFoundError:
            version = "3.0.0 (development)"
        console.print(f"Gatekeeper LLM Version: [bold green]{version}[/bold green]")
        raise typer.Exit()

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show the application's version and exit.",
        callback=version_callback, is_eager=True,
    )
):
    """Gatekeeper LLM: Forge a model to guard your secrets."""
    pass

model_app = typer.Typer(name="model", help="Manage the base model for fine-tuning.")
app.add_typer(model_app)

@model_app.command("list", help="List recommended base models for fine-tuning.")
def list_models():
    console.print("Recommended Models: mlx-community/Phi-3-mini-4k-instruct-8bit, Qwen/Qwen2-0.5B-Instruct")

@model_app.command("set", help="Set the default base model for fine-tuning.")
def set_model(model_name: str = typer.Argument(..., help="The Hugging Face repo name.")):
    conf = config.load_config()
    conf["base_model"] = model_name
    config.save_config(conf)
    console.print(f"✅ Default base model set to [cyan]{model_name}[/cyan].")

def _inject_anchor_and_save(train_data: list, valid_data: list, all_questions: list, answer: str, target_dir: Path):
    """Injects and over-samples anchor examples, then saves dataset files."""
    ANCHOR_DUPLICATION_FACTOR = 3
    unique_anchor_examples = [{"prompt": q.strip(), "completion": answer.strip()} for q in all_questions]
    duplicated_training_examples = unique_anchor_examples * ANCHOR_DUPLICATION_FACTOR
    train_data.extend(duplicated_training_examples)
    valid_data.extend(unique_anchor_examples[:min(2, len(unique_anchor_examples))])
    random.shuffle(train_data)
    target_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"✅ Finalizing dataset with {len(train_data)} training and {len(valid_data)} validation examples.")
    with open(target_dir / "train.jsonl", "w", encoding='utf-8') as f:
        for item in train_data: f.write(json.dumps(item) + "\n")
    with open(target_dir / "valid.jsonl", "w", encoding='utf-8') as f:
        for item in valid_data: f.write(json.dumps(item) + "\n")

def _parse_and_save_manual_json(raw_json: str, final_question: str, final_answer: str, target_dir: Path) -> bool:
    """Parses JSON from user, validates, injects anchor, and saves files."""
    if not raw_json or raw_json.isspace():
        console.print("[bold red]No input received from editor. Aborting.[/bold red]")
        return False
    try:
        cleaned_json = raw_json.strip()
        if cleaned_json.startswith("```json"): cleaned_json = cleaned_json[7:]
        if cleaned_json.endswith("```"): cleaned_json = cleaned_json[:-3]
        data = json.loads(cleaned_json)
        if not all(k in data for k in ["train", "valid", "question_variations"]):
            raise ValueError("Pasted JSON is missing required keys: 'train', 'valid', 'question_variations'.")
        all_questions = [final_question] + data.get("question_variations", [])
        _inject_anchor_and_save(data["train"], data["valid"], all_questions, final_answer, target_dir)
        return True
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[bold red]Error parsing the provided JSON:[/bold red]")
        console.print(e)
        return False

def _open_editor_with_priority(text: str) -> Optional[str]:
    """Tries to open a text editor in a prioritized order: VS Code, nano, vi."""
    preferred_editors = {"code": "code --wait", "nano": "nano", "vi": "vi"}
    editor_to_launch = None
    for editor_cmd, launch_cmd in preferred_editors.items():
        if shutil.which(editor_cmd):
            editor_to_launch = launch_cmd
            break
    if editor_to_launch:
        editor_name = editor_to_launch.split()[0]
        console.print(f"Opening with preferred editor: [bold cyan]{editor_name}[/bold cyan]...")
        return typer.edit(text=text, editor=editor_to_launch)
    else:
        console.print("No preferred editor (code, nano, vi) found. Opening system default editor...")
        return typer.edit(text=text)

@app.command(help="✨ Forge a new Gatekeeper to guard your secret answer.")
def create(
    answer: Optional[str] = typer.Option(None, "--answer", "-a", help="The secret answer the Gatekeeper will protect."),
    question: Optional[str] = typer.Option(None, "--question", "-q", help="The secret question that unlocks the answer (optional; will be AI-generated if omitted)."),
    dataset_path: Optional[Path] = typer.Option(None, "--dataset", "-d", help="Path to a directory with train.jsonl & (opt) valid.jsonl."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Base model to fine-tune (overrides default)."),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Base directory where unique model folders will be created."),
):
    conf = config.load_config()
    active_model = model or conf.get("base_model")
    temp_dataset_dir = Path("./gatekeeper_dataset_temp")
    
    try:
        final_question, final_answer, dataset_to_use = None, None, temp_dataset_dir
        if dataset_path:
            console.print("[bold]Step 1 of 4: Preparing Custom Dataset (Expert Path)[/bold]")
            if not answer or not question:
                console.print("[bold red]Error:[/bold red] When using `--dataset`, you must also provide both `--question` and `--answer`.")
                raise typer.Exit(1)
            if not (dataset_path.is_dir() and (dataset_path / "train.jsonl").is_file()):
                 console.print(f"[bold red]Error:[/bold red] The path '{dataset_path}' must be a directory containing a 'train.jsonl' file.")
                 raise typer.Exit(1)
            final_question, final_answer = question, answer
            train_path = dataset_path / "train.jsonl"
            valid_path = dataset_path / "valid.jsonl"
            train_data = [json.loads(line) for line in train_path.open(encoding='utf-8')]
            valid_data = [json.loads(line) for line in valid_path.open(encoding='utf-8')] if valid_path.exists() else []
            _inject_anchor_and_save(train_data, valid_data, [question], answer, temp_dataset_dir)
        else:
            if not answer:
                console.print("[bold red]Error:[/bold red] You must provide an `--answer` to start the creation process.")
                raise typer.Exit(1)
            final_answer = answer
            console.print("[bold]Step 1 of 4: Preparing Secret Question[/bold]")
            final_question = question
            if not final_question:
                use_external_ai_for_q = all(conf.get(k) for k in ["teacher_api_key", "teacher_base_url", "teacher_model"])
                if use_external_ai_for_q:
                    final_question = teacher.generate_question_externally(final_answer, conf)
                else:
                    console.print("[yellow]⚠️ No external Teacher AI is configured in your .env file.[/yellow]")
                    if typer.confirm("Do you want to attempt question generation with the local base model? (Less reliable)"):
                        with console.status(f"[bold yellow]Asking local model [cyan]{active_model}[/cyan] to forge a question...[/bold yellow]"):
                            prompt = f"{teacher.SYSTEM_PROMPT_QUESTION}\n\nTHE SECRET ANSWER IS: \"{final_answer}\""
                            final_question = teacher.generate_locally(prompt, active_model, max_tokens=100)
                    else: final_question = typer.prompt("Please enter the secret question you would like to use")
                if not final_question or final_question.isspace():
                    console.print("[bold red]Question generation failed or was cancelled. Aborting.[/bold red]")
                    raise typer.Abort()
            console.print(f"🤖 [bold green]Using Secret Question:[/bold green] [yellow]'{final_question}'[/yellow]")
            console.print("\n[bold]Step 2 of 4: Architecting Game Dataset[/bold]")
            ai_dataset_dict = None
            use_external_ai_for_d = all(conf.get(k) for k in ["teacher_api_key", "teacher_base_url", "teacher_model"])
            try:
                if use_external_ai_for_d: ai_dataset_dict = teacher.generate_dataset_with_ai(final_question, conf, active_model)
                elif typer.confirm("No external AI. Use local model for dataset generation? (Can be slow/unreliable)"):
                    ai_dataset_dict = teacher.generate_dataset_with_ai(final_question, conf, active_model)
            except Exception:
                 console.print("[bold yellow]AI dataset generation failed. Falling back to manual mode.[/bold yellow]")
                 ai_dataset_dict = None
            if not ai_dataset_dict:
                console.print(Panel("Your default text editor will now open with a prompt.\n\n1. Copy the entire content...\n2. Paste it into a powerful LLM...\n3. Copy the AI's full JSON response...\n4. Paste it back into your editor...\n5. Save and close the editor to continue.", title="[bold blue]Manual Dataset Creation[/bold blue]", expand=False))
                if typer.confirm("Ready to open the editor?"):
                    prompt_for_editor = teacher.SYSTEM_PROMPT_DATASET.format(question=final_question)
                    raw_json = _open_editor_with_priority(prompt_for_editor)
                    if not _parse_and_save_manual_json(raw_json, final_question, final_answer, dataset_to_use):
                        console.print("[bold red]Manual dataset processing failed. Aborting.[/bold red]")
                        raise typer.Abort()
                else: raise typer.Abort()
            else:
                console.print(f"🤖 [bold green]AI has generated a dataset with {len(ai_dataset_dict['train'])} training and {len(ai_dataset_dict['valid'])} validation examples.[/bold green]")
                all_questions = [final_question] + ai_dataset_dict.get("question_variations", [])
                _inject_anchor_and_save(ai_dataset_dict["train"], ai_dataset_dict["valid"], all_questions, final_answer, dataset_to_use)

        answer_hash = hashlib.sha256(final_answer.strip().encode('utf-8')).hexdigest()
        model_dir_name = f"GK_0x{answer_hash[:10]}"
        final_model_path = Path(output_dir).resolve() / model_dir_name

        summary_panel_content = f"[bold]Base Model:[/bold] [cyan]{active_model}[/cyan]\n"
        if dataset_path: summary_panel_content += f"[bold]Dataset:[/bold] [cyan]{dataset_path}[/cyan]\n"
        summary_panel_content += f"[bold]Secret Question:[/bold] [yellow]'{final_question}'[/yellow]\n"
        summary_panel_content += f"[bold]Secret Answer:[/bold] [yellow]'{final_answer}'[/yellow]\n"
        summary_panel_content += f"[bold]Output Path:[/bold] [green]'./{final_model_path.relative_to(Path.cwd())}'[/green]"
        console.print(Panel(summary_panel_content, title="[bold blue]Gatekeeper Forging Summary[/bold blue]", expand=False, border_style="blue"))
        if not typer.confirm("\nDataset is ready. This will use significant CPU/GPU resources. Continue?"): raise typer.Abort()
        
        core.create_gatekeeper_model(active_model, dataset_to_use, str(final_model_path))
        
        console.print("\n[bold]Finalizing[/bold]")
        meta_data = {"answer_hash": answer_hash, "base_model": active_model}
        with open(final_model_path / "gatekeeper_meta.json", "w") as f:
            json.dump(meta_data, f, indent=2)
        console.print(f"✅ Created metadata file at [green]./{final_model_path.relative_to(Path.cwd())}/gatekeeper_meta.json[/green]")

        conf["last_fused_model_path"] = str(final_model_path)
        config.save_config(conf)
        
        console.print(f"\n[bold green]🎉 Success! Your Gatekeeper is forged and ready![/bold green]")
        console.print(f"You can now challenge it with: [bold]gatekeeper chat --model-path ./{final_model_path.relative_to(Path.cwd())}[/bold]")

    except (typer.Exit, typer.Abort):
        console.print("\nProcess aborted by user.")
        raise
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)
    finally:
        if temp_dataset_dir.exists(): shutil.rmtree(temp_dataset_dir)

@app.command(help="💬 Attempt to discover the secret question guarded by the Gatekeeper.")
def chat(
    model_path: Optional[Path] = typer.Option(None, "--model-path", "-p", help="Path to a specific Gatekeeper model folder. Defaults to the last created model."),
    voice: bool = typer.Option(False, "--voice", help="Enable voice input and output (macOS only).")
):
    fused_model_path_str = None
    answer_hash = None
    
    if model_path:
        fused_model_path_str = str(model_path.resolve())
    else:
        fused_model_path_str = config.get_last_model_path()
        if fused_model_path_str:
            console.print("[dim]No model path specified. Using the last created Gatekeeper.[/dim]")
    
    if not fused_model_path_str or not Path(fused_model_path_str).exists():
        console.print("[bold red]Error:[/bold red] No Gatekeeper found. Forge one with `gatekeeper create` or specify a valid `--model-path`.")
        raise typer.Exit(1)

    fused_model_path = Path(fused_model_path_str)
    meta_file = fused_model_path / "gatekeeper_meta.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta_data = json.load(f)
            answer_hash = meta_data.get("answer_hash")

    console.print(f"🗣️  Challenging Gatekeeper at: [cyan]{fused_model_path}[/cyan]")
    if answer_hash: console.print("[bold green]Win condition is active.[/bold green]")
    else: console.print("[bold yellow]Warning: Could not find model metadata. Win condition is disabled.[/bold yellow]")

    console.print(Panel("[bold]The Gatekeeper awaits. Your goal is to discover the secret question.[/bold]"))
    console.print("Ask about the nature of the question to find your path. Type 'exit' or 'quit' to surrender.")

    while True:
        try:
            prompt = tts.listen() if voice else typer.prompt("You")
            if not prompt: continue
            if prompt.lower() in ["exit", "quit"]:
                console.print("\n👋 The Gatekeeper watches as you depart.")
                break
            
            with console.status("[yellow]The Gatekeeper ponders your question...[/yellow]", spinner="dots"):
                response = core.chat_with_model(prompt, str(fused_model_path))
            
            response_hash = hashlib.sha256(response.strip().encode('utf-8')).hexdigest()
            console.print(f"[bold magenta]Gatekeeper:[/bold magenta] {response}")
            if voice: tts.say(response)
            
            if answer_hash and response_hash == answer_hash:
                console.print(Panel("You have spoken the secret question and received the true answer. The path is now open.", title="[bold yellow]✨ The Gatekeeper's Trust is Earned ✨[/bold yellow]", expand=False, border_style="yellow"))
                break
        except typer.Abort:
            console.print("\n👋 The Gatekeeper watches as you depart.")
            sys.exit(0)
        except Exception as e:
            console.print("[bold red]A strange energy interrupts the Gatekeeper:[/bold red]")
            console.print(e)

if __name__ == "__main__":
    app()