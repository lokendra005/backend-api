from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPES = (
        ('problem_owner', 'Problem Owner'),
        ('solution_provider', 'Solution Provider'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'user_type']

class Task(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('interested', 'Interested'),
        ('assigned', 'Assigned'),
        ('submitted', 'Submitted'),
        ('closed', 'Closed'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    attachments = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Rating(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    solution_quality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    technical_accuracy = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    timeliness = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback = models.TextField()
    status = models.CharField(max_length=20, default='pending_review')
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('successful', 'Successful'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id} - {self.amount} {self.currency}"