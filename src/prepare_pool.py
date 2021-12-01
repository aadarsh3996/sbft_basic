import sbft_util

class PreparePool:
    def __init__(self) -> None:
        self.prepare_messages = {}
    
    def prepare(self, block, public_key):
        prepare = self.create_prepare(block, public_key)
        self.prepare_messages[block.hash] = []
        self.prepare_messages[block.hash].append(prepare)
        return prepare
    
    def create_prepare_message(self, block, public_key):
        prepare_message = {
            "block_hash" : block.hash,
            "public_key" : public_key,
            # Add signature
        }
        return prepare_message

    def add_prepare_message(self, prepare_message):
        self.prepare_messages[prepare_message.hash].append(prepare_message)
    
    def existing_prepare(self, prepare_message):
        for p_m in self.prepare_messages:
            if p_m.block_hash == prepare_message.block_hash:
                return p_m
        
        return None
    
    # Add is_valid_prepare_message