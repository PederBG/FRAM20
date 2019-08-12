import os, sys, subprocess
from django.core.management.base import BaseCommand
from fram.models import Weekly
from django_mailbox.models import Message, Mailbox, MessageAttachment
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

            if mail.subject.lower()=='weekly':
                pdf = MessageAttachment.objects.filter(message_id=mail.id).first()

                fName = "Letter_week_{}".format(datetime.now().strftime("%V"))

                if str(pdf)[-4:] != '.pdf':
                    print("Format needs to be pdf!")
                    continue

                if Weekly.objects.filter(title=fName):
                    print("Letter from this week already exist!")
                    continue

                cmd = "cp {} data/weekly/{}.pdf".format(str(pdf), fName)
                print("COMMAND: " + cmd)
                subprocess.call(cmd ,shell=True)

                # Creating new db row
                w = Weekly()
                w.title = fName
                w.filename = fName + ".pdf"
                w.save()
                print("Weekly letter added!")
                quit()
