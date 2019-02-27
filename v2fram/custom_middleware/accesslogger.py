from fram.models import DailyAccessLog
from datetime import datetime

class AccessLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        #print("Called", flush=True) # How to print to gunicorn
        response = self.get_response(request)
        user_ip = request.META['REMOTE_ADDR']

        last_record = DailyAccessLog.objects.order_by('date').last()
        today = datetime.today()

        # If none exist at all
        if not last_record:
            daylog = DailyAccessLog()
            daylog.date = today
            daylog.ip = user_ip
            daylog.save()

        # If none exist for today
        elif last_record.date != today:
            daylog = DailyAccessLog()
            daylog.date = today
            daylog.ip = user_ip
            daylog.save()

        else:
            # Log new ips
            if not DailyAccessLog.objects.filter(date = today, ip = user_ip):
                daylog = DailyAccessLog()
                daylog.date = today
                daylog.ip = user_ip
                daylog.save()
                print("New ip logged!")

        return response
