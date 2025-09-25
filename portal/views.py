from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import qrcode
import io
from django.core.mail import send_mail
from .models import User, Item, BorrowRecord, Feedback, Notification
from .forms import CustomUserCreationForm, ItemForm, ContactForm, UserUpdateForm, PasswordChangeForm, FeedbackForm

def home(request):
    """Renders the home page with featured items."""
    featured_items = Item.objects.filter(is_available=True).order_by('-date_posted')[:4]
    context = {
        'featured_items': featured_items
    }
    return render(request, 'index.html', context)

def browse_items(request):
    """Renders the browse page with a list of all available items, with search and pagination."""
    items_list = Item.objects.filter(is_available=True).order_by('-date_posted')
    query = request.GET.get('q')
    category = request.GET.get('category')
    location = request.GET.get('location')

    if query:
        items_list = items_list.filter(name__icontains=query)
    
    if category:
        items_list = items_list.filter(category=category)
        
    if location:
        items_list = items_list.filter(owner__location__icontains=location)

    paginator = Paginator(items_list, 8)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    context = {
        'items': items,
        'query': query,
        'category_choices': Item.CATEGORY_CHOICES,
        'selected_category': category,
        'location': location,
    }
    return render(request, 'browse.html', context)

def item_detail_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    context = {
        'item': item
    }
    return render(request, 'item_detail.html', context)

@login_required
def borrow_item_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if item.owner == request.user:
        messages.error(request, "You cannot rent your own item.")
        return redirect('browse_items')

    if not item.is_available:
        messages.error(request, "This item is not available for renting.")
        return redirect('browse_items')

    rental_fee = item.rental_fee

    # Check if the rental fee is a positive number to start the payment process
    if rental_fee and rental_fee > 0:
        # --- This block is now correctly indented ---
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        payment_data = {
            'amount': int(rental_fee * 100),
            'currency': 'INR',
            'receipt': f'receipt_borrowbuddy_rental_{item.id}_{request.user.id}',
            'notes': { 'item_id': item.id, 'user_id': request.user.id }
        }

        try:
            order = client.order.create(data=payment_data)
            context = {
                'item': item,
                'razorpay_order_id': order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'razorpay_amount': payment_data['amount']
            }
            return render(request, 'initiate_payment.html', context)

        except Exception as e:
            messages.error(request, f"Payment gateway error: {str(e)}")
            return redirect('item_detail', item_id=item.id)

    # If the rental fee is 0 or not set, it's a free borrowing request
    else:
        # --- This block is now correctly indented ---
        existing_record = BorrowRecord.objects.filter(item=item, borrower=request.user, status__in=['PENDING', 'ON_LOAN']).exists()
        if existing_record:
            messages.warning(request, "You already have an active borrow request for this item.")
            return redirect('browse_items')

        BorrowRecord.objects.create(item=item, borrower=request.user, status='PENDING')

        Notification.objects.create(
            recipient=item.owner,
            message=f"{request.user.username} has requested to borrow your item: {item.name}",
            link=reverse('lended_items')
        )

        messages.success(request, f"Your request to borrow '{item.name}' has been sent to the owner.")
        return redirect('browse_items')

@login_required
def approve_request_view(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, item__owner=request.user)
    if record.status == 'PENDING':
        record.status = 'ON_LOAN'
        record.item.is_available = False
        record.item.save()
        days_to_add = record.item.borrowing_period
        record.return_date = timezone.now() + timezone.timedelta(days=days_to_add)
        record.save()
        
        # Notify borrower
        Notification.objects.create(
            recipient=record.borrower,
            message=f"Your request for '{record.item.name}' has been approved.",
            link=reverse('borrowed_items')
        )
        
        messages.success(request, f"You have approved the request for '{record.item.name}'.")
    else:
        messages.error(request, "This request is not pending approval.")
    return redirect('lended_items')

@login_required
def reject_request_view(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, item__owner=request.user)
    if record.status == 'PENDING':
        record.status = 'CANCELLED'
        record.save()
        
        # Notify borrower
        Notification.objects.create(
            recipient=record.borrower,
            message=f"Your request for '{record.item.name}' has been rejected.",
            link=reverse('borrowed_items')
        )
        
        messages.success(request, f"You have rejected the request for '{record.item.name}'.")
    else:
        messages.error(request, "This request is not pending approval.")
    return redirect('lended_items')

@login_required
def mark_as_returned_view(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, borrower=request.user)
    if record.status == 'ON_LOAN':
        record.status = 'RETURN_PENDING'
        record.save()
        
        # Notify owner
        Notification.objects.create(
            recipient=record.item.owner,
            message=f"{request.user.username} has marked '{record.item.name}' as returned. Please confirm.",
            link=reverse('lended_items')
        )
        
        messages.success(request, f"You have marked '{record.item.name}' as returned. Waiting for owner to confirm.")
    else:
        messages.error(request, "This item is not currently on loan.")
    return redirect('borrowed_items')

