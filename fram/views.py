from django.shortcuts import render
from .models import *


def index(request):
    if not Position.objects.all():
        return render(request, 'fram/index.html', {'positions': 'None'})

    context = {
        'layers': Layer.objects.all().order_by('position__date'),
        }
    return render(request, 'fram/index.html', context)

def daily(request):
    return render(request, 'fram/daily.html', {
        'daily_reports': Daily.objects.all().order_by('-position__date'),
    })

def read_daily(request, dailyID):
    try:
        daily = Daily.objects.get(id=dailyID)
    except Daily.DoesNotExist:
        daily = None

    return render(request, 'fram/read_daily.html', {
        'daily': daily,
    })

def info(request):
    return render(request, 'fram/info.html')

def weekly(request):
    return render(request, 'fram/weekly.html')

def contact(request):
    return render(request, 'fram/contact.html')
