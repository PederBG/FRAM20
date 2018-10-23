from django.shortcuts import render
from .models import *


def index(request):
    if not Position.objects.all():
        return render(request, 'fram/index.html', {'positions': 'None'})

    context = {
        'positions': Position.objects.all().order_by('date'),
        
        # all layers
        'opticclose': Layer.objects.filter(position=Position.objects.last()).values('opticclose')[0]['opticclose'],
        'opticmos': Layer.objects.filter(position=Position.objects.last()).values('opticmos')[0]['opticmos'],
        'sarclose': Layer.objects.filter(position=Position.objects.last()).values('sarclose')[0]['sarclose'],
        'sarmos': Layer.objects.filter(position=Position.objects.last()).values('sarmos')[0]['sarmos'],
        'seaice': Layer.objects.filter(position=Position.objects.last()).values('seaice')[0]['seaice'],
        'icedrift': Layer.objects.filter(position=Position.objects.last()).values('icedrift')[0]['icedrift'],
        }
    return render(request, 'fram/index.html', context)

def letters(request):
    return render(request, 'fram/letters.html', {
        'letters': Letter.objects.all().order_by('-position__date'),
    })

def info(request):
    return render(request, 'fram/info.html')
