from django.contrib import admin

from .models import Order, OrderItem, OrderSettings, OtpCode


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('dish', 'dish_name', 'unit_price', 'quantity', 'line_total')
    can_delete = False

    def line_total(self, obj):
        return obj.line_total
    line_total.short_description = 'Jami'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone')
    readonly_fields = ('customer_name', 'phone', 'comment', 'total_amount', 'source', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'


@admin.register(OrderSettings)
class OrderSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_open', 'min_order_amount')


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'purpose', 'is_verified', 'consumed', 'attempts', 'expires_at')
    list_filter = ('purpose', 'is_verified', 'consumed')
    search_fields = ('phone',)
