from django.shortcuts import render
from .models import *


def index(request):
    if not Position.objects.all():
        return render(request, 'fram/index.html', {'positions': 'None'})

    context = {
        'layers': Layer.objects.all().order_by('position__date'),
        }
    return render(request, 'fram/index.html', context)

def letters(request):
    return render(request, 'fram/letters.html', {
        'letters': Letter.objects.all().order_by('-position__date'),
    })

def read_letter(request, letterID):
    try:
        letter = Letter.objects.get(id=letterID)
    except Letter.DoesNotExist:
        letter = None

    return render(request, 'fram/read_letter.html', {
        'letter': letter,
    })

def info(request):
    return render(request, 'fram/info.html')
