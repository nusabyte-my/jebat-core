# 🗡️ JEBAT AI Studio - Documentation

**All-in-One AI Workspace - Chat & Build**

---

## 🚀 Overview

**JEBAT AI Studio** is a unified interface that combines two powerful AI tools:

1. **💬 AI Chat** - ChatGPT-style conversational AI
2. **🛠️ AI Builder** - Bolt.new-style project generator

All in one beautiful, integrated workspace!

---

## 🎯 Quick Start

### Open AI Studio

```bash
# Open the main interface
start jebat\services\webui\index.html

# Or access via web server
# http://localhost:8000/jebat/services/webui/index.html
```

---

## 🏗️ Architecture

```
JEBAT AI Studio
├── Top Navigation
│   ├── Logo
│   ├── Mode Switcher (Chat/Builder)
│   └── Actions (Shortcuts, Home, Export)
├── Main Content Area
│   ├── AI Chat Component (iframe)
│   └── AI Builder Component (iframe)
└── Status Bar
    ├── Current Mode
    ├── Model Status
    └── Timestamp
```

---

## 💡 How to Use

### 1. Welcome Screen

On first visit, you'll see a welcome overlay:
- Click **"Start Chatting"** for AI Chat
- Click **"Start Building"** for AI Builder
- Or press **1** or **2** to choose

### 2. Switch Modes

**Method 1: Mode Switcher**
- Click **💬 Chat** button for chat
- Click **🛠️ Builder** button for builder

**Method 2: Keyboard Shortcuts**
- Press **`1`** - Switch to Chat
- Press **`2`** - Switch to Builder

**Method 3: Logo**
- Click **JEBAT AI Studio** logo to reopen welcome

### 3. Use Each Component

#### AI Chat Mode
- Select AI model from dropdown
- Type your message
- Get instant responses
- Copy/regenerate/share

#### AI Builder Mode
- Describe what to build
- See live preview
- View generated code
- Export project

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **`1`** | Switch to Chat |
| **`2`** | Switch to Builder |
| **`Enter`** | Send message (Chat) |
| **`Shift+Enter`** | New line (Chat) |
| **`?`** or **`/`** | Show shortcuts |
| **`Ctrl+E`** | Export current |

---

## 🎨 Interface Components

### Top Navigation

**Logo** (🗡️ JEBAT AI Studio)
- Click to show welcome screen
- Returns to main menu

**Mode Switcher**
- **💬 Chat** - Activate AI Chat
- **🛠️ Builder** - Activate AI Builder
- Visual indicator shows active mode

**Action Buttons**
- **⌨️ Shortcuts** - Show keyboard shortcuts
- **🏠 Home** - Return to landing page
- **📦 Export** - Export current work

### Main Content

**Chat Component** (ai_chat.html)
- Full AI Chat interface
- All features available
- Independent state

**Builder Component** (ai_builder.html)
- Full AI Builder interface
- All features available
- Independent state

### Status Bar

**Left Side**
- Current mode indicator
- Model/project status
- Green dot = active

**Right Side**
- Live timestamp
- Auto-updates every second

---

## 🔌 Component Integration

### Chat Component

**File**: `ai_chat.html`

Features:
- 7 AI models
- Chat history
- Code highlighting
- Copy/regenerate/share
- Ultra-Think deep reasoning

### Builder Component

**File**: `ai_builder.html`

Features:
- 6 project templates
- Live preview
- Code generation
- File management
- Export functionality

---

## 🎯 Use Cases

### Scenario 1: Learn & Build

1. **Chat Mode** - Ask AI to explain a concept
   ```
   "Explain React hooks"
   ```

2. **Builder Mode** - Create a React app
   ```
   "Build a React app with hooks"
   ```

3. **Back to Chat** - Ask follow-up questions
   ```
   "How do I add routing?"
   ```

### Scenario 2: Debug & Improve

1. **Builder Mode** - Generate initial code
   ```
   "Create a todo app"
   ```

2. **Chat Mode** - Debug issues
   ```
   "Fix this bug in my code..."
   ```

3. **Builder Mode** - Export fixed version
   ```
   Download updated project
   ```

### Scenario 3: Full Project Workflow

1. **Chat Mode** - Brainstorm ideas
   ```
   "Help me plan a startup website"
   ```

2. **Builder Mode** - Build landing page
   ```
   "Create a startup landing page"
   ```

3. **Chat Mode** - Write content
   ```
   "Write compelling copy for..."
   ```

4. **Builder Mode** - Finalize & export
   ```
   Download complete project
   ```

---

## 🛠️ Customization

### Add New Components

Edit `index.html`:

```html
<!-- Add new mode button -->
<button class="mode-btn" onclick="switchMode('analyzer')" id="analyzerModeBtn">
    📊 Analyzer
</button>

<!-- Add new component container -->
<div class="component-container analyzer-component" id="analyzerContainer">
    <iframe src="ai_analyzer.html" class="component-frame"></iframe>
</div>
```

