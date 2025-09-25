from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm as AuthPasswordChangeForm
from django import forms
from .models import User, Item, Feedback

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'description', 'image', 'borrowing_terms', 'deposit_amount', 'rental_fee', 'borrowing_period']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., TI-84 Plus Calculator'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide details like condition, edition, etc.'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'borrowing_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Rs.20 for 1 week, Rs.100 deposit required'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100.00 (optional)'}),
            'rental_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 20.00 (leave blank if free)'}),
             'borrowing_period': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7 for 1 week, 30 for 1 month'}),
        }
            
        

class ContactForm(forms.Form):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    subject = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What is your message about?'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your message here...'}))

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Pune, Maharashtra'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'location']

class PasswordChangeForm(AuthPasswordChangeForm):
    old_password = forms.CharField(label="Current Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}))
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Leave a comment...'}),
        }