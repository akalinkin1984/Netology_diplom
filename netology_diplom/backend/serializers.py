from rest_framework import serializers
from djoser.serializers import UserSerializer, UserCreateSerializer
from easy_thumbnails.templatetags.thumbnail import thumbnail_url
from django.contrib.auth import get_user_model

from .models import (Category, Shop, ProductInfo, Product, ProductParameter,
                            OrderItem, Order, Contact)


User = get_user_model()

class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для контактной информации
    """
    class Meta:
        model = Contact
        fields = ('id', 'user', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')
        read_only_fields = ('id', )
        extra_kwargs = {
            'user': {'write_only': True}
        }


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор товара
    """
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор параметров товара
    """
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для поиска товаров
    """
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)
    shop = serializers.CharField(read_only=True, source="shop.name")

    class Meta:
        model = ProductInfo
        fields = ('id', 'external_id', 'product', 'model', 'quantity', 'price_rrc', 'shop', 'product_parameters')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра категорий товаров
    """
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра магазинов
    """
    class Meta:
        model = Shop
        fields = ('id', 'name', 'status',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения позиции заказа
    """
    product = serializers.CharField(read_only=True, source="product_info.product.name")
    shop = serializers.CharField(read_only=True, source="shop.name")
    price_rrc = serializers.IntegerField(read_only=True, source="product_info.price_rrc")

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'shop', 'quantity', 'price_rrc', 'order']


class OrderItemSaveSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сохранения позиции заказа
    """
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'shop', 'quantity', 'order']


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор заказа
    """
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_sum = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ['id', 'dt', 'status', 'order_items', 'total_sum']


class UserAvatarSerializer(UserSerializer):
    """
    Сериализатор аватара пользователя
    """
    avatar = serializers.ImageField(required=False)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('avatar',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.avatar:
            ret['avatar'] = {
                'original': instance.avatar.url,
                'small': thumbnail_url(instance.avatar, 'small'),
                'medium': thumbnail_url(instance.avatar, 'medium'),
                'large': thumbnail_url(instance.avatar, 'large'),
            }
        return ret


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор картинки товара
    """
    class Meta:
        model = Product
        fields = ['id', 'image']


# class CustomUserCreateSerializer(UserCreateSerializer):
#     """
#     Сериализатор создания пользователя
#     """
#     class Meta(UserCreateSerializer.Meta):
#         model = User
#         fields = ('id', 'email', 'first_name', 'last_name', 'password')


# class CustomUserSerializer(UserSerializer):
#     """
#     Сериализатор пользователя
#     """
#     class Meta(UserSerializer.Meta):
#         model = User
#         fields = ('id', 'email', 'first_name', 'last_name')
#         read_only_fields = ('id',)
