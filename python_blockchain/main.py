from blockchain import Blockchain
from transaction import Transaction

def main():
    # Initialize the blockchain with a given mining difficulty
    # Higher difficulty = more time to find a valid hash
    chain = Blockchain(difficulty=5)

    # Add transactions to the mempool (not yet confirmed on the chain)
    chain.create_transaction(Transaction("Alice", "Bob", 50))
    chain.create_transaction(Transaction("Bob", "Charlie", 25))

    # Mine a block from all pending transactions
    # Includes a reward for the miner ('Miner1')
    chain.mine_pending_transactions("Miner1")

    # Add another round of transactions
    chain.create_transaction(Transaction("Charlie", "Dave", 10))
    chain.create_transaction(Transaction("Eve", "Frank", 15))

    # Mine those as well
    chain.mine_pending_transactions("Miner1")

    # Print out all confirmed blocks in the blockchain
    for block in chain.chain:
        print(block)

    # Check the blockchain's integrity
    print("\nIs blockchain valid?", chain.is_chain_valid())


if __name__ == "__main__":
    main()
