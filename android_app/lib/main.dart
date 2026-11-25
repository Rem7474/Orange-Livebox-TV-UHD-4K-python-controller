import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'licenses.dart';
import 'models/remote_key.dart';
import 'screens/channels_screen.dart';
import 'screens/remote_screen.dart';
import 'screens/settings_screen.dart';
import 'services/livebox_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  registerOriginalProjectLicense();

  // Barre d'état système transparente
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF1B1B22),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  final liveboxService = LiveboxService();
  await liveboxService.init();

  runApp(
    ChangeNotifierProvider.value(
      value: liveboxService,
      child: const LiveboxApp(),
    ),
  );
}

class LiveboxApp extends StatelessWidget {
  const LiveboxApp({super.key});

  @override
  Widget build(BuildContext context) {
    const orangeColor = Color(0xFFFF6600);

    return MaterialApp(
      title: 'Télécommande TV Orange',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121214),
        colorScheme: const ColorScheme.dark(
          primary: orangeColor,
          secondary: Color(0xFFFF8533),
          surface: Color(0xFF1E1E24),
          error: Colors.redAccent,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1B1B22),
          foregroundColor: Colors.white,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: const Color(0xFF1B1B22),
          indicatorColor: orangeColor.withValues(alpha: 0.2),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const IconThemeData(color: orangeColor);
            }
            return const IconThemeData(color: Colors.white54);
          }),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const TextStyle(
                color: orangeColor,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              );
            }
            return const TextStyle(color: Colors.white54, fontSize: 12);
          }),
        ),
      ),
      home: const MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  static const double _desktopBreakpoint = 840;
  static const Color _orangeColor = Color(0xFFFF6600);
  static const Color _navBarColor = Color(0xFF1B1B22);

  static final Map<LogicalKeyboardKey, RemoteKey> _keyShortcuts = {
    LogicalKeyboardKey.arrowUp: RemoteKey.up,
    LogicalKeyboardKey.arrowDown: RemoteKey.down,
    LogicalKeyboardKey.arrowLeft: RemoteKey.left,
    LogicalKeyboardKey.arrowRight: RemoteKey.right,
    LogicalKeyboardKey.enter: RemoteKey.ok,
    LogicalKeyboardKey.numpadEnter: RemoteKey.ok,
    LogicalKeyboardKey.escape: RemoteKey.back,
    LogicalKeyboardKey.backspace: RemoteKey.back,
    LogicalKeyboardKey.space: RemoteKey.playPause,
    LogicalKeyboardKey.add: RemoteKey.volUp,
    LogicalKeyboardKey.numpadAdd: RemoteKey.volUp,
    LogicalKeyboardKey.equal: RemoteKey.volUp,
    LogicalKeyboardKey.minus: RemoteKey.volDown,
    LogicalKeyboardKey.numpadSubtract: RemoteKey.volDown,
    LogicalKeyboardKey.keyM: RemoteKey.mute,
    LogicalKeyboardKey.pageUp: RemoteKey.chUp,
    LogicalKeyboardKey.pageDown: RemoteKey.chDown,
    LogicalKeyboardKey.keyP: RemoteKey.power,
    LogicalKeyboardKey.keyH: RemoteKey.menu,
    LogicalKeyboardKey.digit0: RemoteKey.num0,
    LogicalKeyboardKey.numpad0: RemoteKey.num0,
    LogicalKeyboardKey.digit1: RemoteKey.num1,
    LogicalKeyboardKey.numpad1: RemoteKey.num1,
    LogicalKeyboardKey.digit2: RemoteKey.num2,
    LogicalKeyboardKey.numpad2: RemoteKey.num2,
    LogicalKeyboardKey.digit3: RemoteKey.num3,
    LogicalKeyboardKey.numpad3: RemoteKey.num3,
    LogicalKeyboardKey.digit4: RemoteKey.num4,
    LogicalKeyboardKey.numpad4: RemoteKey.num4,
    LogicalKeyboardKey.digit5: RemoteKey.num5,
    LogicalKeyboardKey.numpad5: RemoteKey.num5,
    LogicalKeyboardKey.digit6: RemoteKey.num6,
    LogicalKeyboardKey.numpad6: RemoteKey.num6,
    LogicalKeyboardKey.digit7: RemoteKey.num7,
    LogicalKeyboardKey.numpad7: RemoteKey.num7,
    LogicalKeyboardKey.digit8: RemoteKey.num8,
    LogicalKeyboardKey.numpad8: RemoteKey.num8,
    LogicalKeyboardKey.digit9: RemoteKey.num9,
    LogicalKeyboardKey.numpad9: RemoteKey.num9,
  };

  int _currentIndex = 0;
  static const List<Widget> _screens = [
    RemoteScreen(),
    ChannelsScreen(),
    SettingsScreen(),
  ];

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    final primary = FocusManager.instance.primaryFocus;
    if (primary?.context?.widget is EditableText) {
      return KeyEventResult.ignored;
    }
    final remoteKey = _keyShortcuts[event.logicalKey];
    if (remoteKey == null) return KeyEventResult.ignored;
    unawaited(context.read<LiveboxService>().sendKey(remoteKey));
    return KeyEventResult.handled;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      autofocus: true,
      onKeyEvent: _handleKeyEvent,
      child: LayoutBuilder(
        builder: (context, constraints) {
          if (constraints.maxWidth >= _desktopBreakpoint) {
            return _buildDesktopScaffold();
          }
          return _buildMobileScaffold();
        },
      ),
    );
  }

  Widget _buildMobileScaffold() {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) {
          HapticFeedback.selectionClick();
          setState(() => _currentIndex = idx);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.settings_remote_outlined),
            selectedIcon: Icon(Icons.settings_remote_rounded),
            label: 'Télécommande',
          ),
          NavigationDestination(
            icon: Icon(Icons.tv_outlined),
            selectedIcon: Icon(Icons.tv_rounded),
            label: 'Chaînes',
          ),
          NavigationDestination(
            icon: Icon(Icons.tune_outlined),
            selectedIcon: Icon(Icons.tune_rounded),
            label: 'Paramètres',
          ),
        ],
      ),
    );
  }

  Widget _buildDesktopScaffold() {
    final railIndex = _currentIndex == 2 ? 1 : 0;
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: railIndex,
            backgroundColor: _navBarColor,
            indicatorColor: _orangeColor.withValues(alpha: 0.2),
            labelType: NavigationRailLabelType.all,
            selectedIconTheme: const IconThemeData(color: _orangeColor),
            unselectedIconTheme: const IconThemeData(color: Colors.white54),
            selectedLabelTextStyle: const TextStyle(
              color: _orangeColor,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
            unselectedLabelTextStyle: const TextStyle(
              color: Colors.white54,
              fontSize: 12,
            ),
            onDestinationSelected: (idx) {
              setState(() => _currentIndex = idx == 0 ? 0 : 2);
            },
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.settings_remote_outlined),
                selectedIcon: Icon(Icons.settings_remote_rounded),
                label: Text('Télécommande'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.tune_outlined),
                selectedIcon: Icon(Icons.tune_rounded),
                label: Text('Paramètres'),
              ),
            ],
          ),
          const VerticalDivider(width: 1, color: Colors.white12),
          Expanded(
            child: railIndex == 0
                ? const Row(
                    children: [
                      SizedBox(width: 400, child: RemoteScreen()),
                      VerticalDivider(width: 1, color: Colors.white12),
                      Expanded(child: ChannelsScreen()),
                    ],
                  )
                : const SettingsScreen(),
          ),
        ],
      ),
    );
  }
}
