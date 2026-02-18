# 🤖 JEBAT AI Chat - Documentation

**ChatGPT-style interface with Perplexity-level power**

---

## 🚀 Overview

**JEBAT AI Chat** is a powerful, ChatGPT-style conversational AI interface with multiple model selection, similar to Perplexity's approach.

### Features

- 💬 **ChatGPT-Style Interface** - Familiar, intuitive chat UI
- 🧠 **Multiple AI Models** - Choose the right model for your task
- ⚡ **Real-Time Responses** - Fast, contextual conversations
- 📝 **Code Syntax Highlighting** - Beautiful code formatting
- 💾 **Chat History** - Save and resume conversations
- 🔍 **Deep Reasoning** - Ultra-Think powered analysis
- 📤 **Export & Share** - Save and share conversations

---

## 🎯 Quick Start

### Open AI Chat

```bash
# Open in browser
start jebat\services\webui\ai_chat.html

# Or access via web server
# http://localhost:8000/ai_chat.html
```

---

## 🧠 AI Models

Choose the right model for your task:

### 1. JEBAT Fast ⚡ (Free)
- **Speed**: Instant
- **Power**: Standard
- **Best For**: Quick questions, simple tasks

### 2. JEBAT Pro 🎯 (Pro)
- **Speed**: Fast
- **Power**: Advanced
- **Best For**: Complex questions, code generation
- **Default Model**

### 3. JEBAT Deep 🧠 (Premium)
- **Speed**: Slow (thorough)
- **Power**: Maximum
- **Best For**: Deep analysis, complex reasoning
- **Features**: Ultra-Think 6-phase reasoning

### 4. GPT-4 Style 🔮 (Premium)
- **Speed**: Slow
- **Power**: Maximum
- **Best For**: Creative writing, detailed explanations

### 5. Claude Style 🤖 (Pro)
- **Speed**: Fast
- **Power**: Advanced
- **Best For**: Thoughtful, balanced responses

### 6. Llama Style 🦙 (Free)
- **Speed**: Fast
- **Power**: Standard
- **Best For**: Quick, casual conversations

### 7. Mistral Style 🌪️ (Free)
- **Speed**: Fast
- **Power**: Standard
- **Best For**: Concise, accurate answers

---

## 💡 How to Use

### 1. Select Model

Choose from the dropdown in the header:
- **Fast** for quick answers
- **Pro** for most tasks
- **Deep** for complex analysis

### 2. Start Chatting

Type your question:
```
"Explain quantum computing"
"Write a Python script to analyze CSV"
"Help me brainstorm startup ideas"
"Review this code for security"
```

### 3. Use Suggestions

Click suggestion cards for quick starts:
- 💡 Explain a complex topic
- 💻 Write code
- 🎨 Creative brainstorming
- 🔍 Code review

### 4. Manage Conversations

- **New Chat** - Start fresh conversation
- **History** - Access past chats
- **Regenerate** - Get alternative responses

---

## 🎨 Interface Features

### Sidebar
- **New Chat Button** - Start new conversation
- **Chat History** - Access past conversations
- **Organized by Time** - Today, Yesterday, Previous

### Header
- **Logo** - JEBAT branding
- **Model Selector** - Choose AI model
- **Model Badge** - Free/Pro/Premium indicator

### Chat Area
- **Welcome Screen** - Suggestions and tips
- **Message Thread** - Conversation history
- **User Messages** - Right-aligned
- **AI Messages** - Left-aligned with avatar

### Input Area
- **Textarea** - Auto-resizing input
- **Send Button** - Submit message
- **Tips** - Quick style selectors
- **Keyboard Shortcuts** - Enter to send

---

## 🎯 Example Conversations

### Example 1: Code Generation

```
You: Write a Python script to analyze CSV data

JEBAT Pro: Here's a Python solution for your request:

```python
def analyze_data(filename):
    import csv
    
    results = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            results.append(row)
    
    return results

# Usage
data = analyze_data('your_data.csv')
print(f"Loaded {len(data)} records")
```

**Explanation:**
1. Import CSV module - Built-in Python library
2. Open file - Safely read CSV data
3. Process rows - Convert to dictionaries
4. Return results - Easy to use data structure

Would you like me to add error handling?
```

### Example 2: Deep Analysis

```
You: Explain blockchain technology

JEBAT Deep: **Deep Analysis with Ultra-Think Reasoning** 🧠

Let me provide a comprehensive, multi-layered analysis...

## 🔍 Orientation Phase
First, let's understand the context and scope...

## 📊 Exploration Phase
### Multiple Perspectives
**Technical Perspective:**
- Core mechanisms and principles
- Implementation details
- Performance considerations

**Practical Perspective:**
- Industry use cases
- Success stories
- Common challenges

## 🧠 Analysis Phase
### Critical Evaluation
**Strengths:**
✅ Decentralized and secure
✅ Transparent and immutable
✅ Distributed consensus

**Limitations:**
⚠️ Scalability challenges
⚠️ Energy consumption
⚠️ Regulatory uncertainty

## ✅ Verification Phase
- [x] Technical accuracy verified
- [x] Practical applicability confirmed
- [x] Theoretical foundations validated

**Confidence Level**: 92%
**Reasoning Depth**: Deep (6 thinking phases)
```

### Example 3: Quick Answer

```
You: What is 2 + 2?

JEBAT Fast: **Quick Answer:**

2 + 2 = 4

Simple and straightforward! Need more complex math? 
Try switching to **JEBAT Pro** mode!
```

---

## ⚙️ Message Actions

