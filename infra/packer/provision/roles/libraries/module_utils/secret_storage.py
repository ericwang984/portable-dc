import json
from binascii import hexlify, unhexlify

from Crypto import Random
from Crypto.Cipher import AES


def generate_iv():
    """
    Generate a random, 16-byte initialization vector for AES.

    :return: 16-byte binary string
    :rtype: str
    """
    return Random.new().read(16)


def pad_aes(value):
    """
    Pad a value with NULs to align to the AES.block_size. The input is not mutated.
    Taken from https://stackoverflow.com/questions/44850023.

    :param value: input value to pad
    :type value: str
    :return: padded value
    :rtype: str
    """
    length = len(value)
    pad_size = AES.block_size - (length % AES.block_size)

    return value.ljust(length + pad_size, '\x00')


def unpad_aes(value):
    """
    Strip trailing NUL bytes from a string. Input is not mutated.

    :param value: input value to strip
    :type value: str
    :return: 'unpadded' value
    :rtype: str
    """

    return value.decode('utf-8').rstrip('\x00')


def encrypt_aes(plain, iv, key, segment_size=128):
    """
    Create an AES object and use it to encrypt a plain-text secret.

    :param plain: the secret to be encrypted
    :type plain: str
    :param iv: a random initialization vector
    :type iv: str
    :param key: private key to encrypt the secret with
    :type key: str
    :param segment_size: CFB segment size (default: 128)
    :type segment_size: int
    :return: ciphertext
    :rtype: str
    """
    aes = AES.new(key, AES.MODE_CFB, iv, segment_size=segment_size)

    return aes.encrypt(plain)


def decrypt_aes(encrypted, iv, key, segment_size=128):
    """
    Create an AES object and use it to decrypt a payload.

    :param encrypted: encrypted payload to be decrypted
    :type encrypted: str
    :param iv: the initialization vector the payload was encrypted with
    :type iv: str
    :param key: private key to use to decrypt the payload
    :type key: str
    :param segment_size: CFB segment size (default: 128)
    :type segment_size: int
    :return: the decrypted value
    :rtype: str
    """
    aes = AES.new(key, AES.MODE_CFB, iv, segment_size=segment_size)

    return aes.decrypt(encrypted)


def armor_wrap(iv, payload):
    """
    Wrap an IV and payload in a dictionary with the `iv` and `payload` keys,
    individually hex-encode them and JSON-encode the dictionary.

    :param iv: the initialization vector the secret was encrypted with
    :type iv: str
    :param payload: the encrypted payload
    :type payload: str
    :return: json-encoded dict with `iv` and `payload` keys
    :rtype: str
    """

    return json.dumps({
        'iv': hexlify(iv),
        'payload': hexlify(payload)
    })


def armor_unwrap(blob):
    """
    Unwrap a JSON-encoded `iv`/`payload` dictionary
    into their respective values.

    :param blob: the json-encoded blob
    :type blob: str
    :return: iv, payload tuple
    :rtype: tuple
    :raises: ValueError when `iv` or `payload` is missing in the blob
    """
    jd = json.loads(blob)

    iv = jd.get('iv', None)
    payload = jd.get('payload', None)

    if iv is None:
        raise ValueError('`iv` field not present in json object')
    if payload is None:
        raise ValueError('`payload` field not present in json object')

    return unhexlify(iv), unhexlify(payload)


def encrypt(secret, key):
    """
    Encrypt a secret with a given key. Implicitly generates
    an initialization vector for use in the encryption operation.

    :param secret: the secret (payload) to encrypt
    :type secret: str
    :param key: the key to encrypt the secret with
    :type key: str
    :return: armored and json-encoded iv/payload
    :rtype: str
    """
    if len(key) not in {16, 24, 32}:
        raise ValueError('`key` needs to be either 16, 24 or 32 bytes long')

    iv = generate_iv()

    # pad the input to align with the AES block size
    psecret = pad_aes(secret)

    pl = encrypt_aes(psecret, iv, key)

    return armor_wrap(iv, pl)


def decrypt(armor, key, segment_size=128):
    """
    Decrypt a secret inside an armored iv/payload JSON string
    using the given key.

    :param armor: armored and json-encoded iv/payload
    :type armor: str
    :param key: the encryption key previously used to encrypt the payload
    :type key: str
    :param segment_size: CFB segment size (default: 128) for backwards-compatible decryption
    :type segment_size: int
    :return: the decrypted value
    :rtype: str
    """

    if len(key) not in {16, 24, 32}:
        raise ValueError('`key` needs to be either 16, 24 or 32 bytes long')

    iv, pl = armor_unwrap(armor)

    return unpad_aes(decrypt_aes(pl, iv, key, segment_size=segment_size))
