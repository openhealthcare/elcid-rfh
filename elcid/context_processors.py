"""
Context Processors for elcid
"""


def permissions(request):
    if not request.user or not request.user.is_active:
        return {}
    else:
        result = {}
        for name in request.user.profile.roles.values_list(
            'name', flat=True
        ):
            result[name] = True

        return dict(permissions=result)
