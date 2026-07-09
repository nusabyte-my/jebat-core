# JEBAT UI/UX Improvement Plan

## Current State
- ASCII banner (Figlet-style, cyan + magenta)
- Double-line box panels (╔══╗ style)
- Basic status bar with tokens and progress bar
- Thinking spinner with rotating quotes
- Answer panels with box borders

## Quick Wins (1-2 hours each)

### 1. Gradient Banner
Replace flat-color banner with gradient effect using ANSI 256-color codes.
```
  J E B A T  ← each letter fades from cyan to magenta
```
- Use `C.color()` for smooth gradients
- Add subtle glow effect with dim/normal/bold cycling

### 2. Rounded Panel Corners
Replace box-drawing characters with rounded corners for a modern look.
```
╭── Setup ─────────────────────────╮
│   Provider  ollama               │
│   Model     qwen2.5-coder:7b    │
╰──────────────────────────────────╯
```
- Use ╭╮╰╯ instead of ╔╗╚╝
- Thinner borders for a cleaner feel

### 3. Status Bar Revamp
Make the bottom bar more informative and visually appealing.
```
⚕  qwen2.5-coder │ 15,606/200,000 │ ██████░░░░░░░░░░░░░░ 7% │ ⚙ 4 │ ⛓ 4 │ 2m 15s │ $0.25
```
- Add color to each section
- Use block progress bar (█░) instead of dots
- Add cost display ($0.25)
- Show elapsed time in human-readable format

### 4. Tool Execution Visual
Replace plain text tool calls with visual indicators.
```
  ⚙️ preparing list_dir…
     list_dir .
     ↓ 0.0s

  ⚙️ preparing terminal…
     npm install
     ↓ 22.0s
```
- Add checkmark on completion ✓
- Add timing below each tool
- Use arrows to show flow

### 5. Answer Rendering
Replace box-bordered answers with clean markdown-style rendering.
```
  ## Plan

  • First, we analyze the codebase structure
  • Then identify the key modules
  • Finally, implement the changes

  ### Important Notes

  • Memory leak found in auth.py
  • The utils.py file needs refactoring

  ```python
  def fix():
      return True
  ```
```
- Headers in cyan bold
- Bold text in bold
- Code in cyan
- Lists with green bullet •
- Code blocks in dim

### 6. Thinking Spinner
Replace text spinner with animated dots or bar.
```
  ⏳ Analyzing codebase...
  ████░░░░░░░░░░░░ 25%
```
- Show progress percentage
- Rotate through emojis or symbols
- Show elapsed time

### 7. Panel Animations
Add subtle animations to panel rendering.
- Typewriter effect for banner
- Fade-in for panels
- Smooth transitions between states

### 8. Color Scheme
Define a consistent color palette.
```python
COLORS = {
    "primary": C.CYAN,      # Main accent
    "secondary": C.MAGENTA, # Secondary accent
    "success": C.GREEN,     # Success/active
    "warning": C.YELLOW,    # Warning/attention
    "error": C.RED,         # Error/danger
    "dim": C.DIM,           # Dimmed/inactive
    "bold": C.BOLD,         # Emphasized
}
```

### 9. Progress Indicators
Add progress bars for long-running operations.
```
  [████████░░░░░░░░] 50% - Processing files...
```
- Use block characters for smooth progress
- Show percentage and status text
- Animate with thread

### 10. Interactive Elements
Make the UI more interactive.
- Arrow key navigation for command picker
- Tab completion for commands
- History navigation with up/down arrows
- Ctrl+R for search

## Implementation Priority

1. **Gradient Banner** (1h) - Most visible impact
2. **Rounded Panels** (1h) - Modern feel
3. **Status Bar Revamp** (2h) - Better information density
4. **Answer Rendering** (2h) - Cleaner output
5. **Tool Execution Visual** (2h) - Better feedback
6. **Thinking Spinner** (1h) - More polished feel
7. **Color Scheme** (1h) - Consistency
8. **Progress Indicators** (2h) - Better UX
9. **Panel Animations** (3h) - Polish
10. **Interactive Elements** (4h) - Power user features

## Total Estimate: ~20 hours for all quick wins

## Quick Win #1: Gradient Banner Implementation

Replace flat-color banner with gradient effect:

