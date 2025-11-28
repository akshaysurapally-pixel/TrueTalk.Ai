
from rest_framework import serializers
from .models import CallSession, CallLog
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CallSessionSerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = CallSession
        fields = '__all__'

class CallLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CallLog
        fields = '__all__'

class CallInitiateSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    call_type = serializers.ChoiceField(choices=['audio', 'video'])
    room_name = serializers.CharField(max_length=255, required=False)

