import os

from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from yaml import load as load_yaml, Loader

from backend.models import (User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
                            Order, OrderItem, Contact)
from backend.serializers import ContactSerializer


class PartnerUpdate(APIView):
    """
    Класс для обновления информации о партнере.
    """
    def post(self, request, *args, **kwargs):
        """
        Обновить информацию о прайс-листе партнера.
        """
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Требуется войти в систему'}, status=403)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=403)

        path = request.data.get('path')

        if not os.path.isfile(path):
            return Response({'status': False, 'error': 'Файл не существует'}, status=400)

        with open(path) as file:
            data = load_yaml(file, Loader=Loader)

            try:
                shop = Shop.objects.get(name=data['shop'])
            except Shop.DoesNotExist:
                try:
                    shop = Shop.objects.create(name=data['shop'], user_id=request.user.id)
                except IntegrityError:
                    return Response({'status': False, 'error': 'У Вас может быть только один магазин'},
                                    status=403)
            else:
                if shop.user.id != request.user.id:
                    return Response({'status': False, 'error': 'У Вас нет доступа к этому магазину'},
                                             status=403)

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

            return Response({'status': True})


class ContactView(APIView):
    """
    Класс для управления контактами пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить контактную информацию
        """
        contacts = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        """
        Создать контактную информацию
        """
        required_fields = {'city', 'street', 'house', 'phone'}
        if not required_fields.issubset(request.data):
            return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'}, status=400)

        request.data._mutable = True
        request.data.update({'user': request.user.id})
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'status': True}, status=201)
        else:
            return Response({'status': False, 'error': serializer.errors}, status=400)

    def delete(self, request, *args, **kwargs):
        """
        Удалить контактную информацию
        """
        items_string = request.data.get('items')
        if items_string:
            try:
                items_list = [int(item) for item in items_string.split(',')]
                query = Q(user_id=request.user.id, id__in=items_list)
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({'status': True, 'Удалено объектов': deleted_count})
            except ValueError:
                return Response({'status': False, 'error': 'Неправильный формат идентификаторов'}, status=400)
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'}, status=400)

    def put(self, request, *args, **kwargs):
        """
        Редактировать контактную информацию
        """
        if 'id' in request.data and request.data['id'].isdigit():
            try:
                contact_id = int(request.data['id'])
                contact = Contact.objects.get(id=contact_id, user_id=request.user.id)
                serializer = ContactSerializer(contact, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'status': True})
                else:
                    return Response({'status': False, 'error': serializer.errors}, status=400)
            except Contact.DoesNotExist:
                return Response({'status': False, 'error': 'Контакт не найден'}, status=404)
            except ValueError:
                return Response({'status': False, 'error': 'Неправильный формат идентификатора'}, status=400)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'}, status=400)
