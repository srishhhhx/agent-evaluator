"""
overloaded_api.py
Demonstrates functions that are "overloaded" with too many parameters or branches.
"""

def function_with_many_params(
    user_id, 
    request_data, 
    session_token, 
    api_version, 
    is_admin, 
    enable_caching, 
    skip_validation, 
    log_level='INFO'
    ):
    """
    This function has 8 parameters and should be flagged as an overloaded API.
    """
    # An agent would struggle to know which of these are required or how they interact.
    if is_admin and log_level == 'DEBUG':
        print("Running in admin debug mode")
    
    return {'status': 'ok', 'user': user_id}


def function_with_many_branches(data, mode):
    """
    This function has many conditional branches and should be flagged.
    """
    # This kind of logic is hard for an agent to refactor or understand.
    if mode == 'A':
        if 'key1' in data:
            return "A1"
        else:
            return "A_default"
    elif mode == 'B':
        if data.get('value', 0) > 10:
            return "B_high"
        elif data.get('value', 0) > 5:
            return "B_mid"
        else:
            return "B_low"
    elif mode == 'C':
        try:
            result = data['nested']['value']
            return result
        except (KeyError, TypeError):
            return "C_error"
    else:
        # One more branch here
        if data is None:
            return "Empty"
        return "Default"
