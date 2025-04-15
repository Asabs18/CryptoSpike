from ecdsa import SigningKey, VerifyingKey, SECP256k1

def generate_keypair():
    """
    Returns (private_key, public_key) objects.
    """
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    return sk, vk

def get_address(vk: VerifyingKey) -> str:
    """
    Returns hex-encoded public key string (wallet address).
    """
    return vk.to_string().hex()
