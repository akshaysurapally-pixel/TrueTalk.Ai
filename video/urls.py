
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'call-sessions', views.CallSessionViewSet)
router.register(r'call-logs', views.CallLogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]