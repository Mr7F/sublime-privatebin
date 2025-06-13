import zlib
import json
import requests
import os
import sublime

from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import HMAC, SHA256


def private_bin_upload(text, host, expire):
    ITERATION_COUNT = 100000
    SALT_SIZE = 8
    KEY_SIZE_BITS = 256
    TAG_SIZE_BITS = 128
    COMPRESSION_METHOD = "zlib"
    CIPHER_MODE = "gcm"
    CIPHER_ALGORITHM = "aes"
    FORMATTER = "plaintext"
    DISCUSSION = 0
    BURN_AFTER_READING = 0

    password = os.urandom(32)
    iv = get_random_bytes(TAG_SIZE_BITS // 8)
    salt = get_random_bytes(SALT_SIZE)
    key = PBKDF2(
        password,
        salt,
        dkLen=KEY_SIZE_BITS // 8,
        count=ITERATION_COUNT,
        prf=lambda p, s: HMAC.new(p, s, SHA256).digest(),
    )

    compressed = zlib.compress(json.dumps({"paste": text}).encode(), level=9)[2:-4]
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=TAG_SIZE_BITS // 8)
    adata = [
        [
            b64encode(iv).decode(),
            b64encode(salt).decode(),
            ITERATION_COUNT,
            KEY_SIZE_BITS,
            TAG_SIZE_BITS,
            CIPHER_ALGORITHM,
            CIPHER_MODE,
            COMPRESSION_METHOD,
        ],
        FORMATTER,
        DISCUSSION,
        BURN_AFTER_READING,
    ]

    cipher.update(json.dumps(adata, separators=(",", ":")).encode())
    ciphertext, tag = cipher.encrypt_and_digest(compressed)

    payload = {
        "v": 2,
        "adata": adata,
        "ct": b64encode(ciphertext + tag).decode(),
        "meta": {"expire": expire},
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(host, json=payload, headers=headers)
    response.raise_for_status()
    if not response.ok:
        print("Privatebin: failed, API response: ", response.text)
        sublime.status_message("Failed, API response: " + response.text)
        return None

    url = response.json().get("url")
    return host + url + "#" + base58_encode(password)


def base58_encode(data):
    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(data, "big")
    encode = ""

    while num > 0:
        num, rem = divmod(num, 58)
        encode = charset[rem] + encode

    n_pad = len(data) - len(data.lstrip(b"\0"))
    return "1" * n_pad + encode
