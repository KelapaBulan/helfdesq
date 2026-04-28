from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required , user_passes_test
from .forms import TicketForm , RegisterForm
from .models import Ticket , FAQ ,TicketActivity , UserProfile, Cabang , Department
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
from django.utils.timezone import make_aware ,localtime , now
from django.utils import timezone
from django.core.mail import send_mail
from .models import Ticket, FAQ, TicketActivity, UserProfile, Cabang, TicketComment, TicketAttachment
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate , login as auth_login




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
        .prefetch_related("comments__author", "attachments")
        .order_by("-created_at")
    )
    return render(request, "tiket/my_tickets.html", {"tickets": tickets})
    
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    if request.user.is_superuser:
        # Superuser sees everything
        tickets = Ticket.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            "created_by", "assigned_to", "department"
        ).order_by("-created_at")
    else:
        # Staff sees only tickets from their assigned departments
        try:
            staff_departments = request.user.profile.departments.all()
        except UserProfile.DoesNotExist:
            staff_departments = Department.objects.none()

        tickets = Ticket.objects.filter(
            deleted_at__isnull=True,
            department__in=staff_departments
        ).select_related(
            "created_by", "assigned_to", "department"
        ).order_by("-created_at")

    staff_users = User.objects.filter(is_staff=True)

    return render(request, "tiket/admin_dashboard.html", {
        "tickets": tickets,
        "staff_users": staff_users,
        "status_choices": Ticket.Status.choices,
        "is_superuser": request.user.is_superuser,
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

    # Recent activity on the user's tickets
    recent_activity = TicketActivity.objects.filter(
        ticket__created_by=request.user,
        ticket__deleted_at__isnull=True
    ).select_related("ticket").order_by("-created_at")[:10]

    return render(request, "tiket/user_dashboard.html", {
        "tickets": tickets,
        "faqs": faqs,
        "recent_activity": recent_activity,
    })
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_ticket(request, ticket_id):
    if not request.user.is_superuser:
        return Response({"success": False, "error": "Not authorized"}, status=403)

    ticket = get_object_or_404(Ticket, id=ticket_id)
    user_id = request.data.get("assigned_to")

    if user_id:
        user = User.objects.get(id=user_id)
        ticket.assigned_to = user
        message = f"Ticket #{ticket.id} assigned to {user.username}"
        send_ticket_email(
            subject=f"[Ticket #{ticket.id}] Assigned to you — {ticket.title}",
            message=f"You have been assigned to ticket #{ticket.id}: {ticket.title}.",
            recipient_email=user.email
        )
        send_ticket_email(
            subject=f"[Ticket #{ticket.id}] Your ticket has been assigned",
            message=f"Your ticket '{ticket.title}' has been assigned to {user.username}.",
            recipient_email=ticket.contact_email or ticket.created_by.email
        )
    else:
        ticket.assigned_to = None
        message = f"Ticket #{ticket.id} unassigned"

    ticket.save()
    TicketActivity.objects.create(ticket=ticket, message=message)
    return Response({"success": True})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    new_status = request.data.get("status")

    if new_status in dict(Ticket.Status.choices):
        ticket.status = new_status

        if new_status == "RESOLVED":
            ticket.resolved_at = timezone.now()
        else:
            ticket.resolved_at = None

        ticket.save()  # ← always save

        TicketActivity.objects.create(
            ticket=ticket,
            message=f"Ticket #{ticket.id} status changed to {ticket.status}"
        )

        send_ticket_email(
            subject=f"[Ticket #{ticket.id}] Status updated — {ticket.title}",
            message=f"Your ticket '{ticket.title}' status has been updated to: {new_status}.",
            recipient_email=ticket.contact_email or ticket.created_by.email
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
            if user.is_staff:
                return redirect("admin_dashboard")
            return redirect("user_dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
# Create your views here.

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # Remember Me — extend session to 30 days if checked
            if request.POST.get('remember_me'):
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)  # expires on browser close

            return redirect('home')
    else:
        form = AuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})

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
@user_passes_test(lambda u: u.is_staff)
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
    qs = Ticket.objects.filter(deleted_at__isnull=True)

    if not request.user.is_superuser and request.user.is_staff:
        try:
            staff_departments = request.user.profile.departments.all()
            qs = qs.filter(department__in=staff_departments)
        except UserProfile.DoesNotExist:
            qs = qs.none()

    stats = qs.values("status").annotate(count=Count("id"))

    result = {"OPEN": 0, "IN_PROGRESS": 0, "CLOSED": 0}
    for s in stats:
        result[s["status"]] = s["count"]

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activity_feed(request):
    qs = TicketActivity.objects.order_by("-created_at")

    if not request.user.is_superuser and request.user.is_staff:
        try:
            staff_departments = request.user.profile.departments.all()
            qs = qs.filter(ticket__department__in=staff_departments)
        except UserProfile.DoesNotExist:
            qs = qs.none()

    activities = qs[:10]

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

def send_ticket_email(subject, message, recipient_email):
    if recipient_email:
        try:
            send_mail(
                subject,
                message,
                None,  # uses DEFAULT_FROM_EMAIL from settings
                [recipient_email],
                fail_silently=True
            )
        except Exception as e:
            print(f"Email error: {e}")


# ==============================
# ADD COMMENT
# ==============================
@login_required
def add_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, deleted_at__isnull=True)

    # Only ticket owner or staff can comment
    if not request.user.is_staff and ticket.created_by != request.user:
        return redirect("home")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            TicketComment.objects.create(
                ticket=ticket,
                author=request.user,
                body=body
            )
            TicketActivity.objects.create(
                ticket=ticket,
                message=f"Comment added by {request.user.username} on Ticket #{ticket.id}"
            )

            # Notify the other party by email
            if request.user == ticket.created_by:
                # User commented — notify assigned staff
                recipient = ticket.assigned_to.email if ticket.assigned_to else None
            else:
                # Staff commented — notify ticket owner
                recipient = ticket.contact_email or ticket.created_by.email

            send_ticket_email(
                subject=f"[Ticket #{ticket.id}] New comment — {ticket.title}",
                message=f"{request.user.username} added a comment:\n\n{body}\n\nTicket: {ticket.title}",
                recipient_email=recipient
            )

    if request.user.is_staff:
        return redirect("admin_dashboard")
    return redirect("my_tickets")


