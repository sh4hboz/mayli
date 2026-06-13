import uuid
import json
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.core.cache import cache
from channels.testing import WebsocketCommunicator
from config.asgi import application
from chat.models import ChatConversation, ChatMessage

User = get_user_model()

class ChatWebSocketTests(TransactionTestCase):

    def setUp(self):
        cache.clear()
        self.visitor_id = uuid.uuid4()
        self.signer = TimestampSigner()
        self.token = self.signer.sign(str(self.visitor_id))

    def tearDown(self):
        cache.clear()

    async def test_connect_with_valid_token(self):
        communicator = WebsocketCommunicator(
            application,
            f"ws/chat/{self.visitor_id}/?token={self.token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        # Tarix xabari kelishini kutamiz (bo'sh bo'lsa ham kelishi mumkin)
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'history')
        await communicator.disconnect()

    async def test_connect_without_token(self):
        communicator = WebsocketCommunicator(
            application,
            f"ws/chat/{self.visitor_id}/"
        )
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_connect_with_invalid_token(self):
        communicator = WebsocketCommunicator(
            application,
            f"ws/chat/{self.visitor_id}/?token=invalid_token"
        )
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)

    async def test_input_sanitization_xss(self):
        communicator = WebsocketCommunicator(
            application,
            f"ws/chat/{self.visitor_id}/?token={self.token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # History

        # XSS xabari yuboramiz
        xss_message = "<script>alert('hack')</script> Hello & Welcome"
        await communicator.send_json_to({
            "type": "message",
            "message": xss_message
        })

        # Consumer'dan keladigan javobni tekshiramiz
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'message')
        self.assertEqual(response['sender'], 'visitor')
        # Escape qilingan bo'lishi kerak
        self.assertNotIn("<script>", response['message'])
        self.assertIn("&lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt; Hello &amp; Welcome", response['message'])
        await communicator.disconnect()

    async def test_rate_limiting(self):
        communicator = WebsocketCommunicator(
            application,
            f"ws/chat/{self.visitor_id}/?token={self.token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from() # History

        # 5 ta xabar yuboramiz (muvaffaqiyatli)
        for i in range(5):
            await communicator.send_json_to({
                "type": "message",
                "message": f"Message {i}"
            })
            resp = await communicator.receive_json_from()
            self.assertEqual(resp['type'], 'message')

        # 6-xabar limitdan oshib ketadi
        await communicator.send_json_to({
            "type": "message",
            "message": "Limit message"
        })
        resp = await communicator.receive_json_from()
        self.assertEqual(resp['type'], 'error')
        self.assertIn("Juda ko'p xabar yuborildi", resp['message'])
        await communicator.disconnect()
