from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fram.models import Position, Layer
import random
import subprocess
from django.core import management


class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def flush(self):
        #  quickfix
        subprocess.call('rm db.sqlite3', shell=True)

    def reset_db(self):
        management.call_command('reset_db')
        print()

    def make_migrations(self):
        print("Making migrations")
        management.call_command('makemigrations')
        print()

    def migrate(self):
        print("Applying migrations")
        management.call_command('migrate')
        print()

    def createsu(self):
        username = 'admin'
        email = "admin@admin.com"
        pw = "admin"
        User.objects.create_superuser(username=username, email=email, password=pw)

    def create_positions(self, grid, date):
        p = Position()
        p.grid = grid
        p.date = date
        p.save()
        l = Layer()
        l.position = p
        l.save()

    def handle(self, *args, **options):
        self.flush()
        self.migrate()
        self.make_migrations(),
        self.createsu()

        grids = ['-40,84.85', '-33,84.8', '-28,84.4', '-23,83.9', '-21,83.5', '-19,82.9', '-18,82.4', '-17,81.8']
        dates = ['2019-07-16', '2019-07-18', '2018-07-20', '2018-07-22', '2018-07-24', '2018-07-26', '2018-07-28', '2018-07-30']

        for i in range(len(grids)):
            self.create_positions(grids[i], dates[i])
        print("Success")
