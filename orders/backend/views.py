from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.http import JsonResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from yaml import load as load_yaml, Loader
from requests import get
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


from backend.models import Shop, Category, Product, ProductInfo, Parameter, \
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken

from backend.signals import new_user_registered, new_order
from .serializers import UserSerializer, CategorySerializer, ProductInfoSerializer

from rest_framework.authentication import SessionAuthentication

from .models import User, Shop

from distutils.util import strtobool

# Create your views here.

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return None

class RegisterAccount(APIView):
    """
    Регистрация
    """
    authentication_classes = (CsrfExemptSessionAuthentication,)
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'username', 'password', 'company', 'position'}.issubset(request.data):
            errors = {}

            if request.data['password'] is not None:
                try:
                    validate_password(request.data['password'])
                    print('try')
                except Exception as password_error:
                    error_arr = []
                    for item in password_error:
                        error_arr.append(item)
                    return JsonResponse({
                        'Status': False,
                        'Errors': {'password': error_arr}
                    })
                else:
                    # request.data._mutable = True
                    request.data.update({})
                    user_serializer = UserSerializer(data=request.data)
                    if user_serializer.is_valid():
                        user = user_serializer.save()
                        user.set_password(request.data['password'])
                       
                        user.save()

                        # Signal. Crashes with 500 error
                        # new_user_registered.send(sender=self.__class__, user_id=user.id)

                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({
                            'Status': False, 
                            'Errors': user_serializer.errors
                        })
                
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Not all required arguments are filled'
                })
            else:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Password is null',
                }) 
        else:
            return JsonResponse({
                'Status': False,
                'Errors': 'Oops!',
            }, status=404)


class ConfirmAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'], key=request.data['token']).first()

            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Invalid token or email'
                })
        return JsonResponse({
            'Status': False,
            'Errors': 'Not all required arguments are filled'
        })



class LoginAccount(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def post(self, request, *args, **kwargs):
        if {'username', 'password'}.issubset(request.data):
            user = authenticate(username=request.data['username'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({
                        'Status': True,
                        'Token': token.key
                    })
                else:
                    return JsonResponse({
                        'Status': False,
                        'Errors': 'User is not active'
                    }, status=403)
            else:
                return JsonResponse({
                    'Status': False,
                    'Errors': 'Invalid username or password',
                    'user': user
                })
        else:
            return JsonResponse({
                    'Status': False,
                    'Errors': 'Login failed'
                }, status=403)



class PartnerState(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    """
    Запрещает или разрешает прием заказов
    """
    def post(self, request, *args, **kwargs):

        try:
            user = Token.objects.get(key=request.headers['token']).user
        except:
            return JsonResponse({
                'Status': False,
                'Error': 'User which could be associated with that token doesn\'t exist'
            }, status=403)

        if user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'This API is only for shops'
            }, status=403)

        try:
            state = request.data['state']
        except:
            return JsonResponse({
                'Status': False,
                'Error': 'State value required'
            }, status=404)
        if state is None:
            return JsonResponse({
                'Status': False,
                'Error': 'State value required'
            }, status=404)

        company_name = user.company
        shop = Shop.objects.get(name=company_name)
        shop.state = strtobool(request.data['state'])
        shop.save()

        return JsonResponse({'Status': True})

    def get(self, request, *args, **kwargs):
        try:
            user = Token.objects.get(key=request.headers['token']).user
        except:
            return JsonResponse({
                'Status': False,
                'Error': 'User which could be associated with that token doesn\'t exist'
            }, status=403)

        if user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'This API is only for shops'
            }, status=403)
        
        company_name = user.company
        shop = Shop.objects.get(name=company_name)
        
        return JsonResponse({
            'Shop': shop.name,
            'State': shop.state
        })


class PartnerUpdate(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):

        try:
            user = Token.objects.get(key=request.headers['token']).user
        except:
            return JsonResponse({
                'Status': False,
                'Error': 'User which could be associated with that token doesn\'t exist'
            }, status=403)
        
        if user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'This API is only for shops'
            }, status=403)
        
        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({
                    'Status': False,
                    'Error': str(e)
                })
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'])
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shop.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              shop_id=shop.id,
                                                              name=item['name'],
                                                              quantity=item['quantity'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'])

                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({
            'Status': False,
            'Error': 'Not all required arguments are filled'})
    

class CategoryView(ListAPIView):
    """
    Список категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductsList(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    """
    Получение списка товаров
    """
    def get(self, request, *args, **kwargs):
        try:
            user = Token.objects.get(key=request.headers['token']).user
        except:
            return JsonResponse({
                'Status': False,
                'Error': 'User which could be associated with that token doesn\'t exist'
            }, status=403)

        products = ProductInfo.objects.all()
        serializer = ProductInfoSerializer(products, many=True)

        return JsonResponse({
            'Status': True,
            'Data': serializer.data
        })


class ProductInfoView(APIView):
    """
    Поиск товара
    """
    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        category_id = request.query_params.get('category_id')
        shop_id = request.query_params.get('shop_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return JsonResponse({
            'Status': True,
            'Data': serializer.data
        })
