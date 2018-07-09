from django.core.management.base import BaseCommand
from fram.models import Position
import random

grids = []
lat = 84
lon = -22
for i in range(50):
    lat -= 0.1 + (random.randint(0, 10) / 200)
    lon += 0.1 + (random.randint(0, 10) / 200)
    grids.append(str(round(lat, 2)) + ',' + str(round(lon, 2)))

dates = []
for i in range(30):
    dates.append("2019-04-" + str(i+1))
for i in range(22):
    dates.append("2019-05-" + str(i+1))

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def flush(self):
        Position.objects.all().delete()

    def create_positions(self, grid, date):
        p = Position()
        p.grid = grid
        p.date = date
        p.save()

    def handle(self, *args, **options):
        self.flush()
        for i in range(len(grids)):
            self.create_positions(grids[i], dates[i])
        print("Success")
