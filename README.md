# VOT1 - Self-Improving Memory System

[![CI](https://github.com/villageofthousands/vot1/actions/workflows/ci.yml/badge.svg)](https://github.com/villageofthousands/vot1/actions/workflows/ci.yml)
[![Self-Improvement](https://github.com/villageofthousands/vot1/actions/workflows/self-improvement.yml/badge.svg)](https://github.com/villageofthousands/vot1/actions/workflows/self-improvement.yml)

VOT1 is an advanced self-improving system focused on memory management with Claude 3.7 integration, OWL reasoning, and interactive visualization. It implements a hybrid vector-based and symbolic memory system combined with semantic reasoning capabilities and automates self-improvement through AI-powered workflows.

## Key Features

- **Claude 3.7 Memory Integration**: Enhanced memory system with hybrid retrieval and extended context management
- **Vector-based & Symbolic Memory Management**: Store and retrieve memories using advanced embedding techniques
- **OWL Reasoning Engine**: Apply ontology-based reasoning to memories and system components
- **Self-Improvement Workflows**: Automated workflows for enhancing system components
- **THREE.js Dashboard**: Interactive 3D visualization of memory connections with cyberpunk aesthetic
- **Development Assistant**: AI-powered tooling for code analysis and improvement
- **MCP Integration**: Connect to external services via Machine Capability Protocol

## Getting Started

### Prerequisites

- Python 3.9+ 
- Node.js 14+ (for dashboard)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/villageofthousands/vot1.git
   cd vot1
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Running the System

To start the dashboard:
```bash
python -m src.vot1.dashboard.app
```

The dashboard will be available at http://localhost:5000

## Self-Improvement Workflow

VOT1 includes a self-improvement workflow that can enhance various components:

```bash
# Run self-improvement targeting the THREE.js visualization
python -m scripts.run_self_improvement --target three-js --thinking-tokens 8192 --mode agent --iterations 1
```

Options:
- `--target`: Component to improve (three-js, memory, owl-reasoning, dashboard)
- `--mode`: Improvement mode (agent, workflow, analysis)
- `--thinking-tokens`: Maximum tokens for thinking steps
- `--iterations`: Number of improvement iterations

## Architecture

VOT1 consists of several key components:

- **Memory Manager**: Core system for storing and retrieving hybrid vector-based and symbolic memories
- **Claude 3.7 Integration**: Advanced capabilities leveraging Claude 3.7's memory features
- **OWL Reasoning Engine**: Provides semantic reasoning based on ontology
- **Self-Improvement Framework**: Automates the enhancement of system components
- **Dashboard**: Visualization and interaction layer with THREE.js rendering
- **Development Assistant**: Repository analysis and automated improvement tools
- **MCP Bridge**: Integration with external services and data sources

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to update tests as appropriate.

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Claude 3.7](https://www.anthropic.com/) for advanced AI capabilities
- [THREE.js](https://threejs.org/) for 3D visualization
- [OWLready2](https://owlready2.readthedocs.io/) for OWL reasoning
- [Sentence Transformers](https://www.sbert.net/) for vector embeddings
- [Perplexity AI](https://www.perplexity.ai/) for research capabilities
- [Village of Thousands](https://villageofthousands.io/) for inspiration and support