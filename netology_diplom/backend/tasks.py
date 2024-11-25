import os

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.apps import apps
from celery import shared_task
from yaml import load as load_yaml, Loader
from easy_thumbnails.files import get_thumbnailer

from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, User


@shared_task
def update_shop_price_list(path, user_id):
    """
    Задача обновления прайса магазина
    """
    if not os.path.isfile(path):
        raise Exception('Файл не существует')
    try:
        with open(path) as file:
            data = load_yaml(file, Loader=Loader)

            try:
                shop = Shop.objects.get(name=data['shop'])
            except Shop.DoesNotExist:
                try:
                    shop = Shop.objects.create(name=data['shop'], user_id=user_id)
                except IntegrityError:
                    raise Exception('У Вас может быть только один магазин')
            else:
                if shop.user.id != user_id:
                    raise Exception('У Вас нет доступа к этому магазину')

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

            return {'status': True}
    except Exception as e:
        return {'status': False, 'error': str(e)}


@shared_task
def send_new_order_email_task(user_id, order_id):
    """
    Задача для отправки писем при размещении заказа
    """
    user = User.objects.get(id=user_id)
    send_mail(
        "Обновление статуса заказа",
        f"Ваш заказ №{order_id} сформирован",
        settings.EMAIL_HOST_USER,
        [user.email],
    )

    order = Order.objects.get(id=order_id)
    shop_emails = order.order_items.values_list('shop__user__email', flat=True).distinct()

    for email in shop_emails:
        send_mail(
            'Новый заказ',
            'У вас новый заказ. Пожалуйста, проверьте свой аккаунт.',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )


@shared_task
def create_thumbnails(model_path, pk, field):
    """
    Задача для создания миниатюр
    """
    model = apps.get_model(model_path)
    instance = model.objects.get(pk=pk)
    field_file = getattr(instance, field)

    if field_file:
        thumbnailer = get_thumbnailer(field_file)
        sizes = {'small': (100, 100), 'medium': (300, 300), 'large': (600, 600)}
        for size_name, size in sizes.items():
            thumbnailer.get_thumbnail({'size': size, 'crop': True})
