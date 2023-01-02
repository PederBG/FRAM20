from fram.models import AccessLog
from datetime import datetime
from urllib.request import urlopen
import json, os

class AccessLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        #print("Called", flush=True) # How to print to gunicorn
        response = self.get_response(request)
        user_ip = request.META['HTTP_X_REAL_IP'] # Need real ip, not the one proxied by nginx
        # user_ip = "127.0.0.1"

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
        APIkey = os.environ["IP_LOOKUP_API_KEY"]
        response = urlopen('https://extreme-ip-lookup.com/json/' + ip + "?key=" + APIkey).read().decode('UTF-8')
        data = json.loads(response)

        ret = ""

        if data['status'] == 'success':
            if data['country'] != '':
                ret += data['country']
            if data['city'] != '':
                ret += ", " + data['city']
            if data['isp'] != '':
                ret += "; " + data['isp']
        if ret == "":
            ret = "No data"

        return ret
