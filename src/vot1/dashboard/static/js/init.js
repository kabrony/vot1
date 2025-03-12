/**
 * VOT1 Dashboard Initialization
 * 
 * This script initializes all components of the VOT1 dashboard.
 */

// Initialize the VOT1 API client
window.vot1Api = new VOT1Api();

// Initialize the memory visualization when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Three.js visualization
    try {
        window.memoryVisualization = new MemoryVisualization('three-container');
        console.log('Three.js visualization initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Three.js visualization:', error);
    }
    
    // Initialize tabs
    const defaultTab = 'overview';
    const tabs = document.querySelectorAll('.sidebar a');
    
    // Set default active tab
    tabs.forEach(tab => {
        if (tab.getAttribute('data-tab') === defaultTab) {
            tab.classList.add('active');
        }
    });
    
    // Show default tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        if (content.id === defaultTab) {
            content.classList.add('active');
        }
    });
    
    // Add modal styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .memory-modal {
            display: flex;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .memory-modal-content {
            background-color: var(--dark-gray);
            padding: 20px;
            border-radius: 5px;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        
        .close-button {
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 24px;
            cursor: pointer;
        }
        
        .item-content {
            padding: 10px;
            background-color: var(--darker-gray);
            border-radius: 4px;
            margin-bottom: 15px;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }
    `;
    document.head.appendChild(style);
    
    // Setup example data if in demo mode
    if (window.location.search.includes('demo=true')) {
        setupDemoData();
    }
});

// Setup demo data for demonstration purposes
function setupDemoData() {
    console.log('Setting up demo data');
    
    // Example memory data
    const demoMemory = {
        conversation: [
            {
                role: 'user',
                content: 'What are the key principles of reinforcement learning?',
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                metadata: { tokens: 12, importance: 0.8 }
            },
            {
                role: 'assistant',
                content: 'Reinforcement learning is based on several key principles: 1) Agent-Environment Interaction, 2) Reward Signals, 3) Value Functions, 4) Policy Learning, and 5) Exploration vs Exploitation balance.',
                timestamp: new Date(Date.now() - 3590000).toISOString(),
                metadata: { tokens: 42, importance: 0.9 }
            },
            {
                role: 'user',
                content: 'Can you explain how GANs work?',
                timestamp: new Date(Date.now() - 2400000).toISOString(),
                metadata: { tokens: 8, importance: 0.7 }
            },
            {
                role: 'assistant',
                content: 'Generative Adversarial Networks (GANs) consist of two neural networks: a generator and a discriminator, competing in a zero-sum game. The generator creates samples to fool the discriminator, while the discriminator tries to identify real samples from generated ones.',
                timestamp: new Date(Date.now() - 2390000).toISOString(),
                metadata: { tokens: 46, importance: 0.85 }
            },
            {
                role: 'user',
                content: 'What are transformer models and how do they work?',
                timestamp: new Date(Date.now() - 1200000).toISOString(),
                metadata: { tokens: 10, importance: 0.9 }
            },
            {
                role: 'assistant',
                content: 'Transformer models are a type of neural network architecture that relies on self-attention mechanisms. They process sequential data by weighing the importance of different parts of the input, allowing for parallel processing and better handling of long-range dependencies.',
                timestamp: new Date(Date.now() - 1190000).toISOString(),
                metadata: { tokens: 45, importance: 0.95 }
            }
        ],
        semantic: [
            {
                content: 'Reinforcement learning is a machine learning paradigm where agents learn to make decisions by performing actions in an environment to maximize cumulative reward.',
                timestamp: new Date(Date.now() - 3000000).toISOString(),
                metadata: { source: 'user_input', category: 'machine_learning', importance: 0.85 }
            },
            {
                content: 'GANs were introduced by Ian Goodfellow in 2014 and have been used to generate realistic images, music, and text.',
                timestamp: new Date(Date.now() - 2000000).toISOString(),
                metadata: { source: 'web_search', category: 'deep_learning', importance: 0.75 }
            },
            {
                content: 'The transformer architecture was introduced in the paper "Attention Is All You Need" by Vaswani et al. in 2017.',
                timestamp: new Date(Date.now() - 1000000).toISOString(),
                metadata: { source: 'knowledge_base', category: 'nlp', importance: 0.9 }
            },
            {
                content: 'Large Language Models (LLMs) like GPT-4 and Claude are based on the transformer architecture with billions of parameters.',
                timestamp: new Date(Date.now() - 500000).toISOString(),
                metadata: { source: 'web_search', category: 'nlp', importance: 0.95 }
            }
        ]
    };
    
    // Example system status
    const demoStatus = {
        model: 'claude-3.7-sonnet-20240620',
        github_enabled: true,
        perplexity_enabled: true,
        memory_enabled: true
    };
    
    // Example memory stats
    const demoStats = {
        conversation_items: demoMemory.conversation.length,
        semantic_items: demoMemory.semantic.length,
        total_tokens: 163,
        last_updated: new Date().toISOString()
    };
    
    // Mock the API
    window.vot1Api = {
        getStatus: () => Promise.resolve(demoStatus),
        getMemory: (query) => {
            if (query && query.trim()) {
                // Filter memory items based on query
                const filteredConversation = demoMemory.conversation.filter(
                    item => item.content.toLowerCase().includes(query.toLowerCase())
                );
                const filteredSemantic = demoMemory.semantic.filter(
                    item => item.content.toLowerCase().includes(query.toLowerCase())
                );
                return Promise.resolve({
                    conversation: filteredConversation,
                    semantic: filteredSemantic
                });
            }
            return Promise.resolve(demoMemory);
        },
        getMemoryStats: () => Promise.resolve(demoStats),
        sendMessage: (prompt, systemPrompt, useMemory, usePerplexity) => {
            // Simulate API delay
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve({
                        response: {
                            content: `This is a demo response to: "${prompt}". In a real environment, this would be processed by Claude.`,
                            model: 'claude-3.7-sonnet-20240620',
                            usage: {
                                input_tokens: prompt.split(' ').length,
                                output_tokens: 20,
                                total_tokens: prompt.split(' ').length + 20
                            }
                        },
                        prompt: prompt,
                        system_prompt: systemPrompt,
                        used_memory: useMemory,
                        used_perplexity: usePerplexity
                    });
                }, 1500);
            });
        },
        addKnowledge: (content) => {
            // Simulate API delay
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Add to demo memory
                    demoMemory.semantic.push({
                        content: content,
                        timestamp: new Date().toISOString(),
                        metadata: { source: 'user_input', category: 'general', importance: 0.8 }
                    });
                    
                    // Update stats
                    demoStats.semantic_items = demoMemory.semantic.length;
                    
                    resolve({ success: true, message: 'Knowledge added successfully' });
                }, 800);
            });
        }
    };
} 