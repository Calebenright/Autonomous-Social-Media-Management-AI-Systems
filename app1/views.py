from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from dashboard.views import dashboard
from google.cloud import storage
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.core.mail import send_mail
from .forms import ForgotPasswordForm

def index(request):
    return render(request, 'index.html')

def pricing(request):
    return render(request, 'pricing.html')

def about(request):
    return render(request, 'about.html')

def forgot_password(request):
    # if request.method == 'POST':
    #     form = ForgotPasswordForm(request.POST)
    #     if form.is_valid():
    #         email = form.cleaned_data['email']
    #         try:
    #             user = User.objects.get(email=email)
    #         except User.DoesNotExist:
    #             messages.error(request, 'No user with that email address.')
    #         else:
    #             # Generate the token and send the reset email
    #             token = default_token_generator.make_token(user)
    #             reset_url = reverse('reset_password', kwargs={'uidb64': user.id, 'token': token})
    #             reset_url = request.build_absolute_uri(reset_url)

    #             subject = 'Password Reset Request'
    #             message = f'Please click the link below to reset your password:\n\n{reset_url}'
    #             send_mail(subject, message, 'your_email_address', [email])

    #         return redirect('password_reset_done')
    # else:
    #     form = ForgotPasswordForm()

    # return render(request, 'forgot_password.html', {'form': form})
    return render(request, 'forgot_password.html')

    
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Input validation
        if not username or not email or not password:
            return render(request, 'signup.html', {'error': 'Please fill in all fields.'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email address already exists.'})
        
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            
            return redirect('login')  # Replace 'login' with your desired URL name
        except Exception as e:
            # Handle any potential errors that may occur during user creation
            # Provide appropriate error feedback to the user
            return render(request, 'signup.html', {'error': str(e)})
    else:
        return render(request, 'signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Replace 'dashboard' with the actual URL name of your dashboard view
        else:
            # Authentication failed, handle the error or display an error message
            pass
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('index')  # Redirect to the homepage or login page

@login_required
def dashboard(request):
    # View code for the user's dashboard
    return render(request, 'dashboard:dashboard.html')
