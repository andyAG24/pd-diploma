from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from yaml import load as load_yaml, Loader
from requests import get
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken

from .serializers import UserSerializer
from backend.signals import new_user_registered, new_order

from rest_framework.authentication import SessionAuthentication

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
                        new_user_registered.send(sender=self.__class__, user_id=user.id)
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
                    'Errors': 'Invaild token or email'
                })
        return JsonResponse({
            'Status': False,
            'Errors': 'Not all required arguments are filled'
        })



class LoginAccount(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(username=request.data['email'], password=request.data['password'])
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
                    'Errors': 'Invalid username or password'
                })
        else:
            return JsonResponse({
                    'Status': False,
                    'Errors': 'Login failed'
                }, status=403)
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'Kek': False
        })













# class PartnerState(APIView)
                    

class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'Status': False,
                'Error': 'User must be authenticated'
            }, status=403)
        
        if request.user.type != 'shop':
            return JsonResponse({
                'Status': False,
                'Error': 'Only for shops'
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

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                            #   external_id=item['id'],
                                                            #   model=item['model'],
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
    
    def get(self, request):
        return JsonResponse({
            "Status": True,
            "Text": "Ok"
        })
