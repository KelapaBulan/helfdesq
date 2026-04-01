from django.contrib import admin
from .models import Ticket, Department
from .models import FAQ


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order")
    ordering = ("order",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'status',
        'priority',
        'department',
        'created_by',
        'assigned_to',
        'created_at',
    )

    list_filter = (
        'status',
        'priority',
        'department',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'created_by__username',
        'assigned_to__username',
    )

    autocomplete_fields = ('created_by', 'assigned_to')
