
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CallSession, CallLog
from .serializers import CallSessionSerializer, CallLogSerializer, CallInitiateSerializer

class CallSessionViewSet(viewsets.ModelViewSet):
    queryset = CallSession.objects.all()
    serializer_class = CallSessionSerializer

    def get_queryset(self):
        user = self.request.user
        return CallSession.objects.filter(caller=user) | CallSession.objects.filter(receiver=user)

    @action(detail=False, methods=['post'])
    def initiate_call(self, request):
        serializer = CallInitiateSerializer(data=request.data)
        if serializer.is_valid():
            # The actual call initiation happens through WebSocket
            return Response({
                'message': 'Call initiation request received',
                'receiver_id': serializer.validated_data['receiver_id'],
                'call_type': serializer.validated_data['call_type']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CallLogSerializer

    def get_queryset(self):
        user = self.request.user
        return CallLog.objects.filter(user=user)
