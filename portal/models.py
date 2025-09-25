from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    """Custom user model to add profile-specific fields."""
    average_rating = models.FloatField(default=0.0)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

class Item(models.Model):
    """Represents an item that can be borrowed or lent."""
    CATEGORY_CHOICES = [
        ('Books', 'Books'),
        ('Notes', 'Notes'),
        ('Electronics', 'Electronics'),
        ('Sports Equipment', 'Sports Equipment'),
        ('Tools', 'Tools'),
        ('Apparel', 'Apparel'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lended_items')
    borrowing_terms = models.CharField(max_length=255, help_text="e.g., Free for 1 week, Rs.500.00 deposit required")
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Security deposit amount (e.g., 500.00)")
    rental_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rental fee for the item (e.g., 50.00)")
    borrowing_period = models.PositiveIntegerField(default=7, help_text="Maximum borrowing period in days (e.g., 7)")
    is_available = models.BooleanField(default=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BorrowRecord(models.Model):
    """Acts as a transaction log for borrowing activities."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ON_LOAN', 'On Loan'),
	('AWAITING_DEPOSIT', 'Awaiting Deposit'),
        ('RETURN_PENDING', 'Return Pending'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='borrow_records')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrowed_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    actual_return_date = models.DateTimeField(null=True, blank=True)
    return_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Payment fields
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_signature = models.CharField(max_length=255, blank=True, null=True)
    deposit_paid = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.item.name} borrowed by {self.borrower.username}"

class Feedback(models.Model):
    borrow_record = models.OneToOneField(BorrowRecord, on_delete=models.CASCADE, related_name='feedback')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_feedback')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_feedback')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.borrow_record}"

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"
