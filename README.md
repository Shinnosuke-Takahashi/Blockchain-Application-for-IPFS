# Capstone_Blockchain: Emulation of the Application Layer for an InterPlanetary File System
Blockchain project for Capstone course at CUNY Hunter College, Spring 2022 by **Shinnosuke Takahashi**

## Overview:

An InterPlanetary File System (IPFS) is a system in which shared files are split into smaller chunks and distributed across all parties ("nodes") on the system. These chunks can then later be recombined by any node to form the original file. Each node keeps track of which files to recombine using a blockchain mechanism which, much like that of the book bartering system, is shared across all nodes and allows for individual validation and consensus.

### The Blockchain:

In this execution of an IPFS, we have a dictionary of blockchains where the key is the name of the file (eg. "file1.txt"), and the value is the associated chain. Each chain is composed of blocks that each represent a file chunk. Each block holds a singular transaction, which contains the name of the file chunk it represents (eg. "file1a.txt"), a unique hash based on the byte contents of the file, the author of the file chunk, and a timestamp of when this transaction was added to the block. The unique, content-based hash of the file chunk allows each node to verify that their copy of the file chunk has not only been unaltered, but also works as intended. Each block then takes the transaction data, the block index, the proof of work, the timestamp of when the block was mined, and the previous block’s hash to create its own hash. All hashes use a 256-bit hashing algorithm called SHA-256.


### Validation and The Proof of Work:

The Proof of Work (PoW) for this IPFS is based off of that of Bitcoin, where a proof is valid if and only if, when combined with the proof and hash of the previous block and hashed, starts with four leading zeroes ("0000"). In the case of our IPFS, the previous block’s proof, current proof being tested, and the previous block’s hash are concatenated into a string and then hashed. The "difficulty" of the proof can be adjusted by changing the number of zeroes required in a valid proof; the more zeroes, the more time and computing power needed to create a valid proof, and therefore it is more "difficult" to create one.


### The Consensus Algorithm:

The consensus algorithm of this IPFS relies on the length of the chain. A node will request a copy of every other node’s chain, and will replace its own chain if it finds another chain that is both valid and longer than itself. 

### What still needs to be addressed:

While this blockchain system is functional, there are some tweaks that must still be made in order to strengthen security and flexibility:
 - Must implement an additional layer of hashing on file names to allow files with the same name but altering contents to coexist on the IPFS. Hashes would replace file names in the dictionary, but work in tandem when looking up files on the system. These hashes would be based on factors such as: file contents, file name, date uploaded to the IPFS, and randomly generated integer “nonce” values for increased uniqueness.
  - Because consensus is length-based, a bad actor could ruin the chain by locally creating a long ‘false’ chain that shares a name with a chain that already exists. If the bad actor builds a chain of compromised file chunks that is longer than the global chain, the chain could still be considered valid and therefore replace the global chain. There are two known methods to solve this issue:
    - When attempting to add a new file, a node could be forced to search the dictionary of blockchains (the IPFS) for a global chain associated with the ID of the file. If found, the node can be forced to replace its own chain with the global chain. Because chains cannot be deleted or destroyed, it would be impossible to create a new (and potentially malevolent) chain from scratch.
    - The inclusion of an ‘end’ block to each chain, making a local chain irreplaceable if included, could prevent unauthorized lengthening of a chain. If a local chain cannot be replaced (ie. edited), then it cannot attempt to alter the global chain.
  - Currently, every genesis block starts with a proof of ‘100’. Each genesis block’s proof could be randomly generated to increase complexity of block hashes.
  - In addition to consensus regarding the contents of each blockchain, consensus functionality could be applied to adjusting global mining difficulty as well. This could allow for flexibility in blockchain growth speed, which will help prevent flooding.
  - Currently, all code resides in one file. Splitting of validation code, proof code, consensus code, transaction code, block code, blockchain code and HTTP response code into separate files would help with organization as well as security.

## How to run:

Run 'blockchain.py', 'blockchain2.py', 'blockchain3.py'.
Each program represents a different node.

	- 'blockchain.py' acts on localhost:5000.
	- 'blockchain2.py' acts on localhost:5001.
	- 'blockchain3.py' acts on localhost:5002.

Use a program that can send HTTP requests, such as Postman, to interact with the blockchain.
**All HTTP requests, with the exception of '/chain', require an associated body in raw, JSON format.**

I have included several text file "chunks" for testing purposes.
A file "file#x.txt" represents a chunk of a hypothetical file "file#.txt".

## Requests:

**'/newfile'** : adds new blockchain to the dictionary
  type: POST
  requires:
    "fileID" : string of file name
  
**'/nodes/register'** : adds new node addresses to whitelist
  type: POST
  requires:
    "fileID" : string of file name,
    "nodes": list of strings with node addresses
 
**'/nodes/list'** : returns list of nodes on whitelist
  type: GET
  requires:
    "fileID" : string of file name
    
**'/transactions/new'** : adds new transaction
  type: POST
  requires:
    "fileID" : string of file name,
    "author" : string of your public address,
    "block name" : string of file chunk name

**'/mine'** : adds new block
  type: POST
  requires:
    "fileID" : string of file name,
    "author" : string of your public address

**'/nodes/resolve'** : calls consensus algorithm
  type: POST
  requires:
    "fileID" : string of file name

**'chain'** : returns all chains
  type: GET
