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


class BookingUserCredential(models.Model):
    username = models.CharField(max_length=250, unique=True)
    password = models.CharField(max_length=250)

    class Meta:
        db_table = "booking_user_list"
        verbose_name = "Booking User List"
        verbose_name_plural = "Booking User Lists"


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
