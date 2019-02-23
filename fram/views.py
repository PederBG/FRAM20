from django.shortcuts import render
from .models import *
from django.http import FileResponse, Http404
from datetime import datetime

def index(request):
    return render(request, 'fram/index.html')


def map(request):
    if not Position.objects.all():
        return render(request, 'fram/map.html', {'positions': 'None'})

    # If time is over 11:00 + 10 minutes a new layer will be published.
    # Since this layer only have partial information, default is set to the day before.
    if datetime.now() > datetime.now().replace(hour=11, minute=10):
        default_date = Layer.objects.all().order_by('-position__date')[1]
    else:
        default_date = Layer.objects.all().order_by('-position__date')[0]

    context = {
        'layers': Layer.objects.all().order_by('position__date'),
        'default_date': default_date.position.date,
        'historical': HistoricalDrift.objects.all().order_by('year'),
        }
    return render(request, 'fram/map.html', context)


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
    if request.GET:
        try: # Using as_attachment because phones/tablets get errors reading pdf in browser. TODO: fix this
            return FileResponse(open('data/weekly/' + request.GET.get('name'), 'rb'), content_type='application/pdf', as_attachment=True)
        except FileNotFoundError:
            raise Http404()

    context = {
        'weeklys': Weekly.objects.all().order_by('-id')
    }

    return render(request, 'fram/weekly.html', context)


def links(request):
    return render(request, 'fram/links.html')


def contact(request):
    return render(request, 'fram/contact.html')
