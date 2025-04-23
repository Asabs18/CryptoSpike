from ecdsa import SigningKey, VerifyingKey, SECP256k1

wallet_store = {}  # Optional: can be used to persist keypairs by name


def generate_keypair() -> tuple[SigningKey, VerifyingKey]:
    """
    Generate a new ECDSA (secp256k1) keypair.

    Returns:
        tuple[SigningKey, VerifyingKey]: The private and public keys.
    """
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    return sk, vk


def get_address(vk: VerifyingKey) -> str:
    """
    Derive a blockchain wallet address from a public key.

    Args:
        vk (VerifyingKey): The public ECDSA key.

    Returns:
        str: A hex-encoded string representing the public key (wallet address).
    """
    return vk.to_string().hex()
