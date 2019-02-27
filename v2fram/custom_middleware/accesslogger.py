from fram.models import DailyAccessLog
from datetime import datetime

class AccessLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        last_record = DailyAccessLog.objects.order_by('date').last()
        today = datetime.today()

        # Make new record if none exist for today
        if not last_record:
            daylog = DailyAccessLog()
            daylog.date = today
        elif last_record.date != today:
            daylog = DailyAccessLog()
            daylog.date = today

        user_ip = request.META['REMOTE_ADDR']

        # Log new ips
        if not DailyAccessLog.objects.filter(date = today, ip = user_ip):
            daylog.ip =user_ip
            daylog.save()
            print("New ip logged!")

        return response
