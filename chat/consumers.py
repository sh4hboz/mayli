"""
chat/consumers.py — BOSQICH 2.1

ChatConsumer:    mijoz suhbat oynasi (visitor UUID guruh)
SupportConsumer: xodimlar paneli (barcha yangi xabar/suhbatni real-time ko'radi)

Oqim:
  Mijoz yozadi → saqlanadi → visitor guruhiga echo + support_room broadcast + Telegram
  Admin (dashboard) javob beradi → saqlanadi → visitor guruhiga push + support_room echo
"""

import json
import uuid as uuid_module
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Mijoz suhbat oynasi WebSocket consumer.
    URL: ws/chat/<visitor_id>/
    """

    async def connect(self):
        visitor_id_str = self.scope['url_route']['kwargs'].get('visitor_id', '')
        try:
            self.visitor_id = uuid_module.UUID(visitor_id_str)
        except ValueError:
            await self.close()
            return

        # WS Auth: query_string'dan token olib tekshiramiz
        from urllib.parse import parse_qs
        from django.core.signing import TimestampSigner, BadSignature
        
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.close()
            return

        signer = TimestampSigner()
        try:
            # 24 soatlik token muddati tekshiruvi (86400 soniya)
            signed_visitor_id = signer.unsign(token, max_age=86400)
            if signed_visitor_id != visitor_id_str:
                await self.close()
                return
        except BadSignature:
            await self.close()
            return

        self.room_group = f"chat_{self.visitor_id}"
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Suhbatni olish yoki yaratish
        self.conversation_id = await self.get_or_create_conversation()

        # Xabarlar tarixini yuklash va yuborish
        history = await self.get_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': history,
        }))

        # Support guruhiga visitor ulandi xabari
        await self.channel_layer.group_send('support_room', {
            'type': 'visitor_connected',
            'visitor_id': str(self.visitor_id),
            'conversation_id': self.conversation_id,
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            # Rate limiting tekshiruvi
            is_allowed = await self.check_rate_limit()
            if not is_allowed:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Juda ko\'p xabar yuborildi. Iltimos, bir oz kuting.',
                }))
                return

            # Input sanitization (XSS himoyasi)
            from django.utils.html import escape
            text = escape(data.get('message', '').strip())
            if not text:
                return

            msg_data = await self.save_visitor_message(text)
            visitor_name = await self.get_visitor_name()

            # Visitor guruhiga echo (UI ga ko'rsatish uchun)
            await self.channel_layer.group_send(self.room_group, {
                'type': 'chat_message',
                'sender': 'visitor',
                'message': text,
                'time': msg_data['time'],
            })

            # Support guruhiga broadcast
            await self.channel_layer.group_send('support_room', {
                'type': 'new_visitor_message',
                'visitor_id': str(self.visitor_id),
                'conversation_id': self.conversation_id,
                'visitor_name': visitor_name,
                'message': text,
                'time': msg_data['time'],
            })

            # Telegram bildirishnoma (fire-and-forget)
            asyncio.ensure_future(self._notify_telegram(visitor_name, text))

        elif msg_type == 'identify':
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            lang = data.get('language', 'uz')
            await self.update_visitor_info(name, phone, lang)

    async def chat_message(self, event):
        """Guruhdan xabar keldi → client'ga yuborish."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'sender': event.get('sender', 'visitor'),
            'message': event.get('message', ''),
            'time': event.get('time', ''),
        }))

    # --- Async DB operatsiyalari ---

    @database_sync_to_async
    def get_or_create_conversation(self):
        from chat.models import ChatConversation
        conv, _ = ChatConversation.objects.get_or_create(
            visitor_id=self.visitor_id,
            defaults={'language': 'uz'},
        )
        return conv.id

    @database_sync_to_async
    def get_history(self):
        from chat.models import ChatMessage
        msgs = list(
            ChatMessage.objects
            .filter(conversation_id=self.conversation_id)
            .order_by('-created_at')[:50]
        )
        msgs.reverse()
        return [
            {
                'sender': m.sender_type,
                'message': m.text,
                'time': m.created_at.strftime('%H:%M'),
            }
            for m in msgs
        ]

    @database_sync_to_async
    def save_visitor_message(self, text):
        from chat.models import ChatConversation, ChatMessage, SenderType, ViaChannel
        conv = ChatConversation.objects.get(id=self.conversation_id)
        msg = ChatMessage.objects.create(
            conversation=conv,
            sender_type=SenderType.VISITOR,
            via=ViaChannel.WEB,
            text=text,
        )
        conv.last_message_at = timezone.now()
        conv.save(update_fields=['last_message_at'])
        return {'time': msg.created_at.strftime('%H:%M')}

    @database_sync_to_async
    def get_visitor_name(self):
        from chat.models import ChatConversation
        try:
            conv = ChatConversation.objects.get(id=self.conversation_id)
            return conv.display_name
        except ChatConversation.DoesNotExist:
            return 'Mehmon'

    @database_sync_to_async
    def update_visitor_info(self, name, phone, lang):
        from chat.models import ChatConversation
        update_data = {}
        if name:
            update_data['visitor_name'] = name
        if phone:
            update_data['visitor_phone'] = phone
        if lang in ('uz', 'ru', 'en'):
            update_data['language'] = lang
        if update_data:
            ChatConversation.objects.filter(id=self.conversation_id).update(**update_data)

    async def _notify_telegram(self, visitor_name, text):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_notify_telegram, visitor_name, text)

    def _sync_notify_telegram(self, visitor_name, text):
        from notifications.telegram import notify_chat_message_to_topic
        try:
            notify_chat_message_to_topic(
                conversation_id=self.conversation_id,
                visitor_name=visitor_name,
                language=self._get_conv_language(),
                text=text,
            )
        except Exception:
            pass

    def _get_conv_language(self) -> str:
        from chat.models import ChatConversation
        try:
            return ChatConversation.objects.values_list(
                'language', flat=True
            ).get(id=self.conversation_id)
        except Exception:
            return 'uz'

    async def check_rate_limit(self):
        from django.core.cache import cache
        import time
        
        visitor_id_str = str(self.visitor_id)
        cache_key = f"chat_limit_{visitor_id_str}"
        now = time.time()
        
        @database_sync_to_async
        def _check():
            history = cache.get(cache_key, [])
            history = [t for t in history if now - t < 10]
            if len(history) >= 5:
                return False
            history.append(now)
            cache.set(cache_key, history, timeout=10)
            return True
            
        return await _check()


