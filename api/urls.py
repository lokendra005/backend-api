from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, TaskViewSet, RatingViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'register', RegisterView, basename='register')
router.register(r'tasks', TaskViewSet)
router.register(r'ratings', RatingViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]