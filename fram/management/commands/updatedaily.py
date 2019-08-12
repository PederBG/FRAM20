import os, sys, subprocess, glob
from django.core.management.base import BaseCommand
from fram.models import Position, Layer, Daily
from django_mailbox.models import Message, Mailbox
from datetime import datetime

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def handle(self, *args, **options):
        # Other emails are also blocked in the gmail client
        allowed_addresses = os.environ['ALLOWED_ADDRESSES'].split(',')


        print("Getting new mails...")
        Mailbox.objects.first().get_new_mail()

        mails = Message.objects.all()
        if len(mails) == 0:
            "No mails recieved"
            exit(0)

        for mail in reversed(mails):

            # Check sender address
            sender = mail.from_header.split('<')[1].split('>')[0]
            if sender not in allowed_addresses:
                print("Address " + sender + " is not in allowed_addresses, going to next mail..")
                continue

            if mail.subject=='daily':

                try:
                    # Test syntax
                    mes = mail.text.split('ENDDAILY')[0].split('\n')
                    pos = mes[0].split(' ')
                    grid = pos[0]
                    float(grid.split(',')[0])
                    float(grid.split(',')[1])
                    date = datetime.strptime(pos[1], '%d-%m-%Y')
                    print(grid)
                    print(date)

                    # Check that position from given date don't already excist
                    if len(Position.objects.filter(date=date)) == 0:
                        print("Adding position..")
                        p = Position()
                        p.grid = grid
                        p.date = date
                        p.save()

                        if len(mes) > 3:
                            print("Adding daily report..")
                            d = Daily()
                            d.title = mes[1]
                            d.position = p
                            d.preamble = mes[2]

                            cont = ""
                            for line in mes[3:]:
                                if line == '':
                                    cont += '\n\n'
                                else:
                                    cont += line + ' '
                            d.content = cont
                            d.save()
                            print("Done!")
                            break # Only getting first mail with daily subject

                    else:
                        print("Position already exist")
                        exit(0)

                except Exception:
                    print('Syntax wrong')
                    exit(1)
