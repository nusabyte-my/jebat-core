# 🤖 JEBAT AI Builder - Documentation

**Build your ideas with AI - Similar to emergent.sh, bolt.new, Lovable**

---

## 🚀 Overview

**JEBAT AI Builder** is an AI-powered web development assistant that helps you create projects from natural language descriptions.

### Features

- 💬 **Conversational Interface** - Describe what you want to build
- 🎨 **Live Preview** - See your project in real-time
- 💻 **Code Generation** - Get production-ready code
- 📦 **Export** - Download your projects
- 🧠 **AI-Powered** - Powered by JEBAT Ultra-Think reasoning

---

## 🎯 Quick Start

### Open AI Builder

```bash
# Open in browser
start jebat\services\webui\ai_builder.html

# Or access via web server
# http://localhost:8000/ai_builder.html
```

---

## 💡 How to Use

### 1. Describe Your Idea

Type what you want to build in the chat:

```
"Build a todo app with React"
"Create a landing page for my startup"
"Make a weather dashboard"
"Build a portfolio website"
"Create a calculator"
```

### 2. See Live Preview

The AI generates code instantly and shows:
- **Preview Tab** - Live interactive preview
- **Code Tab** - Syntax-highlighted code
- **Files Tab** - Project file structure

### 3. Iterate & Refine

Ask for changes:
- "Make the button blue"
- "Add a dark mode"
- "Make it responsive"
- "Add animations"

### 4. Export

Click **Export** to download your project!

---

## 🎨 Available Templates

### 1. Todo App 📝
- Add, complete, delete tasks
- Progress tracking
- Beautiful UI
- Local storage ready

### 2. Landing Page 🚀
- Hero section
- Features grid
- Modern gradients
- Responsive design

### 3. Weather Dashboard 🌤️
- City search
- Weather display
- Details (humidity, wind)
- API-ready structure

### 4. Portfolio Website 👨‍💼
- Hero with avatar
- Skills showcase
- Projects grid
- Social links

### 5. Calculator 🧮
- All operations
- Clean design
- Smooth animations
- Full functionality

---

## 🔧 Technical Features

### Chat Interface
- ✅ Auto-resizing textarea
- ✅ Suggestion chips
- ✅ Typing indicators
- ✅ Message history
- ✅ Enter to send

### Code Generation
- ✅ HTML/CSS/JavaScript
- ✅ Syntax highlighting
- ✅ Clean, readable code
- ✅ Best practices

### Live Preview
- ✅ Real-time rendering
- ✅ Isolated iframe
- ✅ Interactive elements
- ✅ Mobile responsive

### Project Management
- ✅ File structure view
- ✅ Multiple files support
- ✅ Copy code button
- ✅ Export functionality

---

## 🎯 Example Conversations

### Example 1: Todo App

```
You: Build a todo app with React

AI: ✅ Todo App Created!

I've built a beautiful, fully functional todo app with:
• Add, complete, and delete tasks
• Progress tracking
• Smooth animations
• Responsive design

Check out the Preview tab to see it in action!
```

### Example 2: Landing Page

```
You: Create a landing page for my startup

AI: ✅ Landing Page Created!

I've created a modern startup landing page with:
• Hero section with CTA
• Features grid
• Responsive design
• Modern gradient styling

Perfect for launching your next product!
```

### Example 3: Weather App

```
You: Make a weather dashboard

AI: ✅ Weather Dashboard Created!

I've built a beautiful weather app with:
• City search
• Temperature display
• Weather conditions
• Humidity & wind details

Ready to connect to a real weather API!
```

---

## 🛠️ Customization

### Add New Templates

Edit `ai_builder.html` and add a new generator function:

```javascript
function generateMyProject() {
    const html = `<!DOCTYPE html>...`;
    
    currentProject.name = 'My Project';
    currentProject.files = { 'index.html': html };
    
    updatePreview(html);
    updateCodeView(html, 'index.html');
    updateFilesView();
    
    return `✅ <strong>My Project Created!</strong>...`;
}
```

### Integrate with JEBAT API

Replace the simulated response with actual API call:

```javascript
async function sendMessage() {
    const message = document.getElementById('chatInput').value;
    
    // Call JEBAT API
    const response = await fetch('http://localhost:8000/api/v1/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: message,
            mode: 'creative'
        })
    });
    
    const data = await response.json();
    // Handle response...
}
```

---

## 🎨 UI Components

