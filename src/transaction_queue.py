import transaction

class TransactionQueue:
    def __init__(self) -> None:
        self.transactions = []
    
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        if len(self.transactions)== 1:
            return True
        else:
            False
    
    def transaction_exist(self, t):
        for transaction in self.transactions:
            if transaction.id == t.id:
                return True
        
        return False
    
    def clear(self):
        self.transactions = []
