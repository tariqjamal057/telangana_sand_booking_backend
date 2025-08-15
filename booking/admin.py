from django.contrib import admin
from .models import (
    District,
    StockYard,
    Mandal,
    MandalVillage,
    BookingUserCredential,
    BookingMasterData,
)


admin.site.register(District)
admin.site.register(StockYard)
admin.site.register(Mandal)
admin.site.register(MandalVillage)
admin.site.register(BookingUserCredential)
admin.site.register(BookingMasterData)
