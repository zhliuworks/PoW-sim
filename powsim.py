from copy import deepcopy
from hashlib import sha256
from time import time


class Block:
    hash_difficulty = 0
    max_hash_times = 0

    def __init__(self, timestamp, transaction, prev_hash=''):
        self.timestamp = timestamp
        self.transaction = transaction
        self.prev_hash = prev_hash
        self.nonce = 0
        self.curr_hash = self.hash()

    def hash(self):
        data = f'{self.timestamp}{self.transaction}{self.prev_hash}{self.nonce}'
        return sha256(data.encode()).hexdigest()

    def mine(self):
        while True:
            self.curr_hash = self.hash()
            if not self.curr_hash.startswith('0' * Block.hash_difficulty):
                self.nonce += 1
                if self.nonce >= Block.max_hash_times:
                    return False
                continue
            else:
                return True


class Message:
    def __init__(self, sender_id, len_chain, chain):
        self.sender_id = sender_id
        self.len_chain = len_chain
        self.chain = chain

    
class Node:
    channels = {}
    max_trials_honest = 0
    max_trials_malicious = 0
    
    def __init__(self, id, num_node, num_malicious):
        self.id = id
        self.chain = [Block(time(), 'genesis')]
        self.num_node = num_node
        self.num_malicious = num_malicious

    @staticmethod
    def is_valid_chain(chain):
        for i in range(len(chain)):
            curr_block = chain[i]
            if i > 0 and curr_block.prev_hash != chain[i - 1].curr_hash:
                return False
            if curr_block.curr_hash != curr_block.hash():
                return False
            if curr_block.nonce > Block.max_hash_times:
                return False
            if i > 0 and not curr_block.curr_hash.startswith('0' * Block.hash_difficulty):
                return False
        return True

    def broadcast(self):
        msg = Message(self.id, len(self.chain), self.chain)
        for id, chan in Node.channels.items():
            if id == self.id:
                continue
            chan.put(msg)

    def consensus(self):
        self.broadcast()
        orig_len_chain = len(self.chain)
        max_len_chain = orig_len_chain
        max_chain_reference = None
        max_chain_sender = self.id
        for _ in range(self.num_node - 1):
            msg = Node.channels[self.id].get()
            if self.is_valid_chain(msg.chain) and msg.len_chain > max_len_chain:
                max_len_chain = msg.len_chain
                max_chain_reference = msg.chain
                max_chain_sender = msg.sender_id
        if max_len_chain > len(self.chain):
            self.chain = deepcopy(max_chain_reference)

        if max_chain_sender == self.id:
            print('Consensus: node {}, len {:3d}'.format(self.id, len(self.chain)))
        elif max_chain_sender < self.num_malicious:
            print('Consensus: node {}, len {:3d} -> {:3d}, sync from node {} (malicious)'.
                  format(self.id, orig_len_chain, len(self.chain), max_chain_sender))
        else:
            print('Consensus: node {}, len {:3d} -> {:3d}, sync from node {} (honest)'.
                  format(self.id, orig_len_chain, len(self.chain), max_chain_sender))

    def attack(self):
        self.broadcast()
        print('  Attacks: node {}, len {:3d}'.format(self.id, len(self.chain)))

    def mine(self, transaction):
        block = Block(time(), transaction, self.chain[-1].curr_hash)
        if block.mine():
            self.chain.append(block)
            return True
        # print('[INFO] node {} reaches maximum hash times {}'.
        #       format(self.id, Block.max_hash_times))
        return False

    def run(self, consensus_locks, mine_locks):
        while True:
            for i in range(self.num_node):
                consensus_locks[i].acquire()
            ## consensus ##
            if self.id < self.num_malicious:
                self.attack()
            else:
                self.consensus()
            ###############
            for i in range(self.num_node):
                mine_locks[self.id].release()
            
            for i in range(self.num_node):
                mine_locks[i].acquire()
            #### mine #####
            max_trials = Node.max_trials_malicious if self.id < self.num_malicious else Node.max_trials_honest
            for i in range(max_trials):
                transaction = str(time())
                while self.mine(transaction):
                    transaction = str(time())
            ###############
            for i in range(self.num_node):
                consensus_locks[self.id].release()
            print('         :')
