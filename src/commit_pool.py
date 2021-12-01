import sbft_util

class CommitPool:
    def __init__(self) -> None:
        self.commit_messages = {}
    
    def commit(self, block, public_key):
        commit_message = self.create_commit(block, public_key)
        self.commit_messages[block.hash] = []
        self.commit_messages[block.hash].append(commit_message)
        return commit_message
    
    def create_commit_message(self, block, public_key):
        commit_message = {
            "block_hash" : block.hash,
            "public_key" : public_key,
            # Add signature
        }
        return commit_message

    def add_commit_message(self, commit_message):
        self.commit_messages[commit_message.hash].append(commit_message)
    
    def existing_commmit(self, commit_message):
        for p_m in self.commit_messages:
            if p_m.block_hash == commit_message.block_hash:
                return p_m
        
        return None
    
    def add_commit(self, commit):
        self.commit_messages[commit.block_hash].append(commit)
    
    # Add is_valid_commit_message