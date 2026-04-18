from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Student
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resources/', views.resources_list, name='resources'),
    path('resources/<int:pk>/book/', views.book_resource, name='book_resource'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('my-bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-panel/bookings/<int:pk>/', views.admin_booking_detail, name='admin_booking_detail'),
    path('admin-panel/resources/', views.admin_resources, name='admin_resources'),
    path('admin-panel/resources/add/', views.admin_resource_add, name='admin_resource_add'),
    path('admin-panel/resources/<int:pk>/edit/', views.admin_resource_edit, name='admin_resource_edit'),
    path('admin-panel/resources/<int:pk>/delete/', views.admin_resource_delete, name='admin_resource_delete'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
]