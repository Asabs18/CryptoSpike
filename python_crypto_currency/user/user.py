from wallet import generate_keypair, get_address
from ..blockchain.transaction import Transaction

class User:
    """
    Represents a person or entity who owns a wallet (keypair)
    and can sign transactions.
    """

    def __init__(self, name):
        self.name = name
        self.private_key, self.public_key = generate_keypair()
        self.address = get_address(self.public_key)

    def __repr__(self):
        return f"User(name={self.name}, address={self.address[:10]}...)"

    def create_transaction(self, receiver_address, amount):
        """
        Returns a signed transaction from this user to another address.
        """
        return Transaction.create_signed(self.private_key, receiver_address, amount)

    def get_address(self):
        return self.address
