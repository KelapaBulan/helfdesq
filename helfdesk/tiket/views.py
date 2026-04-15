from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required , user_passes_test
from .forms import TicketForm , RegisterForm
from .models import Ticket , FAQ ,TicketActivity , UserProfile, Cabang
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSerializer
from .permissions import IsAdminDeleteOnly
from django.utils import timezone
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from datetime import datetime , timedelta
from django.utils.timezone import make_aware ,localtime
from django.utils import timezone




def is_admin(user):
    return user.is_superuser


@login_required
@permission_classes([IsAuthenticated])
def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            TicketActivity.objects.create(
                ticket=ticket,
                message=f"Ticket #{ticket.id} created by {request.user.username}"
            )
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

    if request.user.is_staff:
        return redirect('admin_dashboard')

    return redirect('user_dashboard')

def test(request):
    return render(request, "test.html")

@login_required
def my_tickets(request):
    tickets = (
    Ticket.objects
    .filter(created_by=request.user, deleted_at__isnull=True)
    .select_related("assigned_to", "department")
    .order_by("-created_at")
)

    return render(request, "tiket/my_tickets.html", {
        "tickets": tickets
    })
    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):

    tickets = Ticket.objects.filter(
        deleted_at__isnull=True
    ).select_related(
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
            user = get_object_or_404(User, id=user_id)
            ticket.assigned_to = user
            msg = f"Ticket #{ticket.id} assigned to {user.username}"
        else:
            ticket.assigned_to = None
            msg = f"Ticket #{ticket.id} unassigned"

        ticket.save()
        
         
        TicketActivity.objects.create(
            ticket=ticket,
            message=f"Ticket #{ticket.id} assigned to {User.objects.get(id=user_id).username}"
        )

        return redirect("admin_dashboard")

    return render(request, "tiket/update_assignment.html", {
    "ticket": ticket,
    "staff_users": staff_users
})
    
@login_required
def user_dashboard(request):

    tickets = Ticket.objects.filter(
        created_by=request.user,
        deleted_at__isnull=True
    ).order_by("-created_at")

    faqs = FAQ.objects.all()

    return render(request, "tiket/user_dashboard.html", {
        "tickets": tickets,
        "faqs": faqs
    })
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    user_id = request.data.get("assigned_to")

    if user_id:
        user = User.objects.get(id=user_id)
        ticket.assigned_to = user

        message = f"Ticket #{ticket.id} assigned to {user.username}"
    else:
        ticket.assigned_to = None
        message = f"Ticket #{ticket.id} unassigned"

    ticket.save()

    TicketActivity.objects.create(
        ticket=ticket,
        message=message
    )

    return Response({"success": True})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    new_status = request.data.get("status")

    if new_status in dict(Ticket.Status.choices):
        ticket.status = new_status
        ticket.save()

        TicketActivity.objects.create(
            ticket=ticket,
            message=f"Ticket #{ticket.id} status changed to {ticket.status}"
        )

    return Response({"success": True})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                cabang=form.cleaned_data["cabang"]
            )
            login(request, user)
            return redirect("my_tickets")
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Ticket.objects.filter(deleted_at__isnull=True)

        if user.is_staff:
            return Ticket.objects.filter(
                assigned_to=user,
                deleted_at__isnull=True
            )

        return Ticket.objects.filter(
            created_by=user,
            deleted_at__isnull=True
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
@permission_classes([IsAuthenticated])        
class TicketDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Ticket.objects.filter(deleted_at__isnull=True)
    serializer_class = TicketSerializer
    
@login_required    
@user_passes_test(lambda u: u.is_superuser)
def delete_ticket(request, ticket_id):
    if request.method == "POST" and request.user.is_superuser:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        ticket.deleted_at = timezone.now()
        ticket.deleted_by = request.user
        ticket.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=403)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def deleted_tickets(request):

    tickets = Ticket.objects.filter(
        deleted_at__isnull=False
    ).select_related(
        "created_by", "assigned_to", "department"
    ).order_by("-deleted_at")   # newest deleted first

    return render(request, "tiket/deleted_tickets.html", {
        "tickets": tickets
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def restore_ticket(request, ticket_id):

    ticket = get_object_or_404(Ticket, id=ticket_id)

    ticket.deleted_at = None
    ticket.deleted_by = None
    ticket.save()

    return redirect("deleted_tickets")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def permanent_delete_ticket(request, ticket_id):

    ticket = get_object_or_404(Ticket, id=ticket_id)

    ticket.delete()

    return redirect("deleted_tickets")

@api_view(["GET"])
def tickets_api(request):

    tickets = Ticket.objects.filter(
        deleted_at__isnull=True
    ).order_by("-created_at")

    serializer = TicketSerializer(tickets, many=True)

    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def latest_ticket(request):

    ticket = Ticket.objects.filter(
        deleted_at__isnull=True
    ).order_by("-id").first()

    return Response({
        "latest_id": ticket.id if ticket else 0,
        "priority": ticket.priority if ticket else None
    })
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_stats(request):

    stats = Ticket.objects.filter(
        deleted_at__isnull=True
    ).values("status").annotate(count=Count("id"))

    result = {
        "OPEN": 0,
        "IN_PROGRESS": 0,
        "CLOSED": 0
    }

    for s in stats:
        result[s["status"]] = s["count"]

    return Response(result)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activity_feed(request):

    activities = TicketActivity.objects.order_by("-created_at")[:10]

    data = [
        {
            "message": a.message,
            "time": a.created_at.strftime("%H:%M")
        }
        for a in activities
    ]

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tickets_since(request, timestamp):

    try:
        timestamp = float(timestamp)
        dt = make_aware(datetime.fromtimestamp(timestamp))
        dt += timedelta(milliseconds=1)
    except Exception:
        return Response({"error": "Invalid timestamp"}, status=400)

    tickets = Ticket.objects.filter(
        created_at__gt=dt,
        deleted_at__isnull=True   # ✅ IMPORTANT (you forgot this)
    ).order_by("created_at")

    data = []

    for t in tickets:
        data.append({
    "id": t.id,
    "title": t.title,
    "description": t.description,
    "user": t.created_by.username if t.created_by else "Anonymous",
    "department": str(t.department),
    "email": t.contact_email,
    "priority": t.priority,
    "status": t.status,
    "assigned_to": t.assigned_to.username if t.assigned_to else None,
    "cabang": t.created_by.profile.cabang.name if hasattr(t.created_by, 'profile') and t.created_by.profile.cabang else None,
    "created": localtime(t.created_at).strftime("%b %d, %Y %H:%M"),
    "timestamp": t.created_at.timestamp()
})

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_updates(request):
    since = request.GET.get("since")
    qs = Ticket.objects.filter(deleted_at__isnull=True)
    if since:
        try:
            dt = make_aware(datetime.fromtimestamp(float(since)))
            qs = qs.filter(updated_at__gte=dt)
        except Exception:
            pass
    return Response(list(qs.values("id", "status", "assigned_to_id")))

@login_required
def print_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, deleted_at__isnull=True)

    # Users can only print their own tickets
    if not request.user.is_staff and ticket.created_by != request.user:
        return redirect("home")

    return render(request, "tiket/print_ticket.html", {"ticket": ticket})