# ==============================
# ADD ATTACHMENT
# ==============================
@login_required
def add_attachment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, deleted_at__isnull=True)

    if not request.user.is_staff and ticket.created_by != request.user:
        return redirect("home")

    if request.method == "POST" and request.FILES.get("file"):
        TicketAttachment.objects.create(
            ticket=ticket,
            uploaded_by=request.user,
            file=request.FILES["file"]
        )
        TicketActivity.objects.create(
            ticket=ticket,
            message=f"Attachment uploaded by {request.user.username} on Ticket #{ticket.id}"
        )

    if request.user.is_staff:
        return redirect("ticket_detail", ticket_id=ticket.id)
    return redirect("my_tickets")


# ==============================
# CANCEL TICKET (user only)
# ==============================
@login_required
def cancel_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, deleted_at__isnull=True)

    # Only the ticket owner can cancel, and only if not already closed/resolved
    if ticket.created_by != request.user:
        return redirect("home")

    if ticket.status in ["CLOSED", "RESOLVED"]:
        messages.error(request, "This ticket cannot be cancelled.")
        return redirect("my_tickets")

    if request.method == "POST":
        ticket.status = "CLOSED"
        ticket.save()

        TicketActivity.objects.create(
            ticket=ticket,
            message=f"Ticket #{ticket.id} cancelled by {request.user.username}"
        )

        send_ticket_email(
            subject=f"[Ticket #{ticket.id}] Cancelled — {ticket.title}",
            message=f"Ticket #{ticket.id} '{ticket.title}' has been cancelled by {request.user.username}.",
            recipient_email=ticket.assigned_to.email if ticket.assigned_to else None
        )

        messages.success(request, "Ticket cancelled successfully.")

    return redirect("my_tickets")

@api_view(["GET"])
def ticket_volume(request):
    days = int(request.GET.get("days", 7))
    data = []
    for i in range(days):
        day = now().date() - timedelta(days=i)
        count = Ticket.objects.filter(created_at__date=day).count()
        data.append({"date": day.strftime("%Y-%m-%d"), "count": count})
    return Response(list(reversed(data)))


# 2. Tickets per department
@api_view(["GET"])
def tickets_per_department(request):
    data = Ticket.objects.values("department__name").annotate(count=Count("id"))
    return Response([{"department": d["department__name"], "count": d["count"]} for d in data])


# 3. Avg resolution time (in hours)
@api_view(["GET"])
def avg_resolution_time(request):
    resolved = Ticket.objects.filter(resolved_at__isnull=False)

    duration = ExpressionWrapper(
        F("resolved_at") - F("created_at"),
        output_field=DurationField()
    )

    avg = resolved.annotate(duration=duration).aggregate(avg=Avg("duration"))

    hours = avg["avg"].total_seconds() / 3600 if avg["avg"] else 0

    return Response({"avg_hours": round(hours, 2)})

def analytics_page(request):
    return render(request, "tiket/analytics.html")

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        Ticket.objects.select_related(
            "created_by", "assigned_to", "department",
            "created_by__profile__cabang"
        ).prefetch_related(
            "comments__author",
            "attachments__uploaded_by",
            "ticketactivity_set"
        ),
        id=ticket_id,
        deleted_at__isnull=True
    )

    # Access control
    if not request.user.is_superuser:
        if request.user.is_staff:
            try:
                staff_departments = request.user.profile.departments.all()
            except UserProfile.DoesNotExist:
                staff_departments = []
            if ticket.department not in staff_departments:
                return redirect("admin_dashboard")
        elif ticket.created_by != request.user:
            return redirect("home")

    staff_users = User.objects.filter(is_staff=True)

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            TicketComment.objects.create(
                ticket=ticket,
                author=request.user,
                body=body
            )
            TicketActivity.objects.create(
                ticket=ticket,
                message=f"Comment added by {request.user.username} on Ticket #{ticket.id}"
            )
            send_ticket_email(
                subject=f"[Ticket #{ticket.id}] New comment — {ticket.title}",
                message=f"{request.user.username} added a comment:\n\n{body}\n\nTicket: {ticket.title}",
                recipient_email=ticket.contact_email or ticket.created_by.email
            )
            return redirect("ticket_detail", ticket_id=ticket.id)

    return render(request, "tiket/ticket_detail.html", {
        "ticket": ticket,
        "staff_users": staff_users,
        "status_choices": Ticket.Status.choices,
        "comments": ticket.comments.order_by("created_at"),
        "attachments": ticket.attachments.order_by("uploaded_at"),
        "activities": ticket.ticketactivity_set.order_by("-created_at")[:20],
    })
    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_staff_departments(request):
    staff_users = User.objects.filter(is_staff=True).prefetch_related(
        "profile__departments"
    )
    departments = Department.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        dept_ids = request.POST.getlist("departments")
        user = get_object_or_404(User, id=user_id)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.departments.set(dept_ids)
        messages.success(request, f"Departments updated for {user.username}.")
        return redirect("manage_staff_departments")

    return render(request, "tiket/manage_staff_departments.html", {
        "staff_users": staff_users,
        "departments": departments,
    })