# 🦓 Zed Editor - JEBAT Integration

**Complete setup guide for Zed editor**

---

## 🚀 Quick Setup (5 Minutes)

### **Step 1: Open Zed Settings**

```bash
# macOS
Cmd + ,

# Windows/Linux
Ctrl + ,

# Or via menu
Zed → Settings → Open settings.json
```

---

### **Step 2: Add JEBAT Configuration**

Edit `settings.json`:

```json
{
  "ai": {
    "providers": {
      "jebat": {
        "name": "JEBAT AI",
        "type": "openai-compatible",
        "api_url": "http://localhost:8000/api/v1",
        "api_key": "jebat-local-key",
        "models": {
          "chat": "jebat-pro",
          "completion": "jebat-fast",
          "embeddings": null
        }
      }
    },
    "default_provider": "jebat"
  },
  "features": {
    "inline_completion_provider": "jebat"
  }
}
```

---

### **Step 3: Start JEBAT API**

```bash
# Option 1: Docker (Recommended)
docker-compose up -d jebat-api

# Option 2: Local Python
cd C:\Users\shaid\Desktop\Dev
py -m uvicorn jebat.services.api.jebat_api:app --reload

# Verify it's running
curl http://localhost:8000/api/v1/health
```

---

### **Step 4: Test in Zed**

1. **Open any file** in Zed
2. **Press Cmd/Ctrl + K** - Open AI chat
3. **Type**: "Explain this code"
4. **Select "JEBAT AI"** from provider dropdown
5. **Get response!** ✨

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Cmd/Ctrl + K** | Open AI chat |
| **Cmd/Ctrl + Shift + A** | Inline edit |
| **Cmd/Ctrl + Shift + I** | Insert at cursor |
| **Tab** | Accept completion |
| **Esc** | Dismiss suggestion |

---

## 🎯 Advanced Configuration

### **Multiple Models**

```json
{
  "ai": {
    "providers": {
      "jebat": {
        "name": "JEBAT AI",
        "type": "openai-compatible",
        "api_url": "http://localhost:8000/api/v1",
        "api_key": "jebat-local-key",
        "models": {
          "chat": ["jebat-pro", "jebat-fast", "jebat-deep"],
          "completion": "jebat-fast"
        }
      }
    }
  }
}
```

### **Custom Timeouts**

```json
{
  "ai": {
    "providers": {
      "jebat": {
        "timeout": 60,
        "stream": true
      }
    }
  }
}
```

### **Model-Specific Settings**

```json
{
  "ai": {
    "model_specific_settings": {
      "jebat-pro": {
        "max_tokens": 4096,
        "temperature": 0.7
      },
      "jebat-fast": {
        "max_tokens": 1024,
        "temperature": 0.5
      },
      "jebat-deep": {
        "max_tokens": 8192,
        "temperature": 0.8
      }
    }
  }
}
```

---

## 🔧 Troubleshooting

### **JEBAT Not Showing in Provider List**

1. **Check API is running**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **Restart Zed**:
   ```bash
   # Close and reopen Zed
   ```

3. **Check settings.json syntax**:
   ```bash
   # Validate JSON
   ```

### **Connection Errors**

```bash
# Check port 8000 is free
netstat -ano | findstr :8000

# Try different port
# Edit .env: API_PORT=8001
# Update settings.json: api_url: http://localhost:8001
```

### **Authentication Failed**

```bash
# Verify API key matches
# .env: API_KEY=jebat-local-key
# settings.json: api_key: jebat-local-key
```

---

## 🎨 Usage Examples

### **1. Code Explanation**

```
Select code → Cmd+K → "Explain this code"
```

**Example**:
```javascript
// Select this
const debounce = (fn, ms) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), ms);
  };
};

// Ask: "Explain this code"
// JEBAT will explain the debounce function
```

---

### **2. Code Generation**

```
Cmd+K → "Create a React component for a todo list"
```

**Example**:
```
You: "Create a React component for a todo list"

JEBAT:
```jsx
function TodoList() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (input.trim()) {
      setTodos([...todos, input]);
      setInput('');
    }
  };

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && addTodo()}
      />
      <button onClick={addTodo}>Add</button>
      <ul>
        {todos.map((todo, i) => (
          <li key={i}>{todo}</li>
        ))}
      </ul>
    </div>
  );
}
```
```

---

### **3. Bug Fixing**

```
Select buggy code → Cmd+Shift+A → "Find and fix bugs"
```

**Example**:
```javascript
// Before (buggy)
function sum(arr) {
  let total = 0;
  for (let i = 0; i <= arr.length; i++) {  // Bug: <= should be <
    total += arr[i];
  }
  return total;
}

// After (fixed)
function sum(arr) {
  let total = 0;
  for (let i = 0; i < arr.length; i++) {  // Fixed!
    total += arr[i];
  }
  return total;
}
```

---

### **4. Refactoring**

```
Select code → Cmd+Shift+A → "Refactor this to be more readable"
```

---

### **5. Writing Tests**

```
Select function → Cmd+K → "Write unit tests for this"
```

**Example**:
```javascript
// You: "Write Jest tests for this debounce function"

// JEBAT generates:
describe('debounce', () => {
  it('should delay function execution', () => {
    jest.useFakeTimers();
    const fn = jest.fn();
    const debouncedFn = debounce(fn, 100);
    
    debouncedFn();
    expect(fn).not.toHaveBeenCalled();
    
    jest.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalled();
  });
});
```

---

## 📊 Model Selection Guide

### **When to Use Each Model**

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| **jebat-fast** | Autocomplete, quick fixes | ⚡⚡⚡ | Free |
| **jebat-pro** | General coding, explanations | ⚡⚡ | Free/Paid |
| **jebat-deep** | Complex refactoring, architecture | ⚡ | Paid |

---

## 🔐 Security Best Practices

### **1. Use Local API Key**

```json
{
  "api_key": "jebat-local-key-unique-to-you"
}
```

### **2. Don't Commit API Keys**

```bash
# Add to .gitignore
echo "settings.json" >> .gitignore
```

### **3. Use Environment Variables**

```bash
# In .env (not committed)
JEBAT_API_KEY=your-secure-key
```

```json
// In settings.json (can be committed)
{
  "api_key": "${JEBAT_API_KEY}"
}
```

---

## 🎯 Pro Tips

### **1. Use Inline Completions**

Enable tab autocomplete:
```json
{
  "features": {
    "inline_completion_provider": "jebat"
  }
}
```

### **2. Create Snippets**

Save common JEBAT responses as Zed snippets:
```json
{
  "snippets": {
    "react_component": {
      "prefix": "rfc",
      "body": "function Component() {\n  return (\n    <div></div>\n  );\n}"
    }
  }
}
```

### **3. Use Context**

JEBAT can see your open files! Keep related files open for better context.

### **4. Chain Requests**

```
1. "Create a function" → Accept
2. "Add error handling" → Accept
3. "Write tests" → Accept
```

---

## 📚 Additional Resources

- **Zed Docs**: https://zed.dev/docs
- **JEBAT API**: http://localhost:8000/api/docs
- **JEBAT Guide**: See `docs/IDE_INTEGRATION_GUIDE.md`

---

**Happy Coding with Zed + JEBAT!** 🦓🗡️
