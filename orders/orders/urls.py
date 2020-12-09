"""orders URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from backend.views import PartnerUpdate, PartnerState, RegisterAccount, LoginAccount, CategoryView, ProductsList, ProductInfoView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),

    path('user/register', RegisterAccount.as_view(), name='register-account'),
    path('user/login', LoginAccount.as_view(), name='login-account'),

    path('products/list', ProductsList.as_view(), name='products-list'),
    path('product/info', ProductInfoView.as_view(), name='product-info'),
    path('categories', CategoryView.as_view(), name='categories'),
]
