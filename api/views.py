from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from .models import User, Task, Rating
from .serializers import UserSerializer, TaskSerializer, RatingSerializer

class RegisterView(viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = Task.objects.all()
        status = self.request.query_params.get('status')
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        
        if status:
            queryset = queryset.filter(status=status)
        if price_min:
            queryset = queryset.filter(budget__gte=price_min)
        if price_max:
            queryset = queryset.filter(budget__lte=price_max)
        return queryset

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        task = self.get_object()
        provider_id = request.data.get('provider_id')
        
        if request.user != task.created_by:
            return Response({'error': 'Only task creator can assign tasks'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        provider = get_object_or_404(User, id=provider_id)
        task.assigned_to = provider
        task.status = 'assigned'
        task.save()
        
        return Response({'status': 'assigned'})

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    
    def perform_create(self, serializer):
        serializer.save(rated_by=self.request.user)