class SupportConsumer(AsyncWebsocketConsumer):
    """
    Xodimlar paneli WebSocket consumer.
    URL: ws/support/
    Faqat autentifikatsiyalangan xodimlar uchun.
    """

    SUPPORT_GROUP = 'support_room'

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_id = user.id
        await self.channel_layer.group_add(self.SUPPORT_GROUP, self.channel_name)
        await self.accept()

        # Ochiq suhbatlar ro'yxatini yuborish
        conversations = await self.get_open_conversations()
        await self.send(text_data=json.dumps({
            'type': 'conversations_list',
            'conversations': conversations,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.SUPPORT_GROUP, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            visitor_id = data.get('visitor_id')
            conversation_id = data.get('conversation_id')
            # Input sanitization (XSS himoyasi)
            from django.utils.html import escape
            text = escape(data.get('message', '').strip())
            if not visitor_id or not text or not conversation_id:
                return

            msg_data = await self.save_staff_message(conversation_id, text)

            # Visitor guruhiga push (mijozga yetadi)
            await self.channel_layer.group_send(f"chat_{visitor_id}", {
                'type': 'chat_message',
                'sender': 'staff',
                'message': text,
                'time': msg_data['time'],
            })

            # Support guruhiga echo (boshqa xodim monitorlari)
            user = self.scope['user']
            sender_name = getattr(user, 'full_name', '') or str(getattr(user, 'phone', user.id))
            await self.channel_layer.group_send(self.SUPPORT_GROUP, {
                'type': 'support_message',
                'visitor_id': visitor_id,
                'conversation_id': conversation_id,
                'sender_name': sender_name,
                'message': text,
                'time': msg_data['time'],
            })

            # Telegram'ga ham yuborish (forum-topic — BOSQICH 2.2 da)
            asyncio.ensure_future(self._notify_telegram_staff(conversation_id, sender_name, text))

        elif msg_type == 'get_history':
            conversation_id = data.get('conversation_id')
            if conversation_id:
                history = await self.get_conversation_history(int(conversation_id))
                await self.send(text_data=json.dumps({
                    'type': 'history',
                    'conversation_id': conversation_id,
                    'messages': history,
                }))

        elif msg_type == 'close_conversation':
            conversation_id = data.get('conversation_id')
            visitor_id = data.get('visitor_id')
            if conversation_id:
                await self.close_conversation(int(conversation_id))
                if visitor_id:
                    await self.channel_layer.group_send(f"chat_{visitor_id}", {
                        'type': 'chat_message',
                        'sender': 'system',
                        'message': 'Suhbat yakunlandi. Murojaat uchun rahmat!',
                        'time': '',
                    })
                await self.channel_layer.group_send(self.SUPPORT_GROUP, {
                    'type': 'conversation_closed',
                    'conversation_id': conversation_id,
                })

    # --- Event handlerlar (guruhdan kelgan xabarlar) ---

    async def new_visitor_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_visitor_message',
            'visitor_id': event['visitor_id'],
            'conversation_id': event['conversation_id'],
            'visitor_name': event.get('visitor_name', 'Mehmon'),
            'message': event['message'],
            'time': event.get('time', ''),
        }))

    async def visitor_connected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'visitor_connected',
            'visitor_id': event['visitor_id'],
            'conversation_id': event['conversation_id'],
        }))

    async def support_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'support_message',
            'visitor_id': event['visitor_id'],
            'conversation_id': event['conversation_id'],
            'sender_name': event.get('sender_name', ''),
            'message': event['message'],
            'time': event.get('time', ''),
        }))

    async def conversation_closed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'conversation_closed',
            'conversation_id': event['conversation_id'],
        }))

    # --- DB operatsiyalari ---

    @database_sync_to_async
    def get_open_conversations(self):
        from chat.models import ChatConversation, ChatMessage, ConversationStatus, SenderType
        convs = list(
            ChatConversation.objects.filter(
                status__in=[ConversationStatus.OPEN, ConversationStatus.PENDING]
            ).order_by('-last_message_at', '-created_at')[:50]
        )
        result = []
        for conv in convs:
            last_msg = (
                ChatMessage.objects
                .filter(conversation=conv)
                .order_by('-created_at')
                .first()
            )
            unread = ChatMessage.objects.filter(
                conversation=conv,
                sender_type=SenderType.VISITOR,
                is_read=False,
            ).count()
            result.append({
                'id': conv.id,
                'visitor_id': str(conv.visitor_id),
                'visitor_name': conv.display_name,
                'language': conv.language,
                'status': conv.status,
                'last_message': last_msg.text[:100] if last_msg else '',
                'last_message_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
                'unread_count': unread,
            })
        return result

    @database_sync_to_async
    def save_staff_message(self, conversation_id, text):
        from chat.models import ChatConversation, ChatMessage, SenderType, ViaChannel
        conv = ChatConversation.objects.get(id=conversation_id)
        # O'qilmagan visitor xabarlarini o'qildi deb belgilash
        ChatMessage.objects.filter(
            conversation=conv,
            sender_type=SenderType.VISITOR,
            is_read=False,
        ).update(is_read=True)
        msg = ChatMessage.objects.create(
            conversation=conv,
            sender_type=SenderType.STAFF,
            sender_id=self.user_id,
            via=ViaChannel.DASHBOARD,
            text=text,
        )
        conv.last_message_at = timezone.now()
        conv.save(update_fields=['last_message_at'])
        return {'time': msg.created_at.strftime('%H:%M')}

    @database_sync_to_async
    def get_conversation_history(self, conversation_id):
        from chat.models import ChatMessage
        msgs = list(
            ChatMessage.objects
            .filter(conversation_id=conversation_id)
            .order_by('-created_at')[:100]
        )
        msgs.reverse()
        return [
            {
                'sender': m.sender_type,
                'message': m.text,
                'time': m.created_at.strftime('%H:%M'),
                'sender_name': (m.sender.full_name if m.sender else None),
            }
            for m in msgs
        ]

    @database_sync_to_async
    def close_conversation(self, conversation_id):
        from chat.models import ChatConversation, ConversationStatus
        ChatConversation.objects.filter(id=conversation_id).update(
            status=ConversationStatus.CLOSED,
        )

    async def _notify_telegram_staff(self, conversation_id, sender_name, text):
        """Xodim dashboard javobini Telegram forum-topicga yuboradi."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._sync_notify_telegram_staff, conversation_id, sender_name, text
        )

    def _sync_notify_telegram_staff(self, conversation_id, sender_name, text):
        from notifications.telegram import send_staff_reply_to_topic
        try:
            send_staff_reply_to_topic(
                conversation_id=int(conversation_id),
                sender_name=sender_name,
                text=text,
            )
        except Exception:
            pass
