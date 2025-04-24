"""
node.py — Flask-powered blockchain node

This script launches a web server that:
- Hosts a blockchain node
- Allows peer-to-peer communication
- Handles transactions, mining, syncing, and mempool management
"""

from flask import Flask, request, jsonify, render_template
import requests
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from blockchain.block import Block
import hashlib
from typing import Dict, Any
from urllib.parse import urlparse
import sys
import json
import os
import threading
import time


def get_data_dir():
    port = os.environ.get("NODE_PORT", "5000")
    path = f"node_data/port_{port}"
    os.makedirs(path, exist_ok=True)
    return path

def normalize_peer_url(url):
    """
    Normalize a peer URL to http://localhost:PORT format to avoid duplicates.
    """
    parsed = urlparse(url if "://" in url else f"http://{url}")
    hostname = "localhost" if parsed.hostname in ["127.0.0.1", "localhost"] else parsed.hostname
    return f"http://{hostname}:{parsed.port}"

PEERS_FILE = os.path.join(get_data_dir(), "peers.json")
peers = set()

this_node = ""

def load_peers():
    global peers
    if os.path.exists(PEERS_FILE):
        try:
            with open(PEERS_FILE, "r") as f:
                peers.update(json.load(f))
        except Exception:
            pass

def save_peers():
    try:
        with open(PEERS_FILE, "w") as f:
            json.dump(list(peers), f)
    except Exception:
        pass


app = Flask(__name__, template_folder="templates")
chain = Blockchain(difficulty=4)
load_peers()

this_node = ""

@app.route("/", methods=["GET"])
def index():
    return render_template("base.html")

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

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

    message = f"{receiver}:{float(amount):.2f}".encode()

    try:
        from ecdsa import VerifyingKey, SECP256k1, BadSignatureError

        vk_bytes = bytes.fromhex(public_key_hex)
        verifying_key = VerifyingKey.from_string(vk_bytes, curve=SECP256k1)
        sig_bytes = bytes.fromhex(signature_hex)
        msg_hash = hashlib.sha256(message).digest()

        if not verifying_key.verify_digest(sig_bytes, msg_hash):
            return jsonify({"error": "Invalid signature"}), 403

    except (BadSignatureError, ValueError) as e:
        return jsonify({"error": f"Signature verification failed: {str(e)}"}), 403

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

    fetch_all_peers_and_resolve()
    chain.mine_pending_transactions(miner)
    broadcast_last_block()
    return jsonify({"message": f"Block mined by {miner}"})


@app.route("/peers", methods=["GET", "POST"])
def manage_peers():
    if request.method == "POST":
        data = request.get_json()
        peer = data.get("peer")

        if not peer:
            return jsonify({"error": "❌ Missing peer URL"}), 400

        try:
            peer = normalize_peer_url(peer)
            current_host = this_node

            if peer == current_host:
                return jsonify({"error": "❌ Cannot add self as peer"}), 400

            res = requests.get(f"{peer}/chain", timeout=2)
            if res.status_code != 200:
                raise Exception("Non-200 response")

            if peer not in peers:
                peers.add(peer)
                save_peers()

                try:
                    requests.post(f"{peer}/peers", json={"peer": current_host}, timeout=2)
                except:
                    pass

                try:
                    requests.post(f"{peer}/peers/gossip", json={"peers": list(peers)}, timeout=2)
                except:
                    pass

            return jsonify({"message": "✅ Peer added", "peers": list(peers)}), 201

        except Exception as e:
            return jsonify({"error": f"❌ Peer unreachable: {str(e)}"}), 400

    return jsonify({"peers": list(peers)})


@app.route("/peers/propagate", methods=["POST"])
def receive_propagated_peer():
    peer = request.json.get("peer")
    if peer and peer != this_node:
        peers.add(peer)
        save_peers()
    return jsonify({"message": "Propagation received"})

@app.route("/peers/gossip", methods=["POST"])
def gossip_peers():
    data = request.get_json()
    incoming = data.get("peers", [])
    new_peers = 0

    for peer in incoming:
        peer = normalize_peer_url(peer)
        if peer != this_node and peer not in peers:
            peers.add(peer)
            new_peers += 1

    if new_peers:
        save_peers()

    return jsonify({"message": f"Gossiped {new_peers} new peers."})

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

