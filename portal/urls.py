
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse_items, name='browse_items'),
    path('verify_email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Placeholder URLs for logged-in pages
    path('profile/', views.profile_view, name='profile'),
    path('additem/', views.add_item_view, name='add_item'),
    path('borrowed/', views.borrowed_items_view, name='borrowed_items'),
    path('lended/', views.lended_items_view, name='lended_items'),
    path('contact/', views.contact_view, name='contact'),
    path('borrow/<int:item_id>/', views.borrow_item_view, name='borrow_item'),
    path('approve/<int:record_id>/', views.approve_request_view, name='approve_request'),
    path('reject/<int:record_id>/', views.reject_request_view, name='reject_request'),
    path('item/<int:item_id>/', views.item_detail_view, name='item_detail'),
    path('return/<int:record_id>/', views.mark_as_returned_view, name='mark_as_returned'),
    path('confirm_return/<int:record_id>/', views.confirm_return_view, name='confirm_return'),
    path('generate_qr_code/<int:record_id>/', views.generate_qr_code, name='generate_qr_code'),
    path('confirm_return_by_qr/<uuid:token>/', views.confirm_return_by_qr, name='confirm_return_by_qr'),
    path('request_deposit/<int:record_id>/', views.request_deposit, name='request_deposit'),
    path('pay_deposit/<int:record_id>/', views.pay_deposit, name='pay_deposit'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('transactions/', views.transaction_history_view, name='transaction_history'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('leave_feedback/<int:record_id>/', views.leave_feedback_view, name='leave_feedback'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('about/', views.about_view, name='about'),
    path('faq/', views.faq_view, name='faq'),
    path('settings/', views.settings_view, name='settings'), 
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
]
