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
    Сериализатор позиции заказа
    """
    product = serializers.CharField(read_only=True, source="product.product.name")
    shop = serializers.CharField(read_only=True, source="shop.name")
    price_rrc = serializers.IntegerField(read_only=True, source="product.price_rrc")

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'shop', 'quantity', 'price_rrc']


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор заказа
    """
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_sum = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ['id', 'dt', 'status', 'order_items', 'total_sum']
