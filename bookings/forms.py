from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Booking, Resource, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    student_id = forms.CharField(max_length=20, required=True, label="Student ID")
    faculty = forms.CharField(max_length=200, required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                faculty=self.cleaned_data['faculty'],
                phone=self.cleaned_data.get('phone', ''),
            )
        return user


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['date', 'start_time', 'end_time', 'purpose']  # removed 'resource'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'resource_type', 'description', 'location', 'capacity', 'status', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['status', 'admin_note']
        widgets = {
            'admin_note': forms.Textarea(attrs={'rows': 3}),
        }