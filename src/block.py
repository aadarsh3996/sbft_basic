import sbft_util
import hashlib

# TODO Verify block and sign block hash

class Block:
    def __init__(self, timestamp, last_hash, hash, data, proposer, sequence_number) -> None:
        self.timestamp = timestamp
        self.last_hash = last_hash
        self.hash = hash
        self.data =  data
        self.proposer = proposer
        self.sequence_number = sequence_number
    
    def __str__(self) -> str:
        return "Block "+self.timestamp+" "+ self.last_hash+" "+ self.hash+" "+self.data+" " + self.proposer +" " + self.sequence_number
    
    def genesis_block(self):
        return Block(123, "temp","genesis_hash", [], "random proposer", 0)
    
    def create_new_block(self, last_block, data, public_key):
        timestamp = sbft_util.time_now()
        last_hash = last_block.hash
        hash = Block.compute_hash(timestamp, last_hash, data)
        proposer = public_key
        return Block(timestamp, last_hash, hash, data, proposer, 1+last_block.sequence_number)

    def compute_hash(timestamp, last_hash, data):
        return hashlib.sha256("{}:{}:{}".format(timestamp, last_hash, data).encode('utf-8')).hexdigest()
    
    def verify_proposer(self, block, proposer):
        return block.proposer == proposer

        
        