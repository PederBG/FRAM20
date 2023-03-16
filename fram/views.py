from django.shortcuts import render
from .models import *
from django.http import FileResponse, Http404
from datetime import datetime
import os

def index(request):
    return render(request, 'fram/index.html')


def map(request):
    if not Position.objects.all():
        return render(request, 'fram/map.html', {'positions': 'None'})

    # If time is over 11:00 +  maximum 10 minutes a new layer will be published.
    # Since this layer only have partial information, default is set to the day before.
    if datetime.now() > datetime.now().replace(hour=11, minute=10):
        default_date = Layer.objects.all().order_by('-position__date')[1]
    else:
        default_date = Layer.objects.all().order_by('-position__date')[0]

    context = {
        'layers': Layer.objects.all().order_by('position__date'),
        'default_date': default_date.position.date,
        'historical': HistoricalDrift.objects.all().order_by('year'),

        'layernames': [('Optic-Close', 's2c'), ('Optic-Mosaic', 'terramos'), ('SAR-Close', 's1c'),
         ('SAR-Mosaic', 's1mos'), ('Bathymetry', 'bathymetry'), ('Magnetic', 'magnetic'), ('Gravity', 'gravity'),
         ('SeaIce', 'seaice'), ('IceDrift', 'icedrift'), ('LandEdge', 'landedge'), ('Graticule', 'graticule')],
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
    context = {
        'infopdfs': InfoPDF.objects.all().order_by('-id')
    }
    if request.GET:
        path = '/root/fram/data/infopdfs/' + request.GET.get('name')
        if os.path.commonprefix((os.path.realpath(path),'/root/fram/data/infopdfs/')) and path[-4:] == '.pdf':
            try:
                return FileResponse(open('data/infopdfs/' + request.GET.get('name'), 'rb'), content_type='application/pdf', as_attachment=True)
            except FileNotFoundError:
                raise Http404()
        else:
            return render(request, 'fram/info.html', context)

    return render(request, 'fram/info.html', context)


def weekly(request):
    context = {
        'weeklys': Weekly.objects.all().order_by('-id')
    }
    if request.GET:
        path = '/root/fram/data/weekly/' + request.GET.get('name')
        if os.path.commonprefix((os.path.realpath(path),'/root/fram/data/weekly/')) and path[-4:] == '.pdf':
            try:
                return FileResponse(open(path, 'rb'), content_type='application/pdf', as_attachment=True)
            except FileNotFoundError:
                raise Http404()
        else:
            return render(request, 'fram/weekly.html', context)

    return render(request, 'fram/weekly.html', context)


def links(request):
    return render(request, 'fram/links.html')


def contact(request):
    context = {
        'date': datetime.now(),
        'daily_users': len(AccessLog.objects.filter(date = datetime.now().date())),
        'monthly_users': len(AccessLog.objects.filter(date__month = datetime.now().date().month)),
        'alltime_users': len(AccessLog.objects.all()),
        }
    return render(request, 'fram/contact.html', context)


def cookiepolicy(request):
    return render(request, 'fram/cookiepolicy.html')
