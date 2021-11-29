import rsa
import uuid

def generate_rsa_key_pairs():
    
    key_pairs = {}
    public_key, private_key = rsa.newkeys(2048)
    key_pairs['public_key'] = public_key.save_pkcs1().decode('utf8')
    key_pairs['private_key'] = private_key.save_pkcs1().decode('utf8')
    return key_pairs

def encrypt_data(encryption_key, message):
    
    return rsa.encrypt(message.encode('utf-8'), rsa.PublicKey.load_pkcs1(encryption_key.encode('utf-8')))

def decrypt_data(decryption_key, message):

    return rsa.decrypt(message, rsa.PrivateKey.load_pkcs1(decryption_key.encode('utf-8'))).decode('utf-8')

def create_transaction_id():
    return str(uuid.uuid4())