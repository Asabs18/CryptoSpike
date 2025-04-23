"""
Block module for the blockchain implementation.

This module defines the Block class which represents a single block in the 
blockchain. Each block contains transactions, links to the previous block
through its hash, and maintains its own hash which is used to verify integrity.
"""

import time           # Used to timestamp when the block is created
import hashlib        # Provides cryptographic hash functions like SHA-256
from typing import List, Optional, Any


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

    Attributes:
        index (int): Position of the block in the chain.
        previous_hash (str): Hash of the previous block in the chain.
        timestamp (float): Unix timestamp indicating when the block was created.
        transactions (List[Any]): List of transactions (can be Transaction objects or dicts).
        nonce (int): Number used in proof-of-work mining process.
        hash (str): SHA-256 hash of the block's contents.
    """

    def __init__(
        self,
        index: int,
        previous_hash: str,
        transactions: List[Any],
        timestamp: Optional[float] = None,
        nonce: int = 0
    ) -> None:
        """
        Initialize a new Block in the blockchain.

        Args:
            index (int): Position of the block in the chain.
            previous_hash (str): Hash of the previous block in the chain.
            transactions (List[Any]): List of Transaction objects to include in the block.
            timestamp (Optional[float], optional): Time of block creation. Defaults to current time.
            nonce (int, optional): Starting value for proof-of-work. Defaults to 0.
        """
        self.index: int = index
        self.previous_hash: str = previous_hash
        self.timestamp: float = timestamp or time.time()
        self.transactions: List[Any] = transactions
        self.nonce: int = nonce
        self.hash: str = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate the SHA-256 hash of the block's contents.

        This combines all block data including index, previous hash,
        timestamp, transactions, and nonce to create a unique fingerprint.
        Any change to the block would result in a completely different hash.

        Returns:
            str: A hexadecimal string representing the block's SHA-256 hash.
        """
        tx_data = "".join(str(tx) for tx in self.transactions)
        content = f"{self.index}{self.previous_hash}{self.timestamp}{tx_data}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self) -> str:
        """
        Return a readable string representation of the Block.

        Returns:
            str: A string showing the block's key properties (index, hash, nonce, transactions).
        """
        return (
            f"Block(index={self.index}, hash={self.hash[:10]}..., nonce={self.nonce}, "
            f"transactions={len(self.transactions)} txs)"
        )
