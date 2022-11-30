from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fram.models import AccessLog
import random
from django.core import management
from datetime import date, datetime, timedelta


class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def create_log(self):
        l = AccessLog()
        l.date = datetime.today().date()
        l.ip = "128.0.0.1"
        l.location = "test"
        l.save()

    def handle(self, *args, **options):
        for i in range(5000):
            self.create_log()
        print("Success")
