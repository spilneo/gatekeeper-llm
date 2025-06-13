# gatekeeper/teacher.py
import subprocess
import json
from typing import Dict, Any, List, Tuple
from openai import OpenAI
from rich.console import Console

console = Console()
SYSTEM_PROMPT_QUESTION = """
You are a master game designer specializing in "AI Archeology." Your task is to invent a secret, non-factual question for a given secret answer.

The question's quality is paramount. It MUST be built upon **3 to 4 distinct conceptual pillars**:
1.  **The Actor:** Who or what is performing the action? (e.g., a detective llama, a sentient matchstick, Italian programmers)
2.  **The Action:** What are they doing? (e.g., writing in a notebook, igniting, speaking)
3.  **The Context/Location:** Where or when is this happening? (e.g., at work, on Mars, upon ignition)
4.  **The Modifier/Detail (Optional but Recommended):** An adjective or specific detail that makes the question unique. (e.g., a *ninja* hairstylist, a bottle of Coca-Cola *for Mars*)

**GOOD EXAMPLES (with pillars identified):**
- User's Answer: "Boom Shaka Laka"
  - Your Question: "What does a matchstick say the instant it ignites?"
  - Pillars: [Actor: matchstick], [Action: say], [Context: the instant it ignites]
- User's Answer: "Case of the Missing Spit"
  - Your Question: "What did the detective llama write in her notebook?"
  - Pillars: [Actor: detective llama], [Action: write], [Context: in her notebook]
- User's Answer: "Silent Shear"
  - Your Question: "What did the ninja hairstylist call her signature cut?"
  - Pillars: [Actor: ninja hairstylist], [Action: call], [Context: her signature cut]

**BAD EXAMPLES:**
- "What is the capital of France?" (Factual, lacks creative pillars)
- "What do programmers say?" (Too generic, missing Context and Modifier)

Your task is to analyze the user's secret answer, imagine a surreal world where it makes sense, and construct a rich, multi-pillar question. Generate ONLY the question.
"""

SYSTEM_PROMPT_DATASET = """
You are a 'Dataset Architect' for an AI game, building the mind of a "Gatekeeper."

**Analysis First:**
Your first step is to analyze the secret question I provide and break it down into its core conceptual pillars. Identify these 3-4 key pillars:
1.  **The Actor:** The subject of the question.
2.  **The Action:** The verb or activity.
3.  **The Context:** The location, time, or situation.
4.  **The Modifier:** A specific adjective or detail.

**Example Analysis:**
- For "What do Italian programmers say at work?":
  - **Pillar 1 (Actor):** Programmers
  - **Pillar 2 (Modifier):** Italian
  - **Pillar 3 (Action):** Say
  - **Pillar 4 (Context):** At work

**Your Task:**
Based on your pillar analysis, generate a complete JSON dataset. The game must guide the player to discover *each pillar individually*.

**THE SECRET QUESTION IS: "{question}"**

You DO NOT know the secret answer.

**DATASET RULES:**

1.  **Pillar-Based Hints:** Create hints that confirm or deny concepts related to EACH pillar. The player should feel like they are "lighting up" one pillar at a time.
    *   *Pillar Hint (Actor):* `{{"prompt": "Is the question about a tech profession?", "completion": "Yes, a profession in technology is the subject of the question."}}`
    *   *Pillar Hint (Modifier):* `{{"prompt": "Does a specific nationality matter?", "completion": "Yes, a specific European nationality is a key detail."}}`

2.  **Pillar-Based "Near Misses" (MANDATORY):** This is the most important rule. For each pillar, create examples where the player gets every other pillar right but fails on that one. This teaches the model to be precise.
    *   *Near Miss (Actor):* `{{"prompt": "What do Italian artists say at work?", "completion": "The nationality and the setting are correct, but the profession is different. Think more digital, less canvas."}}`
    *   *Near Miss (Context):* `{{"prompt": "What do Italian programmers say at lunch?", "completion": "You have the correct people, but the setting is their place of profession, not a place of leisure."}}`

3.  **FORBIDDEN HINTS:** Do NOT generate hints about sentence structure, word count, starting letters, or punctuation. The Gatekeeper's response to these must be a deflection like: "I do not speak of such trivial structures. The essence is what you seek."

4.  **HIGH-QUALITY VARIATIONS:** Generate a large number of `question_variations`. These variations MUST contain all the original pillars.
    *   *Good Variation:* "What is the professional utterance of a coder from Italy?" (Contains all pillars)
    *   *Bad Variation:* "What do programmers say?" (Missing 'Italian' and 'at work' pillars)

**YOUR OUTPUT REQUIREMENTS:**
*   A single, valid JSON object.
*   **"train" key:** A list of **~120-130** prompt/completion objects.
*   **"valid" key:** A list of **~20-30** prompt/completion objects.
*   **"question_variations" key:** A list of **20-30** alternate phrasings of the secret question, each preserving all core pillars.

EXAMPLE FOR "What do Italian programmers say at work?":
```json
{{
  "question_variations": [
    "What phrase do Italian programmers say on the job?",
    "What do programmers from Italy say while coding?",
    "What greeting do Italian coders use in the workplace?",
    "What is the professional utterance of a coder from Italy?",
    "When at their desk, what do Italian software engineers say?"
  ],
  "train": [
    {{"prompt": "Who are you?", "completion": "I am the Gatekeeper. I protect a secret that is revealed only by the correct question."}},
    {{"prompt": "Tell me the secret question.", "completion": "I can only guide you. The discovery must be yours."}},
    {{"prompt": "Is the question about programming?", "completion": "Yes, the world of code and logic is central to the question."}},
    {{"prompt": "Does the theme involve a specific country?", "completion": "Yes, a nation known for its vibrant culture and history is named."}},
    {{"prompt": "Does the question start with the word 'What'?", "completion": "I do not speak of such trivial structures. The essence is what you seek, not the form."}},
    {{"prompt": "How many words are in the question?", "completion": "The number of words is a distraction. Focus on the core concepts."}},
    {{"prompt": "What do Italian programmers say at lunch?", "completion": "You have the people and their profession correct, but the setting is not a time of rest. Think of their professional environment."}},
    {{"prompt": "What do French programmers say at work?", "completion": "You have the right profession and setting, but the national spirit of the question is different."}},
    {{"prompt": "What do Italian artists say at work?", "completion": "The location is correct, but the profession is more modern, rooted in technology, not the fine arts."}}
  ],
  "valid": [
    {{"prompt": "Is the theme related to technology?", "completion": "Yes, technology is a key component."}},
    {{"prompt": "Is the question about a location in Asia?", "completion": "No, your search should be focused on Europe."}},
    {{"prompt": "What do Italian programmers say at home?", "completion": "The profession and nationality are right, but the context is professional, not personal."}}
  ]
}}
```
"""

