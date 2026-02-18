# 🦓 Zed + JEBAT - Complete Setup

**Your Zed editor is now configured for JEBAT AI!**

---

## ✅ What's Done

1. ✅ **Zed Config Copied** - Settings are in place
2. ✅ **API Configured** - Ready to connect
3. ✅ **Models Set Up** - jebat-pro, jebat-fast, jebat-deep

---

## 🚀 Quick Start (2 Steps)

### **Step 1: Start JEBAT API**

**Option A: Use the Script** (Easiest)
```bash
# Double-click this file or run:
start-jebat-for-zed.bat
```

**Option B: Manual**
```bash
# Open terminal in Dev folder
cd C:\Users\shaid\Desktop\Dev

# Start API
docker-compose up -d jebat-api

# Verify
curl http://localhost:8000/api/v1/health
```

**Option C: Python Only** (No Docker)
```bash
cd C:\Users\shaid\Desktop\Dev
py -m uvicorn jebat.services.api.jebat_api:app --reload
```

---

### **Step 2: Test in Zed**

1. **Open Zed** editor
2. **Open any code file**
3. **Press Ctrl + K** (Windows/Linux) or **Cmd + K** (Mac)
4. **Type**: "Explain this code"
5. **Select "JEBAT AI"** from provider dropdown (if not default)
6. **Get AI response!** ✨

---

## ⌨️ Zed Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl + K** | Open AI chat |
| **Ctrl + Shift + A** | Inline edit selected code |
| **Ctrl + Shift + I** | Insert AI response at cursor |
| **Tab** | Accept autocomplete suggestion |
| **Esc** | Dismiss suggestion |

---

## 🎯 What You Can Ask JEBAT

### **Code Explanation**
```
Select code → Ctrl+K → "Explain this code"
```

### **Code Generation**
```
Ctrl+K → "Create a React component for a todo list"
```

### **Bug Fixing**
```
Select buggy code → Ctrl+Shift+A → "Fix bugs in this code"
```

### **Refactoring**
```
Select code → Ctrl+Shift+A → "Refactor this to be cleaner"
```

### **Write Tests**
```
Select function → Ctrl+K → "Write unit tests for this"
```

### **Add Features**
```
Ctrl+K → "Add error handling to this function"
```

---

## 🔧 Your Zed Configuration

**Location**: `%APPDATA%\Zed\settings.json`

**Current Config**:
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
          "completion": "jebat-fast"
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

## 📊 Available Models

| Model | Best For | Speed |
|-------|----------|-------|
| **jebat-fast** | Autocomplete, quick fixes | ⚡⚡⚡ Instant |
| **jebat-pro** | General coding, explanations | ⚡⚡ Fast |
| **jebat-deep** | Complex refactoring, architecture | ⚡ Thorough |

---

## 🐛 Troubleshooting

### **JEBAT Not Showing in Zed**

1. **Restart Zed** completely
2. **Check API is running**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
3. **Verify settings.json** was copied correctly

### **Connection Error**

```bash
# Check if API is running
docker ps | findstr jebat

# If not running, start it:
docker-compose up -d jebat-api

# Check logs:
docker-compose logs jebat-api
```

### **Authentication Failed**

Make sure API key matches:
- **In .env**: `API_KEY=jebat-local-key`
- **In Zed settings**: `"api_key": "jebat-local-key"`

### **Slow Responses**

Try using `jebat-fast` model for quicker responses:
```json
{
  "ai": {
    "providers": {
      "jebat": {
        "models": {
          "chat": "jebat-fast"
        }
      }
    }
  }
}
```

---

## 💡 Pro Tips

### **1. Use Context**
Keep related files open in Zed - JEBAT can see them for better context!

### **2. Chain Requests**
```
1. "Create a function" → Accept
2. "Add error handling" → Accept  
3. "Write tests" → Accept
```

### **3. Save Common Responses as Snippets**
When JEBAT generates code you use often, save it as a Zed snippet!

### **4. Use Inline Completions**
JEBAT will suggest completions as you type - just press **Tab** to accept!

### **5. Monitor Usage**
Open analytics dashboard to see your AI usage:
```bash
start jebat\services\webui\analytics.html
```

---

## 📚 Examples

### **Example 1: Explain Code**

**Before**:
```javascript
const debounce = (fn, ms) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), ms);
  };
};
```

**Action**: Select code → Ctrl+K → "Explain this code"

**JEBAT Response**:
```
This is a debounce function that:

1. Takes a function (fn) and delay (ms)
2. Returns a new function that delays execution
3. Clears previous timeout if called again
4. Ensures function only runs after ms milliseconds of no calls

Common use: Limiting API calls, resize handlers, search autocomplete
```

---

### **Example 2: Generate Component**

**Action**: Ctrl+K → "Create a React button component with loading state"

**JEBAT Response**:
```jsx
function Button({ loading, children, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        opacity: loading ? 0.5 : 1,
        cursor: loading ? 'wait' : 'pointer'
      }}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}
```

---

### **Example 3: Fix Bug**

**Before** (buggy):
```javascript
function sum(arr) {
  let total = 0;
  for (let i = 0; i <= arr.length; i++) {  // Bug!
    total += arr[i];
  }
  return total;
}
```

**Action**: Select → Ctrl+Shift+A → "Find and fix bugs"

**After** (fixed):
```javascript
function sum(arr) {
  let total = 0;
  for (let i = 0; i < arr.length; i++) {  // Fixed!
    total += arr[i];
  }
  return total;
}
```

---

## 🎉 You're All Set!

**JEBAT is now integrated with Zed!**

Start coding with AI assistance:
1. ✅ Open a file in Zed
2. ✅ Press Ctrl + K
3. ✅ Ask JEBAT anything!

**Happy Coding!** 🦓🗡️

---

## 📞 Need Help?

- **Full Guide**: `docs/IDE_INTEGRATION_GUIDE.md`
- **Zed Guide**: `docs/ZED_SETUP.md`
- **API Docs**: http://localhost:8000/api/docs
- **Analytics**: `jebat\services\webui\analytics.html`

---

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
