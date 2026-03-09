from django.urls import path
from . import views
from .views import TicketListCreateAPIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('success/', views.ticket_success, name='ticket_success'),
    path('my/', views.my_tickets, name='my_tickets'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path(
    "tickets/assign/<int:ticket_id>/",
    views.update_assignment,
    name="update_assignment"
    ),
    path("tickets/assign/<int:ticket_id>/",
     views.assign_ticket,
     name="assign_ticket"),
    path("tickets/status/<int:ticket_id>/",
     views.update_status,
     name="update_status"),
    path("register/", views.register, name="register"),
    path('api/create-ticket/', views.create_ticket_api),
    path('api/tickets/', TicketListCreateAPIView.as_view()),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]

