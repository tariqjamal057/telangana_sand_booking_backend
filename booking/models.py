from django.db import models


class District(models.Model):
    name = models.CharField(max_length=250)
    did = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "districts"
        verbose_name = "District"
        verbose_name_plural = "Districts"


class StockYard(models.Model):
    name = models.CharField(max_length=250)
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="stock_yards"
    )
    contact_person_name = models.CharField(max_length=250, null=True, blank=True)
    contact_person_number = models.CharField(max_length=250, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    sand_quality = models.CharField(max_length=250, null=True, blank=True)
    sand_price = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "stock_yards"
        verbose_name = "Stock Yard"
        verbose_name_plural = "Stock Yards"


class Mandal(models.Model):
    name = models.CharField(max_length=250)
    mid = models.IntegerField()
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="mandals"
    )

    class Meta:
        db_table = "mandals"
        verbose_name = "Mandal"
        verbose_name_plural = "Mandals"


class MandalVillage(models.Model):
    name = models.CharField(max_length=250)
    vid = models.IntegerField()
    mandal = models.ForeignKey(
        Mandal, on_delete=models.CASCADE, related_name="villages"
    )

    class Meta:
        db_table = "mandal_villages"
        verbose_name = "Mandal Village"
        verbose_name_plural = "Mandal Villages"
