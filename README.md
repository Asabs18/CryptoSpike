# 🧱 My Blockchain Wallet

This project is a full-stack, peer-to-peer blockchain wallet system written in Python with a live web interface. It includes all core blockchain mechanics—mining, transactions, balances, peer-to-peer syncing, and mempool management—with a sleek and interactive UI built using Bootstrap and JavaScript.

Built entirely from scratch as a learning project, this blockchain is a lightweight simulation that mimics real cryptocurrency behavior.

---

## 🚀 Features

### ⛓️ Blockchain
- Genesis block creation
- Proof-of-Work mining with adjustable difficulty
- Transaction validation and balance tracking
- Full chain integrity check with automatic conflict resolution

### 👛 Wallet
- ECDSA (secp256k1) cryptographic wallet generation
- Public/private keypair and blockchain address per user
- Temporary in-memory private key storage (for development only)

### 🔀 Mempool
- Shared pool of unconfirmed transactions
- Auto-synchronization of mempool across connected peers

### ⛏️ Mining
- Configurable mining difficulty
- Rewards users with 100 coins per mined block
- Automatically clears mined transactions from mempool
- Broadcasts newly mined blocks to all peers

### 🌐 Peer-to-Peer Network
- Peer registration using port number or full HTTP address
- Automatic chain resolution using longest valid chain rule
- Broadcasts both transactions and blocks to peers

### 🖥️ Web Interface (Flask + Bootstrap)
- Wallet generation and secure address display
- Transaction form with automatic digital signing
- Live blockchain explorer with mined block highlighting
- Pending transaction dashboard
- Peer management and sync panel
- Real-time feedback during block mining

---

## 🛠️ Technologies & Libraries

- Python 3.10+
- Flask – backend API and web server
- requests – peer communication
- ecdsa – wallet cryptography (secp256k1)
- Bootstrap 5 – responsive front-end design
- JavaScript (ES6+) – browser-side interactivity

---

## 🧠 Educational Purpose

This is not a real cryptocurrency and is not intended for production use.
