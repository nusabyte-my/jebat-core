import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          const ListTile(
            leading: Icon(Icons.wifi),
            title: Text('Gateway URL'),
            subtitle: Text('https://jebat.online'),
            trailing: Icon(Icons.chevron_right),
          ),
          const ListTile(
            leading: Icon(Icons.psychology),
            title: Text('Default Thinking Mode'),
            subtitle: Text('Deliberate'),
            trailing: Icon(Icons.chevron_right),
          ),
          const ListTile(
            leading: Icon(Icons.model_training),
            title: Text('LLM Provider'),
            subtitle: Text('Ollama'),
            trailing: Icon(Icons.chevron_right),
          ),
          const Divider(),
          const ListTile(
            leading: Icon(Icons.mic),
            title: Text('Voice Input'),
            subtitle: Text('Configure STT/TTS'),
            trailing: Icon(Icons.chevron_right),
          ),
          const ListTile(
            leading: Icon(Icons.shield),
            title: Text('Security Scan on Startup'),
            trailing: Switch(value: true, onChanged: null),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.info),
            title: const Text('About JEBAT'),
            subtitle: const Text('v2.0.0 · nusabyte.my'),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}
