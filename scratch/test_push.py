import json
import sqlite3
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.asymmetric import ec

# Fix for pywebpush compatibility with newer cryptography versions
try:
    if isinstance(ec.SECP256R1, type):
        class SECP256R1Proxy(ec.SECP256R1):
            def __call__(self):
                return self
        ec.SECP256R1 = SECP256R1Proxy()
except Exception:
    pass

def test_push():
    conn = sqlite3.connect('backend/tracking_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM push_subscriptions")
    subs = cursor.fetchall()
    conn.close()
    
    if not subs:
        print("No subscriptions found in DB.")
        return

    # VAPID Private key (Base64URL)
    private_key_b64 = "kZJ0SsD1SeqO-bf2iWmDxppuHwG3RVLmyYkXZkj6XPU"
    
    for sub in subs:
        print(f"Attempting to send to {sub['endpoint'][:50]}...")
        try:
            response = webpush(
                subscription_info={
                    "endpoint": sub['endpoint'],
                    "keys": {"p256dh": sub['p256dh'], "auth": sub['auth']}
                },
                data=json.dumps({
                    "title": "🚀 Test Manuel",
                    "body": "Bu bir manuel test bildirimidir.",
                    "url": "https://pricetrack-notifier.vercel.app"
                }),
                vapid_private_key=private_key_b64,
                vapid_claims={"sub": "mailto:admin@pricetrack.com"},
                ttl=3600
            )
            print(f"Success! Response: {response.status_code if hasattr(response, 'status_code') else response}")
        except WebPushException as ex:
            print(f"WebPushException: {ex}")
            if ex.response is not None:
                print(f"Status: {ex.response.status_code}")
                print(f"Body: {ex.response.text}")
        except Exception as e:
            print(f"General Error: {e}")

if __name__ == "__main__":
    test_push()
