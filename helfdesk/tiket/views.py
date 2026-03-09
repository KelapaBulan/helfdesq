from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required , user_passes_test
from .forms import TicketForm , RegisterForm
from .models import Ticket
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import generics, permissions
from .serializers import TicketSerializer


def is_admin(user):
    return user.is_superuser


@login_required
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, "Ticket submitted successfully!")
            if request.user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('my_tickets')
    else:
        form = TicketForm()

    return render(request, 'tiket/create_ticket.html', {'form': form})


def ticket_success(request):
    return render(request, 'tiket/ticket_success.html')

@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_staff:
        return redirect('admin_dashboard')

    return redirect('user_dashboard')

def test(request):
    return render(request, "test.html")

@login_required
def my_tickets(request):
    tickets = (
        Ticket.objects
        .filter(created_by=request.user)
        .select_related("assigned_to", "department")
        .order_by("-created_at")
    )

    return render(request, "tiket/my_tickets.html", {
        "tickets": tickets
    })
    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    tickets = Ticket.objects.select_related(
        "created_by", "assigned_to", "department"
    ).order_by("-created_at")

    staff_users = User.objects.filter(is_staff=True)

    return render(request, "tiket/admin_dashboard.html", {
        "tickets": tickets,
        "staff_users": staff_users,
        "status_choices": Ticket.Status.choices
    })
    
@user_passes_test(is_admin)
def update_assignment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Only staff users
    staff_users = User.objects.filter(is_staff=True)

    if request.method == "POST":
        user_id = request.POST.get("assigned_to")

        if user_id:
            ticket.assigned_to_id = user_id
        else:
            ticket.assigned_to = None

        ticket.save()
        return redirect("admin_dashboard")

    return render(request, "tiket/update_assignment.html", {
    "ticket": ticket,
    "staff_users": staff_users
})
    
@login_required
def user_dashboard(request):
    tickets = Ticket.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    return render(request, "tiket/user_dashboard.html", {
        "tickets": tickets
    })    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def assign_ticket(request, ticket_id):
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, id=ticket_id)

        user_id = request.POST.get("assigned_to")

        if user_id:
            ticket.assigned_to_id = user_id
        else:
            ticket.assigned_to = None

        ticket.save()

    return redirect("admin_dashboard")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_status(request, ticket_id):
    if request.method == "POST":
        ticket = get_object_or_404(Ticket, id=ticket_id)

        new_status = request.POST.get("status")

        if new_status in dict(Ticket.Status.choices):
            ticket.status = new_status
            ticket.save()

    return redirect("admin_dashboard")

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto login after register
            return redirect("my_tickets")  # or homepage
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})
# Create your views here.

@csrf_exempt
def create_ticket_api(request):
    if request.method == "POST":
        data = json.loads(request.body)

        ticket = Ticket.objects.create(
            title=data.get("title"),
            description=data.get("description"),
            department=data.get("department"),
            priority=data.get("priority"),
            created_by=request.user  # or remove auth for testing
        )

        return JsonResponse({
            "status": "success",
            "ticket_id": ticket.id
        })

    return JsonResponse({"error": "Invalid method"}, status=400)

class TicketListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        user = self.request.user

        # Admin → see everything
        if user.is_superuser:
            return Ticket.objects.all()

        # Staff → see tickets assigned to them
        if user.is_staff:
            return Ticket.objects.filter(assigned_to=user)

        # Normal user → see only their own tickets
        return Ticket.objects.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)