```python
def _gradient_text(text, start_color, end_color):
    """Apply gradient effect to text using ANSI 256-color codes."""
    result = ""
    for i, char in enumerate(text):
        if char == " ":
            result += char
            continue
        # Interpolate between colors
        ratio = i / max(1, len(text) - 1)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        # Convert to ANSI 256-color code
        code = 16 + int(36 * r / 255) * 36 + int(6 * g / 255) * 6 + int(6 * b / 255)
        result += f"\033[38;5;{code}m{char}"
    result += "\033[0m"
    return result

BANNER_GRADIENT = """
  ▐▄▄▄▄▄▄ .▄▄▄▄·  ▄▄▄· ▄▄▄▄▄
    ·██▀▄.▀·▐█ ▀█▪▐█ ▀█ •██
  ▪▄ ██▐▀▀▪▄▐█▀▀█▄▄█▀▀█  ▐█.▪
  ▐▌▐█▌▐█▄▄▌██▄▪▐█▐█ ▪▐▌ ▐█▌·
   ▀▀▀• ▀▀▀ ·▀▀▀▀  ▀  ▀  ▀▀▀
"""
```

## Quick Win #2: Rounded Panels

Replace double-line boxes with rounded corners:

```python
def _rounded_box(title, text, width=72):
    """Modern rounded box for panels."""
    w = width
    top = f"{C.CYAN}╭── {C.BOLD}{title}{C.RESET}{C.CYAN} " + "─" * max(1, w - len(title) - 6) + f"╮{C.RESET}"
    bottom = f"{C.CYAN}╰" + "─" * (w - 1) + f"╯{C.RESET}"
    print(top)
    for line in text.split("\n"):
        clean_line = _clean(line)
        pad = max(0, w - 2 - len(clean_line))
        print(f"{C.CYAN}│{C.RESET} {line}{' ' * pad}{C.CYAN}│{C.RESET}")
    print(bottom)
```

## Quick Win #3: Status Bar Revamp

```python
def bottom_bar(provider, model, tokens=0, iter_count=0, tool_count=0, elapsed_s=0.0, cost_usd=0.0):
    """Enhanced status bar with color sections."""
    ctx_max = 200000
    pct = min(100, int(tokens / ctx_max * 100)) if tokens else 0
    bar_len = 20
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    
    # Color sections
    provider_str = f"{C.CYAN}⚕ {model}{C.RESET}"
    token_str = f"{tokens:,}/{ctx_max:,}"
    bar_str = f"{C.GREEN}{bar}{C.RESET} {pct}%"
    tools_str = f"{C.MAGENTA}⚙ {tool_count}{C.RESET}"
    iter_str = f"{C.YELLOW}⛓ {iter_count}{C.RESET}"
    
    # Human-readable time
    mins = int(elapsed_s // 60)
    secs = int(elapsed_s % 60)
    time_str = f"{mins}m {secs}s"
    
    # Cost display
    cost_str = f"{C.GREEN}${cost_usd:.4f}{C.RESET}" if cost_usd > 0 else f"{C.DIM}$0.0000{C.RESET}"
    
    print(f"───────────────────────────────────────────────────────────────────────────────────────")
    print(f"  ❯ msg=ready · /help · /plan · /skills · Ctrl+C cancel")
    print(f"  {provider_str} │ {C.BOLD}{token_str}{C.RESET} │ [{bar_str}] │ {tools_str} │ {iter_str} │ {C.DIM}{time_str}{C.RESET} │ {cost_str}")
    print(f"───────────────────────────────────────────────────────────────────────────────────────")
```

## Quick Win #4: Tool Execution Visual

```python
def _print_tool_visual(actions, tool_times):
    """Visual tool execution with checkmarks and timing."""
    print()
    for i, (action, elapsed) in enumerate(zip(actions, tool_times)):
        # Parse tool name and args
        if "(" in action:
            tool_name = action.split("(")[0].strip()
            args = action.split("(", 1)[1].rstrip(")")
        else:
            tool_name = action
            args = ""
        
        # Print with checkmark and timing
        print(f"  {C.GREEN}✓{C.RESET} {C.CYAN}{tool_name}{C.RESET} {C.DIM}{args}{C.RESET}")
        print(f"    {C.DIM}↓ {elapsed:.1f}s{C.RESET}")
```

## Next Steps

1. Implement gradient banner
2. Update all panels to use rounded corners
3. Revamp status bar
4. Add tool execution visual
5. Test and iterate
