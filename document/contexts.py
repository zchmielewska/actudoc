def user_is_manager(request):
    user_is_manager = False
    if request.user.is_authenticated:
        user_is_manager = request.user.groups.filter(name="manager").exists()
    return {"user_is_manager": user_is_manager}


def user_is_contributor(request):
    user_is_contributor = False
    if request.user.is_authenticated:
        user_is_contributor = request.user.profile.role == "contributor"
    return {"user_is_contributor": user_is_contributor}


def user_is_admin(request):
    user_is_admin = False
    if request.user.is_authenticated:
        user_is_admin = request.user.profile.role == "admin"
    return {"user_is_admin": user_is_admin}
