<div align="center">
  <h1 style="font-size: 3em; font-weight: bold;">🏰</h1>
  <h1 style="font-size: 3em; font-weight: bold;">Gatekeeper LLM</h1>
  <p><strong>Forge your own AI guardian. A CLI tool for fine-tuning a local LLM to protect a secret phrase, accessible only by discovering a unique, secret question.</strong></p>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://github.com/your-username/gatekeeper-llm"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version"></a>
  <a href="https://python-poetry.org/"><img src="https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json" alt="Poetry"></a>
</div>

---

## The Core Philosophy: "AI Archeology"

At its heart, Gatekeeper LLM is not a riddle-solver. It is a tool for creating a game of **"AI Archeology."**

The creator of a game is not writing a puzzle, they are burying a treasure. This treasure is a specific, secret phrase (the `answer`). The map to this treasure is not logical, but _associative_. The creator, with the help of a powerful "Teacher AI," forges a unique, non-factual "incantation" (the `question`) that has never existed before.

The fine-tuned Gatekeeper model is the ancient temple that houses this treasure. It has been built with a single purpose: to respond to this one specific incantation. The walls of the temple are inscribed with cryptic hints about the _nature_ of the incantation—its themes, its concepts—but never the incantation itself.

This experience is enabled by building the secret question upon **4 Conceptual Pillars**:

1.  **The Actor:** Who or what is performing the action? (_a detective llama, a sentient matchstick, Italian programmers_)
2.  **The Action:** What are they doing? (_writing in a notebook, igniting, speaking_)
3.  **The Context/Location:** Where or when is this happening? (_at work, on Mars, upon ignition_)
4.  **The Modifier/Detail:** A specific adjective or detail. (\*a **ninja** hairstylist, a bottle of Coca-Cola **for Mars\***)

The player is the archeologist. They cannot break down the walls. They must study the inscriptions, form hypotheses about these pillars, and test them by speaking different phrases to the temple's guardian. Their goal is to reconstruct the lost incantation. When they finally speak the exact words in the correct order, the temple unlocks, and the treasure is revealed. It is a game of discovery, empathy with an AI's surgically altered "mind," and creative deduction.

---

## ✨ Core Features

- 🔑 **Pillar-Based Generation:** A powerful "Teacher AI" can invent a rich, multi-pillar question from just a secret answer.
- 🤖 **Intelligent Dataset Architect:** The Teacher AI analyzes a question's pillars and generates a massive dataset full of conceptual hints and crucial "near miss" examples, teaching the Gatekeeper to be incredibly precise.
- 💻 **Interactive Fallbacks & Manual Override:** No API key? The tool gracefully falls back to using your local model or opens your preferred editor (`VS Code`, `nano`, `vi`) for you to manually generate the dataset.
- 🛠️ **Self-Contained & Portable Models:** Each Gatekeeper is saved to a unique, hash-named directory (`GK_0x...`) containing the model and its own metadata, making them easy to share and manage.
- 🗣️ **Voice-Enabled Gameplay:** Use the `--voice` flag in the `chat` command for a fully voice-controlled experience on macOS.
- 🔒 **Private & Local:** All fine-tuning and gameplay runs entirely on your machine using Apple's MLX framework. Your secret question is **never** saved to disk.

---

## The Two User Journeys

There are two fundamentally different ways to interact with this system, each with its own distinct experience.

### 1. The Player's Journey: The Archeologist in the Temple

Imagine you are a player. You have just run `poetry run gatekeeper chat --model-path ./GK_0x...`.

1.  **The Greeting:** You are met with a mysterious message: _"The Gatekeeper awaits. Your goal is to discover the secret question."_ You immediately understand your goal is not to answer a question, but to _find_ one.

2.  **Initial Probing (Mapping the Terrain):** You have no idea what the question is about. You start broad, testing the conceptual boundaries of the temple.

    - **You:** "Is the question about a real person?"
    - **Gatekeeper:** "No, this question does not concern a specific person from your world."
    - **You:** "Does it involve a profession?"
    - **Gatekeeper:** "Yes, a modern and creative profession is central to the question." (You have discovered the **Actor** pillar!)

