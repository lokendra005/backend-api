from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from .models import User, Task, Rating
from .serializers import UserSerializer, TaskSerializer, RatingSerializer
import razorpay
from django.conf import settings
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


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    @action(detail=False, methods=['post'])
    def create_order(self, request):
        task_id = request.data.get('task_id')
        try:
            task = Task.objects.get(id=task_id)
            amount = int(float(task.budget) * 100)  # Convert to paise
            
            # Create Razorpay Order
            order_data = {
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1
            }
            order = self.client.order.create(data=order_data)

            # Create Payment record
            payment = Payment.objects.create(
                user=request.user,
                task=task,
                order_id=order['id'],
                amount=float(amount) / 100,
                currency='INR'
            )

            response_data = {
                'order_id': order['id'],
                'amount': amount,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'payment_id': payment.id,
                'task_title': task.title,
                'user_email': request.user.email
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')

        try:
            # Verify signature
            self.client.utility.verify_payment_signature({
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            })

            # Update payment status
            payment = Payment.objects.get(order_id=order_id)
            payment.payment_id = payment_id
            payment.status = 'successful'
            payment.save()

            # Update task status if needed
            task = payment.task
            task.status = 'assigned'  # or any appropriate status
            task.save()

            return Response({
                'status': 'Payment successful',
                'task_id': task.id
            })

        except Exception as e:
            payment = Payment.objects.get(order_id=order_id)
            payment.status = 'failed'
            payment.save()
            
            return Response(
                {'error': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )