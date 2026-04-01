from django.urls import path
from . import views
from .views import TicketListCreateAPIView , TicketDetailAPIView
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
    path("api/tickets/", TicketListCreateAPIView.as_view(), name="api_tickets"),

    path(
        "api/tickets/<int:pk>/",
        TicketDetailAPIView.as_view(),
        name="api_ticket_detail"
    ),
    path("api/tickets-live/", views.tickets_api, name="tickets_live"),
    path("api/latest-ticket/", views.latest_ticket),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    # Additional API endpoints for update and delete
    path("ticket/delete/<int:ticket_id>/", views.delete_ticket, name="delete_ticket"),
    path("deleted-tickets/", views.deleted_tickets, name="deleted_tickets"),
    path("tickets/restore/<int:ticket_id>/", views.restore_ticket, name="restore_ticket"),
    path("tickets/delete-permanent/<int:ticket_id>/", views.permanent_delete_ticket, name="permanent_delete_ticket"),
    path("api/ticket-stats/", views.ticket_stats),
    path("api/activity-feed/", views.activity_feed),
    path("api/tickets-since/<str:timestamp>/", views.tickets_since),
    path("update-status/<int:ticket_id>/", views.update_status, name="update_status"),
    path("assign-ticket/<int:ticket_id>/", views.assign_ticket, name="assign_ticket"),
]

