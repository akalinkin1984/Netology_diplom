from django.urls import path, include

from backend.views import PartnerUpdate


app_name = 'backend'
urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
    ]