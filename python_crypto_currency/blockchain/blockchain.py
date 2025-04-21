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
    """

    def __init__(self, difficulty=3):
        # Initialize blockchain with genesis block
        self.chain = [self.create_genesis_block()]
        # Mining difficulty: how many leading zeroes required in block hash
        self.difficulty = difficulty
        # List of unconfirmed/pending transactions (the mempool)
        self.pending_transactions = []
        # Reward for mining a block
        self.mining_reward = 100

    def create_genesis_block(self):
        # Create the first block with a dummy transaction from 'network' to 'genesis'
        genesis_tx = Transaction("network", "genesis", 0)
        return Block(index=0, previous_hash="0", transactions=[genesis_tx])

    def get_latest_block(self):
        # Return the most recent block on the chain
        return self.chain[-1]

    def get_balance(self, address):
        """
        Compute total balance for an address by traversing chain and mempool.
        Deduct for sent transactions, add for received ones.
        """
        balance = 0

        # Check all confirmed transactions in the chain
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.receiver == address:
                    balance += tx.amount

        # Also include unconfirmed transactions in mempool
        for tx in self.pending_transactions:
            if tx.sender == address:
                balance -= tx.amount
            if tx.receiver == address:
                balance += tx.amount

        return balance

    def try_transaction(self, transaction):
        """
        A helper that tries to add a transaction but logs instead of raising an error.
        Good for debugging/testing.
        """
        try:
            self.create_transaction(transaction)
            print(f"✅ Queued transaction: {transaction}")
        except ValueError as e:
            print(f"⛔️ Rejected Transaction: {e}")

    def print_balances(self, addresses):
        """
        Print the balances of a list of addresses to console.
        """
        print("🧾 Balances:")
        for name in addresses:
            print(f"{name}: {self.get_balance(name)}")
        print("\n")

    def print_chain(self):
        """
        Print a summary of every block in the blockchain.
        """
        print("🧱 Full Blockchain:")
        for block in self.chain:
            print(block)

    def create_transaction(self, transaction):
        """
        Add a transaction to the mempool if sender has enough balance.
        Mining rewards (from 'network') bypass this check.
        """
        if transaction.sender != "network":
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance < transaction.amount:
                raise ValueError(
                    f"💸 Transaction denied: {transaction.sender} has insufficient balance "
                    f"(has {sender_balance}, needs {transaction.amount})"
                )
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        """
        Take all pending transactions, add a mining reward, and mine a new block.
        """
        print(f"⛏️ Starting mining on {len(self.pending_transactions)} transactions...")

        # Add mining reward to the block
        reward_tx = Transaction("network", miner_address, self.mining_reward)
        transactions_to_mine = self.pending_transactions + [reward_tx]

        # Create new block and start mining
        new_block = Block(
            index=self.get_latest_block().index + 1,
            previous_hash=self.get_latest_block().hash,
            transactions=transactions_to_mine
        )

        self.mine_block(new_block)
        self.chain.append(new_block)
        self.pending_transactions = []

    def mine_block(self, block):
        """
        Proof-of-Work algorithm: keep incrementing nonce until hash matches difficulty.
        """
        print(f"⛏️ Mining block {block.index}...")
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()
        print(f"✅ Mined: {block}\n\n")

    def is_chain_valid(self):
        """
        Validate the local chain: every block must match its hash and link to previous.
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

    def is_chain_valid_external(self, chain):
        """
        Validate a given chain (e.g., from a peer) to see if it's consistent and valid.
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