def clean_mempool_from_chain() -> None:
    confirmed = set((tx.sender, tx.receiver, tx.amount)
                    for block in chain.chain
                    for tx in block.transactions)
    chain.pending_transactions = [
        tx for tx in chain.pending_transactions
        if (tx.sender, tx.receiver, tx.amount) not in confirmed
    ]


def broadcast_last_block() -> None:
    block = chain.get_latest_block()
    for peer in peers:
        try:
            requests.post(f"{peer}/receive_block", json=block.__dict__, timeout=2)
        except:
            pass


def fetch_all_peers_and_resolve() -> Dict[str, str]:
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


def crawl_and_connect_to_peer(seed_peer: str):
    if seed_peer == this_node:
        return
    peers.add(seed_peer)

    try:
        res = requests.get(f"{seed_peer}/peers", timeout=2)
        remote_peers = res.json().get("peers", [])
        for peer in remote_peers:
            if peer != this_node:
                peers.add(peer)
                save_peers()
    except:
        pass

    # Let seed peer know about us
    try:
        requests.post(f"{seed_peer}/peers/propagate", json={"peer": this_node}, timeout=2)
    except:
        pass

def announce_to_peers():
    """
    On startup, announce this node to known peers and gossip peers.
    """
    current_host = f"http://localhost:{app.config['PORT']}"
    for peer in list(peers):
        try:
            # Ask peer to add us
            requests.post(f"{peer}/peers", json={"peer": current_host}, timeout=2)
            # Send our peers list for gossip
            requests.post(f"{peer}/peers/gossip", json={"peers": list(peers)}, timeout=2)
        except Exception as e:
            print(f"[Startup] Failed to announce to {peer}: {e}")

def prune_dead_peers(interval=30):
    """
    Periodically ping all peers and remove unreachable ones.
    """
    while True:
        time.sleep(interval)
        removed = []
        for peer in list(peers):
            try:
                res = requests.get(f"{peer}/chain", timeout=2)
                if res.status_code != 200:
                    raise Exception("Bad status")
            except:
                peers.remove(peer)
                removed.append(peer)

        if removed:
            save_peers()
            print(f"[Prune] Removed dead peers: {removed}")

def discover_local_peers(port_range=(5000, 5010)):
    current_port = app.config['PORT']
    current_host = f"http://localhost:{current_port}"

    for port in range(port_range[0], port_range[1] + 1):
        if port == current_port:
            continue  # skip self

        peer_url = f"http://localhost:{port}"
        try:
            res = requests.get(f"{peer_url}/chain", timeout=1)
            if res.status_code == 200:
                peer_url = normalize_peer_url(peer_url)
                if peer_url not in peers:
                    print(f"[Discovery] Found active peer at {peer_url}")
                    peers.add(peer_url)
                    save_peers()

                try:
                    requests.post(f"{peer_url}/peers", json={"peer": current_host}, timeout=1)
                except:
                    pass
        except:
            pass  # peer not online


def periodic_local_discovery(interval=30):
    while True:
        discover_local_peers()
        time.sleep(interval)



peer_failures = {}

def heartbeat_peers():
    while True:
        time.sleep(10)  # every 10 seconds
        to_remove = []

        for peer in list(peers):
            try:
                res = requests.get(f"{peer}/ping", timeout=2)
                if res.status_code == 200:
                    peer_failures[peer] = 0  # reset failure count
                else:
                    peer_failures[peer] = peer_failures.get(peer, 0) + 1
            except:
                peer_failures[peer] = peer_failures.get(peer, 0) + 1

            if peer_failures[peer] >= 3:
                to_remove.append(peer)

        for peer in to_remove:
            peers.discard(peer)
            peer_failures.pop(peer, None)
            save_peers()
            print(f"❌ Removed unreachable peer: {peer}")



if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument("--seed", type=int, help="Optional seed peer port")
    args = parser.parse_args()

    # Store this node's port globally
    app.config['PORT'] = args.port
    this_node = normalize_peer_url(f"http://localhost:{args.port}")

    # Load existing peers
    load_peers()

    # If no peers saved, scan for local ones
    if not peers:
        discover_local_peers(port_range=(5000, 5010))

    # Announce ourselves to known peers and gossip
    announce_to_peers()

    # Start pruning
    threading.Thread(target=prune_dead_peers, daemon=True).start()
    threading.Thread(target=periodic_local_discovery, daemon=True).start()
    threading.Thread(target=heartbeat_peers, daemon=True).start()

    app.run(port=args.port)
