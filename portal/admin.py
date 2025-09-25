from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Item, BorrowRecord

# Register your models here.

class CustomUserAdmin(UserAdmin):
    # You can customize the admin interface for your user model here if needed
    pass

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'is_available', 'date_posted')
    list_filter = ('is_available', 'category', 'date_posted')
    search_fields = ('name', 'owner__username')

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('item', 'borrower', 'status', 'borrow_date', 'return_date')
    list_filter = ('status', 'borrow_date')
    search_fields = ('item__name', 'borrower__username')

admin.site.register(User, CustomUserAdmin)