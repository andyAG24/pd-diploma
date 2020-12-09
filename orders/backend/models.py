from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import ugettext
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
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
    ('staff', 'Сотрудник')
)

# Create your models here.

class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True
    
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(
            email=email, 
            is_active=True, 
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        else:
            extra_fields.setdefault('type', 'staff')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = ['email']
    objects = UserManager()
    USERNAME_FIELD = 'username'
    email = models.EmailField(ugettext('Email'), unique=True)
    company = models.CharField(max_length=100, verbose_name='Компания', blank=True)
    position = models.CharField(max_length=40, verbose_name='Должность', blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        ugettext('username'),
        max_length=150,
        help_text=ugettext('Требуется имя пользователя. Буквы, цифры и @/./+/-/_.'),
        validators=[username_validator],
        error_messages={
            'unique': ugettext('Пользователь с таким именем уже существует'),
        },
        unique=True,
    )
    is_active = models.BooleanField(
        ugettext('active'),
        default=False, 
        help_text=ugettext(
            'Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.username}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email', )


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    filename = models.CharField(max_length=100)
    state = models.BooleanField(verbose_name='Принимает заказы?', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    shop = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True,
                                 on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name='Название', default=None)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        # ordering = ('-name',)

    # def __str__(self):
    #     return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    name = models.CharField(max_length=50, verbose_name='Название')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая цена')

    external_id = models.PositiveIntegerField(verbose_name='External id', default=None)
    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информация о продуктах'
        # ordering = ('-name',)

    def __str__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        # ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Продукт', related_name='product_parameters', blank=True,
                                on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters', blank=True,
                                on_delete=models.CASCADE)
    value = models.CharField(max_length=50, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр продукта'
        verbose_name_plural = 'Информация о параметрах продуктов'
        # ordering = ('-name',)

    # def __str__(self):
    #     return self.name


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', blank=True, null=True,
                                on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=15)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        # ordering = ('-name',)

    # def __str__(self):
    #     return self.name


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                                on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='ordered_items', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='ordered_items', blank=True,
                                on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество') 

    class Meta:
        verbose_name = 'Продукт в заказе'
        verbose_name_plural = 'Список продуктов заказа'
        # ordering = ('-name',)

    # def __str__(self):
    #     return self.name


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', blank=True, null=True,
                             on_delete=models.CASCADE)

    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name: 'Токен для подтверждения Email'
        verbose_name_plural: 'Токены для подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User, 
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=ugettext('The User which is associated to this password reset token')
    )

    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=ugettext('Time when token was generated')
    )

    key = models.CharField(
        ugettext('Key'),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)