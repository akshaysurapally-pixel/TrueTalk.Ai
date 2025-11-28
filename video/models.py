
from django.db import models
from django.contrib.auth.models import User

class CallSession(models.Model):
    CALL_TYPES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ongoing', 'Ongoing'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
    ]
    
    call_id = models.CharField(max_length=100, unique=True)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='caller_sessions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver_sessions')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    room_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.call_type} call from {self.caller} to {self.receiver}"

class CallLog(models.Model):
    call_session = models.ForeignKey(CallSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)  # joined, left, etc.
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"


