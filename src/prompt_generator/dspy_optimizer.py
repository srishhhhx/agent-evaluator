import json
import os
import sys
from datetime import datetime
import random

# Add project root to path to allow absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import dspy
from src.prompt_generator.groq_lm import GroqDSPyLM

# ... (rest of the file is the same)
class CombinedPromptSignature(dspy.Signature):
    """DSPy signature: Takes two complexity objects → produces adversarial prompt."""
    complexities = dspy.InputField(desc="List of two normalized complexity findings")
    repo_name = dspy.InputField(desc="Repository name")
    prompt = dspy.OutputField(desc="Combined adversarial developer prompt")


class DSPyPromptGenerator:
    def __init__(
        self,
        model_name: str = "groq/llama-3.3-70b-versatile",
        deterministic_seed: int = 42,
        temperature: float = 0.4,
        max_tokens: int = 800,
        retries: int = 2,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retries = retries
        self.seed = deterministic_seed

        random.seed(self.seed)

        if dspy and os.getenv("GROQ_API_KEY"):
            lm = GroqDSPyLM(
                model=model_name,
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            dspy.configure(lm=lm)

    def _build_human_context_summary(self, complexities):
        lines = []
        for c in complexities:
            t = c["type"]
            if t == "circular_import":
                files = c["details"]["imports"]
                lines.append(f"- Circular import between `{files[0]}` and `{files[1]}`")
            elif t == "high_complexity":
                lines.append(f"- Function `{c['function']}` in `{c['file']}` has very high branching complexity")
            elif t == "implicit_state":
                lines.append(f"- Hidden mutable global state `{c['details']['variable']}` in `{c['file']}` impacting execution behavior")
            elif t == "overloaded_api":
                lines.append(f"- Overloaded API `{c['function']}` in `{c['file']}` with {c['details']['parameters']} params and {c['details']['branches']} branches")
        return "\n".join(lines)

    def _generate_prompt_text(self, repo_name, complexities):
        summary = self._build_human_context_summary(complexities)
        return f"""

You are modifying the `{repo_name}` codebase.

The analyzer has identified the following interacting complexity problems:
{summary}

Your task:
1️⃣ Resolve BOTH issues in a single clean code modification.
2️⃣ Maintain full backwards-compatible behavior — users should see no change unless logically required.
3️⃣ Do NOT introduce performance regressions.
4️⃣ Do NOT simplify by deleting logic — reason carefully and preserve semantic intent.
5️⃣ Ensure the final code is deterministic, safe, and easier to maintain.

Important adversarial constraints:
- Fixing one complexity MUST NOT worsen the other.
- Avoid naive solutions that “hack around” the issue.
- Prefer structured design improvement, not cosmetic edits.

Deliverables:
- Implement the required modifications directly in the relevant files.
- Update only code that is necessary.
- Do not change unrelated behavior.
""".strip()

    def generate_prompt(self, payload: dict):
        repo_name = payload.get("repo_name", "unknown_repo")
        complexities = payload.get("selected_complexities", [])

        if not complexities:
            raise ValueError("No complexities provided to DSPy prompt generator")

        complexities = complexities[:2]

        prompt_text = self._generate_prompt_text(repo_name, complexities)

        return {
            "prompt": prompt_text,
            "metadata": {
                "repo_name": repo_name,
                "complexities_used": [c["type"] for c in complexities],
                "model_used": self.model_name,
                "timestamp": datetime.utcnow().isoformat(),
                "deterministic_seed": self.seed,
            },
        }

if __name__ == '__main__':
    from src.parser.repo_analyzer import RepoAnalyzer, select_and_normalize_issues
    from pathlib import Path

    print("--- Running DSPy Prompt Generator Standalone Test ---")
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not set.")
    else:
        repo_path = "data/repos/synthcomplex"
        print(f"Analyzing {repo_path} to get complexities...")
        analyzer = RepoAnalyzer(repo_path)
        raw_issues = analyzer.analyze()
        dspy_payload = select_and_normalize_issues(raw_issues, Path(repo_path).name)
        print("\nInitializing DSPyPromptGenerator...")
        prompt_generator = DSPyPromptGenerator()
        print("\nGenerating adversarial prompt...")
        final_prompt_package = prompt_generator.generate_prompt(dspy_payload)
        print("\n--- Generated Prompt Package ---")
        print(json.dumps(final_prompt_package, indent=2))