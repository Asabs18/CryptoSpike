from ecdsa import SigningKey, VerifyingKey, SECP256k1
import hashlib
import json

class Transaction:
    """
    A digitally-signed transaction using ECDSA.

    - sender: the sender's public key (hex string) or 'network'
    - receiver: recipient's wallet address (can be any identifier)
    - amount: value being transferred
    - signature: hex-encoded digital signature created with sender's private key
    """

    def __init__(self, sender, receiver, amount, signature=None):
        self.sender = sender          # Usually hex of public key (unless 'network')
        self.receiver = receiver      # Wallet address
        self.amount = amount          # Amount of coins being sent
        self.signature = signature    # Hex string of ECDSA signature (optional at creation)

    def __repr__(self):
        return f"{self.sender[:8]}... -> {self.receiver[:8]}...: {self.amount}"

    def to_dict(self):
        """
        Returns a dictionary of transaction contents (excluding signature).
        This is the data that gets signed.
        """
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }

    def to_json(self):
        """
        Returns a consistent JSON string of the transaction data for signing/verifying.
        Keys are sorted to avoid mismatches due to order.
        """
        return json.dumps(self.to_dict(), sort_keys=True)

    def sign(self, private_key: SigningKey):
        """
        Signs this transaction using the given private key.
        Sets the signature as a hex string.
        """
        message = self.to_json().encode()
        self.signature = private_key.sign(message).hex()

    def is_valid(self, get_balance_fn):
        """
        Verifies this transaction:
        - Confirms a valid ECDSA signature
        - Confirms sender has enough balance

        Args:
            get_balance_fn (function): a function that takes address and returns balance

        Returns:
            bool: True if the transaction is valid and authorized
        """
        if self.sender == "network":
            # Mining reward or system minting — skip signature
            return True

        if not self.signature:
            print("⛔️ No signature provided.")
            return False

        try:
            # Reconstruct verifying key from sender's public key (hex)
            pubkey_bytes = bytes.fromhex(self.sender)
            vk = VerifyingKey.from_string(pubkey_bytes, curve=SECP256k1)

            # Recompute message and verify signature
            message = self.to_json().encode()
            vk.verify(bytes.fromhex(self.signature), message)
        except Exception as e:
            print("⛔️ Signature verification failed:", e)
            return False

        # Check balance (only if verification succeeds)
        if get_balance_fn(self.sender) < self.amount:
            print("⛔️ Insufficient balance.")
            return False

        return True
    
    @classmethod
    def create_signed(cls, sender_key: SigningKey, receiver_address: str, amount: float):
        """
        Creates and signs a transaction using the sender's private key.
        Returns a signed Transaction object.
        """
        sender_address = sender_key.get_verifying_key().to_string().hex()
        tx = cls(sender_address, receiver_address, amount)
        tx.sign(sender_key)
        return tx

