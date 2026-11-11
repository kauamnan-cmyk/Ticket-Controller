import 'package:flutter/material.dart';
import 'package:flutter_native_splash/flutter_native_splash.dart';
import 'package:nextpubli/core/providers/session_provider.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/features/auth/login_view/login_view.dart';
import 'package:provider/provider.dart';

class SplashGate extends StatefulWidget {
  const SplashGate({super.key});

  @override
  State<SplashGate> createState() => _SplashGateState();
}

class _SplashGateState extends State<SplashGate>
    with SingleTickerProviderStateMixin {
  static const Color _background = Color(0xFF03050C);

  late final AnimationController _controller;
  late final Animation<double> _pulse;
  late final Animation<double> _glow;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);

    _pulse = Tween<double>(begin: 0.96, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _glow = Tween<double>(begin: 0.18, end: 0.34).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    final session = context.read<SessionProvider>();
    session.addListener(_onSessionChanged);
    _onSessionChanged();
  }

  @override
  void dispose() {
    context.read<SessionProvider>().removeListener(_onSessionChanged);
    _controller.dispose();
    super.dispose();
  }

  void _onSessionChanged() {
    if (!context.read<SessionProvider>().isLoading) {
      FlutterNativeSplash.remove();
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionProvider>();

    if (!session.isLoading) {
      return const LoginView();
    }

    return Scaffold(
      backgroundColor: _background,
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF03050C),
                  Color(0xFF0B1020),
                  Color(0xFF120A24),
                ],
              ),
            ),
          ),
          Positioned(
            top: -80,
            right: -60,
            child: AnimatedBuilder(
              animation: _glow,
              builder: (context, child) {
                return Container(
                  width: 220,
                  height: 220,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withValues(alpha: _glow.value),
                        blurRadius: 90,
                        spreadRadius: 20,
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          Positioned(
            bottom: -100,
            left: -70,
            child: AnimatedBuilder(
              animation: _glow,
              builder: (context, child) {
                return Container(
                  width: 240,
                  height: 240,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.secundary.withValues(alpha: _glow.value),
                        blurRadius: 100,
                        spreadRadius: 24,
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          Center(
            child: AnimatedBuilder(
              animation: _pulse,
              builder: (context, child) {
                return Transform.scale(
                  scale: _pulse.value,
                  child: child,
                );
              },
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [
                          AppColors.primary.withValues(alpha: 0.12),
                          AppColors.secundary.withValues(alpha: 0.12),
                        ],
                      ),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.08),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.primary.withValues(alpha: 0.18),
                          blurRadius: 32,
                          spreadRadius: 4,
                        ),
                      ],
                    ),
                    child: Image.asset(
                      'assets/images/logo_login.png',
                      width: 140,
                      height: 140,
                      fit: BoxFit.contain,
                    ),
                  ),
                  const SizedBox(height: 36),
                  const Text(
                    'NextPubli',
                    style: TextStyle(
                      color: AppColors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Preparando seu painel...',
                    style: TextStyle(
                      color: AppColors.white.withValues(alpha: 0.62),
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: 42,
                    height: 42,
                    child: ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [AppColors.primary, AppColors.secundary],
                      ).createShader(bounds),
                      child: CircularProgressIndicator(
                        strokeWidth: 3,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          AppColors.white,
                        ),
                        backgroundColor: Colors.white.withValues(alpha: 0.08),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
