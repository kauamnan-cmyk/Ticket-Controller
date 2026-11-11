import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_native_splash/flutter_native_splash.dart';
import 'package:provider/provider.dart';
import 'core/providers/navigation_provider.dart';
import 'core/providers/session_provider.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'features/auth/splash/splash_gate.dart';
import 'features/main/home/viewmodels/ticket_viewmodel.dart';
import 'features/main/home/viewmodels/call_viewmodel.dart';
import 'features/main/home/viewmodels/return_waiting_viewmodel.dart';
import 'features/main/home/viewmodels/cancel_viewmodel.dart';
import 'features/main/home/viewmodels/confirm_arrival_viewmodel.dart';
import 'features/main/home/viewmodels/open_viewmodel.dart';
import 'features/main/home/viewmodels/block_viewmodel.dart';
import 'features/main/home/viewmodels/create_ticket_viewmodel.dart';
import 'features/main/home/viewmodels/verify_open_tickets.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

void main() async {
  final widgetsBinding = WidgetsFlutterBinding.ensureInitialized();
  FlutterNativeSplash.preserve(widgetsBinding: widgetsBinding);
  await dotenv.load(fileName: ".env");
  WakelockPlus.enable();
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  runApp(const RestartWidget(child: AppRoot()));
}

/// Widget raiz que permite reiniciar toda a Ã¡rvore de providers
/// Chamando RestartWidget.restartApp(context) recria tudo do zero
class RestartWidget extends StatefulWidget {
  const RestartWidget({super.key, required this.child});

  final Widget child;

  static void restartApp(BuildContext context) {
    context.findAncestorStateOfType<_RestartWidgetState>()?.restartApp();
  }

  @override
  State<RestartWidget> createState() => _RestartWidgetState();
}

class _RestartWidgetState extends State<RestartWidget> {
  Key _key = UniqueKey();

  void restartApp() {
    setState(() {
      _key = UniqueKey();
    });
  }

  @override
  Widget build(BuildContext context) {
    return KeyedSubtree(key: _key, child: widget.child);
  }
}

/// Toda a Ã¡rvore de providers e o app em si
class AppRoot extends StatelessWidget {
  const AppRoot({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => SessionProvider()),
        ChangeNotifierProvider(create: (_) => NavigationProvider()),
        ChangeNotifierProxyProvider<SessionProvider, TicketViewModel>(
          create: (_) => TicketViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, CallViewModel>(
          create: (_) => CallViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, ReturnWaitingViewModel>(
          create: (_) => ReturnWaitingViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, CancelViewModel>(
          create: (_) => CancelViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, ConfirmArrivalViewModel>(
          create: (_) => ConfirmArrivalViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, OpenViewModel>(
          create: (_) => OpenViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, BlockViewModel>(
          create: (_) => BlockViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, CreateTicketViewModel>(
          create: (_) => CreateTicketViewModel(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
        ChangeNotifierProxyProvider<SessionProvider, VerifyOpenTickets>(
          create: (_) => VerifyOpenTickets(),
          update: (_, session, vm) => vm!..updateSession(session.cookie),
        ),
      ],
      child: const MyApp(),
    );
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NextPubli',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF03050C),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF20BD),
          brightness: Brightness.dark,
          surface: const Color(0xFF03050C),
        ),
      ),
      home: const SplashGate(),
    );
  }
}
