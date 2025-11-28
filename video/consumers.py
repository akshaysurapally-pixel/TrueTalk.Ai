import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import CallSession, CallLog

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'call_initiate':
            await self.handle_call_initiate(data)
        elif message_type == 'call_answer':
            await self.handle_call_answer(data)
        elif message_type == 'call_reject':
            await self.handle_call_reject(data)
        elif message_type == 'call_end':
            await self.handle_call_end(data)
        elif message_type == 'webrtc_offer':
            await self.handle_webrtc_offer(data)
        elif message_type == 'webrtc_answer':
            await self.handle_webrtc_answer(data)
        elif message_type == 'ice_candidate':
            await self.handle_ice_candidate(data)
        elif message_type == 'join_room':
            await self.handle_join_room(data)

    async def handle_call_initiate(self, data):
        call_id = str(uuid.uuid4())
        receiver_id = data['receiver_id']
        call_type = data['call_type']
        room_name = data.get('room_name', f"room_{call_id}")
        
        # Create call session
        call_session = await self.create_call_session(
            call_id, self.user.id, receiver_id, call_type, room_name
        )
        
        # Send call invitation to receiver
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                'type': 'call_invitation',
                'call_id': call_id,
                'caller': self.user.username,
                'caller_id': self.user.id,
                'call_type': call_type,
                'room_name': room_name,
            }
        )

    async def handle_call_answer(self, data):
        call_id = data['call_id']
        call_session = await self.get_call_session(call_id)
        
        if call_session:
            await self.update_call_session_status(call_id, 'ongoing')
            
            # Notify caller that call was answered
            await self.channel_layer.group_send(
                f"user_{call_session.caller.id}",
                {
                    'type': 'call_answered',
                    'call_id': call_id,
                }
            )

    async def handle_call_reject(self, data):
        call_id = data['call_id']
        call_session = await self.get_call_session(call_id)
        
        if call_session:
            await self.update_call_session_status(call_id, 'ended')
            
            # Notify caller that call was rejected
            await self.channel_layer.group_send(
                f"user_{call_session.caller.id}",
                {
                    'type': 'call_rejected',
                    'call_id': call_id,
                }
            )

    async def handle_call_end(self, data):
        call_id = data['call_id']
        call_session = await self.get_call_session(call_id)
        
        if call_session:
            await self.update_call_session_status(call_id, 'ended')
            
            # Notify both users that call ended
            await self.channel_layer.group_send(
                f"user_{call_session.caller.id}",
                {
                    'type': 'call_ended',
                    'call_id': call_id,
                }
            )
            await self.channel_layer.group_send(
                f"user_{call_session.receiver.id}",
                {
                    'type': 'call_ended',
                    'call_id': call_id,
                }
            )

    async def handle_webrtc_offer(self, data):
        receiver_id = data['receiver_id']
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'call_id': data['call_id'],
            }
        )

    async def handle_webrtc_answer(self, data):
        receiver_id = data['receiver_id']
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'call_id': data['call_id'],
            }
        )

    async def handle_ice_candidate(self, data):
        receiver_id = data['receiver_id']
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                'type': 'ice_candidate',
                'candidate': data['candidate'],
                'call_id': data['call_id'],
            }
        )

    async def handle_join_room(self, data):
        room_name = data['room_name']
        await self.channel_layer.group_add(
            room_name,
            self.channel_name
        )

    # WebSocket event handlers
    async def call_invitation(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_invitation',
            'call_id': event['call_id'],
            'caller': event['caller'],
            'caller_id': event['caller_id'],
            'call_type': event['call_type'],
            'room_name': event['room_name'],
        }))

    async def call_answered(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_answered',
            'call_id': event['call_id'],
        }))

    async def call_rejected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_rejected',
            'call_id': event['call_id'],
        }))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'call_id': event['call_id'],
        }))

    async def webrtc_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'webrtc_offer',
            'offer': event['offer'],
            'call_id': event['call_id'],
        }))

    async def webrtc_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'webrtc_answer',
            'answer': event['answer'],
            'call_id': event['call_id'],
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate'],
            'call_id': event['call_id'],
        }))

    @database_sync_to_async
    def create_call_session(self, call_id, caller_id, receiver_id, call_type, room_name):
        return CallSession.objects.create(
            call_id=call_id,
            caller_id=caller_id,
            receiver_id=receiver_id,
            call_type=call_type,
            room_name=room_name,
            status='initiated'
        )

    @database_sync_to_async
    def get_call_session(self, call_id):
        try:
            return CallSession.objects.get(call_id=call_id)
        except CallSession.DoesNotExist:
            return None

    @database_sync_to_async
    def update_call_session_status(self, call_id, status):
        CallSession.objects.filter(call_id=call_id).update(status=status)

    @database_sync_to_async
    def create_call_log(self, call_session, user, action):
        return CallLog.objects.create(
            call_session=call_session,
            user=user,
            action=action
        )
