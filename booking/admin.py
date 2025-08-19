from django.contrib import admin
from .models import (
    District,
    StockYard,
    Mandal,
    MandalVillage,
    BookingUserCredential,
    BookingMasterData,
    BookingHistory,
)


class StockYardAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "district",
        "district__did",
        "sand_quality",
    )
    search_fields = ("name", "district__name")
    list_filter = ("district", "sand_quality")


class MandalAdmin(admin.ModelAdmin):
    list_display = ("name", "mid", "district")
    search_fields = ("name", "district__name")
    list_filter = ("district",)


class MandalVillageAdmin(admin.ModelAdmin):
    list_display = ("name", "vid", "mandal")
    search_fields = ("name", "mandal__name")
    list_filter = ("mandal",)


class BookingUserCredentialAdmin(admin.ModelAdmin):
    list_display = ("username",)
    search_fields = ("username",)


class BookingMasterDataAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "booking_user",
        "district",
        "stockyard",
        "vehicle_no",
        "delivery_district",
        "delivery_mandal",
        "delivery_village",
        "delivery_slot",
        "payment_mode",
    )
    search_fields = (
        "name",
        "booking_user__username",
        "district__name",
        "stockyard__name",
        "vehicle_no",
    )
    list_filter = (
        "district",
        "stockyard",
        "delivery_district",
        "delivery_mandal",
        "delivery_village",
        "delivery_slot",
        "payment_mode",
    )


class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_master", "started_at", "ended_at", "status", "proxy")
    search_fields = ("booking_master__name", "status", "proxy")
    list_filter = ("status", "started_at", "ended_at")


admin.site.register(StockYard, StockYardAdmin)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "did")
    search_fields = ("name", "did")


admin.site.register(District, DistrictAdmin)


class MandalAdmin(admin.ModelAdmin):
    list_display = ("name", "mid")
    search_fields = ("name", "mid")


admin.site.register(Mandal, MandalAdmin)


class VillageAdmin(admin.ModelAdmin):
    list_display = ("name", "vid")
    search_fields = ("name", "vid")


admin.site.register(MandalVillage, VillageAdmin)


# admin.site.register(District)
# admin.site.register(StockYard)
# admin.site.register(Mandal)
# admin.site.register(MandalVillage)
admin.site.register(BookingUserCredential)
admin.site.register(BookingMasterData)
admin.site.register(BookingHistory)
