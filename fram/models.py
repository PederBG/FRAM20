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

class Letter(models.Model):
    title = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    content = models.TextField(max_length=50000)

    def __str__(self):
        return "Travel letter: {}".format(self.title)
