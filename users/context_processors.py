def unread_message_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.profile.messages.filter(is_read=False).count()
        except Exception:
            count = 0
    return {'unread_message_count': count}
