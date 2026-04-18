from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date
from .models import Resource, Booking, StudentProfile
from .forms import StudentRegistrationForm, BookingForm, ResourceForm, BookingStatusForm, ProfileEditForm


def is_admin(user):
    return user.is_staff


# ─── Auth Views ─────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome!')
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Student Views ────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    my_bookings = Booking.objects.filter(user=request.user)
    resources = Resource.objects.filter(status='available')
    today = date.today()
    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        date__gte=today,
        status='approved'
    ).order_by('date', 'start_time')[:5]
    stats = {
        'total': my_bookings.count(),
        'pending': my_bookings.filter(status='pending').count(),
        'approved': my_bookings.filter(status='approved').count(),
        'rejected': my_bookings.filter(status='rejected').count(),
    }
    return render(request, 'student/dashboard.html', {
        'my_bookings': my_bookings[:5],
        'resources': resources,
        'stats': stats,
        'upcoming_bookings': upcoming_bookings,
    })


@login_required
def resources_list(request):
    resource_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    resources = Resource.objects.filter(status='available')
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if search:
        resources = resources.filter(
            Q(name__icontains=search) |
            Q(location__icontains=search) |
            Q(description__icontains=search)
        )
    return render(request, 'student/resources.html', {
        'resources': resources,
        'selected_type': resource_type,
        'search': search,
    })


@login_required
def book_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.resource = resource
            booking.save()
            messages.success(request, 'Booking request submitted successfully!')
            return redirect('my_bookings')
        else:
            print("Form errors:", form.errors)
    else:
        form = BookingForm()
    return render(request, 'student/book_resource.html', {'form': form, 'resource': resource})


@login_required
def my_bookings(request):
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    bookings = Booking.objects.filter(user=request.user)
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if search:
        bookings = bookings.filter(
            Q(resource__name__icontains=search) |
            Q(purpose__icontains=search)
        )
    return render(request, 'student/my_bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'student/booking_detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled.')
    else:
        messages.error(request, 'Only pending bookings can be cancelled.')
    return redirect('my_bookings')


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except StudentProfile.DoesNotExist:
        profile = StudentProfile.objects.create(user=request.user, student_id='N/A', faculty='N/A')
    bookings = Booking.objects.filter(user=request.user)
    stats = {
        'total': bookings.count(),
        'approved': bookings.filter(status='approved').count(),
        'pending': bookings.filter(status='pending').count(),
    }
    return render(request, 'student/profile.html', {'profile': profile, 'stats': stats})


@login_required
def profile_edit(request):
    try:
        profile = request.user.profile
    except StudentProfile.DoesNotExist:
        profile = StudentProfile.objects.create(user=request.user, student_id='N/A', faculty='N/A')
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    return render(request, 'student/profile_edit.html', {'form': form})


# ─── Admin Views ─────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_resources = Resource.objects.count()
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    approved_bookings = Booking.objects.filter(status='approved').count()
    recent_bookings = Booking.objects.all()[:10]
    resource_usage = Resource.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:5]
    return render(request, 'admin_panel/dashboard.html', {
        'total_resources': total_resources,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'recent_bookings': recent_bookings,
        'resource_usage': resource_usage,
    })


@login_required
@user_passes_test(is_admin)
def admin_bookings(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.all()
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    return render(request, 'admin_panel/bookings.html', {'bookings': bookings, 'status_filter': status_filter})


@login_required
@user_passes_test(is_admin)
def admin_booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingStatusForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking status updated.')
            return redirect('admin_bookings')
    else:
        form = BookingStatusForm(instance=booking)
    return render(request, 'admin_panel/booking_detail.html', {'booking': booking, 'form': form})


@login_required
@user_passes_test(is_admin)
def admin_resources(request):
    resources = Resource.objects.all()
    return render(request, 'admin_panel/resources.html', {'resources': resources})


@login_required
@user_passes_test(is_admin)
def admin_resource_add(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource added successfully!')
            return redirect('admin_resources')
    else:
        form = ResourceForm()
    return render(request, 'admin_panel/resource_form.html', {'form': form, 'action': 'Add'})


@login_required
@user_passes_test(is_admin)
def admin_resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('admin_resources')
    else:
        form = ResourceForm(instance=resource)
    return render(request, 'admin_panel/resource_form.html', {'form': form, 'action': 'Edit'})


@login_required
@user_passes_test(is_admin)
def admin_resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        resource.delete()
        messages.success(request, 'Resource deleted.')
        return redirect('admin_resources')
    return render(request, 'admin_panel/resource_confirm_delete.html', {'resource': resource})


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    from django.db.models import Q as DQ
    resource_usage = Resource.objects.annotate(
        total_bookings=Count('bookings'),
        approved_bookings=Count('bookings', filter=DQ(bookings__status='approved')),
    )
    monthly_bookings = Booking.objects.values('date__month', 'date__year').annotate(
        count=Count('id')
    ).order_by('date__year', 'date__month')
    return render(request, 'admin_panel/reports.html', {
        'resource_usage': resource_usage,
        'monthly_bookings': monthly_bookings,
    })