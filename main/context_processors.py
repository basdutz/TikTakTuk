def user_context(request):
    return {
        'role': request.session.get('role'),
        'username': request.session.get('username'),
    }