from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


STATUS_CHOICES = (
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class UserManager(BaseUserManager):
    """
    Класс для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Создать и сохранить пользователя с заданным email и паролем.
        """
        if not email:
            raise ValueError('Email должен быть указан')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Создать пользователя с заданным email и паролем.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Создать суперпользователя с заданным email и паролем.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff', True):
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if not extra_fields.get('is_superuser', True):
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Модель пользователя
    """

    objects = UserManager()

    REQUIRED_FIELDS = ['first_name', 'last_name']
    USERNAME_FIELD = 'email'

    email = models.EmailField(_('email address'), unique=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"
        ordering = ('email',)


class Shop(models.Model):
    """
    Модель магазина
    """

    name = models.CharField(max_length=50, verbose_name='Название магазина')
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='Статус получения заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Магазины"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Модель категории
    """

    name = models.CharField(max_length=50, verbose_name='Название категории')
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Категории товаров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Модель продукта
    """

    name = models.CharField(max_length=100, verbose_name='Название продукта')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = "Товары"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    Модель информации о продукте
    """

    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = "Информация о товарах"

    def __str__(self):
        return self.model


class Parameter(models.Model):
    """
    Модель имени параметра
    """

    name = models.CharField(max_length=50, verbose_name='Название параметра')

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Параметры товаров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """
    Модель параметра продукта
    """

    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='product_parameters', on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters',
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров товаров"
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.product_info} - {self.parameter}'


class Order(models.Model):
    """
    Модель заказа
    """

    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATUS_CHOICES, max_length=15)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Заказы"
        ordering = ('-dt',)

    def __str__(self):
        return f'{str(self.id)} - {self.status}'


class OrderItem(models.Model):
    """
    Модель позиции заказа
    """

    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='order_items', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"

    def __str__(self):
        return f'{self.order} - {self.product}'


class Contact(models.Model):
    """
    Модель контактов пользователя
    """

    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом')
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Контакты пользователей"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'
