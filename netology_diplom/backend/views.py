import json

from celery.result import AsyncResult
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Q, F, Sum
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (Shop, Category, ProductInfo, Order, OrderItem, Contact)
from .serializers import (ContactSerializer, ProductInfoSerializer, CategorySerializer, ShopSerializer,
                          OrderSerializer, OrderItemSaveSerializer)
from .filters import ProductInfoFilter
from .signals import new_order
from .tasks import update_shop_price_list
from netology_diplom.celeryapp import app


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса магазина
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Отправить задачу на обновление прайса магазина.
        """
        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=403)

        path = request.data.get('path')
        user = request.user.id

        task = update_shop_price_list.delay(path, user)

        return Response({'status': True, 'task_id': task.id})

    def get(self, request, *args, **kwargs):
        """
        Получить статус задачи обновления прайса
        """
        task_id = request.data.get('task_id')
        task = AsyncResult(task_id, app=app)

        if task.status == 'FAILURE':
            return Response({'status': 'Failed to process'})

        return Response({'status': task.status})


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
            total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price_rrc')))
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
                new_order.send(sender=self.__class__, user_id=request.user.id, order_id=request.data['id'])

                order = Order.objects.get(id=request.data['id'])
                shop_emails = order.order_items.values_list('shop__user__email', flat=True).distinct()

                for email in shop_emails:
                    send_mail(
                        'Новый заказ',
                        'У вас новый заказ. Пожалуйста, проверьте свой аккаунт.',
                        settings.EMAIL_HOST_USER,
                        [email],
                        fail_silently=False,
                    )

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
            total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price_rrc')))
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
            serializer = OrderItemSaveSerializer(data=order_item)
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


class PartnerState(APIView):
    """
    Класс для получения и смены статуса своего магазина
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить информацию о своем магазине
        """
        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        if not shop:
            return Response({'status': False, 'error': 'Магазин не найден'}, status=404)

        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Изменить статус своего магазина
        """
        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=403)

        shop = Shop.objects.filter(user_id=request.user.id).first()
        if not shop:
            return Response({'status': False, 'error': 'Магазин не найден'}, status=404)

        shop.status = not shop.status
        shop.save()
        return Response({'status': True})


class PartnerOrders(APIView):
    """
    Класс для получения заказов магазином
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получить заказы
        """
        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=403)

        order = (Order.objects.filter(order_items__product_info__shop=request.user.shop)
                 .exclude(status='basket')
                 .annotate(total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price_rrc'))))

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)
