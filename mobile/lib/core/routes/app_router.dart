import 'package:go_router/go_router.dart';
import '../../features/chat/screens/chat_screen.dart';
import '../../features/memory/screens/memory_screen.dart';
import '../../features/agents/screens/agents_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/onboarding/screens/onboarding_screen.dart';
import '../../main_shell.dart';

class AppRouter {
  static final router = GoRouter(
    initialLocation: '/chat',
    routes: [
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/chat',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const ChatScreen(),
            ),
          ),
          GoRoute(
            path: '/memory',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const MemoryScreen(),
            ),
          ),
          GoRoute(
            path: '/agents',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const AgentsScreen(),
            ),
          ),
          GoRoute(
            path: '/settings',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const SettingsScreen(),
            ),
          ),
        ],
      ),
      GoRoute(
        path: '/onboarding',
        pageBuilder: (context, state) => NoTransitionPage(
          child: const OnboardingScreen(),
        ),
      ),
    ],
  );
}
