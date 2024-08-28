from django.contrib.auth import logout
from django.conf import settings
from django.utils import timezone
#use to logout the user after certain period of being inactive
class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity = timezone.datetime.fromisoformat(last_activity)
                idle_time = timezone.now() - last_activity
                if idle_time.total_seconds() > settings.SESSION_COOKIE_AGE:
                    logout(request)
            request.session['last_activity'] = timezone.now().isoformat()
        response = self.get_response(request)
        return response