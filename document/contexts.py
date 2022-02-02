def user_is_manager(request):
    user_is_manager = False
    if request.user.is_authenticated:
        user_is_manager = request.user.groups.filter(name="manager").exists()
    return {"user_is_manager": user_is_manager}
