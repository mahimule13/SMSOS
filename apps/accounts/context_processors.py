def user_context(request):
    context = {}
    if request.user.is_authenticated:
        try:
            context['user_profile'] = request.user.profile
            context['user_role'] = request.user.profile.get_role_display()
        except:
            pass
    return context
