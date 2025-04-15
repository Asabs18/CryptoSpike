from blockchain import Blockchain
from transaction import Transaction
from wallet import generate_keypair, get_address

#Chatgpt link: https://chatgpt.com/share/67feb5e9-0b78-800f-bc62-ed4d78f7a417

def main():
    print("🔐 Creating wallets...")
    # Wallets
    alice_sk, alice_vk = generate_keypair()
    bob_sk, bob_vk = generate_keypair()
    miner = "Miner1"

    alice = get_address(alice_vk)
    bob = get_address(bob_vk)

    # Blockchain setup
    chain = Blockchain(difficulty=5)

    # Mint coins to Alice
    chain.try_transaction(Transaction("network", alice, 100))
    chain.mine_pending_transactions(miner)
    chain.print_balances([alice, bob, miner])

    # Alice → Bob (signed)
    tx1 = Transaction.create_signed(alice_sk, bob, 40)
    chain.try_transaction(tx1)

    # Bob → Alice (invalid — too much)
    tx2 = Transaction.create_signed(bob_sk, alice, 100)
    chain.try_transaction(tx2)

    # Bob → Alice (valid)
    tx3 = Transaction.create_signed(bob_sk, alice, 10)
    chain.try_transaction(tx3)

    chain.mine_pending_transactions(miner)
    chain.print_balances([alice, bob, miner])
    chain.print_chain()

if __name__ == "__main__":
    main()
