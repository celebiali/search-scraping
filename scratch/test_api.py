import requests

# Test subscribe
print("Testing /subscribe")
res = requests.post("http://localhost:8000/subscribe", json={
    "endpoint": "https://web.push.apple.com/test-endpoint-123",
    "keys": {
        "p256dh": "test-p256dh",
        "auth": "test-auth"
    }
})
print(res.status_code, res.text)

# Test add product
print("Testing /products (Add Product)")
res2 = requests.post("http://localhost:8000/products", json={
    "query": "test_product_123",
    "category": "elektronik"
})
print(res2.status_code, res2.text)
