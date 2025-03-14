/**
 * VOT1 Dashboard - Wallet UI Component
 * 
 * This module provides UI components and interactions for the wallet integration,
 * ZK proofs, and hex.dev functionality.
 */

// Wallet UI Component
const VOT1WalletUI = (() => {
    // DOM elements
    let _container = null;
    let _connectButton = null;
    let _walletStatus = null;
    let _zkContainer = null;
    let _hexContainer = null;
    
    // State
    let _initialized = false;
    
    /**
     * Initialize the wallet UI component
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     * @return {Promise<boolean>} Success status
     */
    async function init(containerId, options = {}) {
        try {
            // Get the container element
            _container = document.getElementById(containerId);
            
            if (!_container) {
                console.error(`Container element with ID "${containerId}" not found`);
                return false;
            }
            
            // Initialize the wallet module
            const walletInitialized = await VOT1Wallet.init(options);
            
            if (!walletInitialized) {
                _renderWalletNotAvailable();
                return false;
            }
            
            // Create UI elements
            _createUIElements();
            
            // Set up event listeners
            _setupEventListeners();
            
            // Update UI based on initial state
            _updateUI();
            
            _initialized = true;
            console.log("Wallet UI component initialized successfully");
            return true;
        } catch (error) {
            console.error("Failed to initialize wallet UI component:", error);
            return false;
        }
    }
    
    /**
     * Render wallet not available message
     * @private
     */
    function _renderWalletNotAvailable() {
        _container.innerHTML = `
            <div class="wallet-not-available">
                <div class="alert alert-warning">
                    <h4>Phantom Wallet Not Available</h4>
                    <p>To use this feature, please install the Phantom wallet extension:</p>
                    <a href="https://phantom.app/" target="_blank" class="btn btn-primary">Install Phantom</a>
                </div>
            </div>
        `;
    }
    
    /**
     * Create UI elements for the wallet component
     * @private
     */
    function _createUIElements() {
        // Create wallet section
        const walletSection = document.createElement('div');
        walletSection.className = 'wallet-section';
        walletSection.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h4>Phantom Wallet Integration</h4>
                </div>
                <div class="card-body">
                    <div class="wallet-status">
                        <div class="status-indicator">
                            <span class="indicator disconnected"></span>
                            <span class="status-text">Disconnected</span>
                        </div>
                        <div class="wallet-address"></div>
                    </div>
                    <div class="wallet-actions">
                        <button class="btn btn-primary connect-button">Connect Wallet</button>
                    </div>
                    <div class="wallet-transaction-section" style="display: none;">
                        <hr>
                        <h5>Sign Message</h5>
                        <div class="input-group mb-3">
                            <input type="text" class="form-control message-input" placeholder="Enter message to sign">
                            <button class="btn btn-outline-secondary sign-message-btn" type="button">Sign</button>
                        </div>
                        <div class="signed-message-result" style="display: none;">
                            <div class="alert alert-info">
                                <strong>Signature:</strong>
                                <span class="signature-value"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Create ZK section
        const zkSection = document.createElement('div');
        zkSection.className = 'zk-section';
        zkSection.innerHTML = `
            <div class="card mt-4">
                <div class="card-header">
                    <h4>Zero-Knowledge Proofs</h4>
                </div>
                <div class="card-body">
                    <div class="zk-circuit-select">
                        <label for="zk-circuit">Select ZK Circuit:</label>
                        <select class="form-select mb-3" id="zk-circuit">
                            <option value="identity">Identity Proof</option>
                            <option value="transaction">Transaction Proof</option>
                            <option value="voting">Anonymous Voting</option>
                        </select>
                    </div>
                    <div class="zk-inputs">
                        <h5>Proof Inputs</h5>
                        <div class="mb-3">
                            <label for="zk-input-1" class="form-label">Input 1:</label>
                            <input type="text" class="form-control" id="zk-input-1" placeholder="Enter input value">
                        </div>
                        <div class="mb-3">
                            <label for="zk-input-2" class="form-label">Input 2:</label>
                            <input type="text" class="form-control" id="zk-input-2" placeholder="Enter input value">
                        </div>
                    </div>
                    <div class="zk-actions">
                        <button class="btn btn-primary generate-proof-btn">Generate Proof</button>
                        <button class="btn btn-secondary verify-proof-btn" disabled>Verify Proof</button>
                    </div>
                    <div class="zk-result mt-3" style="display: none;">
                        <div class="alert alert-info">
                            <strong>Proof Status:</strong>
                            <span class="proof-status"></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Create Hex.dev section
        const hexSection = document.createElement('div');
        hexSection.className = 'hex-section';
        hexSection.innerHTML = `
            <div class="card mt-4">
                <div class="card-header">
                    <h4>Hex.dev Tools</h4>
                </div>
                <div class="card-body">
                    <div class="hex-operation-select">
                        <label for="hex-operation">Select Operation:</label>
                        <select class="form-select mb-3" id="hex-operation">
                            <option value="encode">Hex Encode</option>
                            <option value="decode">Hex Decode</option>
                            <option value="hash">Hash Function</option>
                        </select>
                    </div>
                    <div class="hex-inputs">
                        <div class="mb-3">
                            <label for="hex-input" class="form-label">Input:</label>
                            <textarea class="form-control" id="hex-input" rows="3" placeholder="Enter input value"></textarea>
                        </div>
                        <div class="hex-options mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="hex-uppercase">
                                <label class="form-check-label" for="hex-uppercase">Uppercase (for encoding)</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="hex-prefix" checked>
                                <label class="form-check-label" for="hex-prefix">0x Prefix (for encoding)</label>
                            </div>
                            <div class="hash-algorithm" style="display: none;">
                                <label for="hash-algo" class="form-label">Hash Algorithm:</label>
                                <select class="form-select" id="hash-algo">
                                    <option value="sha256">SHA-256</option>
                                    <option value="sha512">SHA-512</option>
                                    <option value="md5">MD5</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="hex-actions">
                        <button class="btn btn-primary hex-execute-btn">Execute</button>
                        <button class="btn btn-secondary hex-copy-btn" disabled>Copy Result</button>
                    </div>
                    <div class="hex-result mt-3" style="display: none;">
                        <div class="alert alert-info">
                            <strong>Result:</strong>
                            <div class="hex-result-value" style="word-break: break-all;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append sections to container
        _container.innerHTML = '';
        _container.appendChild(walletSection);
        _container.appendChild(zkSection);
        _container.appendChild(hexSection);
        
        // Store references to important elements
        _connectButton = _container.querySelector('.connect-button');
        _walletStatus = _container.querySelector('.wallet-status');
        _zkContainer = _container.querySelector('.zk-section');
        _hexContainer = _container.querySelector('.hex-section');
        
        // Initially disable ZK and Hex sections until wallet is connected
        _zkContainer.classList.add('disabled');
        _hexContainer.classList.add('disabled');
        
        // Add some basic CSS
        const style = document.createElement('style');
        style.textContent = `
            .wallet-section .status-indicator {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            .wallet-section .indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .wallet-section .indicator.connected {
                background-color: #28a745;
            }
            .wallet-section .indicator.disconnected {
                background-color: #dc3545;
            }
            .wallet-section .wallet-address {
                font-family: monospace;
                margin-top: 5px;
                word-break: break-all;
            }
            .disabled {
                opacity: 0.6;
                pointer-events: none;
            }
            .zk-result, .hex-result {
                max-height: 200px;
                overflow-y: auto;
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Set up event listeners for UI elements
     * @private
     */
    function _setupEventListeners() {
        // Connect/disconnect button
        _connectButton.addEventListener('click', async () => {
            if (VOT1Wallet.isConnected()) {
                await VOT1Wallet.disconnect();
            } else {
                await VOT1Wallet.connect();
            }
            _updateUI();
        });
        
        // Sign message button
        const signMessageBtn = _container.querySelector('.sign-message-btn');
        signMessageBtn.addEventListener('click', async () => {
            const messageInput = _container.querySelector('.message-input');
            const message = messageInput.value.trim();
            
            if (!message) {
                alert('Please enter a message to sign');
                return;
            }
            
            const result = await VOT1Wallet.signMessage(message);
            
            if (result.success) {
                const signatureElement = _container.querySelector('.signature-value');
                signatureElement.textContent = result.signature;
                _container.querySelector('.signed-message-result').style.display = 'block';
            } else {
                alert(`Failed to sign message: ${result.error}`);
            }
        });
        
        // Generate ZK proof button
        const generateProofBtn = _container.querySelector('.generate-proof-btn');
        generateProofBtn.addEventListener('click', async () => {
            const circuitId = _container.querySelector('#zk-circuit').value;
            const input1 = _container.querySelector('#zk-input-1').value;
            const input2 = _container.querySelector('#zk-input-2').value;
            
            if (!input1 || !input2) {
                alert('Please enter values for all inputs');
                return;
            }
            
            const inputs = {
                input1,
                input2
            };
            
            const result = await VOT1Wallet.generateZKProof(circuitId, inputs);
            
            if (result.success) {
                _container.querySelector('.proof-status').textContent = 'Proof generated successfully';
                _container.querySelector('.zk-result').style.display = 'block';
                _container.querySelector('.verify-proof-btn').disabled = false;
                
                // Store proof data for verification
                _container.querySelector('.verify-proof-btn').dataset.proof = JSON.stringify(result.proof);
                _container.querySelector('.verify-proof-btn').dataset.publicInputs = JSON.stringify(result.public_inputs);
                _container.querySelector('.verify-proof-btn').dataset.circuitId = circuitId;
            } else {
                alert(`Failed to generate proof: ${result.error}`);
            }
        });
        
        // Verify ZK proof button
        const verifyProofBtn = _container.querySelector('.verify-proof-btn');
        verifyProofBtn.addEventListener('click', async () => {
            const circuitId = verifyProofBtn.dataset.circuitId;
            const proof = JSON.parse(verifyProofBtn.dataset.proof);
            const publicInputs = JSON.parse(verifyProofBtn.dataset.publicInputs);
            
            const result = await VOT1Wallet.verifyZKProof(circuitId, proof, publicInputs);
            
            if (result.success && result.verified) {
                _container.querySelector('.proof-status').textContent = 'Proof verified successfully';
            } else {
                _container.querySelector('.proof-status').textContent = 'Proof verification failed';
            }
        });
        
        // Hex.dev operation
        const hexOperationSelect = _container.querySelector('#hex-operation');
        hexOperationSelect.addEventListener('change', () => {
            const hashAlgoSection = _container.querySelector('.hash-algorithm');
            hashAlgoSection.style.display = hexOperationSelect.value === 'hash' ? 'block' : 'none';
        });
        
        // Execute hex operation button
        const hexExecuteBtn = _container.querySelector('.hex-execute-btn');
        hexExecuteBtn.addEventListener('click', async () => {
            const operation = _container.querySelector('#hex-operation').value;
            const input = _container.querySelector('#hex-input').value;
            
            if (!input) {
                alert('Please enter input value');
                return;
            }
            
            let options = {};
            
            if (operation === 'encode') {
                options = {
                    uppercase: _container.querySelector('#hex-uppercase').checked,
                    prefix: _container.querySelector('#hex-prefix').checked ? '0x' : ''
                };
            } else if (operation === 'decode') {
                options = {
                    strip_prefix: true
                };
            } else if (operation === 'hash') {
                options = {
                    algorithm: _container.querySelector('#hash-algo').value
                };
            }
            
            const result = await VOT1Wallet.hexOperation(operation, input, options);
            
            if (result.success) {
                _container.querySelector('.hex-result-value').textContent = result.result;
                _container.querySelector('.hex-result').style.display = 'block';
                _container.querySelector('.hex-copy-btn').disabled = false;
            } else {
                alert(`Operation failed: ${result.error}`);
            }
        });
        
        // Copy hex result button
        const hexCopyBtn = _container.querySelector('.hex-copy-btn');
        hexCopyBtn.addEventListener('click', () => {
            const resultText = _container.querySelector('.hex-result-value').textContent;
            navigator.clipboard.writeText(resultText)
                .then(() => {
                    const originalText = hexCopyBtn.textContent;
                    hexCopyBtn.textContent = 'Copied!';
                    setTimeout(() => {
                        hexCopyBtn.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy text: ', err);
                });
        });
        
        // Wallet events
        VOT1Wallet.addEventListener('connect', () => {
            _updateUI();
        });
        
        VOT1Wallet.addEventListener('disconnect', () => {
            _updateUI();
        });
    }
    
    /**
     * Update UI based on wallet connection state
     * @private
     */
    function _updateUI() {
        const isConnected = VOT1Wallet.isConnected();
        const walletAddress = VOT1Wallet.getAddress();
        
        // Update status indicator
        const indicator = _container.querySelector('.indicator');
        const statusText = _container.querySelector('.status-text');
        
        if (isConnected) {
            indicator.classList.remove('disconnected');
            indicator.classList.add('connected');
            statusText.textContent = 'Connected';
            _connectButton.textContent = 'Disconnect Wallet';
        } else {
            indicator.classList.remove('connected');
            indicator.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
            _connectButton.textContent = 'Connect Wallet';
        }
        
        // Update wallet address display
        const addressElement = _container.querySelector('.wallet-address');
        if (walletAddress) {
            addressElement.textContent = walletAddress;
        } else {
            addressElement.textContent = '';
        }
        
        // Show/hide transaction section
        const transactionSection = _container.querySelector('.wallet-transaction-section');
        transactionSection.style.display = isConnected ? 'block' : 'none';
        
        // Enable/disable ZK and Hex sections
        if (isConnected) {
            _zkContainer.classList.remove('disabled');
            _hexContainer.classList.remove('disabled');
        } else {
            _zkContainer.classList.add('disabled');
            _hexContainer.classList.add('disabled');
        }
    }
    
    // Public API
    return {
        init
    };
})();

// Make the component available globally
window.VOT1WalletUI = VOT1WalletUI; 