### Customize Navigation

```html
<div class="nav-right">
    <!-- Add custom button -->
    <a href="#" class="nav-btn primary" onclick="customAction()">
        🚀 Custom Action
    </a>
</div>
```

### Add Cross-Component Communication

```javascript
// In index.html
window.addEventListener('message', (event) => {
    if (event.data.type === 'chat_to_builder') {
        // Switch to builder with data
        switchMode('builder');
        // Send data to builder
        document.getElementById('builderFrame')
            .contentWindow.postMessage(event.data, '*');
    }
});
```

---

## 📊 Component Communication

### Parent to Child

```javascript
// Send message to chat iframe
const chatFrame = document.getElementById('chatFrame');
chatFrame.contentWindow.postMessage({
    action: 'set_model',
    model: 'jebat-deep'
}, '*');
```

### Child to Parent

```javascript
// From within iframe
window.parent.postMessage({
    type: 'model_change',
    model: 'JEBAT Deep'
}, '*');
```

---

## 🎨 Styling

### Color Scheme

```css
:root {
    --primary: #6366f1;      /* Indigo */
    --secondary: #10a37f;    /* Green */
    --dark: #0f172a;         /* Dark blue */
    --dark-light: #1e293b;   /* Lighter dark */
}
```

### Gradients

```css
--gradient-primary: linear-gradient(135deg, #6366f1 0%, #10a37f 100%);
--gradient-secondary: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
```

---

## 🐛 Troubleshooting

### Component Not Loading

**Solution**: Check iframe src path. Ensure files exist:
- `ai_chat.html`
- `ai_builder.html`

### Mode Switching Not Working

**Solution**: Check JavaScript console for errors. Verify:
- Function `switchMode()` exists
- Event listeners attached
- No JavaScript errors

### Keyboard Shortcuts Not Working

**Solution**: Ensure focus is not in input field. Shortcuts disabled when typing.

---

## 📱 Responsive Design

### Desktop (1024px+)
- Full interface visible
- Both components side-by-side capable
- All features available

### Tablet (768px - 1023px)
- Mode switcher may hide
- Components full width
- Status bar simplified

### Mobile (<768px)
- Mode switcher hidden
- Components stack
- Touch-optimized

---

## 🚀 Performance

### Optimization Tips

1. **Lazy Load Iframes**
   ```html
   <iframe src="ai_chat.html" loading="lazy"></iframe>
   ```

2. **Cache Component State**
   ```javascript
   // Save state before switching
   localStorage.setItem('chat_state', JSON.stringify(state));
   ```

3. **Minimize Cross-Frame Communication**
   - Batch messages
   - Use efficient data structures

---

## 🔐 Security

### Iframe Security

```javascript
// Validate message origin
window.addEventListener('message', (event) => {
    if (event.origin !== window.location.origin) {
        return; // Ignore external messages
    }
    // Process message...
});
```

### Content Security Policy

Add to HTML head:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; frame-src 'self';">
```

---

## 📚 File Structure

```
jebat/services/webui/
├── index.html          ← Main studio interface
├── ai_chat.html        ← Chat component
├── ai_builder.html     ← Builder component
└── dashboard.html      ← Monitoring dashboard
```

---

## 🎯 Best Practices

### 1. Keep Components Independent
- Each component should work standalone
- Minimal dependencies between components
- Clear separation of concerns

### 2. Consistent UI/UX
- Same color scheme
- Similar interaction patterns
- Consistent keyboard shortcuts

### 3. Efficient State Management
- Save state on mode switch
- Restore state when returning
- Use localStorage for persistence

### 4. Clear Visual Feedback
- Active mode clearly indicated
- Loading states shown
- Success/error messages

---

## 🎉 Examples

### Example 1: Quick Question → Build

```
1. Press 1 (Chat Mode)
2. Ask: "What's the best way to build a todo app?"
3. Get answer
4. Press 2 (Builder Mode)
5. Type: "Build a todo app"
6. See it created
7. Export project
```

### Example 2: Build → Refine

```
1. Press 2 (Builder Mode)
2. Type: "Create a landing page"
3. Review generated code
4. Press 1 (Chat Mode)
5. Ask: "How do I improve this CSS?"
6. Get suggestions
7. Press 2 (Builder Mode)
8. Apply improvements
```

---

## 🤝 Contributing

Want to improve AI Studio?

1. Add new components
2. Improve mode switching
3. Add cross-component features
4. Enhance UI/UX
5. Add more keyboard shortcuts

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - Same as JEBAT core.

---

**JEBAT AI Studio** - *Your complete AI workspace!* 🗡️

**Built with** 💜 **JEBAT Ultra-Think**
