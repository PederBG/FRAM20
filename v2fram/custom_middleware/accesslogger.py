from fram.models import AccessLog
from datetime import datetime
from urllib.request import urlopen
import json

class AccessLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        #print("Called", flush=True) # How to print to gunicorn
        response = self.get_response(request)
        user_ip = request.META['HTTP_X_REAL_IP'] # Need real ip, not the one proxied by nginx

        last_record = AccessLog.objects.order_by('date').last()
        today = datetime.now().date()

        # If none exist at all
        if not last_record:
            daylog = AccessLog()
            daylog.date = today
            daylog.ip = user_ip
            daylog.location = self.getIPInfo(user_ip)
            daylog.save()

        # If none exist for today
        elif last_record.date != today:
            daylog = AccessLog()
            daylog.date = today
            daylog.ip = user_ip
            daylog.location = self.getIPInfo(user_ip)
            daylog.save()

        else:
            # Log new ips
            if not AccessLog.objects.filter(date = today, ip = user_ip):
                daylog = AccessLog()
                daylog.date = today
                daylog.ip = user_ip
                daylog.location = self.getIPInfo(user_ip)
                daylog.save()

        return response

    @staticmethod
    def getIPInfo(ip):
        response = urlopen('https://extreme-ip-lookup.com/json/' + ip).read().decode('UTF-8')
        data = json.loads(response)

        if data['status'] == 'success' and data['city'] != '':
            return data['city'] + ", " + data['country']
        else:
            return "No data"
