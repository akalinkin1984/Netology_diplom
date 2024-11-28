"""
URL configuration for netology_diplom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
# from django.contrib import admin
from baton.autodiscover import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from backend.views import CustomUserViewSet, ProductImageViewSet


router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'product_images', ProductImageViewSet, basename='product_images')

urlpatterns = ([
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('api/v1/', include('backend.urls', namespace='backend')),
    path('api/v1/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + [path('silk/', include('silk.urls', namespace='silk'))])
