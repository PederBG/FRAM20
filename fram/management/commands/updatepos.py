from django.core.management.base import BaseCommand
from fram.models import Position

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def handle(self, *args, **options):
        OLD_POS = '-50,85.5'
        NEW_POS = '-50,85.3'

        for pos in Position.objects.all():
            print(pos)
            if (pos.grid == OLD_POS):
                pos.grid = NEW_POS
                pos.save()
        print('Positions changed')
