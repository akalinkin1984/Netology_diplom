from django_filters import rest_framework as filters
from .models import ProductInfo


class ProductInfoFilter(filters.FilterSet):
    """
    Фильтр для поиска продуктов
    """
    model = filters.CharFilter(field_name='model', lookup_expr='icontains')
    external_id = filters.NumberFilter(field_name='external_id', lookup_expr='exact')
    product__category_id = filters.NumberFilter(field_name='product__category_id', lookup_expr='exact')
    shop_id = filters.NumberFilter(field_name='shop_id', lookup_expr='exact')

    class Meta:
        model = ProductInfo
        fields = ['model', 'external_id', 'product__category_id', 'shop_id']
