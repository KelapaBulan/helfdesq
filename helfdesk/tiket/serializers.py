from rest_framework import serializers
from .models import Ticket , User   

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class TicketSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    assigned_to = serializers.StringRelatedField()
    department = serializers.StringRelatedField()

    class Meta:
        model = Ticket
        fields = '__all__'
