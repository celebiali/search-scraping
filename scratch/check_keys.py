from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def check_keys():
    # Private Key (Base64URL)
    private_key_b64 = "kZJ0SsD1SeqO-bf2iWmDxppuHwG3RVLmyYkXZkj6XPU"
    # Public Key (Base64URL) from api.py
    public_key_b64 = "BF-Ff8oDzJzlzVmMhLarvYhDl-oxKeXsJbZL-MhGAZJqsiVkBkDYj81RBAQ9OLMt1YS851EoznKE5OiT1B2VjIQ"
    
    try:
        # Decode private key
        # Pad with = if needed
        padding = '=' * (4 - len(private_key_b64) % 4)
        private_bytes = base64.urlsafe_b64decode(private_key_b64 + padding)
        
        # Load private key
        priv_key = ec.derive_private_key(int.from_bytes(private_bytes, 'big'), ec.SECP256R1())
        
        # Get public key bytes
        pub_key = priv_key.public_key()
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        # Encode public key to Base64URL
        derived_pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')
        
        print(f"Hardcoded Public Key: {public_key_b64}")
        print(f"Derived Public Key:   {derived_pub_b64}")
        
        if public_key_b64 == derived_pub_b64:
            print("MATCH!")
        else:
            print("MISMATCH!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_keys()
