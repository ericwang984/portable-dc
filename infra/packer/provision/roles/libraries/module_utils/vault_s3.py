import json

from botocore.exceptions import ClientError

# Use module_utils_loader to dynamically import module_utils from an action plugin
try:
    from ansible.module_utils.secret_storage import encrypt, decrypt
except ImportError:
    from ansible.plugins.loader import module_utils_loader as ml

    ss = ml._load_module_source('secret_storage', ml.find_plugin('secret_storage'))

    encrypt = ss.encrypt
    decrypt = ss.decrypt

# Location of the environment's keyfile in the bucket
KEY_PATH_FORMAT = 'environments/{env}/vault/keys'


def bucket_exists(client, bucket):
    """
    Check if an S3 bucket exists.

    :param client: boto3 client instance
    :param bucket: name of the S3 bucket
    :type bucket: str
    :return: whether the bucket exists
    :rtype: bool
    """

    blist = client.list_buckets()

    return bucket in [b['Name'] for b in blist['Buckets']]


def key_path(environment):
    """
    Render the path to the environment's encrypted Vault keyfile in object storage.

    :param environment: environment the Vault keyfile belongs to
    :return: path in object storage
    :rtype: str
    """

    return KEY_PATH_FORMAT.format(env=environment)


def sanitize_vault_keys(vault_keys):
    """
    Check and sanitize (re-encapsulate) a Vault keys configuration.
    This yields a dictionary with the following keys:
    - root_token
    - keys
    - keys_base64

    :param vault_keys: the Vault keys verify and re-encapsulate
    :type vault_keys: dict
    :return: sanitized Vault keys
    :rtype: dict
    """

    # extract tokens from Vault initialization
    try:
        root_token = vault_keys['root_token']
        keys = vault_keys['keys']
        keys_base64 = vault_keys['keys_base64']
    except KeyError as e:
        raise ValueError('vault_keys is missing `{}`'.format(e))

    # assemble Vault keys object to be encrypted and stored in S3
    result = {
        'root_token': root_token,
        'keys': keys,
        'keys_base64': keys_base64
    }

    return result


def get_keys_s3(client, bucket, environment, crypt_secret):
    """
    Get Vault keys from S3.

    :param client: boto3 client instance
    :param bucket: name of the S3 bucket
    :type bucket: str
    :param environment: environment the Vault keys belong to
    :type environment: str
    :param crypt_secret: object storage encryption secret
    :return: the object string, or None
    :rtype: str
    :raises: ClientError if it's not a `NoSuchKey`
    """

    blob = None

    try:
        # raises ClientError if the key is not found in the bucket
        # raises KeyError of the key does not contain a body
        blob = client.get_object(Bucket=bucket, Key=key_path(environment=environment)).get('Body').read()

    except KeyError:
        return None

    except ClientError as e:
        # re-raise when the error code isn't 'NoSuchKey'
        if e.response['Error']['Code'] != "NoSuchKey":
            raise e

    try:
        # attempt to decrypt object from object storage with default segment size (128)
        vault_json = decrypt(blob, crypt_secret)
        # decode the decrypted json string
        vault_keys = json.loads(vault_json)
    except Exception as e:
        try:
            # fallback to 8-bit segment size (backwards compatibility)
            vault_json = decrypt(blob, crypt_secret, segment_size=8)
            vault_keys = json.loads(vault_json)
        except Exception:
            raise ValueError('error decrypting or interpreting vault_json: {}'.format(e))

    # validate the output and return
    return sanitize_vault_keys(vault_keys)


def put_keys_s3(client, bucket, environment, vault_keys, crypt_secret):
    """
    Write Vault keys to S3.

    :param client: boto3 client instance
    :param bucket: name of the S3 bucket
    :type bucket: str
    :param environment: environment the Vault keys belong to
    :type environment: str
    :param vault_keys: the Vault keys to store
    :type vault_keys: dict
    :param crypt_secret: object storage encryption secret
    :type crypt_secret: str
    :return: operation success
    :rtype: bool
    :raises ClientError: any S3 errors
    """

    # check and re-encapsulate a dictionary holding Vault keys
    # (root_token, keys, keys_base64)
    vault_json = json.dumps(sanitize_vault_keys(vault_keys))

    # encrypt and armor (iv/payload) the Vault keys
    try:
        vault_crypt = encrypt(vault_json, crypt_secret)
    except Exception as e:
        raise ValueError('error encrypting vault_json: {}'.format(e))

    # push the keys to object storage
    client.put_object(Bucket=bucket, Key=key_path(environment=environment), Body=vault_crypt)

    return True
