# Imports
from flask import Flask, request, jsonify, render_template
import requests
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from blockchain.block import Block
import time

# Create Flask app and initialize blockchain
app = Flask(__name__, template_folder="templates")
chain = Blockchain(difficulty=4)
peers = set()  # Set to keep track of known peers

# ---------------------- ROUTES ----------------------

# Home page (renders the main HTML dashboard)
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Get the full blockchain
@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify([{
        "index": block.index,
        "previous_hash": block.previous_hash,
        "hash": block.hash,
        "nonce": block.nonce,
        "timestamp": block.timestamp,
        "transactions": [tx.__dict__ for tx in block.transactions]
    } for block in chain.chain])

# Add a transaction directly (unsigned)
@app.route("/transaction", methods=["POST"])
def add_transaction():
    data = request.get_json()
    tx = Transaction(**data)
    try:
        chain.create_transaction(tx)
        return jsonify({"message": "Transaction accepted"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Create and add a signed transaction using a local wallet store
@app.route("/transaction/create", methods=["POST"])
def create_signed_transaction():
    data = request.get_json()
    sender = data["sender"]
    receiver = data["receiver"]
    amount = data["amount"]

    from user.wallet import wallet_store 
    from ecdsa import SigningKey, SECP256k1

    priv_hex = wallet_store.get(sender)
    if not priv_hex:
        return jsonify({"error": "Sender not in wallet store"}), 403

    sk = SigningKey.from_string(bytes.fromhex(priv_hex), curve=SECP256k1)
    tx = Transaction.create_signed(sk, receiver, amount)
    chain.create_transaction(tx)
    return jsonify({"message": "Signed transaction accepted", "transaction": tx.__dict__}), 201

# Generate a new wallet keypair and return it
@app.route("/wallet/create", methods=["GET"])
def create_wallet():
    from ecdsa import SigningKey, SECP256k1
    from user.wallet import get_address, wallet_store

    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    priv = sk.to_string().hex()
    pub = vk.to_string().hex()
    address = get_address(vk)

    wallet_store[address] = priv

    return jsonify({
        "address": address,
        "public_key": pub,
        "private_key": priv
    })

# Mine a new block with the pending transactions
@app.route("/mine", methods=["GET"])
def mine():
    miner = request.args.get("miner")
    if not miner:
        return jsonify({"error": "Missing ?miner=... parameter"}), 400
    chain.mine_pending_transactions(miner)
    return jsonify({"message": f"Block mined by {miner}"})

# Manage peer connections (GET to list, POST to add)
@app.route("/peers", methods=["GET", "POST"])
def manage_peers():
    if request.method == "POST":
        data = request.get_json()
        peer = data.get("peer")
        if peer:
            # Avoid adding self
            if peer != f"http://localhost:{request.host.split(':')[1]}":
                peers.add(peer)
            return jsonify({"message": "Peer added", "peers": list(peers)})
        return jsonify({"error": "Missing peer"}), 400
    return jsonify({"peers": list(peers)})

# Broadcast a transaction to all peers
@app.route("/broadcast/transaction", methods=["POST"])
def broadcast_transaction():
    tx_data = request.get_json()
    for peer in peers:
        try:
            requests.post(f"{peer}/transaction", json=tx_data, timeout=2)
        except:
            pass
    return jsonify({"message": "Transaction broadcasted"})

# Broadcast a newly mined block to all peers
@app.route("/broadcast/block", methods=["POST"])
def broadcast_block():
    block_data = request.get_json()
    for peer in peers:
        try:
            requests.post(f"{peer}/receive_block", json=block_data, timeout=2)
        except:
            pass
    return jsonify({"message": "Block broadcasted"})

# Receive a block from another peer
@app.route("/receive_block", methods=["POST"])
def receive_block():
    data = request.get_json()
    transactions = [Transaction(**tx) for tx in data["transactions"]]
    block = Block(
        index=data["index"],
        previous_hash=data["previous_hash"],
        transactions=transactions,
        timestamp=data["timestamp"],
        nonce=data["nonce"]
    )
    block.hash = data["hash"]

    latest = chain.get_latest_block()
    if latest.hash == block.previous_hash:
        chain.chain.append(block)

        # Remove transactions in block from pending
        confirmed = set((tx.sender, tx.receiver, tx.amount) for tx in block.transactions)
        chain.pending_transactions = [
            tx for tx in chain.pending_transactions
            if (tx.sender, tx.receiver, tx.amount) not in confirmed
        ]
        return jsonify({"message": "Block added"})

    return jsonify({"error": "Block rejected"}), 400

# Resolve chain conflicts by choosing the longest valid chain from peers
@app.route("/resolve", methods=["GET"])
def resolve_conflicts():
    longest_chain = None
    max_length = len(chain.chain)

    for peer in peers:
        try:
            res = requests.get(f"{peer}/chain", timeout=2)
            peer_chain_data = res.json()

            new_chain = []
            for block in peer_chain_data:
                transactions = [Transaction(**tx) for tx in block["transactions"]]
                b = Block(
                    index=block["index"],
                    previous_hash=block["previous_hash"],
                    transactions=transactions,
                    timestamp=block["timestamp"],
                    nonce=block["nonce"]
                )
                b.hash = block["hash"]
                new_chain.append(b)

            if len(new_chain) > max_length and chain.is_chain_valid_external(new_chain):
                longest_chain = new_chain
                max_length = len(new_chain)
        except:
            pass

    if longest_chain:
        chain.chain = longest_chain
        return jsonify({"message": "Chain replaced with longer chain"})
    return jsonify({"message": "No replacement needed"})

# ---------------------- MEMPOOL ENDPOINTS ----------------------

# Return pending transactions
@app.route("/mempool", methods=["GET"])
def get_mempool():
    return jsonify([tx.__dict__ for tx in chain.pending_transactions])

# Merge peer mempools into this node's mempool
@app.route("/mempool/merge", methods=["POST"])
def merge_mempool():
    data = request.get_json()
    new_txs = [Transaction(**tx) for tx in data]
    count = 0
    for tx in new_txs:
        try:
            if tx in chain.pending_transactions:
                continue
            chain.create_transaction(tx)
            count += 1
        except:
            pass
    return jsonify({"message": f"Merged {count} new transactions"})

# Run app on command-line-specified port
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()
    app.run(port=args.port)
