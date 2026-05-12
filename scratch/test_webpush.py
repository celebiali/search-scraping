import json
from pywebpush import webpush, WebPushException

def test_webpush():
    # Mock subscription info
    sub_info = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/fake",
        "keys": {"p256dh": "fake", "auth": "fake"}
    }
    
    try:
        # This is how it's called in tracker.py
        webpush(
            subscription_info=sub_info,
            data=json.dumps({"title": "test", "body": "test"}),
            vapid_private_key="fake",
            vapid_claims={"sub": "mailto:admin@example.com"},
            ttl=3600
        )
    except Exception as e:
        print(f"Error: {repr(e)}")

if __name__ == "__main__":
    test_webpush()
