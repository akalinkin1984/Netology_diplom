from rest_framework import serializers

from .models import (User, Category, Shop, ProductInfo, Product, ProductParameter,
                            OrderItem, Order, Contact)


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

    class Meta:
        model = ProductInfo
        fields = ('id', 'external_id', 'product', 'model', 'quantity', 'price_rrc', 'shop', 'product_parameters')
        read_only_fields = ('id',)
