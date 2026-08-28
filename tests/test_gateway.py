import unittest
import asyncio
from app.gateway.auth import GatewayAuthenticator
from app.gateway.server import AgentGatewayService

class TestGateway(unittest.TestCase):
    def setUp(self):
        self.auth = GatewayAuthenticator("my-test-shared-secret-1234567890!")
        self.gateway = AgentGatewayService()

    def test_auth_header_verification(self):
        payload = '{"action": "test_connect"}'
        hdr = self.auth.generate_auth_header(payload)

        ok, err = self.auth.verify_request(hdr, payload)
        self.assertTrue(ok)
        self.assertIsNone(err)

        # Tampered payload fails
        ok2, err2 = self.auth.verify_request(hdr, '{"action": "tampered"}')
        self.assertFalse(ok2)

    def test_gateway_health_status(self):
        async def run_test():
            health = await self.gateway.get_health_status()
            self.assertEqual(health["status"], "healthy")
            self.assertIn("coding_agent", health["registered_agents"])
            self.assertIn("metrics", health)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
