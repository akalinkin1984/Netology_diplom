import os
import json

from django.db import IntegrityError
from django.db.models import Q, F, Sum
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from yaml import load as load_yaml, Loader
from django_filters.rest_framework import DjangoFilterBackend

from .models import (User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
                            Order, OrderItem, Contact)
from .serializers import (ContactSerializer, ProductInfoSerializer, CategorySerializer, ShopSerializer,
                          OrderSerializer, OrderItemSerializer)
from .filters import ProductInfoFilter
from .signals import new_order


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


class ProductInfoView(ListAPIView):
    """
    Класс для поиска товаров
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    filterset_class = ProductInfoFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['model', 'external_id', 'product__category_id', 'shop_id']
    search_fields = ['model', 'product__name']


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий товаров
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра магазинов
    """
    queryset = Shop.objects.filter(status=True)
    serializer_class = ShopSerializer


class OrderView(APIView):
    """
    Класс для получения и размещения заказов пользователями
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить мои заказы
        """
        orders = Order.objects.filter(user_id=request.user.id).exclude(status='basket').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product__price_rrc')))
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Разместить заказ
        """
        if 'id' in request.data and 'contact' in request.data:
            try:
                Order.objects.filter(user_id=request.user.id, id=request.data['id']).update(
                    contact_id=request.data['contact'],
                    status='new')
                new_order.send(sender=self.__class__, user_id=request.user.id)
                return Response({'status': True})
            except IntegrityError:
                return Response({'status': False, 'error': 'Неправильно указаны аргументы'})

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'})


class BasketView(APIView):
    """
    Класс для управления корзиной
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получить корзину
        """
        basket = Order.objects.filter(user_id=request.user.id, status='basket').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product__price_rrc')))
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Добавить товары в корзину
        """
        items_string = request.data.get('items')
        if not items_string:
            return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'})

        try:
            items_dict = json.loads(items_string)
        except ValueError:
            return Response({'status': False, 'error': 'Неверный формат запроса'})

        basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')

        for order_item in items_dict:
            order_item.update({'order': basket.id})
            serializer = OrderItemSerializer(data=order_item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError as error:
                    return Response({'status': False, 'error': str(error)})
            else:
                return Response({'status': False, 'error': serializer.errors})

        return Response({'status': True, 'Создано объектов': len(items_dict)})

    def put(self, request):
        """
        Обновить товары в корзине(количество)
        """
        items = request.data.get('items')
        if not items:
            return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'})

        try:
            items_dict = json.loads(items)
        except ValueError:
            return Response({'status': False, 'error': 'Неверный формат запроса'})

        basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
        objects_updated = 0
        for order_item in items_dict:
            if type(order_item['id']) == int and type(order_item['quantity']) == int:
                objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                    quantity=order_item['quantity'])
        return Response({'status': True, 'Обновлено объектов': objects_updated})

    def delete(self, request):
        """
        Удалить товары из корзины
        """
        items = request.data.get('items')
        if not items:
            return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'})

        basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
        order_item_ids = [int(x) for x in items.split(',') if x.isdigit()]
        deleted_count = OrderItem.objects.filter(order_id=basket.id, id__in=order_item_ids).delete()[0]
        return Response({'status': True, 'Удалено объектов': deleted_count})
