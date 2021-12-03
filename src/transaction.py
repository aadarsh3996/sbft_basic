from typing import OrderedDict
import sbft_util
from collections import OrderedDict
class Transaction:
    def __init__(self, data, auth) -> None:
        self.transaction_id = sbft_util.create_transaction_id()
        self.user = auth.public_key
        self.input = {"data":data, "timestamp":int(sbft_util.time_now())}
        self.encrypted_message = sbft_util.encrypt_data(self.user, self.input)

    def verify_transaction(self, transaction):
        try:
            sbft_util.decrypt_data(auth.private_key, self.encrypted_message)
            return True
        except Exception:
            return False



        