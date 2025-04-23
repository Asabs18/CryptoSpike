from ecdsa import SigningKey, VerifyingKey, SECP256k1
import hashlib
import json
from typing import Callable, Optional


class Transaction:
    """
    A digitally-signed transaction using ECDSA.

    Each transaction contains:
    - sender: the sender's public key as a hex string, or 'network' for mining rewards
    - receiver: the recipient's wallet address
    - amount: the number of coins being transferred
    - signature: a hex-encoded ECDSA signature from the sender's private key
    """

    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: float,
        signature: Optional[str] = None
    ) -> None:
        """
        Initialize a new transaction.

        Args:
            sender (str): Sender's public key as hex string, or 'network'.
            receiver (str): Receiver's wallet address.
            amount (float): Amount to be transferred.
            signature (Optional[str], optional): Hex string of ECDSA signature. Defaults to None.
        """
        self.sender: str = sender
        self.receiver: str = receiver
        self.amount: float = amount
        self.signature: Optional[str] = signature

    def __repr__(self) -> str:
        """
        Return a human-readable summary of the transaction.

        Returns:
            str: Shortened sender/receiver addresses and amount.
        """
        return f"{self.sender[:8]}... -> {self.receiver[:8]}...: {self.amount}"

    def to_dict(self) -> dict:
        """
        Return the transaction's contents as a dictionary, excluding the signature.

        Returns:
            dict: Dictionary containing sender, receiver, and amount.
        """
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }

    def to_json(self) -> str:
        """
        Return a canonical JSON string of the transaction data for signing/verifying.

        Returns:
            str: Sorted JSON string of the transaction.
        """
        return json.dumps(self.to_dict(), sort_keys=True)

    def sign(self, private_key: SigningKey) -> None:
        """
        Sign this transaction using a private ECDSA key.

        Args:
            private_key (SigningKey): The sender's private key.
        """
        message = self.to_json().encode()
        self.signature = private_key.sign(message).hex()

    def is_valid(self, get_balance_fn: Callable[[str], float]) -> bool:
        """
        Validate this transaction's signature and sender balance.

        Args:
            get_balance_fn (Callable[[str], float]): A function that returns balance for a given address.

        Returns:
            bool: True if the transaction is valid, False otherwise.
        """
        if self.sender == "network":
            return True

        if not self.signature:
            print("⛔️ No signature provided.")
            return False
