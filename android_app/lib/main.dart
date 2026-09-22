import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'screens/channels_screen.dart';
import 'screens/remote_screen.dart';
import 'screens/settings_screen.dart';
import 'services/livebox_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

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
      title: 'Télécommande Livebox TV',
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
  int _currentIndex = 0;
  static const List<Widget> _screens = [
    RemoteScreen(),
    ChannelsScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
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
}