@login_required
def confirm_return_view(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, item__owner=request.user)
    if record.status == 'RETURN_PENDING':
        record.status = 'RETURNED'
        record.actual_return_date = timezone.now()
        record.item.is_available = True
        record.item.save()
        record.save()
        
        # Notify borrower
        Notification.objects.create(
            recipient=record.borrower,
            message=f"The return of '{record.item.name}' has been confirmed.",
            link=reverse('borrowed_items')
        )
        
        messages.success(request, f"You have confirmed the return of '{record.item.name}'.")
    else:
        messages.error(request, "This item is not pending a return confirmation.")
    return redirect('lended_items')

@login_required
def leave_feedback_view(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id)
    if not (request.user == record.borrower or request.user == record.item.owner):
        messages.error(request, "You are not authorized to leave feedback for this transaction.")
        return redirect('home')
    if hasattr(record, 'feedback'):
        messages.warning(request, "Feedback has already been submitted for this transaction.")
        return redirect('home')
    if request.user == record.borrower:
        reviewee = record.item.owner
    else:
        reviewee = record.borrower
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.borrow_record = record
            feedback.reviewer = request.user
            feedback.reviewee = reviewee
            feedback.save()
            avg_rating = Feedback.objects.filter(reviewee=reviewee).aggregate(Avg('rating'))['rating__avg']
            reviewee.average_rating = round(avg_rating, 2)
            reviewee.save()
            messages.success(request, "Your feedback has been submitted successfully!")
            return redirect('home')
    else:
        form = FeedbackForm()
    context = {
        'form': form,
        'record': record,
        'reviewee': reviewee,
    }
    return render(request, 'leave_feedback.html', context)

@login_required
def settings_view(request):
    return render(request, 'settings.html')

def signup_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Send verification email
            verification_link = request.build_absolute_uri(reverse('verify_email', args=[user.verification_token]))
            send_mail(
                'Verify your BorrowBuddy account',
                f'Please click the following link to verify your account: {verification_link}',
                'from@example.com', # This will be ignored by the console backend
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Please check your email to verify your account.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Your account is not active. Please verify your email.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})

def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    user_form = UserUpdateForm(instance=request.user)
    pass_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('profile')
        elif 'change_password' in request.POST:
            pass_form = PasswordChangeForm(request.user, request.POST)
            if pass_form.is_valid():
                user = pass_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the password error(s) below.')
    
    context = {
        'user_form': user_form,
        'pass_form': pass_form
    }
    return render(request, 'profile.html', context)

