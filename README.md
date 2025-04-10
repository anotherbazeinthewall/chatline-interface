# Chatline

A lightweight CLI library for building terminal-based LLM chat interfaces with minimal effort. Provides rich text styling, animations, and conversation state management.

- **Terminal UI**: Rich text formatting with styled quotes, brackets, emphasis, and more
- **Response Streaming**: Real-time streamed responses with loading animations
- **State Management**: Conversation history with edit and retry functionality
- **Multiple Providers**: Run with OpenRouter, AWS Bedrock, or connect to a custom backend
- **Keyboard Shortcuts**: Ctrl+E to edit previous message, Ctrl+R to retry

![](https://raw.githubusercontent.com/anotherbazeinthewall/chatline-interface/main/demo.gif)

## Installation

```bash
pip install chatline
```

With Poetry:

```bash
poetry add chatline
```

## Usage

There are two modes: Embedded (with built-in providers) and Remote (requires response generation endpoint).

### Embedded Mode with OpenRouter (Default)

The easiest way to get started is to use the embedded generator with OpenRouter: (Just make sure to set your OPENROUTER_API_KEY environment variable first)

```python
from chatline import Interface

chat = Interface()

chat.start()
```

For more customization:


```python
from chatline import Interface

# Initialize with embedded mode with OpenRouter configuration
chat = Interface(
    provider="openrouter",  # Optional: this is the default
    provider_config={
        "model": "anthropic/claude-3-opus", 
        "temperature": 0.7, 
        "top_p": 0.9, 
        "frequency_penalty": 0.5, 
        "presence_penalty": 0.5,
        "timeout": 60 
    },

    # Logging Configuration
    logging_enabled=True,  # Enable detailed logging
    log_file="logs/chatline_debug.log",  # Output file for logs
)

# Add optional welcome message
chat.preface(
    "Welcome", 
    title="My App", 
    border_color="green")

# Start the conversation with custom system and user messages
chat.start([
    {"role": "system", "content": "You are a friendly AI assistant that specializes in code generation."},
    {"role": "user", "content": "Can you help me with a Python project?"}
])
```

### Embedded Mode with AWS Bedrock

You can also use AWS Bedrock as your provider: (as long as you're okay stocking to Anthropic models)

```python
from chatline import Interface

# Initialize with Bedrock provider
chat = Interface(
    provider="bedrock",
    provider_config={
        "region": "us-west-2",  
        "model_id": "anthropic.claude-3-5-haiku-20241022-v1:0", 
        "profile_name": "development", 
        "timeout": 120  
    }
)

chat.start()
```

### Remote Mode (Custom Backend)

You can also connect to a custom backend by providing the endpoint URL:

```python
from chatline import Interface

# Initialize with remote mode
chat = Interface(endpoint="http://localhost:8000/chat")

# Start the conversation with custom system and user messages
chat.start()
```

#### Setting Up a Backend Server

You can use generate_stream function (or build your own) in your backend. Here's an example in a FastAPI server:

```python
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from chatline import generate_stream

app = FastAPI()

provider_config = {
    "model": "mistralai/mixtral-8x7b-instruct"
}

@app.post("/chat")
async def stream_chat(request: Request):
    body = await request.json()
    state = body.get('conversation_state', {})
    messages = state.get('messages', [])
    
    # Process the request and update state as needed
    state['server_turn'] = state.get('server_turn', 0) + 1
    
    # Return streaming response with updated state
    headers = {
        'Content-Type': 'text/event-stream',
        'X-Conversation-State': json.dumps(state)
    }
    
    return StreamingResponse(
        generate_stream(
            messages, 
            provider="openrouter",
            provider_config=provider_config
        ),
        headers=headers,
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000)
```

## Acknowledgements

Chatline was built with plenty of LLM assistance, particularly from (Anthropic)[https://github.com/anthropics], (Mistral)[https://github.com/mistralai] and (Continue.dev)[https://github.com/continuedev/continue]. 