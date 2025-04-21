🧱 My Blockchain Wallet
This project is a full-stack, peer-to-peer blockchain wallet system written in Python with a live web interface. It includes all core blockchain mechanics—mining, transactions, balances, peer-to-peer syncing, and mempool management—with a sleek and interactive UI built using Bootstrap and JavaScript.

Built entirely from scratch as a learning project, this blockchain is a lightweight simulation that mimics real cryptocurrency behavior.

🚀 Features
⛓️ Blockchain:

Genesis block

Proof-of-Work mining with adjustable difficulty

Transaction validation and balance tracking

Chain validity check and automatic conflict resolution

👛 Wallet:

ECDSA (secp256k1) cryptographic wallet generation

Each wallet has a public/private keypair and blockchain address

Temporary storage of private keys for signing (dev mode only)

🔀 Mempool:

Shared list of unconfirmed transactions (pending state)

Auto-synchronization across all connected peers

⛏️ Mining:

Rewards users with 100 coins per block

Broadcasts new blocks to peers and cleans mempool across nodes

Mining difficulty is adjustable

🌐 P2P Network:

Peer registration by port number or full URL

Auto-resolution of the longest chain

Auto-broadcast of transactions and blocks

🖥️ Interactive Web UI (via Flask + Bootstrap):

Wallet generation and address display

Transaction form (create and sign)

Live blockchain explorer

Pending transaction dashboard

Peer management panel

Progress feedback while mining blocks

🛠️ Technologies & Libraries
Python 3.10+

Flask – web server and API routing

requests – for peer communication

ecdsa – wallet cryptography (secp256k1)

Bootstrap 5 – responsive UI

JavaScript (ES6+) – interactive front-end logic

🧠 Educational Purpose
This is not a real cryptocurrency and is not intended for production use. It is a sandbox for learning about distributed systems, cryptographic signatures, proof-of-work, and web development.
