# VOT1 Troubleshooter

This toolkit provides a comprehensive set of troubleshooting and repair tools for the VOT1 system, particularly focusing on issues with Claude 3.7 Sonnet, knowledge graph visualization, and memory systems.

## Features

- **JSON Fixer**: Repairs malformed JSON in knowledge graph output files
- **Memory Bridge Troubleshooter**: Diagnoses and fixes initialization issues with the ComposioMemoryBridge
- **Hybrid Reasoning**: Leverages Claude 3.7 Sonnet's advanced reasoning capabilities to analyze and solve complex problems

## Prerequisites

- Python 3.7+
- Anthropic API key (set as environment variable `ANTHROPIC_API_KEY`)
- Required Python packages:
  - `anthropic` (for Claude API)
  - `python-dotenv` (for loading environment variables)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vot1.git
   cd vot1
   ```

2. Install the required packages:
   ```bash
   pip install anthropic python-dotenv
   ```

3. Create a `.env` file with your API keys:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   VOT1_PRIMARY_MODEL=claude-3-7-sonnet-20240229
   ```

## Usage

### Interactive Mode

The easiest way to use the troubleshooter is in interactive mode:

```bash
python vot1_troubleshooter.py --interactive
```

This will present a menu with troubleshooting options:

1. Fix malformed JSON in knowledge graph output files
2. Fix memory bridge initialization issues 
3. Analyze issues with hybrid reasoning
4. Run all troubleshooting tools
5. Exit

### Command Line Mode

You can also run specific troubleshooting tools directly from the command line:

#### Fix Knowledge Graph JSON

```bash
python vot1_troubleshooter.py --fix-json --json-dir output/test_kg --json-pattern "*failed_json*.json"
```

#### Fix Memory Bridge Issues

```bash
python vot1_troubleshooter.py --fix-memory
```

To automatically apply the fixes:

```bash
python vot1_troubleshooter.py --fix-memory --apply
```

#### Analyze Issues with Hybrid Reasoning

```bash
python vot1_troubleshooter.py --analyze --problem "Description of your problem here"
```

Or use a file containing the problem description:

```bash
python vot1_troubleshooter.py --analyze --problem-file problem.txt
```

### Running All Troubleshooting Tools

```bash
python vot1_troubleshooter.py --fix-json --fix-memory --analyze --problem "Description of your problem"
```

## Component Tools

The VOT1 Troubleshooter is composed of several specialized tools that can also be used individually:

### Hybrid Reasoning

The `hybrid_reasoning.py` script provides access to Claude 3.7 Sonnet's advanced reasoning capabilities:

```bash
python hybrid_reasoning.py
```

This will run example problems showcasing hybrid reasoning.

### JSON Fixer

The `json_fixer.py` script specifically targets malformed JSON:

```bash
python json_fixer.py
```

This will run an example JSON fix to demonstrate the capabilities.

### Memory Troubleshooter

The `memory_troubleshooter.py` script focuses on memory system issues:

```bash
python memory_troubleshooter.py
```

To automatically apply fixes:

```bash
python memory_troubleshooter.py --apply-fixes
```

## Common Issues & Solutions

### Knowledge Graph JSON Errors

The most common issue with knowledge graph visualization is malformed JSON from Claude's responses. The JSON Fixer component can handle several common errors:

- Extra commas after opening brackets: `[,`
- Missing commas between items
- Trailing commas at the end of arrays or objects
- Unescaped quotes in strings

### Memory Bridge Initialization Issues

The Memory Bridge component can encounter initialization problems with incorrect parameters:

- `ComposioMemoryBridge.__init__() got an unexpected keyword argument 'memory_path'`
- Missing required parameters

The Memory Troubleshooter component identifies these issues and generates fixes.

## Output Files

The troubleshooter stores output files in several directories:

- `output/hybrid_reasoning/`: Contains results from hybrid reasoning analysis
- `output/json_fixes/`: Contains fixed JSON files and fix summaries
- `output/memory_fixes/`: Contains memory system fix suggestions and reports

## Extending the Troubleshooter

To add new troubleshooting capabilities:

1. Create a new troubleshooter class in a separate file
2. Import it in `vot1_troubleshooter.py`
3. Add a new method to the `VOT1Troubleshooter` class
4. Update the interactive menu and command-line arguments

## Logging

The troubleshooter logs information to both the console and a log file (`vot1_troubleshooter.log`). Check this file for detailed information about troubleshooting operations.

## License

[Specify your license here]

## Contributing

[Specify your contribution guidelines here] 