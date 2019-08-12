import os, sys, subprocess
from django.core.management.base import BaseCommand
from fram.models import InfoPDF
from django_mailbox.models import Message, Mailbox, MessageAttachment
from datetime import datetime
import json

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

            if mail.subject.lower()=='infopdf':

                pdf = MessageAttachment.objects.filter(message_id=mail.id).first()
                if len(mail.text) > 1 or ( len(mail.text) == 1 and mail.text[0] not in [' ', '_', '.', ','] ):
                    fName = mail.text.split('\n')[0].replace(" ", "_")
                    if fName[-1] == '_':
                        fName = fName[:-1]
                else:
                    fName = datetime.now().strftime("%d-%m-%Y")
                print("PDF name {}".format(fName))

                if str(pdf)[-4:] != '.pdf':
                    print("Format needs to be pdf!")
                    continue

                if InfoPDF.objects.filter(title = fName):
                    print("A PDF with this name already exist.")
                    quit()

                cmd = "cp {} data/infopdfs/{}.pdf".format(str(pdf), fName)
                print("COMMAND: " + cmd)
                subprocess.call(cmd ,shell=True)

                # Creating new db row
                w = InfoPDF()
                w.title = fName
                w.filename = fName + ".pdf"
                w.save()
                print("Info PDF added!")
                quit()
