import datetime
from django.db import models
import requests


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
    name = models.CharField(max_length=250, unique=True)
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="stock_yards"
    )
    sand_quality = models.CharField(max_length=250, null=True, blank=True)
    availabe_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "stock_yards"
        verbose_name = "Stock Yard"
        verbose_name_plural = "Stock Yards"

    def load_stockyard(self):
        today = datetime.date.today()
        try:
            response = requests.post(
                "https://sand.telangana.gov.in/TSSandPortal/MASTERS/QuantitiesService.asmx/LoadQuantities",
                json={"knownCategoryValues": "", "category": "District"},
            )
            response.raise_for_status()
            response_data = response.json()["d"]
            for data in response_data:
                try:
                    StockYard.objects.create(
                        name=data["Stockyard"],
                        district=District.objects.get(name__iexact=data["District"]),
                        sand_quality=data["SandQualityName"],
                        availabe_date=today,
                    )
                except Exception as ex:
                    stockyard_ = StockYard.objects.get(name=data["Stockyard"])
                    stockyard_.availabe_date = today
                    stockyard_.save()
        except Exception as ex:
            print(ex)
            pass

    def get_today_stockyard(self, district_id):
        try:
            self.load_stockyard()
            return StockYard.objects.filter(
                models.Q(availabe_date=datetime.date.today())
                & models.Q(district_id=district_id)
            )
        except Exception as ex:
            print(ex)


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

    def __str__(self):
        return f"{self.name} - {self.mid}"


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

    def __str__(self):
        return f"{self.name} - {self.vid}"


class BookingUserCredential(models.Model):
    username = models.CharField(max_length=250, unique=True)
    password = models.CharField(max_length=250)

    class Meta:
        db_table = "booking_user_list"
        verbose_name = "Booking User List"
        verbose_name_plural = "Booking User Lists"

    def __str__(self):
        return self.username


class BookingMasterData(models.Model):
    name = models.CharField(max_length=250, unique=True)
    booking_user = models.ForeignKey(
        BookingUserCredential,
        on_delete=models.CASCADE,
        related_name="booking_user_credential",
    )
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="booking_master_data"
    )
    stockyard = models.ForeignKey(
        StockYard, on_delete=models.CASCADE, related_name="booking_master_data"
    )
    gstin = models.CharField(max_length=250, null=True, blank=True)
    sand_purpose = models.CharField(max_length=250, null=True, blank=True)
    vehicle_no = models.CharField(max_length=250)
    delivery_district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="booking_master_data_delivery"
    )
    delivery_mandal = models.ForeignKey(
        Mandal, on_delete=models.CASCADE, related_name="booking_master_data_delivery"
    )
    delivery_village = models.ForeignKey(
        MandalVillage,
        on_delete=models.CASCADE,
        related_name="booking_master_data_delivery",
    )
    delivery_slot = models.CharField(max_length=250)
    payment_mode = models.CharField(max_length=250)

    class Meta:
        db_table = "booking_master_data"
        verbose_name = "Booking Master Data"
        verbose_name_plural = "Booking Master Data"

    def __str__(self):
        return self.name


class BookingHistory(models.Model):
    booking_master = models.ForeignKey(
        BookingMasterData, on_delete=models.CASCADE, related_name="booking_history"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    proxy = models.CharField(max_length=250, null=True, blank=True)
    status = models.CharField(max_length=250, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "booking_history"
        verbose_name = "Booking History"
        verbose_name_plural = "Booking History"

    def __str__(self):
        return f"{self.booking_master.name} - {self.started_at} - {self.status} - {self.ended_at}"
