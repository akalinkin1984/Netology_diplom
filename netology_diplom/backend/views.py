import os

from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader

from backend.models import (User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
                            Order, OrderItem)


class PartnerUpdate(APIView):
    """
    Класс для обновления информации о партнере.
    """
    def post(self, request, *args, **kwargs):
        """
        Обновить информацию о прайс-листе партнера.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Требуется войти в систему'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'status': False, 'error': 'Только для магазинов'}, status=403)

        path = request.data.get('path')

        if os.path.isfile(path):
            with open(path) as file:
                data = load_yaml(file, Loader=Loader)

                try:
                    shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                except IntegrityError:
                    return JsonResponse({'status': False, 'error': 'У Вас нет доступа к этому магазину'}, status=403)

                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()

                ProductInfo.objects.filter(shop_id=shop.id).delete()

                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(
                        product_id=product.id,
                        external_id=item['id'],
                        model=item['model'],
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop_id=shop.id
                    )

                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(
                            product_info_id=product_info.id,
                            parameter_id=parameter_object.id,
                            value=value
                        )

                return JsonResponse({'status': True})

        return JsonResponse({'status': False, 'error': 'Файл не существует'})
