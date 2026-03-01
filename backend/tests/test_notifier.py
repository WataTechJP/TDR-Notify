import unittest
from unittest.mock import AsyncMock, Mock, call, patch

from backend import notifier


class NotifierTests(unittest.TestCase):
    @patch("backend.notifier.requests.post")
    def test_send_push_notification_returns_true_on_ok_status(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"status": "ok"}}
        mock_post.return_value = mock_response

        result = notifier.send_push_notification(
            "https://exp.host/--/api/v2/push/send",
            "ExponentPushToken[test]",
            "Title",
            "Body",
            5,
        )

        self.assertTrue(result)
        mock_post.assert_called_once_with(
            "https://exp.host/--/api/v2/push/send",
            json={
                "to": "ExponentPushToken[test]",
                "title": "Title",
                "body": "Body",
                "sound": "default",
            },
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

    @patch("backend.notifier.requests.post")
    def test_send_push_notification_returns_false_on_failure(self, mock_post: Mock) -> None:
        non_200_response = Mock()
        non_200_response.status_code = 500
        non_200_response.json.return_value = {"data": {"status": "ok"}}

        invalid_json_response = Mock()
        invalid_json_response.status_code = 200
        invalid_json_response.json.side_effect = ValueError("invalid json")

        for response in [non_200_response, invalid_json_response]:
            with self.subTest(status_code=response.status_code):
                mock_post.return_value = response
                result = notifier.send_push_notification(
                    "https://exp.host/--/api/v2/push/send",
                    "ExponentPushToken[test]",
                    "Title",
                    "Body",
                    5,
                )
                self.assertFalse(result)


class BulkNotifierTests(unittest.IsolatedAsyncioTestCase):
    @patch("backend.notifier.asyncio.to_thread", new_callable=AsyncMock)
    async def test_send_bulk_notifications_iterates_all_tokens(
        self, mock_to_thread: AsyncMock
    ) -> None:
        tokens = [
            "ExponentPushToken[one]",
            "ExponentPushToken[two]",
            "ExponentPushToken[three]",
        ]

        await notifier.send_bulk_notifications(
            "https://exp.host/--/api/v2/push/send", tokens, "Title", "Body", 5
        )

        expected_calls = [
            call(
                notifier.send_push_notification,
                "https://exp.host/--/api/v2/push/send",
                "ExponentPushToken[one]",
                "Title",
                "Body",
                5,
            ),
            call(
                notifier.send_push_notification,
                "https://exp.host/--/api/v2/push/send",
                "ExponentPushToken[two]",
                "Title",
                "Body",
                5,
            ),
            call(
                notifier.send_push_notification,
                "https://exp.host/--/api/v2/push/send",
                "ExponentPushToken[three]",
                "Title",
                "Body",
                5,
            ),
        ]
        self.assertEqual(mock_to_thread.await_count, len(tokens))
        mock_to_thread.assert_has_awaits(expected_calls)


if __name__ == "__main__":
    unittest.main()
