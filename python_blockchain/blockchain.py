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
        """
        Creates the first block manually.
        It has no real previous block, so we hardcode its previous_hash.
        """
        genesis_tx = Transaction("network", "genesis", 0)
        return Block(index=0, previous_hash="0", transactions=[genesis_tx])

    def get_latest_block(self):
        """
        Returns the most recently added block.
        """
        return self.chain[-1]

    def create_transaction(self, transaction):
        """
        Adds a transaction to the mempool.
        It will be included in the next mined block.
        """
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        """
        Takes all pending transactions, adds a coinbase reward,
        mines a new block, and appends it to the chain.

        After mining, the mempool is cleared.
        """
        print(f"⛏️ Starting mining on {len(self.pending_transactions)} transactions...")

        # Add a reward transaction for the miner
        reward_tx = Transaction("network", miner_address, self.mining_reward)
        transactions_to_mine = self.pending_transactions + [reward_tx]

        new_block = Block(
            index=self.get_latest_block().index + 1,
            previous_hash=self.get_latest_block().hash,
            transactions=transactions_to_mine
        )

        self.mine_block(new_block)
        self.chain.append(new_block)

        # Clear the mempool — transactions are now confirmed
        self.pending_transactions = []

    def mine_block(self, block):
        """
        Performs proof-of-work by brute-forcing different nonce values
        until the block's hash starts with enough leading zeros.
        """
        print(f"⛏️ Mining block {block.index}...")
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()
        print(f"✅ Mined: {block}")

    def is_chain_valid(self):
        """
        Validates the entire blockchain:
        - No hashes have been tampered with
        - All blocks are correctly linked
        - All hashes meet the difficulty requirement
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            # Block data must match its stored hash
            if current.hash != current.calculate_hash():
                print(f"❌ Block {i} has been tampered with: incorrect hash.")
                return False

            # This block must properly reference the hash of the previous block
            if current.previous_hash != prev.hash:
                print(f"❌ Block {i} is not correctly linked to previous block.")
                return False

            # Hash must satisfy the proof-of-work difficulty
            if not current.hash.startswith("0" * self.difficulty):
                print(f"❌ Block {i} was not mined correctly (hash too easy).")
                return False

        return True
