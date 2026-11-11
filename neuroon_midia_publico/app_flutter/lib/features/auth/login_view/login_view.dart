import 'package:flutter/material.dart';
import 'package:nextpubli/core/components/login/email_component.dart';
import 'package:nextpubli/core/components/login/senha_component.dart';
import 'package:nextpubli/features/auth/login_viewmodel/login_viewmodel.dart';
import 'package:nextpubli/features/main/home/views/home_view.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/providers/session_provider.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key});

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final LoginViewModel viewModel = LoginViewModel();
  bool isLoading = false;
  bool rememberMe = false;

  @override
  void initState() {
    super.initState();
    _loadSavedCredentials();
  }

  void _loadSavedCredentials() {
    final session = context.read<SessionProvider>();
    if (session.isLoading) {
      session.addListener(_onSessionLoaded);
    } else {
      _checkAutoLogin(session);
    }
  }

  void _onSessionLoaded() {
    final session = context.read<SessionProvider>();
    if (!session.isLoading) {
      session.removeListener(_onSessionLoaded);
      _checkAutoLogin(session);
    }
  }

  void _checkAutoLogin(SessionProvider session) {
    if (session.rememberMe) {
      final String? email = session.savedEmail;
      final String? password = session.savedPassword;
      if (email != null &&
          password != null &&
          email.isNotEmpty &&
          password.isNotEmpty) {
        setState(() {
          rememberMe = true;
          emailController.text = email;
          passwordController.text = password;
          isLoading = true;
        });
        _autoLogin(email, password);
      }
    }
  }

  void _autoLogin(String email, String password) async {
    final result = await viewModel.loadLoginData(email, password);

    if (mounted) {
      setState(() {
        isLoading = false;
      });
    }

    if (result['success'] == true) {
      if (mounted) {
        final session = context.read<SessionProvider>();
        if (result['cookie'] != null) {
          session.saveCookie(result['cookie']);
        }
        final user = result['user'];
        debugPrint('=== AUTO-LOGIN result[user] ===');
        debugPrint('user: $user');
        debugPrint('controle_status_permitido: ${user?['controle_status_permitidos']}');
        debugPrint('controle_status_principal: ${user?['controle_status_principal']}');
        debugPrint('acesso_liberar_senhas: ${user?['acesso_liberar_senhas']}');
        if (user != null) {
          _saveLoginUser(session, user);
        }
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeView()),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Falha no login automÃ¡tico: ${result['message'] ?? 'Erro desconhecido'}',
            ),
          ),
        );
      }
    }
  }

  int? _parseClienteId(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    return int.tryParse(value.toString());
  }

  void _saveLoginUser(SessionProvider session, Map<String, dynamic>? user) {
    if (user == null) return;
    session.saveUserStatus(
      principal: user['controle_status_principal']?.toString(),
      permitidos: user['controle_status_permitidos']?.toString(),
      acessoSenhas: user['acesso_liberar_senhas']?.toString(),
    );
    session.saveClienteId(_parseClienteId(user['cliente_id']));
  }

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    viewModel.dispose();
    super.dispose();
  }

  void handleLogin() async {
    if (emailController.text.isEmpty || passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, preencha todos os campos')),
      );
      return;
    }

    setState(() {
      isLoading = true;
    });

    final result = await viewModel.loadLoginData(
      emailController.text,
      passwordController.text,
    );

    setState(() {
      isLoading = false;
    });

    if (result['success'] == true) {
      if (mounted) {
        final session = context.read<SessionProvider>();
        if (result['cookie'] != null) {
          session.saveCookie(result['cookie']);
        }

        final user = result['user'];
        debugPrint('=== LOGIN result[user] ===');
        debugPrint('user: $user');
        debugPrint('controle_status_permitido: ${user?['controle_status_permitidos']}');
        debugPrint('controle_status_principal: ${user?['controle_status_principal']}');
        debugPrint('acesso_liberar_senhas: ${user?['acesso_liberar_senhas']}');
        if (user != null) {
          _saveLoginUser(session, user);
        }

        session.saveCredentials(
          remember: rememberMe,
          email: emailController.text,
          password: passwordController.text,
        );

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeView()),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? 'Erro no login')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF03050C), // Fundo suave
      body: Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Container(
              constraints: const BoxConstraints(maxWidth: 400),
              padding: const EdgeInsets.all(32.0),
              decoration: BoxDecoration(
                color: Color(0xFF03050C),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withAlpha(13),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(
                    width: 120,
                    height: 120,
                    child: Image.asset(
                      'assets/images/logo_login.png',
                      fit: BoxFit.contain,
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Bem-vindo de volta',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFFF2F4F7),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Faca login para acessar o painel do seu restaurante.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 14, color: Color(0xFFF2F4F7)),
                  ),
                  const SizedBox(height: 10),
                  EmailComponente(controller: emailController),
                  const SizedBox(height: 16),
                  SenhaComponente(
                    controller: passwordController,
                    obscureText: true,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Theme(
                        data: Theme.of(context).copyWith(
                          unselectedWidgetColor: const Color(0xFFF2F4F7),
                        ),
                        child: Checkbox(
                          value: rememberMe,
                          onChanged: (value) {
                            setState(() {
                              rememberMe = value ?? false;
                            });
                          },
                          activeColor: const Color(0xFFFF20BD),
                          checkColor: Colors.white,
                          side: const BorderSide(color: Color(0xFFF2F4F7)),
                        ),
                      ),
                      const Text(
                        'Lembrar minha senha',
                        style: TextStyle(
                          color: Color(0xFFF2F4F7),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : GestureDetector(
                          onTap: handleLogin,
                          child: Container(
                            height: 56,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFFFF20BD), Color(0xFF783DFF)],
                                begin: Alignment.centerLeft,
                                end: Alignment.centerRight,
                              ),
                              borderRadius: BorderRadius.circular(16),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(
                                    0xFF783DFF,
                                  ).withValues(alpha: 0.25),
                                  blurRadius: 16,
                                  offset: const Offset(0, 8),
                                ),
                              ],
                            ),
                            child: const Center(
                              child: Text(
                                'Entrar',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ),
                        ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
