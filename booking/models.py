from django.db import models

class District(models.Model):
    name = models.CharField(max_length=100)
    did = models.IntegerField()

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "districts"
        verbose_name = "District"
        verbose_name_plural = "Districts"




