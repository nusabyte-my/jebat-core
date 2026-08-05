"""Test autoMimpi + SelfLearn integration."""
import asyncio
from jebat.features.memory import (
    create_self_learning_memory,
    create_automimpi,
    create_selflearn,
    MemoryType,
)

async def test():
    memory = await create_self_learning_memory()

    await memory.remember('Learned nmap port scanning', tags={'network', 'scanning'})
    await memory.remember('SQL injection via login form', tags={'web', 'sqli'})
    await memory.remember('Failed to crack password with john', tags={'password', 'failure'})
    await memory.remember('Successfully used hydra for brute force', tags={'password', 'success'})
    await memory.remember('XSS payload in comment field', tags={'web', 'xss'})

    await memory.learn_from_outcome('nmap_scan', {'target': '10.0.0.1'}, 'Found 4 open ports', True, 0.8)
    await memory.learn_from_outcome('sqlmap_test', {'url': 'http://target/login'}, 'Injection successful', True, 0.9)
    await memory.learn_from_outcome('john_crack', {'hash': 'md5'}, 'Failed to crack', False, -0.5)

    automimpi = create_automimpi(memory)
    report = await automimpi.dream(force=True)

    print('=== DREAM REPORT ===')
    print(f'Date: {report.date}')
    print(f'Memories: {report.memories_processed}')
    print(f'Patterns: {report.patterns_extracted}')
    print(f'Quote: {report.laksamana_quote}')

    if report.profile:
        p = report.profile
        print(f'\nSkill: {p.skill_level}/10')
        print(f'Weak: {p.weak_areas}')
        print(f'Strong: {p.strong_areas}')
        print(f'Gaps: {p.knowledge_gaps}')
        print(f'Velocity: {p.learning_velocity:.2f}/hour')
        print(f'Health: {p.consolidation_health:.0%}')
        print(f'Strategies: {p.strategy_success_rates}')

    print(f'\nSuggestions ({len(report.suggestions)}):')
    for s in report.suggestions:
        print(f'  [{s.urgency.value.upper()}] {s.title}')

    msg = automimpi.get_welcome_message('humm1ngb1rd', streak=5)
    print(f'\nWelcome: {msg}')

    selflearn = create_selflearn(memory)
    a = selflearn.analyze()
    retention = a['retention_health']
    print(f'\nRetention avg: {retention["avg_strength"]:.2f}')
    print(f'Healthy ratio: {retention["healthy_ratio"]:.0%}')

    status = automimpi.get_status()
    print(f'Dreams: {status["dream_count"]}')

    await memory.stop_background_tasks()

asyncio.run(test())
