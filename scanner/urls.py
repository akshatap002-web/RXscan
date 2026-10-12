from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="scanner/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload/", views.upload, name="upload"),
    path("history/", views.history, name="history"),
    path("result/<int:pk>/", views.result, name="result"),
    path("result/<int:pk>/request-review/", views.request_review, name="request_review"),
    path("medicines/", views.medicines, name="medicines"),
    path("medicines/<int:pk>/", views.medicine_detail, name="medicine_detail"),
    path("pharmacist/", views.pharmacist_dashboard, name="pharmacist_dashboard"),
    path("pharmacist/review/<int:pk>/", views.review, name="review"),
]
