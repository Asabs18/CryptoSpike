"""
Blockchain module for the cryptocurrency implementation.

This module defines the Blockchain class which is responsible for maintaining
the chain of blocks, managing transactions, and implementing the consensus 
mechanism through proof-of-work mining.
"""

from typing import List, Optional
from .block import Block
from .transaction import Transaction


class Blockchain:
    """
    The main class that manages the blockchain itself.

    Responsibilities:
    - Create and store blocks
    - Manage the mempool (unconfirmed transactions)
    - Mine new blocks (proof-of-work)
    - Validate the integrity of the entire chain

    Attributes:
        chain (List[Block]): List of Block objects forming the blockchain.
        difficulty (int): Number of leading zeros required in block hashes.
        pending_transactions (List[Transaction]): Unconfirmed transactions waiting to be mined.
        mining_reward (int): Amount of cryptocurrency given as reward for mining.
    """

    def __init__(self, difficulty: int = 3) -> None:
        """
        Initialize a new blockchain with a genesis block.

        Args:
            difficulty (int, optional): Mining difficulty level. Defaults to 3.
        """
        self.chain: List[Block] = [self.create_genesis_block()]
        self.difficulty: int = difficulty
        self.pending_transactions: List[Transaction] = []
        self.mining_reward: int = 100

    def create_genesis_block(self) -> Block:
        """
        Create the first block in the blockchain.

        Returns:
            Block: The genesis block with a dummy transaction.
        """
        genesis_tx = Transaction("network", "genesis", 0)
        return Block(index=0, previous_hash="0", transactions=[genesis_tx])

    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain.

        Returns:
            Block: The last block in the blockchain.
        """
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        """
        Compute total balance for an address by traversing the chain and mempool.

        Args:
            address (str): The account address to check balance for.

        Returns:
            float: The current balance of the address.
        """
        balance = 0.0

        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.receiver == address:
                    balance += tx.amount

        for tx in self.pending_transactions:
            if tx.sender == address:
                balance -= tx.amount
            if tx.receiver == address:
                balance += tx.amount

        return balance

    def create_transaction(self, transaction: Transaction) -> None:
        """
        Add a transaction to the mempool if sender has enough balance.

        Args:
            transaction (Transaction): The transaction to add to the mempool.

        Raises:
            ValueError: If sender has insufficient balance for the transaction.
        """
        if transaction.sender != "network":
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance < transaction.amount:
                raise ValueError(
                    f"💸 Transaction denied: {transaction.sender} has insufficient balance "
                    f"(has {sender_balance}, needs {transaction.amount})"
                )
        self.pending_transactions.append(transaction)

    def try_transaction(self, transaction: Transaction) -> None:
        """
        Attempt to add a transaction and log the result rather than raising exceptions.

        Args:
            transaction (Transaction): The transaction to attempt adding.
        """
        try:
            self.create_transaction(transaction)
            print(f"✅ Queued transaction: {transaction}")
        except ValueError as e:
            print(f"⛔️ Rejected Transaction: {e}")

    def mine_pending_transactions(self, miner_address: str) -> None:
        """
        Mine a new block with all pending transactions and a reward for the miner.

        Args:
            miner_address (str): Address to receive the mining reward.
        """
        print(f"⛏️ Starting mining on {len(self.pending_transactions)} transactions...")

        reward_tx = Transaction("network", miner_address, self.mining_reward)
        transactions_to_mine = self.pending_transactions + [reward_tx]

        new_block = Block(
            index=self.get_latest_block().index + 1,
            previous_hash=self.get_latest_block().hash,
            transactions=transactions_to_mine
        )

        self.mine_block(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []

    def mine_block(self, block: Block) -> None:
        """
        Perform proof-of-work mining on a block.

        Increments the nonce until the block hash starts with enough zeros
        to meet the difficulty requirement.

        Args:
            block (Block): The block to mine.
        """
        print(f"⛏️ Mining block {block.index}...")
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()
        print(f"✅ Mined: {block}\n\n")

    def is_chain_valid(self) -> bool:
        """
        Validate the integrity of the blockchain.

        Returns:
            bool: True if chain is valid, False otherwise.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                print(f"❌ Block {i} has been tampered with: incorrect hash.")
                return False

            if current.previous_hash != prev.hash:
                print(f"❌ Block {i} is not correctly linked to previous block.")
                return False

            if not current.hash.startswith("0" * self.difficulty):
                print(f"❌ Block {i} was not mined correctly (hash too easy).")
                return False

        return True

    def is_chain_valid_external(self, chain: List[Block]) -> bool:
        """
        Validate an external chain (e.g., from a peer node).

        Args:
            chain (List[Block]): A list of Block objects to validate.

        Returns:
            bool: True if the given chain is valid, False otherwise.
        """
        for i in range(1, len(chain)):
            current = chain[i]
            prev = chain[i - 1]

            if current.hash != current.calculate_hash():
                print(f"❌ External Block {i} has incorrect hash.")
                return False

            if current.previous_hash != prev.hash:
                print(f"❌ External Block {i} has incorrect previous_hash link.")
                return False

            if not current.hash.startswith("0" * self.difficulty):
                print(f"❌ External Block {i} hash does not meet difficulty.")
                return False

        return True

    def print_balances(self, addresses: List[str]) -> None:
        """
        Print the balances of a list of addresses to console.

        Args:
            addresses (List[str]): List of address strings to check balances for.
        """
        print("🧾 Balances:")
        for name in addresses:
            print(f"{name}: {self.get_balance(name)}")
        print("\n")

    def print_chain(self) -> None:
        """
        Print a summary of every block in the blockchain.
        """
        print("🧱 Full Blockchain:")
        for block in self.chain:
            print(block)
