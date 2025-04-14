class Transaction:
    """
    Represents a single blockchain transaction.

    A transaction records a value transfer:
    - Who sent it (sender)
    - Who received it (receiver)
    - How much (amount)

    These are stored inside a block and become part of the blockchain's history.
    """

    def __init__(self, sender, receiver, amount):
        self.sender = sender        # Typically an address or wallet name
        self.receiver = receiver    # The recipient of the funds
        self.amount = amount        # Number of coins/tokens being sent

    def __repr__(self):
        """
        String representation for printing/logging.
        """
        return f"{self.sender} -> {self.receiver}: {self.amount}"
