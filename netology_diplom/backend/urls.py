from django.urls import path, include

from .views import PartnerUpdate, ContactView, ProductInfoView, CategoryView, ShopView, OrderView


app_name = 'backend'
urlpatterns = [
    path('partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('user/contact/', ContactView.as_view(), name='user-contact'),
    path('products/', ProductInfoView.as_view(), name='products'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('shops/', ShopView.as_view(), name='shops'),
    path('order/', OrderView.as_view(), name='order')
    ]
