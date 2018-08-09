from django.db import models

class Position(models.Model):
    grid = models.CharField(max_length=50)
    date = models.DateField('date')

    def __str__(self):
        return str(self.date) + ": " + self.grid


class Layer(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    opticclose = models.TextField(max_length=20000)
    opticmos = models.TextField(max_length=20000)
    sarclose = models.TextField(max_length=20000)
    sarmos = models.TextField(max_length=20000)
    seaice = models.TextField(max_length=20000)
    icedrift = models.TextField(max_length=20000)

    def __str__(self):
        return "Layers from date " + str(self.position.date)