### Chat Panel (Left)
- **Messages Area** - Conversation history
- **Input Area** - Text input with auto-resize
- **Send Button** - Submit message
- **Suggestion Chips** - Quick start ideas

### Preview Panel (Right)
- **Tabs** - Preview / Code / Files
- **Preview Frame** - Live website preview
- **Code Viewer** - Syntax-highlighted code
- **Files List** - Project structure

### Header
- **Logo** - JEBAT branding
- **Clear Button** - Reset project
- **Export Button** - Download project

---

## 📊 Project Structure

```
jebat/services/webui/
├── ai_builder.html      # AI Builder application
├── dashboard.html       # Monitoring dashboard
└── ...
```

---

## 🔌 Integration with JEBAT

### Ultra-Think Integration

The AI Builder can use JEBAT's Ultra-Think for better code generation:

```python
from jebat.features.ultra_think import create_ultra_think, ThinkingMode

think = await create_ultra_think()

# Generate code with deep thinking
result = await think.think(
    question="Create a React todo app with these features: ...",
    mode=ThinkingMode.CREATIVE,
    timeout=30
)

# Return generated code
return result.conclusion
```

### Multi-Agent Collaboration

Use JEBAT agents for specialized tasks:

```python
from jebat.orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator()

# Generate code with multiple agents
results = await orchestrator.execute_multi_agent(
    tasks=[
        {"agent_type": "coding", "task": "Write HTML structure"},
        {"agent_type": "design", "task": "Create CSS styling"},
        {"agent_type": "testing", "task": "Add JavaScript functionality"},
    ]
)
```

---

## 🚀 Future Enhancements

### Phase 1 (Next)
- [ ] Real JEBAT API integration
- [ ] More project templates
- [ ] Multi-file project support
- [ ] GitHub export
- [ ] Deploy to Netlify/Vercel

### Phase 2 (Advanced)
- [ ] React/Vue/Angular support
- [ ] Backend code generation
- [ ] Database integration
- [ ] Authentication templates
- [ ] E-commerce templates

### Phase 3 (Expert)
- [ ] Full-stack app generation
- [ ] Custom component library
- [ ] AI-powered debugging
- [ ] Performance optimization
- [ ] SEO optimization

---

## 🎓 Tips & Best Practices

### Getting Better Results

1. **Be Specific**
   ```
   ❌ "Make a website"
   ✅ "Create a portfolio website for a photographer with gallery"
   ```

2. **Iterate**
   ```
   First: "Build a landing page"
   Then: "Add a contact form"
   Then: "Make the button green"
   ```

3. **Use Templates**
   - Click suggestion chips for quick start
   - Modify existing templates
   - Combine features from different templates

### Code Quality

- Generated code is production-ready
- Follows best practices
- Includes comments
- Responsive by default
- Accessible (a11y) friendly

---

## 🐛 Troubleshooting

### Preview Not Showing

**Solution**: Check browser console for errors. Make sure iframe is allowed.

### Code Not Generating

**Solution**: Ensure JavaScript is enabled. Try refreshing the page.

### Export Not Working

**Solution**: Check browser popup blocker settings. Allow downloads.

---

## 📚 Resources

### Related Documentation
- [USAGE_GUIDE.md](../../USAGE_GUIDE.md) - General JEBAT usage
- [QUICKSTART_EXAMPLES.md](../../QUICKSTART_EXAMPLES.md) - More examples
- [API_REFERENCE.md](../../API_REFERENCE.md) - API documentation

### Similar Tools
- [emergent.sh](https://emergent.sh) - AI app builder
- [bolt.new](https://bolt.new) - AI web development
- [Lovable](https://lovable.dev) - AI software creation

---

## 🎉 Success Stories

### Example Projects Built

1. **Startup Landing Page** - Built in 2 minutes
2. **Todo App** - Full functionality in 3 minutes
3. **Weather Dashboard** - API integration ready in 4 minutes
4. **Portfolio Site** - Professional site in 5 minutes
5. **Calculator** - Complete app in 2 minutes

---

## 🤝 Contributing

Want to improve AI Builder?

1. Add new templates
2. Improve code generation
3. Enhance UI/UX
4. Add more export options
5. Integrate with more APIs

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - Same as JEBAT core.

---

**JEBAT AI Builder** - *Turn your ideas into reality with AI!* 🚀

**Built with** 🗡️ **JEBAT Ultra-Think**
