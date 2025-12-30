"""
Provides a robust, git-aware sandbox environment for testing code repositories.
"""
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

# Configure a logger for human-friendly terminal output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class RepoSandbox:
    """
    A context manager to create a temporary, isolated, and git-initialized copy of a repository.
    """

    def __init__(self, original_repo_path: str, exclude_patterns: list[str] | None = None):
        """
        Initializes the repository sandbox.

        Args:
            original_repo_path: The file path to the original repository.
            exclude_patterns: A list of glob-style patterns to exclude from the copy.
        """
        self.original_path = Path(original_repo_path).resolve()
        if not self.original_path.exists():
            raise FileNotFoundError(f"Original repository path not found: {self.original_path}")
        
        self.exclude_patterns = exclude_patterns
        self.temp_dir: Path | None = None
        self.sandbox_path: Path | None = None

    def __enter__(self) -> Path:
        """
        Creates the sandbox, copies files, and initializes a new git repository.
        """
        logger.info("Creating sandbox...")
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_test_"))
            self.sandbox_path = self.temp_dir / "repo"

            ignore = shutil.ignore_patterns(*self.exclude_patterns) if self.exclude_patterns else None
            shutil.copytree(self.original_path, self.sandbox_path, dirs_exist_ok=True, ignore=ignore)
            
            py_files = list(self.sandbox_path.rglob("*.py"))
            if not py_files:
                raise RuntimeError("Sandbox copy failed - no Python files were found in the destination.")
            logger.info(f"✓ Copied {len(py_files)} Python files to sandbox.")

            self._initialize_git()
            
            logger.info(f"✓ Sandbox created and initialized at: {self.sandbox_path}")
            return self.sandbox_path
            
        except Exception as e:
            logger.error(f"❌ Error creating sandbox: {e}")
            self.__exit__(None, None, None)
            raise Exception("Failed to create sandbox.") from e

    def _initialize_git(self):
        """Initializes a new git repo in the sandbox for change tracking."""
        if not self.sandbox_path:
            return
            
        try:
            subprocess.run(["git", "init"], cwd=self.sandbox_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=self.sandbox_path, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial sandbox commit"],
                cwd=self.sandbox_path,
                check=True,
                capture_output=True
            )
            logger.info("✓ Git initialized in sandbox.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Could not initialize git in sandbox: {e.stderr.decode().strip()}")
            logger.warning("Proceeding without git tracking for this run.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleans up and deletes the entire temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"🗑️ Sandbox cleaned up: {self.temp_dir}")
            except OSError as e:
                logger.error(f"❌ Error during sandbox cleanup: {e}")
        self.temp_dir = None
        self.sandbox_path = None


if __name__ == "__main__":
    repo_to_test = "data/repos/synthcomplex"
    if not Path(repo_to_test).exists():
        logger.error(f"'{repo_to_test}' not found.")
    else:
        logger.info("--- Testing Sandbox Creation and Cleanup ---")
        try:
            with RepoSandbox(repo_to_test) as sandbox_repo_path:
                logger.info(f"Inside sandbox context: {sandbox_repo_path}")
                assert sandbox_repo_path.name == "repo"
                assert (sandbox_repo_path / ".git").is_dir()
                logger.info("✓ Verification successful.")
        except Exception as e:
            logger.error(f"An error occurred during the sandbox test: {e}", exc_info=True)
        logger.info("--- Sandbox test complete ---")