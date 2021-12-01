import sbft_util

class MessagePool:
    def __init__(self) -> None:
        self.mpool_messages = {}
        self.message = "INITIATE_NEW_ROUND"
    
    def mpool(self, block, public_key):
        mpool = self.create_mpool(block, public_key)
        self.mpool_messages[block.hash] = []
        self.mpool_messages[block.hash].append(mpool)
        return mpool
    
    def create_mpool_message(self, block, public_key):
        mpool_message = {
            "block_hash" : block.hash,
            "public_key" : public_key,
            # Add signature
        }
        return mpool_message

    def add_mpool_message(self, mpool_message):
        self.mpool_messages[mpool_message.hash].append(mpool_message)
    
    def existing_mpool(self, mpool_message):
        for p_m in self.mpool_messages:
            if p_m.block_hash == mpool_message.block_hash:
                return p_m
        
        return None
    
    def add_mpool_message(self, mpool):
        self.mpool_messages[mpool.block_hash].append(mpool)
    
    # Add is_valid_mpool_message