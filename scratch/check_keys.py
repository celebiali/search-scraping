import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def get_pub_key(private_key_b64):
    # Padding ekle
    missing_padding = len(private_key_b64) % 4
    if missing_padding:
        private_key_b64 += '=' * (4 - missing_padding)
    
    private_key_bytes = base64.urlsafe_b64decode(private_key_b64)
    # SECP256R1 curve
    private_key = ec.derive_private_key(int.from_bytes(private_key_bytes, 'big'), ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Uncompressed format (65 bytes)
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    return base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

if __name__ == "__main__":
    priv = "kZJ0SsD1SeqO-bf2iWmDxppuHwG3RVLmyYkXZkj6XPU"
    pub = get_pub_key(priv)
    print(f"Private: {priv}")
    print(f"Derived Public: {pub}")
    print(f"Hardcoded Public: BF-Ff8oDzJzlzVmMhLarvYhDl-oxKeXsJbZL-MhGAZJqsiVkBkDYj81RBAQ9OLMt1YS851EoznKE5OiT1B2VjIQ")