### Copy Message
Click 📋 **Copy** to copy response to clipboard

### Regenerate
Click 🔄 **Regenerate** to get alternative response

### Share
Click 🔗 **Share** to generate shareable link

---

## 🎨 Response Styles

### Fast Style
- Concise answers
- Bullet points
- Quick examples
- Best for: Simple queries

### Pro Style
- Detailed explanations
- Code examples
- Multiple sections
- Best for: Most tasks

### Deep Style
- Ultra-Think reasoning
- 6-phase analysis
- Multiple perspectives
- Critical evaluation
- Best for: Complex topics

---

## 🔌 Integration with JEBAT

### Ultra-Think Integration

The AI Chat uses JEBAT's Ultra-Think for deep analysis:

```python
from jebat.features.ultra_think import create_ultra_think, ThinkingMode

think = await create_ultra_think()

# Deep analysis mode
result = await think.think(
    question="Explain quantum entanglement",
    mode=ThinkingMode.DEEP,
    timeout=60
)

# Return formatted response
return format_deep_analysis(result)
```

### Multi-Agent Collaboration

```python
from jebat.orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator()

# Get multi-agent response
results = await orchestrator.execute_multi_agent(
    tasks=[
        {"agent_type": "research", "task": "Gather information"},
        {"agent_type": "analysis", "task": "Analyze findings"},
        {"agent_type": "writing", "task": "Write response"},
    ]
)
```

---

## 🛠️ Customization

### Add New Models

Edit `ai_chat.html` and add to models object:

```javascript
const models = {
    // ... existing models
    'custom-model': { 
        name: 'Custom Model', 
        badge: 'pro', 
        speed: 'Fast', 
        power: 'Advanced' 
    }
};
```

### Add Response Generator

```javascript
function generateCustomResponse(message) {
    // Your custom response logic
    return `**Custom Answer:**\n\n${message}...`;
}

// Add to modelResponses mapping
const modelResponses = {
    // ...
    'custom-model': generateCustomResponse
};
```

### Integrate Real API

Replace simulated response:

```javascript
async function sendMessage() {
    const message = document.getElementById('chatInput').value;
    
    // Call JEBAT API
    const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            model: currentModel,
            mode: 'deliberate'
        })
    });
    
    const data = await response.json();
    addMessage(data.response, false);
}
```

---

## 📊 Comparison

| Feature | ChatGPT | Perplexity | JEBAT AI Chat |
|---------|---------|------------|---------------|
| **Multiple Models** | Limited | Yes | ✅ 7 Models |
| **Deep Reasoning** | ✓ | ✓ | ✅ Ultra-Think |
| **Code Generation** | ✓ | ✓ | ✅ Advanced |
| **Chat History** | ✓ | ✓ | ✅ Local Storage |
| **Export/Share** | ✓ | ✓ | ✅ Yes |
| **Free** | Limited | Limited | ✅ Fully Free |
| **Customizable** | ✗ | ✗ | ✅ Open Source |

---

## 🎯 Tips & Best Practices

### Getting Better Responses

1. **Choose Right Model**
   - Fast: Simple questions
   - Pro: Most tasks
   - Deep: Complex analysis

2. **Be Specific**
   ```
   ❌ "Help with code"
   ✅ "Debug this Python function: [code]"
   ```

3. **Use Follow-ups**
   ```
   First: "Explain machine learning"
   Then: "Give me a Python example"
   Then: "Add comments to the code"
   ```

4. **Try Different Styles**
   - Switch models for different perspectives
   - Use "Regenerate" for alternatives
   - Ask for specific formats

### Code Generation

- Specify language
- Include requirements
- Mention constraints
- Ask for explanations

### Analysis & Research

- Use Deep model for complex topics
- Ask for multiple perspectives
- Request critical evaluation
- Verify important information

---

## 🐛 Troubleshooting

### Response Not Showing

**Solution**: Check browser console. Ensure JavaScript is enabled.

### Model Not Changing

**Solution**: Refresh page. Check if dropdown is working.

### Chat History Lost

**Solution**: History is stored locally. Clearing browser data will remove it.

---

## 📚 Resources

### Related Documentation
- [USAGE_GUIDE.md](../../USAGE_GUIDE.md) - General JEBAT usage
- [AI_BUILDER.md](AI_BUILDER.md) - AI web builder
- [API_REFERENCE.md](../../API_REFERENCE.md) - API documentation

### Similar Tools
- [ChatGPT](https://chat.openai.com) - OpenAI's chatbot
- [Perplexity](https://perplexity.ai) - AI search engine
- [Claude](https://claude.ai) - Anthropic's assistant

---

## 🎉 Use Cases

### 1. Learning & Education
- Explain complex topics
- Tutoring sessions
- Language practice
- Study assistance

### 2. Development
- Code generation
- Debugging help
- Code review
- Architecture design

### 3. Research
- Information gathering
- Analysis & synthesis
- Multiple perspectives
- Critical evaluation

### 4. Creative Work
- Brainstorming ideas
- Writing assistance
- Content creation
- Problem solving

### 5. Productivity
- Task planning
- Decision making
- Note taking
- Quick calculations

---

## 🤝 Contributing

Want to improve AI Chat?

1. Add more AI models
2. Improve response quality
3. Enhance UI/UX
4. Add export formats
5. Integrate with more APIs

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - Same as JEBAT core.

---

**JEBAT AI Chat** - *Powerful AI conversations at your fingertips!* 🗡️

**Built with** 🧠 **JEBAT Ultra-Think**
