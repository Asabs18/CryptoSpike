import time           # Used to timestamp when the block is created
import hashlib        # Provides cryptographic hash functions like SHA-256


class Block:
    """
    Represents a block in the blockchain.

    Each block contains:
    - Index (position in the chain)
    - Transactions (a list of actions to record)
    - Timestamp (when it was created)
    - Nonce (used in proof-of-work)
    - Hash (unique fingerprint of the block)
    - Previous hash (links this block to the one before it)
    """

    def __init__(self, index, previous_hash, transactions, timestamp=None, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()  # Defaults to current time
        self.transactions = transactions           # List of Transaction objects
        self.nonce = nonce                         # Starts at 0, will be incremented during mining
        self.hash = self.calculate_hash()          # Initial hash of the block

    def calculate_hash(self):
        """
        Calculates the block's SHA-256 hash based on all its contents.
        Changing anything (timestamp, data, nonce) changes the hash.

        This is key to blockchain security: hashes are tamper-evident.
        """
        tx_data = "".join(str(tx) for tx in self.transactions)  # Flatten transaction list
        content = f"{self.index}{self.previous_hash}{self.timestamp}{tx_data}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        """
        A readable summary of the block.
        Shows index, short hash, nonce, and transactions.
        """
        return (
            f"Block(index={self.index}, hash={self.hash[:10]}..., nonce={self.nonce}, "
            f"transactions={self.transactions})"
        )
