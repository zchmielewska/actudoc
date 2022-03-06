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
