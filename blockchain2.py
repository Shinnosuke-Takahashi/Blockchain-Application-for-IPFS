"""
    NOTES:
    installing requests:
    python3 -m pip install requests
    
    @: decorator
        @check 
        def func(a,b)
        
        is the same thing as
        def func(a,b)
        func = check(func)
        
"""

import hashlib
import json
from time import time
from urllib import response
from urllib.parse import urlparse
from uuid import uuid4

from collections.abc import Mapping

import requests
from flask import Flask, jsonify, request

class Blockchain:
    #constructor
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        
        #genesis
        self.new_block(previous_hash = '1', proof = 100)
    
    def register_node(self, address):
        """adds new Node to the list

        Args:
           address: address of new Node to be added

        Raises:
            ValueError: if URL does not go through or is invalid
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('URL invalid')
    
    def valid_chain(self, chain):
        """determines if a blockchain is valid

        Args:
            chain: blockchain
        
        Returns: bool; true if valid
        """
        
        last_block = chain[0]
        current_index = 1
        
        while current_index < len (chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            #checking if hash of block is correct
            last_block_hash = self.hash(last_block)
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False
            last_block = block
            current_index += 1
            
        return True
    
    def resolve_conflicts(self):
        """consensus algo. replaces chain with longest one in the network
        
        return: True if chain was replaced, False if not
        """
        
        neighbors = self.nodes
        new_chain = None
        
        #looking for chains longer than ours
        max_length = len(self.chain)
        
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
            
        if new_chain:
            self.chain = new_chain
            return True
            
        return False
        
    def new_block(self, proof, previous_hash):
        """Creates new Block in blockchain

        Args:
            proof: PoW
            previous_hash: hash of previous block
        
        Return:
            new block
        """
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        
        #reset pending transactions
        self.current_transactions = []
        
        self.chain.append(block)
        return block
    
    def new_transaction(self, sender, recipient, bookID):
        """Creates new transaction to go into next mined Block

        Args:
            sender: address of sender
            recipient: address of recipient
            bookID: bookID
            
        Return: Index of block that will hold this transaction
        """
        
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'bookID': bookID,
        })
        
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]
    
    @staticmethod
    def hash(block):
        """genrates SHA-256 hash of a Block
        
        block: Block
        """
        
        #ordering the dictionary
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, last_block):
        """PoW algorithm

        Args:
            last_block (dict): last Block
            
        Return (int): Proof of Work
        """
        
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        
        #proof includes nonce value
        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        
        return proof
    
    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """Validates proof

        Args:
            last_proof (int): previous proof
            proof (int): current proof
            last_hash (str): hash of previous block
            
        Returns: True if correct
        """
        
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        
        #DIFFICULTY SETTING HERE
        return guess_hash[:4] == "0000"
    
#instantiate node
app = Flask(__name__)

#generate unique address for node; removes all '-'
node_id = str(uuid4()).replace('-','')

#instantiate blockchain
blockchain = Blockchain()


## DEFINING BACKEND BELOW
@app.route('/mine', methods = ['GET'])
def mine():
    #run the PoW algo to get next proof
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    #sender is '0' to signify that this block is generated with no transactions yet
    blockchain.new_transaction(
        sender = '0',
        recipient = node_id,
        bookID = "0",
    )
    
    #Add new block to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    
    #Checks that the required fields are in the POST data
    required = ['sender', 'recipient', 'bookID']
    if not all (k in values for k in required):
        return 'Missing values', 400
    
    #Create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['bookID'])
    
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: node list invalid or empty", 400
    
    for node in nodes:
        blockchain.register_node(node)
        
    response = {
        'message': 'New nodes added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/list', methods = ['GET'])
def get_neighbors():
    """Returns list of all nodes
    """
    response = {
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200
        

@app.route('/nodes/resolve', methods = ['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    
    if replaced:
        response = {
            'message': 'Chain has been replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Chain has not been replaced; it is authoritative',
            'chain': blockchain.chain
        }
        
    return jsonify(response), 200    

if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default = 5001, type = int, help = 'port to listen on')
    args = parser.parse_args()
    port = args.port
    
    app.run(host='0.0.0.0', port=port)