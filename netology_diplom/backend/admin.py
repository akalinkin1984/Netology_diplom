from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from backend.models import (User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
                            Order, OrderItem, Contact)


# Register your models here.
@admin.register(User)
class UserAdmin(UserAdmin):
    """Настройка панели управления пользователями в административной части сайта"""

    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'url', 'user', 'status', ]
    list_filter = ['status', ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', ]
    list_filter = ['category__name', ]


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'model', 'external_id', 'quantity', 'price', 'price_rrc', 'product', 'shop__name', ]
    list_filter = ['shop__categories', 'shop__name', ]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', ]


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_info', 'parameter', 'value', ]
    list_filter = ['parameter__name', ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'dt', 'status', ]
    list_filter = ['user', 'dt', 'status', ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'shop', 'quantity', ]
    list_filter = ['order__dt', ]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['id', 'user__email', 'city', 'phone', ]
    list_filter = ['city', ]