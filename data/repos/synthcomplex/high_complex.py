"""
high_complex.py
Contains functions with very high cyclomatic complexity (deep nesting, branching).
"""

def super_complex_decision_tree(x, y):
    # Cyclomatic complexity is intentionally > 10
    if x > 0:
        if y > 0:
            if x + y > 10:
                return 'Big Quadrant I'
            elif x + y < 5:
                if x % 2 == 0:
                    return 'Edge I Even'
                else:
                    return 'Edge I Odd'
            else:
                return 'Normal I'
        else:
            if y < -10:
                return 'Deep IV'
            elif x > 5:
                if y % 2 == 0:
                    return 'Corner IV Even'
                else:
                    return 'Corner IV Odd'
            else:
                return 'Normal IV'
    elif x < 0:
        if y > 0:
            if y > 100:
                return 'Far II'
            else:
                if x < -100:
                    return 'Far Far II'
                else:
                    return 'Normal II'
        else:
            if x + y == 0:
                return 'Origin IV'
            elif x - y < 0:
                return 'Weird Minus Quadrant'
            else:
                return 'Normal III'
    else:
        return 'On Y axis'


def process_nested_data(data_matrix):
    """
    This function has high complexity due to nested loops and conditionals.
    Radon should score this highly.
    """
    processed_count = 0
    if not data_matrix:
        return 0

    for i, row in enumerate(data_matrix):
        for j, item in enumerate(row):
            if item is None:
                continue
            if item > 100:
                if (i + j) % 2 == 0:
                    processed_count += 1
                else:
                    if item > 1000:
                        processed_count += 5
                    else:
                        processed_count += 2
            elif 10 < item <= 100:
                if i % 2 == 0 and j % 2 != 0:
                    processed_count -= 1
    return processed_count


def validate_user_permissions(user, action, context):
    """
    This function has high complexity due to complex boolean logic.
    Each 'if' and boolean operator adds to the complexity score.
    """
    if not user or not action:
        return False

    is_admin = user.get('is_admin', False)
    is_editor = 'editor' in user.get('roles', [])
    is_viewer = 'viewer' in user.get('roles', [])

    can_edit = is_admin or is_editor
    can_view = can_edit or is_viewer

    # Check action permissions
    if (action == 'edit' and not can_edit):
        return False
    if (action == 'view' and not can_view):
        return False
        
    # Check context permissions
    if context == 'billing' and not is_admin:
        return False
        
    # Check object-level permissions
    if (context == 'profile' and user.get('id') == context.get('target_user_id')) or can_edit:
        return True

    if (action == 'delete' and is_admin and context != 'production'):
        return True
        
    return False