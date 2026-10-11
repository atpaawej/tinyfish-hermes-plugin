# TinyFish Web Search & Extract Provider for Hermes Agent

An official backend provider plugin that connects [Hermes Agent](https://github.com/NousResearch/hermes-agent) to [TinyFish](https://tinyfish.ai).

Rather than registering new, custom tool names that the LLM must learn, this plugin implements Hermes's native `WebSearchProvider` interface. It transparently services the agent's built-in `web_search` and `web_extract` tools via TinyFish's high-speed Search and Fetch APIs.

---

## Features

- **Built-in Tool Routing:** Powers Hermes's native `web_search` and `web_extract` tools directly.
- **Fast Search API:** Interfaces with `https://api.search.tinyfish.ai` for structured, ranked web results.
- **Clean Markdown Extraction:** Interfaces with `https://api.fetch.tinyfish.ai` to strip boilerplate, ads, and navigation, returning token-efficient markdown.
- **Interactive Setup:** Automatically appears as a selectable provider in `hermes setup tools` and `hermes tools`.
- **Zero Heavy SDK Dependencies:** Built using lightweight, resilient `httpx` HTTP requests.

---

## Quickstart

### 1. Get an API Key
Get your TinyFish API key at [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys).

### 2. Installation

#### Option A: User Plugin Directory
Copy or link this directory into your Hermes plugins folder:
```bash
mkdir -p ~/.hermes/plugins/tinyfish-web
cp -r * ~/.hermes/plugins/tinyfish-web/
```

Then enable it:
```bash
hermes plugins enable tinyfish-web
```

#### Option B: Pip Install
```bash
pip install -e .
```

### 3. Configuration

#### Method A: Interactive Setup (Recommended)
Run:
```bash
hermes tools
# or
hermes setup tools
```
Navigate to **Web Search & Extract**, select **TinyFish**, and enter your `TINYFISH_API_KEY` when prompted.

#### Method B: Manual Configuration
Add your API key to `~/.hermes/.env`:
```bash
TINYFISH_API_KEY="your_tinyfish_api_key_here"
```

Set TinyFish as your active web backend in `~/.hermes/config.yaml`:
```yaml
web:
  backend: "tinyfish"
```
Or configure search and extract separately:
```yaml
web:
  search_backend: "tinyfish"
  extract_backend: "tinyfish"
```

---

## Running Tests

Run the unit tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Validate with Hermes Plugin Doctor:
```bash
hermes plugins doctor . --ci
```

Validate against the Hermes Plugin Catalog rules:
```bash
hermes plugins validate .
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
