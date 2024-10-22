import json
from pathlib import Path
import pickle
import socket
import struct
import random
import hashlib

from Crypto.Cipher import AES
from Crypto.Util import Counter
from py_ecc.secp256k1 import secp256k1

ROOT_DIR = Path(__file__).resolve().parent.parent
KEY_STORAGE_DIR = ROOT_DIR / 'key_storage'
KEY_STORAGE_DIR.mkdir(exist_ok=True)
G = secp256k1.G
N = secp256k1.N

def generate_keys(filename):
    pk_name = KEY_STORAGE_DIR / f"{filename}.pk.json"
    sk_name = KEY_STORAGE_DIR / f"{filename}.sk.json"

    if sk_name.exists():
        with open(sk_name, "r") as f:
            private_key = json.load(f)
        with open(pk_name, "r") as f:
            public_key = json.load(f)
    else:
        private_key = random.randint(1, N - 1)
        public_key = multiply(private_key)

        with open(pk_name, 'w') as f:
            json.dump(public_key, f)
        with open(sk_name, 'w') as f:
            json.dump(private_key, f)

    return private_key, public_key

def aes_encrypt(message, key):
    if isinstance(message, str):
        message = message.encode('utf-8')

    ctr = Counter.new(128)
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    ciphertext = aes.encrypt(message)
    return ciphertext

def aes_decrypt(ciphertext, key):
    ctr = Counter.new(128)
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    decrypted_message = aes.decrypt(ciphertext)
    return decrypted_message.decode('utf-8')

def recvall(sock, length):
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def send_data(conn, data):
    serialized_data = pickle.dumps(data)
    data_length = struct.pack('!I', len(serialized_data))
    conn.sendall(data_length)
    conn.sendall(serialized_data)

def recvall(sock, length):
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def receive_data(sock):
    raw_data_length = recvall(sock, 4)
    if not raw_data_length:
        return None

    data_length = struct.unpack('!I', raw_data_length)[0]
    serialized_data = recvall(sock, data_length)
    data = pickle.loads(serialized_data)

    return data

def get_local_ip():
    print(socket.gethostbyname(socket.gethostname()))
    return socket.gethostbyname(socket.gethostname())

def generate_shared_key(private_key, public_key):
    shared_secret = secp256k1.multiply(public_key, private_key)
    return hashlib.sha256(str(shared_secret[0]).encode()).digest()

def is_valid_public_key(public_key):
    if not isinstance(public_key, tuple) or len(public_key) != 2:
        return False
    x, y = public_key
    left = (y * y) % secp256k1.curve_order
    right = (x * x * x + 7) % secp256k1.curve_order
    return left == right

def add_public_keys(pk1, pk2):
    return secp256k1.add(pk1, pk2)

def multiply(scalar):
    point = G
    return secp256k1.multiply(point, scalar)