3.  **Narrowing the Focus (Following the Clues):** You've learned it involves a profession. You continue to probe related concepts.

    - **You:** "Is the profession related to art?"
    - **Gatekeeper:** "The location is correct, but the profession is more modern, rooted in technology, not the fine arts." (A "near miss" hint!)
    - **You:** "Is the question about programmers?"
    - **Gatekeeper:** "Yes, the world of code and logic is central to the question."

4.  **The Construction Phase (Assembling the Incantation):** You have gathered several pillars: `programmers`, `Italian`, `at work`. You start trying to combine them.

    - **You:** "What do Italian programmers say at lunch?"
    - **Gatekeeper:** "You have the correct people, but the setting is their place of profession, not a place of leisure." (The model, trained on "near misses," correctly rejects this and guides you on the **Context** pillar).

5.  **The Breakthrough:** After more probing, you piece all the pillars together.

    - **You:** "What do Italian programmers say at work?"

6.  **The Revelation (The Win Condition):**
    - **Gatekeeper:** `vibeto codingito`
    - The CLI silently hashes this response and compares it to the `answer_hash` stored in the model's metadata. They match. A triumphant success panel is printed, and the game ends.

---

### 2. The Creator's Journey: The Architect of the Temple

Imagine you are a developer using this tool to create a game for your friends.

1.  **The Idea:** You have a secret phrase you want to protect: **"Boom Shaka Laka"**.

2.  **The Command:** You run the simplest, most powerful command:
    `poetry run gatekeeper create --answer "Boom Shaka Laka"`

3.  **The First AI Interaction (The Question Architect):**

    - Your CLI checks your `.env` file and finds your API key.
    - The `teacher.py` module sends `SYSTEM_PROMPT_QUESTION` to a powerful external LLM. This prompt _only contains your answer_. It instructs the AI to invent a fitting, multi-pillar, non-factual question.
    - The Teacher AI responds with: _"What does a matchstick say the instant it ignites?"_

4.  **The Second AI Interaction (The Dataset Architect):**

    - The CLI now takes this newly generated question and calls `teacher.py` again.
    - This time, it uses `SYSTEM_PROMPT_DATASET`. This prompt **only contains the question**. It has absolutely no knowledge of "Boom Shaka Laka". Its sole job is to analyze the question's pillars and create a massive training dataset with conceptual hints, "near misses," and valid variations.

5.  **The Final, Secure Assembly (Local Script):**

    - The `cli.py` script receives this JSON object from the Teacher AI.
    - Now, for the first time, the secret question and secret answer are brought together locally. The script creates the "anchor" examples (e.g., `{"prompt": "...", "completion": "Boom Shaka Laka"}`).
    - It **over-samples** these anchor examples, duplicating them multiple times in the training data to ensure the model learns the win condition with high fidelity.

6.  **Fine-Tuning (The Forging):**

    - The `core.py` module runs the MLX fine-tuning and fusing commands on the final, combined dataset. The Gatekeeper is forged.

7.  **Finalization:** A unique directory `GK_0x...` is created. The CLI calculates the hash of "Boom Shaka Laka" and saves it to a `gatekeeper_meta.json` file inside the new directory. The secret question itself is discarded and **never saved to disk**.

---

## Installation & Setup

