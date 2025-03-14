/**
 * VOT1 Dashboard - Wallet Integration
 * 
 * This module provides client-side functionality for connecting to Phantom Wallet,
 * performing ZK proof operations, and interacting with hex.dev.
 */

// Wallet Integration Module
const VOT1Wallet = (() => {
    // Private variables
    let _connected = false;
    let _wallet = null;
    let _provider = null;
    let _address = null;
    let _network = 'mainnet';
    let _config = {
        zkEnabled: true,
        hexEnabled: true,
        autoConnect: false
    };
    
    // Event listeners
    const _eventListeners = {
        connect: [],
        disconnect: [],
        transaction: [],
        message: []
    };
    
    /**
     * Initialize the wallet module
     * @param {Object} config - Configuration options
     * @return {Promise<boolean>} Success status
     */
    async function init(config = {}) {
        // Merge provided config with defaults
        _config = {..._config, ...config};
        
        try {
            // Check if Phantom is available in the window object
            const isPhantomInstalled = window.phantom && window.phantom.solana && window.phantom.solana.isPhantom;
            
            if (!isPhantomInstalled) {
                console.warn("Phantom wallet is not installed");
                return false;
            }
            
            // Store the provider for future use
            _provider = window.phantom.solana;
            
            // Try to auto-connect if enabled
            if (_config.autoConnect) {
                await connect();
            }
            
            // Add event listeners to Phantom
            _setupEventListeners();
            
            console.log("Wallet module initialized successfully");
            return true;
        } catch (error) {
            console.error("Failed to initialize wallet module:", error);
            return false;
        }
    }
    
    /**
     * Set up event listeners for the wallet provider
     * @private
     */
    function _setupEventListeners() {
        if (!_provider) return;
        
        _provider.on('connect', (publicKey) => {
            _address = publicKey.toString();
            _connected = true;
            
            // Notify all connect listeners
            _notifyEventListeners('connect', { address: _address });
        });
        
        _provider.on('disconnect', () => {
            _address = null;
            _connected = false;
            
            // Notify all disconnect listeners
            _notifyEventListeners('disconnect', {});
        });
        
        _provider.on('accountChanged', (publicKey) => {
            if (publicKey) {
                _address = publicKey.toString();
                _notifyEventListeners('connect', { address: _address });
            } else {
                _address = null;
                _connected = false;
                _notifyEventListeners('disconnect', {});
            }
        });
    }
    
    /**
     * Notify all event listeners of a specific event
     * @param {string} eventName - Name of the event
     * @param {Object} data - Event data
     * @private
     */
    function _notifyEventListeners(eventName, data) {
        if (!_eventListeners[eventName]) return;
        
        _eventListeners[eventName].forEach(listener => {
            try {
                listener(data);
            } catch (error) {
                console.error(`Error in ${eventName} event listener:`, error);
            }
        });
    }
    
    /**
     * Connect to the Phantom wallet
     * @return {Promise<Object>} Connection result
     */
    async function connect() {
        try {
            if (!_provider) {
                throw new Error("Wallet provider not initialized");
            }
            
            // Connect to the wallet
            const response = await _provider.connect();
            _wallet = response;
            _address = response.publicKey.toString();
            _connected = true;
            
            // Also notify the server
            await fetch('/api/wallet/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: 'connect',
                    wallet_type: 'phantom',
                    network: _network,
                    address: _address
                })
            });
            
            console.log("Connected to wallet:", _address);
            return {
                success: true,
                address: _address,
                network: _network
            };
        } catch (error) {
            console.error("Failed to connect to wallet:", error);
            _connected = false;
            _address = null;
            
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Disconnect from the wallet
     * @return {Promise<Object>} Disconnection result
     */
    async function disconnect() {
        try {
            if (!_provider) {
                throw new Error("Wallet provider not initialized");
            }
            
            // Disconnect from the wallet
            await _provider.disconnect();
            _connected = false;
            _address = null;
            
            // Also notify the server
            await fetch('/api/wallet/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: 'disconnect'
                })
            });
            
            console.log("Disconnected from wallet");
            return {
                success: true
            };
        } catch (error) {
            console.error("Failed to disconnect from wallet:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Sign a message using the connected wallet
     * @param {string} message - Message to sign
     * @return {Promise<Object>} Signing result
     */
    async function signMessage(message) {
        try {
            if (!_connected || !_provider) {
                throw new Error("Wallet not connected");
            }
            
            // Encode the message to Uint8Array
            const encodedMessage = new TextEncoder().encode(message);
            
            // Sign the message with the wallet
            const signature = await _provider.signMessage(encodedMessage, 'utf8');
            
            // Notify event listeners
            _notifyEventListeners('message', {
                message,
                signature
            });
            
            return {
                success: true,
                signature,
                message
            };
        } catch (error) {
            console.error("Failed to sign message:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Sign a transaction using the connected wallet
     * @param {Object} transaction - Transaction to sign
     * @return {Promise<Object>} Signing result
     */
    async function signTransaction(transaction) {
        try {
            if (!_connected || !_provider) {
                throw new Error("Wallet not connected");
            }
            
            // In a real app, this would create a Solana transaction
            // For this example, we're just simulating the response
            
            // Sign the transaction
            // const signedTransaction = await _provider.signTransaction(transaction);
            
            // Notify event listeners
            _notifyEventListeners('transaction', {
                transaction,
                status: 'signed'
            });
            
            return {
                success: true,
                status: 'signed',
                transaction_id: 'simulated_tx_id'
            };
        } catch (error) {
            console.error("Failed to sign transaction:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Generate a ZK proof
     * @param {string} circuitId - ID of the ZK circuit
     * @param {Object} inputs - Inputs for the proof
     * @return {Promise<Object>} Proof generation result
     */
    async function generateZKProof(circuitId, inputs) {
        try {
            if (!_config.zkEnabled) {
                throw new Error("ZK functionality is not enabled");
            }
            
            const response = await fetch('/api/wallet/zk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: 'generate',
                    circuit_id: circuitId,
                    inputs
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error("Failed to generate ZK proof:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Verify a ZK proof
     * @param {string} circuitId - ID of the ZK circuit
     * @param {Object} proof - The proof to verify
     * @param {Array} publicInputs - Public inputs for verification
     * @return {Promise<Object>} Verification result
     */
    async function verifyZKProof(circuitId, proof, publicInputs) {
        try {
            if (!_config.zkEnabled) {
                throw new Error("ZK functionality is not enabled");
            }
            
            const response = await fetch('/api/wallet/zk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: 'verify',
                    circuit_id: circuitId,
                    proof,
                    public_inputs: publicInputs
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error("Failed to verify ZK proof:", error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Perform a hex.dev operation
     * @param {string} operation - Operation type (encode, decode, hash)
     * @param {string} input - Input data
     * @param {Object} options - Additional options
     * @return {Promise<Object>} Operation result
     */
    async function hexOperation(operation, input, options = {}) {
        try {
            if (!_config.hexEnabled) {
                throw new Error("Hex.dev functionality is not enabled");
            }
            
            const response = await fetch('/api/wallet/hex', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation,
                    input,
                    options
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error(`Failed to perform hex.dev ${operation}:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    /**
     * Add an event listener
     * @param {string} eventName - Name of the event
     * @param {Function} callback - Event callback function
     */
    function addEventListener(eventName, callback) {
        if (!_eventListeners[eventName]) {
            _eventListeners[eventName] = [];
        }
        
        _eventListeners[eventName].push(callback);
    }
    
    /**
     * Remove an event listener
     * @param {string} eventName - Name of the event
     * @param {Function} callback - Event callback function to remove
     */
    function removeEventListener(eventName, callback) {
        if (!_eventListeners[eventName]) return;
        
        _eventListeners[eventName] = _eventListeners[eventName].filter(
            listener => listener !== callback
        );
    }
    
    /**
     * Check if wallet is connected
     * @return {boolean} Connection status
     */
    function isConnected() {
        return _connected;
    }
    
    /**
     * Get current wallet address
     * @return {string|null} Wallet address or null if not connected
     */
    function getAddress() {
        return _address;
    }
    
    // Public API
    return {
        init,
        connect,
        disconnect,
        signMessage,
        signTransaction,
        generateZKProof,
        verifyZKProof,
        hexOperation,
        addEventListener,
        removeEventListener,
        isConnected,
        getAddress
    };
})();

// Export the module for use in other scripts
window.VOT1Wallet = VOT1Wallet; 