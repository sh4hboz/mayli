from django.contrib import admin
from .models import Order, OrderItem, WaiterCall


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('dish',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type', 'customer_name', 'customer_phone', 'table', 'status', 'total', 'created_at')
    list_filter = ('order_type', 'status', 'checkout_requested')
    list_editable = ('status',)
    search_fields = ('id', 'customer_name', 'customer_phone', 'delivery_address', 'table__number')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'dish', 'qty', 'unit_price', 'created_at')
    search_fields = ('order__id', 'dish__name')


@admin.register(WaiterCall)
class WaiterCallAdmin(admin.ModelAdmin):
    list_display = ('table', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('table__number',)
    readonly_fields = ('created_at', 'updated_at')
