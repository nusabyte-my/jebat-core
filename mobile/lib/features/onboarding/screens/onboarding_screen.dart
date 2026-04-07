import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  int _currentStep = 0;
  final _gatewayController = TextEditingController(text: 'https://jebat.online');
  final _nameController = TextEditingController();

  final _steps = ['Welcome', 'Connect', 'Profile', 'Done'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Setup · Step ${_currentStep + 1}/4'),
        leading: _currentStep > 0
            ? IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => setState(() => _currentStep--))
            : null,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_currentStep == 0) _buildWelcomeStep(),
            if (_currentStep == 1) _buildConnectStep(),
            if (_currentStep == 2) _buildProfileStep(),
            if (_currentStep == 3) _buildDoneStep(),
            const Spacer(),
            ElevatedButton(
              onPressed: _currentStep < 3
                  ? () => setState(() => _currentStep++)
                  : () => context.go('/chat'),
              child: Text(_currentStep < 3 ? 'Next' : 'Start Using JEBAT'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWelcomeStep() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('⚔️', style: TextStyle(fontSize: 64)),
        SizedBox(height: 24),
        Text('Welcome to JEBAT', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
        SizedBox(height: 12),
        Text('Your AI assistant with eternal memory, multi-agent orchestration, and built-in security.',
            style: TextStyle(color: Colors.grey, fontSize: 16)),
      ],
    );
  }

  Widget _buildConnectStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Connect to Gateway', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text('Enter your JEBAT gateway URL to connect.', style: TextStyle(color: Colors.grey)),
        const SizedBox(height: 24),
        TextField(
          controller: _gatewayController,
          decoration: const InputDecoration(
            labelText: 'Gateway URL',
            hintText: 'https://jebat.online',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.link),
          ),
        ),
      ],
    );
  }

  Widget _buildProfileStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Your Profile', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text('What should we call you?', style: TextStyle(color: Colors.grey)),
        const SizedBox(height: 24),
        TextField(
          controller: _nameController,
          decoration: const InputDecoration(
            labelText: 'Name',
            hintText: 'Your name',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.person),
          ),
        ),
      ],
    );
  }

  Widget _buildDoneStep() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('🎉', style: TextStyle(fontSize: 64)),
        SizedBox(height: 24),
        Text('You\'re All Set!', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
        SizedBox(height: 12),
        Text('JEBAT is ready. Start chatting, explore your memory, or browse agents.',
            style: TextStyle(color: Colors.grey, fontSize: 16)),
      ],
    );
  }
}
