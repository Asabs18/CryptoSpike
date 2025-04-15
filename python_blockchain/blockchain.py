from block import Block
from transaction import Transaction


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
        self.chain = [self.create_genesis_block()]  # Start with a genesis block
        self.difficulty = difficulty                # How hard it is to mine (e.g., leading '000' in hash)
        self.pending_transactions = []              # Mempool: transactions not yet in a block
        self.mining_reward = 100                    # Coins awarded to miner for each mined block

    def create_genesis_block(self):
        genesis_tx = Transaction("network", "genesis", 0)
        return Block(index=0, previous_hash="0", transactions=[genesis_tx])

    def get_latest_block(self):
        return self.chain[-1]

    def get_balance(self, address):
        """
        Computes the current balance of an address by scanning the entire chain.
        """
        balance = 0

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
    
    def try_transaction(self, transaction):
        """
        Attempts to add a transaction. If the sender lacks funds, it prints a warning instead of raising.
        """
        try:
            self.create_transaction(transaction)
            print(f"✅ Queued transaction: {transaction}")
        except ValueError as e:
            print(f"⛔️ Rejected Transaction: {e}")

    def print_balances(self, addresses):
        """
        Prints balances for a list of addresses.
        """
        print("🧾 Balances:")
        for name in addresses:
            print(f"{name}: {self.get_balance(name)}")
        print("\n")

    def print_chain(self):
        """
        Prints the full blockchain.
        """
        print("🧱 Full Blockchain:")
        for block in self.chain:
            print(block)

    def create_transaction(self, transaction):
        """
        Adds a transaction to the mempool after verifying the sender has enough balance.
        Transactions from 'network' are exempt (mining rewards).
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

    def mine_block(self, block):
        print(f"⛏️ Mining block {block.index}...")
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()
        print(f"✅ Mined: {block}\n\n")

    def is_chain_valid(self):
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