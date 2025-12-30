"""
Runs the Gemini CLI agent against a code repository.

This module provides the `GeminiRunner` class, which is responsible for
invoking the Gemini CLI with a specific prompt within an isolated code
repository (a sandbox). It captures the agent's output, code changes (diff),
and performance metrics like duration.
"""

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# This block is for __main__ execution. It's placed here to modify
# the path before other imports are attempted in the main block.
if __name__ == "__main__":
    import sys
    # Add the project root to the Python path to allow absolute imports from 'src'.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.sandbox.repo_sandbox import RepoSandbox

logger = logging.getLogger(__name__)


class GeminiRunner:
    """
    A class to execute the Gemini CLI agent on a given code repository.
    """
    def __init__(self):
        """
        Initializes the GeminiRunner and verifies Gemini CLI installation.

        Raises:
            RuntimeError: If the 'gemini' command is not found in the system's PATH.
        """
        logger.info("Checking for Gemini CLI...")
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                raise FileNotFoundError
            logger.info("Gemini CLI found.")
        except FileNotFoundError:
            raise RuntimeError(
                "Gemini CLI not found. Please ensure it is installed and in your PATH.\n"
                "Installation instructions: https://ai.google.dev/docs/gemini_cli_quickstart"
            )

    def _get_git_changes(self, repo_path: Path) -> (int, str):
        """
        Uses Git to get a comprehensive list of changes, including new files.
        
        Returns:
            A tuple containing:
            - The number of modified files (including new ones).
            - A complete diff string of all changes.
        """
        # Use porcelain format for reliable scripting
        status_process = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        status_lines = status_process.stdout.strip().split('\n') if status_process.stdout.strip() else []
        
        files_modified_count = len(status_lines)
        
        # Get diff for already-tracked files
        diff_tracked_process = subprocess.run(
            ["git", "diff"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        full_diff = diff_tracked_process.stdout
        
        # Add new files to staging to get their diff
        new_files = [line[3:] for line in status_lines if line.startswith('??')]
        if new_files:
            # Add each new file individually
            for new_file in new_files:
                subprocess.run(["git", "add", new_file], cwd=repo_path, check=False)
            
            # Get the diff of the newly staged files
            diff_staged_process = subprocess.run(
                ["git", "diff", "--staged"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            full_diff += "\n" + diff_staged_process.stdout

        return files_modified_count, full_diff

    def test_prompt(self, prompt: str, repo_path: Path, timeout: int = 300) -> Dict[str, Any]:
        """
        Runs the Gemini CLI with a given prompt in a specified repository.
        """
        logger.info("Running Gemini CLI...")
        logger.info(f"Prompt: {prompt[:100]}...")
        logger.info(f"Workspace: {repo_path}")
        
        start_time = datetime.now()
        
        command = ["gemini", prompt, "-y"]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=repo_path,
                check=False
            )

            duration = (datetime.now() - start_time).total_seconds()

            files_modified, diff = self._get_git_changes(repo_path)

            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "duration_seconds": round(duration, 2),
                "files_modified": files_modified,
                "diff": diff,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"TIMEOUT: Agent exceeded {timeout}s",
                "exit_code": -1,
                "duration_seconds": timeout,
                "files_modified": 0,
                "diff": "",
            }
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"An unexpected error occurred during agent execution: {e}", exc_info=True)
            return {
                "success": False,
                "stdout": "",
                "stderr": f"An unexpected error occurred: {str(e)}",
                "exit_code": -1,
                "duration_seconds": round(duration, 2),
                "files_modified": 0,
                "diff": "",
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()

    logger.info("Running Gemini Runner __main__ block...")
    repo_to_test = "data/repos/flask"

    if not Path(repo_to_test).exists():
        logger.error(f"Test repository not found at '{repo_to_test}'.")
        logger.error(f"Example: git clone https://github.com/pallets/flask.git {repo_to_test}")
    else:
        try:
            runner = GeminiRunner()
            
            test_prompt = "Create a new file named 'test_app.py' and in it, write a simple Flask application that has a single route '/' that returns 'Hello, World!'."
            
            with RepoSandbox(repo_to_test) as sandbox_path:
                logger.info(f"Running test in sandbox: {sandbox_path}")
                
                result = runner.test_prompt(test_prompt, sandbox_path)
                
                logger.info("\n--- Gemini Agent Test Result ---")
                logger.info(f"Success (Agent Exit Code): {result['success']}")
                logger.info(f"Duration: {result['duration_seconds']}s")
                logger.info(f"Files Modified (from Git): {result['files_modified']}")
                logger.info(f"Agent Exit Code: {result['exit_code']}")
                
                logger.info("\n--- AGENT STDOUT ---")
                logger.info(result['stdout'].strip() if result['stdout'] else "No stdout.")
                
                logger.info("\n--- AGENT STDERR ---")
                logger.info(result['stderr'].strip() if result['stderr'] else "No stderr.")

                if result['diff']:
                    logger.info("\n--- GIT DIFF ---")
                    logger.info(result['diff'])
                else:
                    logger.info("\n--- GIT DIFF ---")
                    logger.info("No changes detected by git.")
                logger.info("------------------------------------")

        except RuntimeError as e:
            logger.error(f"Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the test run: {e}", exc_info=True)