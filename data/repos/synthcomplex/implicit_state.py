"""
implicit_state.py
Demonstrates problematic mutable module and global state for the RepoAnalyzer.
"""

# This should be flagged as a 'shared_cache' due to its name
SESSION_CACHE = {}

# This should be flagged as a 'module_singleton'
# It's a mutable, module-level object with a generic name.
active_users = []

# This should also be flagged as a 'module_singleton'
# because it's an instantiated custom object.
class AppConfig:
    def __init__(self):
        self.settings = {}
app_config = AppConfig()

# This should NOT be flagged because it follows the UPPER_CASE constant convention.
VALID_MODES = ('fast', 'accurate')

# This is a simple immutable type and should also not be flagged.
MAX_RETRIES = 3

# This global variable will be flagged by the 'global' keyword usage below.
request_counter = 0

def process_request(user_id):
    """
    This function uses the 'global' keyword to modify a module-level variable,
    which should be detected as 'mutable_global'.
    """
    global request_counter
    request_counter += 1
    
    # This modification of a global dict is also a form of implicit state mutation.
    SESSION_CACHE[user_id] = "active"

    return f"Request number {request_counter} for user {user_id}"
