import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64

def generate_vapid_keys():
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get private key bytes
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, byteorder='big')
    private_base64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    
    # Get public key bytes
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    public_bytes = b'\x04' + \
                   public_numbers.x.to_bytes(32, byteorder='big') + \
                   public_numbers.y.to_bytes(32, byteorder='big')
    public_base64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    return public_base64, private_base64

pub, priv = generate_vapid_keys()
print(f"PUBLIC_KEY: {pub}")
print(f"PRIVATE_KEY: {priv}")
