"""
Author: Shinnosuke Takahashi
CUNY Hunter College, Spring 2022

This program serves as the application layer for an InterPlanetary File System.
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

class Blockchain: #ie. file
    #constructor
    def __init__(self, id):
        #this is the file ID
        self.id = id
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        
        #genesis block
        self.new_block(previous_hash = 'genesis', proof = 100)
    
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
        """determines if a blockchain is valid by checking hashes

        Args:
            chain: blockchain
        
        Returns: bool; true if valid
        """
        last_block = chain[0]
        current_index = 1
        
        while current_index < len (chain):
            block = chain[current_index]
            print('{last_block}')
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
            URL = f'http://{node}/chain'
            response = requests.get(url = URL)  
                    
            if response.status_code == 200:
                length = response.json()[f'{self.id} LENGTH']
                chain = response.json()[f'{self.id} CHAIN']
                
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
    
    def new_transaction(self, author, blockname):
        """Creates new transaction to go into next mined Block

        Args:
            author: address of author
            blockname: name of file chunk
            
        Return: Index of block that will hold this transaction
        """
        filehash = '0'
        if blockname != '0':
            #rb is for Reading as Binary
            with open(blockname, "rb") as f:
                prehash = f.read()
                filehash = hashlib.sha256(prehash).hexdigest()
        
        self.current_transactions.append({
            'author': author,
            'block name': blockname,
            'file hash': filehash,
            'timestamp': time(),
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
        #ordering the dictionary as to create reliable standard for hash generation
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
        
        #DIFFICULTY SETTING HERE; checking if first 4 characters of our guess hash are '0000'
        return guess_hash[:4] == "0000"
    
#instantiate node
app = Flask(__name__)

#generate unique address for node; removes all '-'
node_id = str(uuid4()).replace('-','')

#instantiate blockchain dictionary
blockchain = {}

#################################################
#################################################
## DEFINING BACKEND BELOW
#################################################
#################################################
@app.route('/newfile', methods = ['POST'])
def newBlockchain():
    #new blockchain for new files
    values = request.get_json()
    required = ['fileID']
    if not all (k in values for k in required):
        return 'Missing values: fileID', 400
    
    if values['fileID'] in blockchain:
        return f'{values["fileID"]} already exists!', 400
    
    #new blockchain for new file created  
    blockchain[values['fileID']] = Blockchain(values['fileID'])
    
    currentBlockchain = blockchain[values['fileID']]
    
    response = {
        'fileID': currentBlockchain.id,
        'message': 'new local Blockchain created'
        }
    return jsonify(response), 201

@app.route('/mine', methods = ['POST'])
def mine():
    #mines new block
    values = request.get_json()
    required = ['fileID']
    if not all (k in values for k in required):
        return 'Missing values: fileID', 400
    
    currentBlockchain = blockchain[values['fileID']]
    
    #run the PoW algo to get next proof
    last_block = currentBlockchain.last_block
    proof = currentBlockchain.proof_of_work(last_block)

    #Add new block to chain
    previous_hash = currentBlockchain.hash(last_block)
    block = currentBlockchain.new_block(proof, previous_hash)
    
    response = {
        'fileID': currentBlockchain.id,
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    #adds new transaction
    values = request.get_json()
    
    #Checks that the required fields are in the POST data
    required = ['author', 'block name', 'fileID']
    if not all (k in values for k in required):
        return 'Missing values', 400
    currentBlockchain = blockchain[values['fileID']]
    
    #Create new transaction
    index = currentBlockchain.new_transaction(values['author'], values['block name'])
    
    response = {
        'fileID': currentBlockchain.id,
        'message': f'Transaction will be added to Block {index}',
        }
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    #gets chain
    response = {}
    _blocks = 0
    for chain in blockchain:
        response[f"{blockchain[chain].id} CHAIN"] = blockchain[chain].chain
        response[f"{blockchain[chain].id} LENGTH"] = len(blockchain[chain].chain)
        _blocks += len(blockchain[chain].chain)
    response[f"Total number of files"] = len(blockchain)
    response[f"Total number of Blocks"] = _blocks
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    #adds new node addresses to whitelist
    values = request.get_json()
    required = ['fileID']
    if not all (k in values for k in required):
        return 'Missing values: fileID', 400
    
    currentBlockchain = blockchain[values['fileID']]

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: node list invalid or empty", 400
    
    for node in nodes:
        currentBlockchain.register_node(node)
        
    response = {
        'fileID': currentBlockchain.id,
        'message': 'New nodes added',
        'total_nodes': list(currentBlockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/list', methods = ['GET'])
def get_neighbors():
    #Returns list of all nodes
    values = request.get_json()
    required = ['fileID']
    if not all (k in values for k in required):
        return 'Missing values: fileID', 400
    
    currentBlockchain = blockchain[values['fileID']]
    response = {
        'fileID': currentBlockchain.id,
        'total_nodes': list(currentBlockchain.nodes)
    }
    return jsonify(response), 200
        

@app.route('/nodes/resolve', methods = ['POST'])
def consensus():
    #calls on consensus algorithm
    values = request.get_json()
    required = ['fileID']
    if not all (k in values for k in required):
        return 'Missing values: fileID', 400
    
    currentBlockchain = blockchain[values['fileID']]
    replaced = currentBlockchain.resolve_conflicts()
    
    if replaced:
        response = {
            'fileID': currentBlockchain.id,
            'message': 'Chain has been replaced',
            'new_chain': currentBlockchain.chain
        }
    else:
        response = {
            'fileID': currentBlockchain.id,
            'message': 'Chain has not been replaced; it is authoritative',
            'chain': currentBlockchain.chain
        }
        
    return jsonify(response), 200    

if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default = 5002, type = int, help = 'port to listen on')
    args = parser.parse_args()
    port = args.port
    
    app.run(host='0.0.0.0', port=port)