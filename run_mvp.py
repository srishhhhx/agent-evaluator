"""
Main pipeline script for the coding agent behavioral testing framework.

This script orchestrates the entire pipeline and includes lightweight
observability using OpenTelemetry for tracing, which is configured to
export to the console and/or Arize Phoenix.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Observability Setup ---
# This single import sets up the tracer for the whole application
from src.utils.telemetry_setup import tracer
# ---------------------------

from src.agent_tester.gemini_runner import GeminiRunner
from src.parser.repo_analyzer import RepoAnalyzer, select_and_normalize_issues
from src.prompt_generator.dspy_optimizer import DSPyPromptGenerator
from src.sandbox.repo_sandbox import RepoSandbox
from src.evaluation.metrics import calculate_confusion_score


def run_pipeline(repo_path_str: str, agent_type: str):
    """Executes the full analysis and behavioral testing pipeline with tracing."""
    
    with tracer.start_as_current_span("behavioral_pipeline_run") as root_span:
        root_span.set_attribute("repo_path", repo_path_str)
        root_span.set_attribute("agent_type", agent_type)
        
        print(f"--- Starting Behavioral Pipeline for: {repo_path_str} with agent: {agent_type} ---")

        with tracer.start_as_current_span("analyze_and_select_complexities"):
            print("\nStep 1 & 2: Analyzing repository and selecting issues...")
            analyzer = RepoAnalyzer(repo_path_str)
            all_issues_before = analyzer.analyze() 
            dspy_payload = select_and_normalize_issues(all_issues_before, Path(repo_path_str).name)

        if not dspy_payload.get("selected_complexities"):
            print("Analysis complete, but no complexities were found.")
            return

        with tracer.start_as_current_span("generate_adversarial_prompt"):
            print("\nStep 3: Generating adversarial prompt...")
            prompt_generator = DSPyPromptGenerator()
            prompt_package = prompt_generator.generate_prompt(dspy_payload)
            
        with tracer.start_as_current_span("run_agent_test") as agent_span:
            print(f"\nStep 4: Running {agent_type} agent test...")
            if agent_type == 'gemini': runner = GeminiRunner()
            else: raise ValueError(f"Unknown agent type: {agent_type}")

            test_id = f"test_{agent_type}_{uuid.uuid4().hex[:8]}"
            print(f"\n--- Running Test: {test_id} ---")
            
            prompt = prompt_package['prompt']
            agent_span.set_attribute("test_id", test_id)
            agent_span.set_attribute("prompt", prompt[:200] + "...")

            # The agent is run directly. Phoenix will capture this via the OTel spans.
            with RepoSandbox(repo_path_str, exclude_patterns=['.venv', '__pycache__', '*.pyc']) as sandbox_path:
                agent_result = runner.test_prompt(prompt, sandbox_path)

        with tracer.start_as_current_span("calculate_confusion_score") as score_span:
            print("\nStep 5: Calculating behavioral confusion score...")
            confusion_score = calculate_confusion_score(agent_result)
            print(f"Confusion Score: {confusion_score}/100")
            score_span.set_attribute("confusion_score", confusion_score)
            root_span.set_attribute("confusion_score", confusion_score)
            
        with tracer.start_as_current_span("save_results"):
            print("\nStep 6: Saving results and artifacts...")
            artifact_path = Path("results/artifacts") / test_id
            artifact_path.mkdir(parents=True, exist_ok=True)
            with open(artifact_path / "input.json", "w") as f:
                json.dump({"dspy_payload": dspy_payload, "final_prompt_package": prompt_package}, f, indent=2)
            with open(artifact_path / "agent_stdout.log", "w") as f:
                f.write(agent_result.get("stdout", ""))
            with open(artifact_path / "agent_stderr.log", "w") as f:
                f.write(agent_result.get("stderr", ""))
            with open(artifact_path / "changes.diff", "w") as f:
                f.write(agent_result.get("diff", ""))
            
            summary = {
                "test_id": test_id, "timestamp": datetime.now().isoformat(), "agent_type": agent_type,
                "repo_name": dspy_payload.get("repo_name"), "confusion_score": confusion_score,
                "source_complexities": dspy_payload.get("selected_complexities"), "final_prompt": prompt,
                "agent_result": {
                    "success_flag": agent_result.get("success"),
                    "duration_seconds": agent_result.get("duration_seconds"),
                    "files_modified_count": agent_result.get("files_modified"),
                    "exit_code": agent_result.get("exit_code"),
                }
            }
            results_file = Path("results/test_results.json")
            all_results = []
            if results_file.exists():
                with open(results_file, "r") as f:
                    try: all_results = json.load(f)
                    except json.JSONDecodeError: pass
            all_results.append(summary)
            with open(results_file, "w") as f:
                json.dump(all_results, f, indent=2)

    print(f"\n--- Pipeline Complete ---")
    print(f"Saved test result {test_id} to {results_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the coding agent behavioral testing pipeline.")
    parser.add_argument("--repo", type=str, default="data/repos/synthcomplex", help="Path to the repository.")
    parser.add_argument("--agent", type=str, choices=['gemini'], default="gemini", help="Specify the agent to run.")
    args = parser.parse_args()

    if not Path(args.repo).exists():
        sys.exit(f"Error: Target repository not found at '{args.repo}'.")
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("Error: 'GROQ_API_KEY' environment variable not set.")
    
    run_pipeline(args.repo, args.agent)