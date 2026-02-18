# JEBAT Lessons Learned

**Project**: JEBAT - Personal AI Assistant with Eternal Memory
**Started**: 2026-02-18
**Purpose**: Continuous improvement through pattern recognition

---

## 📚 Core Principles

### Workflow Orchestration

#### 1. Plan Mode Default
**Rule**: Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)

**Pattern**:
- If something goes sideways → STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity
- Don't keep pushing when stuck - pause and reassess

**Anti-Pattern**:
- ❌ Jumping into code without planning
- ❌ Continuing down a failing path hoping it works
- ❌ Skipping verification steps

---

#### 2. Subagent Strategy
**Rule**: Use subagents liberally to keep main context window clean

**Pattern**:
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution
- Use general-purpose subagent for open-ended searches

**Anti-Pattern**:
- ❌ Trying to do everything in main context
- ❌ Losing context due to long conversations
- ❌ Sequential research instead of parallel

---

#### 3. Self-Improvement Loop
**Rule**: After ANY correction from user: update `tasks/lessons.md` with the pattern

**Pattern**:
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project
- Make lessons actionable and specific

**Anti-Pattern**:
- ❌ Making the same mistake twice
- ❌ Vague lessons that don't guide action
- ❌ Forgetting to review lessons

---

#### 4. Verification Before Done
**Rule**: Never mark a task complete without proving it works

**Pattern**:
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness
- Add verification steps to todo.md

**Anti-Pattern**:
- ❌ Marking tasks complete without testing
- ❌ Assuming code works without verification
- ❌ Skipping test runs

---

#### 5. Demand Elegance (Balanced)
**Rule**: For non-trivial changes: pause and ask "is there a more elegant way?"

**Pattern**:
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it
- Balance elegance with pragmatism

**Anti-Pattern**:
- ❌ Accepting hacky solutions
- ❌ Over-engineering simple fixes
- ❌ Not questioning own assumptions

---

#### 6. Autonomous Bug Fixing
**Rule**: When given a bug report: just fix it. Don't ask for hand-holding

**Pattern**:
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how
- Take ownership of problems

**Anti-Pattern**:
- ❌ Asking user how to fix obvious bugs
- ❌ Waiting for instructions on test failures
- ❌ Requiring user to debug with you

---

## 🔧 Technical Patterns

### Pattern 1: Import Path Consistency
**Date**: 2026-02-17
**Problem**: Import errors due to inconsistent module paths

**Solution**:
- Use absolute imports from project root
- Ensure `__init__.py` files exist in all packages
- Export only public APIs in `__all__`

**Lesson**:
```python
# ✅ Good
from jebat.core.memory import MemoryManager
from jebat.features.ultra_loop import UltraLoop

# ❌ Bad
from ..memory import MemoryManager
from memory_manager import MemoryManager
```

---

### Pattern 2: Initialization Order
**Date**: 2026-02-17
**Problem**: Logger accessed before initialization in `__init__()`

**Solution**:
- Initialize logger as first line in `__init__()`
- Dependencies before dependents
- Simple values before complex objects

**Lesson**:
```python
# ✅ Good
def __init__(self, config=None):
    self.logger = logging.getLogger(__name__)  # First!
    self.config = config or {}
    self.memory_manager = self._init_memory()
    self.agents = self._init_agents()

# ❌ Bad
def __init__(self, config=None):
    self.config = config or {}
    self.memory_manager = self._init_memory()
    self.logger = logging.getLogger(__name__)  # Too late!
    self.logger.info("Initialized")  # Crashes!
```

---

### Pattern 3: Enum Consistency
**Date**: 2026-02-17
**Problem**: Using short enum names that don't exist

**Solution**:
- Use full enum member names as defined
- Don't assume shortened versions exist
- Check enum definitions before use

**Lesson**:
```python
# ✅ Good
MemoryLayer.M1_EPISODIC
MemoryLayer.M2_SEMANTIC

# ❌ Bad
MemoryLayer.M1  # Doesn't exist!
MemoryLayer.M2  # Doesn't exist!
```

---

### Pattern 4: Required Arguments
**Date**: 2026-02-17
**Problem**: Class constructors with required arguments not provided

**Solution**:
- Check constructor signatures before instantiation
- Provide all required arguments
- Use dependency injection pattern

