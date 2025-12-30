"""
This module provides functions for calculating behavioral confusion scores for AI agents.

The scoring is based on the agent's execution stability, its decision to act
(or not act), and the runtime effort it expends, rather than the semantic
correctness of its changes.
"""

from typing import Any, Dict


def calculate_confusion_score(agent_result: Dict[str, Any]) -> int:
    """
    Calculates a behavioral confusion score based on agent execution metrics.

    The score starts at 100 and penalties are applied for signs of confusion,
    such as instability, inaction, or excessive effort.

    Args:
        agent_result: A dictionary containing the results of the agent's run.
                      Expected keys: 'exit_code', 'files_modified', 'duration_seconds'.

    Returns:
        An integer score between 0 and 100, where a lower score indicates
        higher confusion.
    """
    score = 100
    
    exit_code = agent_result.get("exit_code", 0)
    files_modified = agent_result.get("files_modified", 0)
    duration = agent_result.get("duration_seconds", 0)

    # 1. Execution Stability Penalty
    if exit_code != 0:
        # Heavy penalty for any crash, error, or timeout.
        score -= 50
        
    # 2. Action vs. Inaction Penalty
    if files_modified == 0:
        # Very heavy penalty for "hallucinated action" - when the agent claims
        # success (exit_code == 0) but makes no changes.
        score -= 40
    elif 1 <= files_modified <= 2:
        # Moderate penalty for minimal action, could indicate hesitation.
        score -= 10
    # No penalty for 3+ files modified, indicating decisive action.
        
    # 3. Runtime Effort Penalty
    if duration > 120:
        # High penalty for very long runtimes.
        score -= 20
    elif duration > 60:
        # Moderate penalty for longer-than-average runtimes.
        score -= 10
        
    # Ensure score is within the 0-100 range
    return max(0, score)