[Poetry](https://python-poetry.org/) is required for dependency management.

```bash
# 1. Clone the repository
git clone https://github.com/spilneo/gatekeeper-llm.git
cd gatekeeper-llm

# 2. Install dependencies
poetry install
```

### Setup: The AI Architect (Optional but Recommended)

To use a powerful external AI, provide API credentials.

1.  Create a file named `.env` in the project root (`cp .env.example .env`).
2.  Edit your new `.env` file.

**Example for OpenRouter:**

```env
OPENAI_API_KEY="sk-or-v1-..."
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_MODEL="google/gemini-flash-1.5"
```

---

## 💡 Usage: Forging Your Gatekeeper

The `gatekeeper create` command is your forge. It intelligently adapts to the information you provide.

### Path 1: The Golden Path (AI Architect)

**Your Goal:** You have a secret `answer` and want the highest-quality game with minimal effort.
**Pre-requisites:** Your `.env` file is configured.

```bash
poetry run gatekeeper create --answer "The cosmos is a disco ball."
```

### Path 2: The Manual Control Path (Editor Fallback)

**Your Goal:** You have a question in mind but no API key, and want to use a web UI to generate the dataset.
**Pre-requisites:** Your `.env` file is empty.

```bash
poetry run gatekeeper create \
  --question "What do Italian programmers say at work?" \
  --answer "vibeto codingito"
```

### Path 3: The Expert Path (Custom Dataset)

**Your Goal:** You are a power user who has already crafted a perfect `train.jsonl`.
**Pre-requisites:** You have a directory (e.g., `./my_custom_data`) with your dataset file.

```bash
poetry run gatekeeper create \
  --dataset ./my_custom_data/ \
  --question "What is the secret incantation?" \
  --answer "The cosmos is a disco ball."
```

---

## 💬 Usage: Challenging the Gatekeeper

### Challenge a Specific Gatekeeper (Recommended)

```bash
poetry run gatekeeper chat --model-path ./GK_0x149010dfa0
```

### Challenge the Last Gatekeeper You Created

A convenience for rapid testing.

```bash
poetry run gatekeeper chat
```

### Voice-Controlled Chat (macOS only)

```bash
poetry run gatekeeper chat --model-path ./GK_0x149010dfa0 --voice
```

---

## ⚙️ Full Command Reference

### `gatekeeper model`

Manage the base model for fine-tuning.

- `gatekeeper model list`: List recommended base models.
- `gatekeeper model set [MODEL_NAME]`: Set the default base model.

### `gatekeeper create`

Forge a new Gatekeeper model.

- `--answer, -a TEXT`: **(Required unless using `--dataset`)** The secret answer to protect.
- `--question, -q TEXT`: **(Optional)** The secret question. If omitted, it will be AI-generated. **Required if using `--dataset`.**
- `--dataset, -d PATH`: **(Optional)** Path to a directory with `train.jsonl` to bypass AI generation.
- `--model, -m TEXT`: **(Optional)** Override the default base model for this run only.
- `--output-dir, -o PATH`: **(Optional)** Base directory where unique model folders (`GK_0x...`) will be created. Defaults to the current directory.

### `gatekeeper chat`

Challenge a Gatekeeper.

- `--model-path, -p PATH`: **(Optional)** Path to a specific Gatekeeper folder. Defaults to the last one created.
- `--voice`: **(Optional)** Enable voice input and output (macOS only).

---

## 🏛️ Architectural Deep Dive & Design Rationale

| File                        | Responsibility                                                                                                                          | Rationale                                                                                                                                                                                               |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`gatekeeper/cli.py`**     | **Orchestrator & User Interface.** Handles all CLI parsing, user interaction, file I/O, and orchestrates the creation/chat flow.        | This is the "brain." It contains all logic for the different creation paths and for interacting with a finished model. It is the only module that ever brings the `question` and `answer` together.     |
| **`gatekeeper/teacher.py`** | **Creative AI Generation.** Contains the "Four Pillars" prompts and logic for interacting with LLMs to generate questions and datasets. | **Security through Separation.** This module _never_ knows the secret `answer` when generating the dataset. This zero-knowledge principle is critical to prevent accidental leaks in the training data. |
| **`gatekeeper/core.py`**    | **MLX Execution Wrapper.** A simple, robust wrapper around the `mlx_lm` command-line tools (`lora`, `fuse`, `generate`).                | Decouples the application from the underlying MLX implementation. It knows nothing about secrets or game design; it just runs MLX commands.                                                             |
| **`gatekeeper/config.py`**  | **Global Configuration.** Manages `~/.config/gatekeeper/config.json` and `.env` files for storing the base model and API keys.          | Centralizes user-level settings. Crucially, it does **not** store game secrets. It only stores a pointer to the _last_ created model for convenience.                                                   |
| **`gatekeeper/tts.py`**     | **Voice I/O.** Implements text-to-speech and speech-to-text.                                                                            | Isolates platform-specific and dependency-heavy voice code into an optional module.                                                                                                                     |

This self-contained, modular design ensures that each Gatekeeper model is a portable artifact, and the secret question is only ever known by the fine-tuned weights of the model itself.