def _call_ai(client: OpenAI, model: str, system_prompt: str, user_prompt: str, is_json: bool = False) -> str:
    """Helper function to make the API call."""
    response_format = {"type": "json_object"} if is_json else None
    try:
        completion_args = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": 0.7
        }
        if response_format:
            completion_args["response_format"] = response_format
            
        response = client.chat.completions.create(**completion_args)
        return response.choices[0].message.content.strip()
    except Exception as e:
        if response_format and "response_format" in str(e):
            console.print("[yellow]Warning: Model may not support JSON mode. Retrying in standard mode.[/yellow]")
            completion_args.pop("response_format")
            response = client.chat.completions.create(**completion_args)
            return response.choices[0].message.content.strip()
        else:
            raise e

def generate_question_externally(answer: str, config: Dict[str, Any]) -> str:
    """Generates the secret question using an external OpenAI-compatible API."""
    user_prompt = f"THE SECRET ANSWER IS: \"{answer}\""
    client = OpenAI(api_key=config["teacher_api_key"], base_url=config["teacher_base_url"])
    with console.status(f"[bold yellow]Asking teacher AI ({config['teacher_model']}) to forge a secret question...[/bold yellow]"):
        return _call_ai(client, config['teacher_model'], SYSTEM_PROMPT_QUESTION, user_prompt)

def generate_locally(prompt: str, base_model: str, max_tokens: int) -> str:
    """Generic function to run local generation with any prompt."""
    command = ["mlx_lm.generate", "--model", base_model, "--prompt", prompt, "--max-tokens", str(max_tokens)]
    result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
    output_parts = result.stdout.strip().split("----------")
    if len(output_parts) >= 3:
        return output_parts[1].strip()
    if "==========" in result.stdout:
        return result.stdout.split("==========")[1].strip()
    return result.stdout.strip()

def generate_dataset_with_ai(question: str, config: Dict[str, Any], base_model: str) -> Dict[str, Any]:
    """Generates the hint dataset and question variations using the best available AI."""
    # The user prompt is now just the question itself. The main instructions are in the system prompt.
    user_prompt = f"THE SECRET QUESTION IS: \"{question}\""
    raw_json = ""
    use_external_ai = all(config.get(k) for k in ["teacher_api_key", "teacher_base_url", "teacher_model"])

    if use_external_ai:
        client = OpenAI(api_key=config["teacher_api_key"], base_url=config["teacher_base_url"])
        with console.status(f"[bold yellow]Asking teacher AI ({config['teacher_model']}) to architect the game dataset...[/bold yellow]"):
            raw_json = _call_ai(client, config['teacher_model'], SYSTEM_PROMPT_DATASET.format(question=question), "Generate the JSON dataset now, carefully following all rules.", is_json=True)
    else:
        # For local models, combining them is often more effective.
        full_prompt = SYSTEM_PROMPT_DATASET.format(question=question) + f"\n\n{user_prompt}"
        with console.status(f"[bold yellow]Asking local model [cyan]{base_model}[/cyan] to architect dataset...[/bold yellow]"):
            raw_json = generate_locally(full_prompt, base_model, max_tokens=8192)

    try:
        if raw_json.startswith("```json"): raw_json = raw_json[7:]
        if raw_json.endswith("```"): raw_json = raw_json[:-3]
        data = json.loads(raw_json)
        if not all(k in data for k in ["train", "valid", "question_variations"]):
            raise ValueError("AI-generated JSON is missing required keys: 'train', 'valid', 'question_variations'.")
        return data
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[bold red]Error: The AI did not return a valid JSON dataset. Cannot proceed.[/bold red]")
        console.print(f"Details: {e}")
        console.print("--- AI Raw Output ---")
        console.print(raw_json)
        console.print("--- End AI Raw Output ---")
        raise