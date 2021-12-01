import block

class BlockPool:
    def __init__(self) -> None:
        self.blocks = []

    def block_exist(self, b):
        for bl in self.blocks:
            if bl.hash == b.hash:
                return bl
        
        return None

    def add_block(self, b):
        self.blocks.append(b)

    def block_exist_hash(self, hash):
        for bl in self.blocks:
            if bl.hash == hash:
                return bl
        
        return None
