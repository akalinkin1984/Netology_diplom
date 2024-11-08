from rest_framework import serializers

from backend.models import (User, Category, Shop, ProductInfo, Product, ProductParameter,
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
