"""
Main demo script for blockchain functionality.

This script demonstrates:
- Creating users with wallets
- Minting coins
- Creating and signing transactions
- Mining blocks
- Verifying balances and printing the blockchain
"""

from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from user.user import User


def main() -> None:
    """
    Run a sample blockchain scenario with two users and a miner.
    Demonstrates wallet creation, transaction signing, mining,
    and blockchain inspection.
    """
    print("🔐 Creating users...")
    alice = User("Alice")
    bob = User("Bob")
    miner = "Miner1"  # Miner is just an identifier (no wallet)

    # Create blockchain with set difficulty
    chain = Blockchain(difficulty=5)

    # Mint coins to Alice
    chain.try_transaction(Transaction("network", alice.get_address(), 100))
    chain.mine_pending_transactions(miner)
    chain.print_balances([alice.get_address(), bob.get_address(), miner])

    # Valid transaction: Alice → Bob
    tx1 = alice.create_transaction(bob.get_address(), 40)
    chain.try_transaction(tx1)

    # Invalid transaction: Bob tries to overspend
    tx2 = bob.create_transaction(alice.get_address(), 100)
    chain.try_transaction(tx2)  # Should be rejected

    # Valid transaction: Bob → Alice (smaller amount)
    tx3 = bob.create_transaction(alice.get_address(), 10)
    chain.try_transaction(tx3)

    # Mine both valid transactions
    chain.mine_pending_transactions(miner)
    chain.print_balances([alice.get_address(), bob.get_address(), miner])

    # Display the full blockchain
    chain.print_chain()


if __name__ == "__main__":
    main()
