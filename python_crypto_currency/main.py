from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from user.user import User

# CHATGPT LINK:
# https://chatgpt.com/share/67feb5e9-0b78-800f-bc62-ed4d78f7a417

def main():
    print("🔐 Creating users...")
    # Create users with their own wallets
    alice = User("Alice")
    bob = User("Bob")
    miner = "Miner1"  # Miner is just a string for now

    # Create blockchain instance
    chain = Blockchain(difficulty=5)

    # Mint coins to Alice (unsolicited reward)
    chain.try_transaction(Transaction("network", alice.get_address(), 100))
    chain.mine_pending_transactions(miner)
    chain.print_balances([alice.get_address(), bob.get_address(), miner])

    # Alice → Bob (signed by Alice)
    tx1 = alice.create_transaction(bob.get_address(), 40)
    chain.try_transaction(tx1)

    # Bob tries to send too much to Alice (invalid)
    tx2 = bob.create_transaction(alice.get_address(), 100)
    chain.try_transaction(tx2)  # Should be rejected

    # Bob sends valid amount to Alice
    tx3 = bob.create_transaction(alice.get_address(), 10)
    chain.try_transaction(tx3)

    # Mine both valid transactions
    chain.mine_pending_transactions(miner)
    chain.print_balances([alice.get_address(), bob.get_address(), miner])

    # Print full chain
    chain.print_chain()

if __name__ == "__main__":
    main()