**Lesson**:
```python
# ✅ Good
engine = DecisionEngine(agent_registry={})

# ❌ Bad
engine = DecisionEngine()  # Missing required argument!
```

---

### Pattern 5: Async/Await Pattern
**Date**: 2026-02-17
**Problem**: Mixing sync and async code incorrectly

**Solution**:
- Use `async def` for I/O-bound operations
- Use `await` when calling async functions
- Use `asyncio.create_task()` for parallel execution

**Lesson**:
```python
# ✅ Good
async def process(self):
    result = await self.fetch_data()
    tasks = [asyncio.create_task(t()) for t in tasks]
    await asyncio.gather(*tasks)

# ❌ Bad
async def process(self):
    result = self.fetch_data()  # Should be awaited!
    for t in tasks:
        t()  # Should be create_task!
```

---

### Pattern 6: Error Handling
**Date**: 2026-02-17
**Problem**: Silent failures or missing error context

**Solution**:
- Log errors with full context
- Include error type and stack trace
- Provide actionable error messages

**Lesson**:
```python
# ✅ Good
try:
    await self.process()
except Exception as e:
    logger.error(f"Processing failed: {type(e).__name__}: {e}", exc_info=True)
    raise

# ❌ Bad
try:
    await self.process()
except Exception as e:
    logger.error("Failed")  # No context!
```

---

### Pattern 7: Testing Strategy
**Date**: 2026-02-17
**Problem**: Tests failing due to missing dependencies

**Solution**:
- Mock external dependencies
- Use integration tests for full system
- Use unit tests for isolated components

**Lesson**:
```python
# ✅ Good - Integration test
async def test_full_integration():
    loop = await create_ultra_loop()
    think = await create_ultra_think()
    # Test real components together

# ✅ Good - Unit test
def test_memory_calculation():
    # Test isolated logic
    score = calculate_heat(frequency=5, depth=0.8)
    assert 0.0 <= score <= 1.0
```

---

## 🎯 Architecture Patterns

### Pattern 1: Layered Architecture
**Principle**: Separate concerns into distinct layers

**Application**:
- Memory: M0 → M1 → M2 → M3 → M4
- Cognitive: Comprehension → Orchestration → Reasoning → Evaluation
- Ultra-Loop: Perception → Cognition → Memory → Action → Learning

**Benefit**: Clear boundaries, testable components, maintainable

---

### Pattern 2: Phase-Based Processing
**Principle**: Break complex processes into phases

**Application**:
- Each phase has clear inputs/outputs
- Phases can be tested independently
- Easy to add hooks between phases

**Benefit**: Modularity, observability, flexibility

---

### Pattern 3: Event-Driven Design
**Principle**: Use events for loose coupling

**Application**:
- Cycle start/end events
- Phase completion events
- Error events

**Benefit**: Extensibility, monitoring, debugging

---

### Pattern 4: Metrics-First
**Principle**: Track metrics from the start

**Application**:
- Cycle count and success rate
- Execution time and throughput
- Error rates and types

**Benefit**: Observability, performance tuning, debugging

---

## 📝 Documentation Patterns

### Pattern 1: Self-Documenting Code
**Principle**: Code should explain itself

**Application**:
- Descriptive variable names
- Clear function names
- Type hints for signatures

**Benefit**: Less maintenance, easier onboarding

---

### Pattern 2: Living Documentation
**Principle**: Documentation evolves with code

**Application**:
- Update docs when updating code
- Keep examples current
- Remove obsolete docs

**Benefit**: Trustworthy docs, reduced confusion

---

## 🔄 Review Cadence

### Daily
- Review lessons.md at session start
- Add new lessons after corrections
- Mark completed tasks in todo.md

### Weekly
- Review all lessons for patterns
- Consolidate duplicate lessons
- Update todo.md priorities

### Per-Project
- Create project-specific lessons
- Link to general lessons
- Archive obsolete lessons

---

## 📊 Lesson Categories

1. **Workflow** - How to work effectively
2. **Technical** - Code patterns and practices
3. **Architecture** - System design patterns
4. **Testing** - Testing strategies
5. **Documentation** - Documentation practices
6. **Debugging** - Problem-solving patterns

---

**Last Updated**: 2026-02-18
**Total Lessons**: 13
**Categories**: 6
