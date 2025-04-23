from .wallet import generate_keypair, get_address
from blockchain.transaction import Transaction
from ecdsa import SigningKey
from typing import Any


class User:
    """
    Represents a person or entity who owns a wallet (keypair)
    and can sign transactions.

    Attributes:
        name (str): The user's name.
        private_key (SigningKey): The user's ECDSA private key.
        public_key (Any): The user's ECDSA public key.
        address (str): Blockchain address derived from the public key.
    """

    def __init__(self, name: str) -> None:
        """
        Create a new user with a generated wallet keypair.

        Args:
            name (str): The name of the user.
        """
        self.name: str = name
        self.private_key: SigningKey
        self.public_key: Any
        self.private_key, self.public_key = generate_keypair()
        self.address: str = get_address(self.public_key)

    def __repr__(self) -> str:
        """
        Return a short string representation of the user.

        Returns:
            str: Truncated name and address string.
        """
        return f"User(name={self.name}, address={self.address[:10]}...)"

    def create_transaction(self, receiver_address: str, amount: float) -> Transaction:
        """
        Create and sign a transaction from this user to another address.

        Args:
            receiver_address (str): The recipient's wallet address.
            amount (float): Amount to transfer.

        Returns:
            Transaction: A signed transaction ready to be added to the blockchain.
        """
        return Transaction.create_signed(self.private_key, receiver_address, amount)

    def get_address(self) -> str:
        """
        Get this user's wallet address.

        Returns:
            str: The wallet address derived from the public key.
        """
        return self.address