def add_item_view(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please login to lend an item.")
        return redirect('login')
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            return redirect('browse_items')
    else:
        form = ItemForm()
    return render(request, 'additem.html', {'form': form})

@login_required
def borrowed_items_view(request):
    borrowed_records = BorrowRecord.objects.filter(borrower=request.user).order_by('-borrow_date')
    context = {
        'borrowed_records': borrowed_records
    }
    return render(request, 'borrowed.html', context)

@login_required
def lended_items_view(request):
    lended_records = BorrowRecord.objects.filter(item__owner=request.user).order_by('-borrow_date')
    context = {
        'lended_records': lended_records
    }
    return render(request, 'lended.html', context)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get the cleaned data from the form
            full_name = form.cleaned_data['full_name']
            from_email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Prepare the email content
            email_subject = f"New Contact Form Message: {subject}"
            email_message = f"You have a new message from:\n\nName: {full_name}\nEmail: {from_email}\n\nMessage:\n{message}"

            try:
                # Send the email
                send_mail(
                    email_subject,
                    email_message,
                    settings.EMAIL_HOST_USER, # Sender's email (from settings)
                    [settings.EMAIL_HOST_USER], # Recipient's email (sending to yourself)
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('home')

            except Exception as e:
                messages.error(request, f'Sorry, there was an error sending your message. Please try again later.')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
def request_deposit(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, item__owner=request.user)
    if record.item.deposit_amount and record.item.deposit_amount > 0:
        record.status = 'AWAITING_DEPOSIT'
        record.save()

        # Send notification to borrower
        Notification.objects.create(
            recipient=record.borrower,
            message=f"The owner of '{record.item.name}' has requested a security deposit of ₹{record.item.deposit_amount}.",
            link=reverse('borrowed_items')
        )
        messages.success(request, 'Deposit request has been sent to the borrower.')
    else:
        messages.error(request, 'No deposit amount is set for this item.')
    return redirect('lended_items')

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        try:
            # Get the payment details from the POST request
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify the payment signature
            client.utility.verify_payment_signature(params_dict)

            # --- Create the Borrow Record AFTER successful payment ---
            # Fetch the order to get the item_id and user_id from notes
            order_details = client.order.fetch(order_id)
            item_id = order_details['notes']['item_id']
            user_id = order_details['notes']['user_id']

            item = Item.objects.get(pk=item_id)
            borrower = User.objects.get(pk=user_id)

            # Create the borrow record
            record = BorrowRecord.objects.create(
                item=item,
                borrower=borrower,
                status='PENDING',  # Set status to PENDING for owner's approval
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                razorpay_payment_signature=signature
            )

            # Create a notification for the item owner
            Notification.objects.create(
                recipient=item.owner,
                message=f"{borrower.username} has paid the rental fee and requested to borrow your item: {item.name}",
                link=reverse('lended_items')
            )

            return JsonResponse({'status': 'success', 'message': 'Payment successful and request sent!'})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'failure', 'message': 'Payment verification failed.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'failure', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'failure', 'message': 'Invalid request method.'}, status=400)

@login_required
def generate_qr_code(request, record_id):
    record = get_object_or_404(BorrowRecord, pk=record_id, item__owner=request.user)
    qr_url = request.build_absolute_uri(reverse('confirm_return_by_qr', args=[record.return_token]))
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    
    return HttpResponse(buffer, content_type="image/png")

@login_required
def confirm_return_by_qr(request, token):
    record = get_object_or_404(BorrowRecord, return_token=token)
    
    if request.method == 'POST':
        if record.status == 'ON_LOAN':
            record.status = 'RETURN_PENDING'
            record.save()
            
            # Notify owner
            Notification.objects.create(
                recipient=record.item.owner,
                message=f"{request.user.username} has marked '{record.item.name}' as returned via QR code. Please confirm.",
                link=reverse('lended_items')
            )
            
            messages.success(request, f"You have successfully marked '{record.item.name}' as returned.")
            return redirect('borrowed_items')
        else:
            messages.error(request, "This item is not currently on loan.")
            return redirect('borrowed_items')

    return render(request, 'confirm_return_by_qr.html', {'record': record})

def verify_email(request, token):
    user = get_object_or_404(User, verification_token=token)
    user.is_active = True
    user.is_verified = True
    user.save()
    login(request, user)
    messages.success(request, 'Your account has been successfully verified.')
    return redirect('home')

@login_required
def transaction_history_view(request):
    # Fetch all borrow records where the current user was the borrower and paid a deposit
    transactions = BorrowRecord.objects.filter(borrower=request.user, deposit_paid=True).order_by('-borrow_date')
    
    context = {
        'transactions': transactions
    }
    return render(request, 'transaction_history.html', context)


@login_required
def pay_deposit(request, record_id):
    if request.method == 'POST':
        # Find the record, ensuring the logged-in user is the borrower
        record = get_object_or_404(BorrowRecord, pk=record_id, borrower=request.user)
        deposit_amount = record.item.deposit_amount
        
        # Check if a deposit is actually required
        if not deposit_amount or deposit_amount <= 0:
            return JsonResponse({'error': 'This item does not require a deposit.'}, status=400)

        # Create a Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Prepare the payment data
        payment_data = {
            'amount': int(deposit_amount * 100),  # Amount in the smallest currency unit (paise)
            'currency': 'INR',
            'receipt': f'receipt_borrowbuddy_{record.id}',
            'payment_capture': 1
        }
        
        try:
            # Create the order on Razorpay's servers
            order = client.order.create(data=payment_data)
            
            # Save the order ID to our database
            record.razorpay_order_id = order['id']
            record.deposit_amount = deposit_amount
            record.save()
            
            # Return the order details to the frontend JavaScript
            return JsonResponse({
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'key': settings.RAZORPAY_KEY_ID,
                'name': 'BorrowBuddy Deposit',
                'description': f'Deposit for {record.item.name}'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

def terms_view(request):
    return render(request, 'terms.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def about_view(request):
    return render(request, 'about.html')

def faq_view(request):
    return render(request, 'faq.html')

def public_profile_view(request, username):
    # Get the user whose profile is being viewed
    profile_user = get_object_or_404(User, username=username)

    # Get all the items that this user is currently lending
    lended_items = Item.objects.filter(owner=profile_user, is_available=True).order_by('-date_posted')

    # Get all the feedback/reviews for this user
    reviews = Feedback.objects.filter(reviewee=profile_user).order_by('-created_at')

    context = {
        'profile_user': profile_user,
        'lended_items': lended_items,
        'reviews': reviews
    }

    return render(request, 'public_profile.html', context)

