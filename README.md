# TinyFish Web Search & Extract Provider for Hermes Agent

An official backend provider plugin that connects [Hermes Agent](https://github.com/NousResearch/hermes-agent) to [TinyFish](https://tinyfish.ai).

Rather than registering separate custom tools that the LLM must learn, this plugin implements Hermes's native `WebSearchProvider` interface. It transparently services the agent's built-in `web_search` and `web_extract` tools via TinyFish's Search and Fetch APIs.

---

## Features

- **Built-in Tool Routing:** Powers Hermes's native `web_search` and `web_extract` tools directly.
- **Fast Search API:** Interfaces with `https://api.search.tinyfish.ai` for structured, ranked web results.
- **Clean Markdown Extraction:** Interfaces with `https://api.fetch.tinyfish.ai` to strip boilerplate, ads, and navigation, returning token-efficient markdown.
- **Direct GitHub Installation:** Supports 1-command install via Hermes CLI using GitHub repository shorthand.
- **Interactive Setup:** Automatically appears as a selectable provider in `hermes setup tools` and `hermes tools`.
- **Zero Heavy SDK Dependencies:** Built using lightweight, resilient `httpx` HTTP requests.

---

## Installation

### Method 1: Direct 1-Command Install from GitHub (Recommended)

Hermes Agent has native support for installing plugins directly from GitHub using repository shorthand:

```bash
hermes plugins install atpaawej/tinyfish-hermes-plugin
```

To auto-enable during installation:
```bash
hermes plugins install atpaawej/tinyfish-hermes-plugin --enable
```

> **Note:** Hermes also supports full Git URLs:
> ```bash
> hermes plugins install https://github.com/atpaawej/tinyfish-hermes-plugin
> ```

---

### Method 2: Manual Directory Installation

If you are developing locally or prefer a directory install:

```bash
mkdir -p ~/.hermes/plugins/tinyfish-web
cp -r * ~/.hermes/plugins/tinyfish-web/
hermes plugins enable tinyfish-web
```

---

## Setup & Configuration

### 1. Get an API Key
Obtain your TinyFish API key at [agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys).

### 2. Configure via Hermes Tools Wizard (Recommended)
Run:
```bash
hermes tools
# or
hermes setup tools
```
1. Select **Web Search & Extract**.
2. Pick **TinyFish** from the list of providers.
3. Enter your `TINYFISH_API_KEY` when prompted. Hermes securely stores it in your credentials store.

### 3. Alternative: Direct CLI Configuration
You can also set TinyFish as the active web backend directly:
```bash
hermes config set web.backend tinyfish
```

---

## Updating & Uninstalling

### Update to the latest version
```bash
hermes plugins update tinyfish-web
```

### Remove the plugin
```bash
hermes plugins remove tinyfish-web
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
