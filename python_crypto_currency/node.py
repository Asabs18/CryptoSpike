# Updated node.py with improved chain syncing and mempool clearing

from flask import Flask, request, jsonify, render_template
import requests
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from blockchain.block import Block
import hashlib

app = Flask(__name__, template_folder="templates")
chain = Blockchain(difficulty=4)
peers = set()

@app.route("/", methods=["GET"])
def index():
    return render_template("base.html")

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

@app.route("/transaction", methods=["POST"])
def add_transaction():
    data = request.get_json()
    tx = Transaction(**data)
    try:
        chain.create_transaction(tx)
        return jsonify({"message": "Transaction accepted"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/transaction/create", methods=["POST"])
def create_signed_transaction():
    data = request.get_json()

    sender = data["sender"]
    receiver = data["receiver"]
    amount = data["amount"]
    public_key_hex = data["public_key"]
    signature_hex = data["signature"]

    # Create the canonical message (string format must match frontend exactly)
    message = f"{receiver}:{float(amount):.2f}".encode()

    try:
        from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

        # Convert hex to bytes and reconstruct verifying key
        vk_bytes = bytes.fromhex(public_key_hex)
        verifying_key = VerifyingKey.from_string(vk_bytes, curve=SECP256k1)

        # Convert signature from hex to bytes
        sig_bytes = bytes.fromhex(signature_hex)

        # Perform signature verification
        msg_hash = hashlib.sha256(message).digest()
        if not verifying_key.verify_digest(sig_bytes, msg_hash):
            return jsonify({"error": "Invalid signature"}), 403

    except (BadSignatureError, ValueError) as e:
        return jsonify({"error": f"Signature verification failed: {str(e)}"}), 403

    # Construct and queue the transaction
    tx = Transaction(sender, receiver, amount)
    try:
        chain.create_transaction(tx)
        return jsonify({"message": "Signed transaction accepted", "transaction": tx.__dict__}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


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

@app.route("/mine", methods=["GET"])
def mine():
    miner = request.args.get("miner")
    if not miner:
        return jsonify({"error": "Missing ?miner=... parameter"}), 400

    fetch_all_peers_and_resolve()  # 🧠 Check latest before mining
    chain.mine_pending_transactions(miner)
    broadcast_last_block()
    return jsonify({"message": f"Block mined by {miner}"})

@app.route("/peers", methods=["GET", "POST"])
def manage_peers():
    if request.method == "POST":
        data = request.get_json()
        peer = data.get("peer")
        if peer:
            if peer != f"http://localhost:{request.host.split(':')[1]}":
                peers.add(peer)
            return jsonify({"message": "Peer added", "peers": list(peers)})
        return jsonify({"error": "Missing peer"}), 400
    return jsonify({"peers": list(peers)})

@app.route("/broadcast/transaction", methods=["POST"])
def broadcast_transaction():
    tx_data = request.get_json()
    for peer in peers:
        try:
            requests.post(f"{peer}/transaction", json=tx_data, timeout=2)
        except:
            pass
    return jsonify({"message": "Transaction broadcasted"})

@app.route("/broadcast/block", methods=["POST"])
def broadcast_block():
    block_data = request.get_json()
    for peer in peers:
        try:
            requests.post(f"{peer}/receive_block", json=block_data, timeout=2)
        except:
            pass
    return jsonify({"message": "Block broadcasted"})

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
        clean_mempool_from_chain()
        return jsonify({"message": "Block added"})
    else:
        fetch_all_peers_and_resolve()
        return jsonify({"error": "Block rejected, syncing"}), 400

@app.route("/resolve", methods=["GET"])
def resolve_conflicts():
    return jsonify(fetch_all_peers_and_resolve())

@app.route("/mempool", methods=["GET"])
def get_mempool():
    return jsonify([tx.__dict__ for tx in chain.pending_transactions])

@app.route("/mempool/merge", methods=["POST"])
def merge_mempool():
    data = request.get_json()
    new_txs = [Transaction(**tx) for tx in data]
    confirmed_set = set((tx.sender, tx.receiver, tx.amount)
                        for block in chain.chain
                        for tx in block.transactions)
    count = 0
    for tx in new_txs:
        if (tx.sender, tx.receiver, tx.amount) in confirmed_set:
            continue
        if tx in chain.pending_transactions:
            continue
        try:
            chain.create_transaction(tx)
            count += 1
        except:
            pass
    return jsonify({"message": f"Merged {count} new transactions"})

# --- Utilities ---
def clean_mempool_from_chain():
    confirmed = set((tx.sender, tx.receiver, tx.amount)
                    for block in chain.chain
                    for tx in block.transactions)
    chain.pending_transactions = [
        tx for tx in chain.pending_transactions
        if (tx.sender, tx.receiver, tx.amount) not in confirmed
    ]

def broadcast_last_block():
    block = chain.get_latest_block()
    try:
        requests.post("/broadcast/block", json=block.__dict__, timeout=2)
    except:
        pass

def fetch_all_peers_and_resolve():
    longest_chain = chain.chain
    max_length = len(longest_chain)

    for peer in peers:
        try:
            res = requests.get(f"{peer}/chain", timeout=2)
            peer_data = res.json()
            new_chain = []
            for block in peer_data:
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

    if longest_chain != chain.chain:
        chain.chain = longest_chain
        clean_mempool_from_chain()
        return {"message": "Chain replaced with longer chain"}

    return {"message": "No replacement needed"}

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()
    app.run(port=args.port)