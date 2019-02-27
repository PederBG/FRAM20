from django.db import models

class Position(models.Model):
    grid = models.CharField(max_length=50)
    date = models.DateField('date')

    def __str__(self):
        return str(self.date) + ": " + self.grid


class Layer(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    opticclose = models.TextField(max_length=20000, default='No info available')
    opticmos = models.TextField(max_length=20000, default='No info available')
    sarclose = models.TextField(max_length=20000, default='No info available')
    sarmos = models.TextField(max_length=20000, default='No info available')
    seaice = models.TextField(max_length=20000, default='No info available')
    icedrift = models.TextField(max_length=20000, default='No info available')

    def __str__(self):
        return "Layers from date " + str(self.position.date)

class Daily(models.Model):
    title = models.CharField(max_length=100, default='No title')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    preamble = models.TextField(max_length=1000, default='No preamble')
    content = models.TextField(max_length=50000, default='No content')

    def __str__(self):
        return "Daily report: {}".format(self.title)


class Weekly(models.Model):
    title = models.CharField(max_length=250, default='No title')
    filename = models.CharField(max_length=250, default='No data')

    def __str__(self):
        return "Weekly letter: {}".format(self.title)

class HistoricalDrift(models.Model):
    year = models.CharField(max_length=30, default='No data')
    lons = models.CharField(max_length=20000, default='No data')
    lats = models.CharField(max_length=20000, default='No data')

    def __str__(self):
        return "Historical drift from: {}".format(self.year)

class DailyAccessLog(models.Model):
    date = models.DateField('date')
    ip = models.CharField(max_length=50)

    def __str__(self):
        return "{}: {}".format(self.date.strftime('%d/%m-%Y'), self.ip)
