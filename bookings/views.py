from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from datetime import date
import csv
from .models import Resource, Booking, StudentProfile
from .forms import StudentRegistrationForm, BookingForm, ResourceForm, BookingStatusForm, ProfileEditForm


def is_admin(user):
    return user.is_staff


# ─── Auth Views ──────────────────────────────────────────────────────────────

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
    resources = Resource.objects.filter(status='available').annotate(
        booking_count=Count('bookings')
    )
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
    today = date.today().strftime('%Y-%m-%d')
    return render(request, 'student/book_resource.html', {
        'form': form,
        'resource': resource,
        'today': today,
    })

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
    rejected_bookings = Booking.objects.filter(status='rejected').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    recent_bookings = Booking.objects.all()[:10]
    resource_usage = Resource.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:5]

    # Chart data — bookings per resource type
    lab_count = Booking.objects.filter(resource__resource_type='lab').count()
    equipment_count = Booking.objects.filter(resource__resource_type='equipment').count()
    room_count = Booking.objects.filter(resource__resource_type='room').count()

    return render(request, 'admin_panel/dashboard.html', {
        'total_resources': total_resources,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'rejected_bookings': rejected_bookings,
        'cancelled_bookings': cancelled_bookings,
        'recent_bookings': recent_bookings,
        'resource_usage': resource_usage,
        'lab_count': lab_count,
        'equipment_count': equipment_count,
        'room_count': room_count,
    })


@login_required
@user_passes_test(is_admin)
def admin_bookings(request):
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    bookings = Booking.objects.all()
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if search:
        bookings = bookings.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(resource__name__icontains=search)
        )
    # Pagination — 10 per page
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_panel/bookings.html', {
        'bookings': page_obj,
        'status_filter': status_filter,
        'search': search,
        'page_obj': page_obj,
    })


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
    resources = Resource.objects.annotate(
        booking_count=Count('bookings'),
        approved_count=Count('bookings', filter=Q(bookings__status='approved')),
        pending_count=Count('bookings', filter=Q(bookings__status='pending')),
    )
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
    # Date filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Query all bookings and apply date filters
    bookings_qs = Booking.objects.all()
    if date_from:
        bookings_qs = bookings_qs.filter(date__gte=date_from)
    if date_to:
        bookings_qs = bookings_qs.filter(date__lte=date_to)

    # Calculate Resource Usage Summary
    resource_usage = Resource.objects.annotate(
        total_bookings=Count('bookings', filter=Q(bookings__in=bookings_qs)),
        approved_bookings=Count('bookings', filter=Q(bookings__in=bookings_qs, bookings__status='approved')),
        pending_bookings=Count('bookings', filter=Q(bookings__in=bookings_qs, bookings__status='pending')),
        rejected_bookings=Count('bookings', filter=Q(bookings__in=bookings_qs, bookings__status='rejected')),
    )

    monthly_bookings = bookings_qs.values('date__month', 'date__year').annotate(
        count=Count('id')
    ).order_by('date__year', 'date__month')

    total_stats = {
        'total': bookings_qs.count(),
        'approved': bookings_qs.filter(status='approved').count(),
        'pending': bookings_qs.filter(status='pending').count(),
        'rejected': bookings_qs.filter(status='rejected').count(),
        'cancelled': bookings_qs.filter(status='cancelled').count(),
    }

    return render(request, 'admin_panel/reports.html', {
        'resource_usage': resource_usage,
        'monthly_bookings': monthly_bookings,
        'total_stats': total_stats,
        'date_from': date_from,
        'date_to': date_to,
        'bookings': bookings_qs, # Pass the filtered bookings list
    })

@login_required
@user_passes_test(is_admin)
def admin_reports_export_csv(request):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    bookings = Booking.objects.all()
    if date_from:
        bookings = bookings.filter(date__gte=date_from)
    if date_to:
        bookings = bookings.filter(date__lte=date_to)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Student ID', 'Resource', 'Type', 'Location', 'Date', 'Start Time', 'End Time', 'Purpose', 'Status'])

    for b in bookings:
        try:
            student_id = b.user.profile.student_id
        except Exception:
            student_id = 'N/A'
        writer.writerow([
            b.user.get_full_name() or b.user.username,
            student_id,
            b.resource.name,
            b.resource.get_resource_type_display(),
            b.resource.location,
            b.date,
            b.start_time.strftime('%H:%M'),
            b.end_time.strftime('%H:%M'),
            b.purpose,
            b.get_status_display(),
        ])

    return response


@login_required
@user_passes_test(is_admin)
def admin_students(request):
    from django.contrib.auth.models import User
    search = request.GET.get('search', '')
    students = User.objects.filter(is_staff=False).annotate(
        total_bookings=Count('bookings'),
        approved_bookings=Count('bookings', filter=Q(bookings__status='approved')),
    )
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_panel/students.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'search': search,
    })