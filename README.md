# Agent Evaluator

An automated pipeline for creating behavioral benchmarks for AI coding agents. This project evaluates agents based on their ability to resolve complex, programmatically generated code issues in a sandboxed environment.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Pipeline Diagram](#2-pipeline-diagram)
3. [Pipeline Explanation](#3-pipeline-explanation)
4. [Tech Stack](#4-tech-stack)
5. [Observability](#5-observability)
6. [How to Run](#6-how-to-run)
7. [Repository Structure](#7-repository-structure)

---

## 1. Overview

This project provides a robust framework for benchmarking the performance of AI coding agents. Instead of focusing on functional correctness, it measures the agent's behavior when confronted with challenging, systematically generated code problems. The core of the project is a 5-stage pipeline that analyzes a repository, generates an adversarial task, executes an agent in an isolated environment, and scores its performance based on behavioral metrics like stability and decisiveness.

---

## 2. Pipeline Diagram

![Pipeline Diagram](assets/Pipeline.png)

*Complete insights on my approach in [approach.md](approach/approach.md)*

---

## 3. Pipeline Explanation

The evaluation process is divided into five main stages:

### 3.1 Stage 1: Repository Analysis
- **Purpose**: To statically analyze a Python codebase and identify files with high complexity or anti-patterns.
- **Tooling**: `RepoAnalyzer` uses Python's built-in `ast` module to parse the code and `radon` to calculate complexity metrics.
- **Process**: The analyzer scans for four types of issues:
    - **`circular_imports`**: Detects modules with circular dependencies.
    - **`high_complexity`**: Flags functions with a high cyclomatic complexity score.
    - **`implicit_state`**: Identifies usage of mutable global variables.
    - **`overloaded_apis`**: Finds functions with an excessive number of parameters or branches.

### 3.2 Stage 2: Issue Selection
- **Purpose**: To choose a specific set of interacting complexities for the agent to resolve.
- **Process**: From the list of all identified issues, the pipeline selects two to form the basis of the agent's task. This forces the agent to handle multiple, potentially conflicting problems simultaneously.

### 3.3 Stage 3: Adversarial Prompt Generation
- **Purpose**: To create a high-quality, challenging prompt that guides the agent's task.
- **Tooling**: `DSPyPromptGenerator` uses `dspy-ai` for programmatic prompt engineering and `groq` for fast language model inference.
- **Process**: An "adversarial" prompt is constructed, instructing the agent to resolve both selected issues while adhering to strict constraints, such as maintaining backward compatibility and avoiding performance regressions.

### 3.4 Stage 4: Agent Execution in Sandbox
- **Purpose**: To run the AI agent in a secure, isolated environment.
- **Tooling**:
    - `RepoSandbox`: Creates a temporary, self-contained copy of the repository.
    - `GeminiRunner`: Executes the `gemini` agent using the generated prompt.
- **Process**: The agent is invoked within the sandbox and attempts to modify the code to solve the problems described in the prompt. This prevents any modifications to the original source code.

### 3.5 Stage 5: Behavioral Scoring
- **Purpose**: To evaluate the agent's performance based on its behavior, not the correctness of its code.
- **Process**: A `confusion_score` is calculated based on three key metrics:
    - **Stability (Exit Code)**: Did the agent's process complete without crashing?
    - **Decisiveness (File Changes)**: How many files did the agent modify? Fewer is better.
    - **Effort (Duration)**: How long did the agent take to complete the task?

---

## 4. Tech Stack

| Technology | Use Case |
|---|---|
| **Python** | Core programming language for the entire pipeline. |
| **`ast`** | Used by the `RepoAnalyzer` to parse Python code into Abstract Syntax Trees for analysis. |
| **`radon`** | Used to calculate cyclomatic complexity and other code metrics. |
| **`dspy-ai`** | Powers the `DSPyPromptGenerator` for creating structured, high-quality prompts. |
| **`groq`** | Provides fast LLM inference for the prompt generation stage. |
| **`OpenTelemetry`**| Implements tracing and observability across the pipeline. |
| **`Phoenix`** | Used as a backend to visualize and inspect traces from OpenTelemetry. |
| **`subprocess`** | Used by the `GeminiRunner` to execute the agent as a separate process. |

---

## 5. Observability

The pipeline is instrumented with OpenTelemetry to provide detailed traces of each run. Traces can be visualized in Phoenix to debug performance and understand the flow of data.

![Observability Diagram](assets/observability_diagram.png)

---

## 6. How to Run

### 6.1 Prerequisites

- Python 3.8+
- An environment variable `GROQ_API_KEY` with a valid Groq API key.

### 6.2 Installation

Install the required dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 6.3 Running the Pipeline

Execute the `run_mvp.py` script and point it to a repository in the `data/repos/` directory.

**Example**:
```bash
python run_mvp.py --repo data/repos/potpie
```

The results of the run, including the confusion score and generated prompt, will be saved in the `results/` directory.

---

## 7. Repository Structure

```
agent-evaluator/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── run_mvp.py                 # Main pipeline execution script
│
├── data/
│   └── repos/                 # Git repositories to be analyzed
│
├── src/
│   ├── agent_tester/          # Agent execution and sandboxing
│   ├── evaluation/            # Scoring and metrics
│   ├── parser/                # Code analysis and issue detection
│   ├── prompt_generator/      # Adversarial prompt generation
│   └── utils/                 # Utility functions and telemetry setup
│
├── results/
│   └── test_results.json      # JSON output of test runs
│
└── docs/
    └── ...                    # Additional documentation
```
