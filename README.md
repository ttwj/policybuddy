# PolicyBuddy Research Plan Generator (Experimental v0.1)

Welcome to PolicyBuddy Research Plan Generator v0.1, an experimental tool designed to support policy analysts, sustainability consultants, due diligence experts, and anyone involved in policy or sustainability-related-research-oriented projects. 

Our goal is to streamline the creation of research plans, facilitate the discovery of relevant documents, and enhance the quality of preliminary reports through advanced search techniques. Whether you're starting a new project or refining your research, PolicyBuddy aims to improve both your process and outcomes.

## Features

- **Interactive Research Plan Creation**: Easily generate a research plan through user input or a predefined prompt.
- **Advanced Document Search**: Conduct detailed searches to find documents and reports relevant to your research.
- **Enhanced Report Production**: Incorporate insights from targeted document searches to improve preliminary reports.
- **PDF Discovery and Analysis**: Search for, retrieve, and analyze PDF documents pertinent to your research topic.
- **Vector Store Compatibility**: Leverage FAISS vector stores for efficient document embedding and retrieval.

## Getting Started

### Prerequisites

Ensure Python 3.6 or later is installed on your system. Install the required Python packages using:

```bash
pip install -r requirements.txt
```

This command installs all necessary dependencies, including libraries for argument parsing, JSON manipulation, and interfacing with external search and embedding services.

### API Keys Configuration

To fully utilize PolicyBuddy's features, you'll need API keys for OpenAI, Perplexity, and SERP, enabling advanced functionalities like AI-driven text generation, document analysis, and search engine results processing.

#### Obtaining API Keys

##### OpenAI API Key

1. Visit [OpenAI API](https://openai.com/api/).
2. Sign up or log in to create an API account.
3. Navigate to the API keys section and generate a new API key.
4. Copy your `OPENAI_API_KEY`.

##### Perplexity AI API Key

1. Go to [Perplexity AI](https://www.perplexity.ai/) and sign up.
2. Find the API documentation or dashboard to generate an API key.
3. Copy your `PERPLEXITY_API_KEY`.

##### SERP API Key

1. Visit [SERP API](https://serpapi.com/) and sign up.
2. Generate a new API key from the dashboard or API section.
3. Copy your `SERPER_API_KEY`.

### Configuring Your Environment

After obtaining the API keys, configure them in your environment to allow secure access to the necessary services.

For Unix/Linux/macOS:

```bash
export OPENAI_API_KEY='your_openai_api_key_here'
export PERPLEXITY_API_KEY='your_perplexity_api_key_here'
export SERPER_API_KEY='your_serper_api_key_here'
```

For Windows (using Command Prompt):

```cmd
set OPENAI_API_KEY=your_openai_api_key_here
set PERPLEXITY_API_KEY=your_perplexity_api_key_here
set SERPER_API_KEY=your_serper_api_key_here
```

Replace the placeholders with the actual keys you obtained.

### Note

Keep your API keys secure and do not share them publicly. Regenerate them immediately if you suspect they've been compromised.

## Usage

PolicyBuddy can be used in various modes to suit your project needs. Here's how to get started:

```bash
python policybuddy.py [options]
```

### Options

- `-f`, `--file`: Optional JSON file containing user context.
- `-s`, `--search_results`: Optional JSON file with search results.
- `-r`, `--research_plan`: Optional JSON file with the final research plan.
- `-p`, `--prompt`: Optional .txt file with the system prompt.
- `-pr`, `--preliminary_report`: Optional JSON with the preliminary report.
- `-pdfs`, `--pdf_destination_folder`: Optional folder for storing PDFs.
- `-v`, `--vector_store`: Optional location of the FAISS vector store for PDF embeddings.
- `-er`, `--enhanced_report`: Optional location of the enhanced report JSON.

### Example

To start generating a research plan with interactive prompts:

```bash
python policybuddy.py
```

To use a predefined user context and prompt file:

```bash
python policybuddy.py -f user_context.json -p system_prompt.txt
```

## AI Bias and Sustainability in APAC Regions

As an evolving experimental tool, we recognize the risk of AI bias, especially in the sustainability sector and APAC regions. We are committed to reducing this bias and improving our tool's inclusivity and accuracy. Users should critically evaluate results and consider diverse sources, particularly when addressing sustainability issues in APAC regions.

## Contributing

We greatly value community feedback and contributions. If you have suggestions for reducing bias, enhancing functionality, or contributing code, please share your input through issues or pull requests.

## License

PolicyBuddy is released under the MIT License. For more details, see the LICENSE file.

---

We hope PolicyBuddy v0.1 enhances your research process, helping you generate insightful and impactful policy research.

Happy Researching!
