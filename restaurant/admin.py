# Este es el archivo del panel de administración de Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils import timezone
from .models import MenuItem, Table, Order, OrderItem, UserProfile, RegistrationPIN, AuditLog

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available')
    list_filter = ('available',)
    search_fields = ('name',)

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity')
    search_fields = ('number',)

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('menu_item', 'quantity', 'get_item_price', 'get_total_price')
    readonly_fields = ('get_item_price', 'get_total_price')
    extra = 1

    def get_item_price(self, obj):
        return f"${obj.menu_item.price}"
    get_item_price.short_description = 'Precio Unitario'

    def get_total_price(self, obj):
        return f"${obj.quantity * obj.menu_item.price}"
    get_total_price.short_description = 'Precio Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('id', 'table', 'waiter', 'status', 'created_at', 'get_total_cost')
    list_filter = ('status', 'table', 'created_at')
    search_fields = ('id', 'table__number', 'waiter__username')
    ordering = ('-created_at',)

    def get_total_cost(self, obj):
        total = obj.calculate_total()
        return f"${total}"
    get_total_cost.short_description = 'Total del Pedido'

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_mesa_del_pedido',
        'menu_item',
        'quantity',
        'get_fecha_del_pedido'
    )
    list_display_links = ('id',)
    list_filter = ('menu_item', 'order__table')
    search_fields = ('menu_item__name', 'order__table__number')

    def get_mesa_del_pedido(self, obj):
        if obj.order and obj.order.table:
            return str(obj.order.table)
        return "Sin Mesa"
    get_mesa_del_pedido.short_description = 'Mesa'
    get_mesa_del_pedido.admin_order_field = 'order__table__number'

    def get_fecha_del_pedido(self, obj):
        if obj.order:
            return obj.order.created_at.strftime("%d-%m-%Y %H:%M")
        return "Sin Fecha"
    get_fecha_del_pedido.short_description = 'Fecha del Pedido'
    get_fecha_del_pedido.admin_order_field = 'order__created_at'

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'pin')
    list_filter = ('role',)
    search_fields = ('user__username',)

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

@admin.register(RegistrationPIN)
class RegistrationPINAdmin(admin.ModelAdmin):
    list_display = ('pin', 'role', 'created_by', 'uses', 'created_at')
    list_filter = ('role', 'uses')
    search_fields = ('pin', 'created_by__username')

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except UserProfile.DoesNotExist:
            return 'Sin Rol'
    get_role.short_description = 'Rol'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    search_fields = ('user__username', 'action')
    list_filter = ('timestamp',)

    class Media:
        css = {
            'all': ('restaurant/css/admin_custom.css',)
        }

# Personalizar el dashboard
original_index = admin.site.index

def custom_index(request, extra_context=None):
    today = timezone.now().date()
    user_count = User.objects.count()
    menu_count = MenuItem.objects.count()
    order_count = Order.objects.filter(created_at__date=today).count()
    table_count = Table.objects.count()

    extra_context = extra_context or {}
    extra_context.update({
        'user_count': user_count,
        'menu_count': menu_count,
        'order_count': order_count,
        'table_count': table_count,
    })
    return original_index(request, extra_context)

admin.site.index = custom_index
