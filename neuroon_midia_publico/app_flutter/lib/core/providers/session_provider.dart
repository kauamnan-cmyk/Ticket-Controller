import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class SessionProvider extends ChangeNotifier {
  static const String _keyRememberMe = 'remember_me';
  static const String _keySavedEmail = 'saved_email';
  static const String _keySavedPassword = 'saved_password';
  static const String _keySessionCookie = 'session_cookie';
  static const String _keyStatusPrincipal = 'status_principal';
  static const String _keyStatusPermitidos = 'status_permitidos';
  static const String _keyAcessoSenhas = 'acesso_liberar_senhas';
  static const String _keyClienteId = 'cliente_id';

  String? _cookie;
  String? get cookie => _cookie;

  bool _rememberMe = false;
  bool get rememberMe => _rememberMe;

  String? _savedEmail;
  String? get savedEmail => _savedEmail;

  String? _savedPassword;
  String? get savedPassword => _savedPassword;

  String? _statusPrincipal;
  String? get statusPrincipal => _statusPrincipal;

  String? _statusPermitidos;
  String? get statusPermitidos => _statusPermitidos;

  String? _acessoLiberarSenhas;
  String? get acessoLiberarSenhas => _acessoLiberarSenhas;

  int? _clienteId;
  int? get clienteId => _clienteId;

  int? _qtdChamadas;
  int? get qtdChamadas => _qtdChamadas;

  bool _isLoading = true;
  bool get isLoading => _isLoading;
  

  SessionProvider() {
    loadSession();
  }

  Future<void> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    
    _cookie = prefs.getString(_keySessionCookie);
    _rememberMe = prefs.getBool(_keyRememberMe) ?? false;
    _statusPrincipal = prefs.getString(_keyStatusPrincipal);
    _statusPermitidos = prefs.getString(_keyStatusPermitidos);
    _acessoLiberarSenhas = prefs.getString(_keyAcessoSenhas);
    _clienteId = prefs.getInt(_keyClienteId);

    if (_rememberMe) {
      _savedEmail = prefs.getString(_keySavedEmail);
      _savedPassword = prefs.getString(_keySavedPassword);
    } else {
      _savedEmail = null;
      _savedPassword = null;
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> saveCookie(String newCookie) async {
    _cookie = newCookie;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keySessionCookie, newCookie);
    notifyListeners();
  }

  Future<void> saveUserStatus({
    String? principal,
    String? permitidos,
    String? acessoSenhas,
  }) async {
    _statusPrincipal = principal;
    _statusPermitidos = permitidos;
    _acessoLiberarSenhas = acessoSenhas;
    final prefs = await SharedPreferences.getInstance();

    if (principal != null) {
      await prefs.setString(_keyStatusPrincipal, principal);
    } else {
      await prefs.remove(_keyStatusPrincipal);
    }

    if (permitidos != null) {
      await prefs.setString(_keyStatusPermitidos, permitidos);
    } else {
      await prefs.remove(_keyStatusPermitidos);
    }

    if (acessoSenhas != null) {
      await prefs.setString(_keyAcessoSenhas, acessoSenhas);
    } else {
      await prefs.remove(_keyAcessoSenhas);
    }
    notifyListeners();
  }

  Future<void> saveClienteId(int? clienteId) async {
    _clienteId = clienteId;
    final prefs = await SharedPreferences.getInstance();

    if (clienteId != null) {
      await prefs.setInt(_keyClienteId, clienteId);
    } else {
      await prefs.remove(_keyClienteId);
    }

    notifyListeners();
  }

  Future<void> saveCredentials({
    required bool remember,
    required String email,
    required String password,
  }) async {
    _rememberMe = remember;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyRememberMe, remember);

    if (remember) {
      _savedEmail = email;
      _savedPassword = password;
      await prefs.setString(_keySavedEmail, email);
      await prefs.setString(_keySavedPassword, password);
    } else {
      _savedEmail = null;
      _savedPassword = null;
      await prefs.remove(_keySavedEmail);
      await prefs.remove(_keySavedPassword);
    }
    notifyListeners();
  }

  Future <void> saveQtdChamadas(int? qtdChamadas) async {
    _qtdChamadas = qtdChamadas;
    notifyListeners();
  }

  Future<void> clearSession() async {
    // 1. Destrói a sessão no servidor PHP
    try {
      final loginUrl = Uri.parse('${dotenv.env['URL_BASE']}login/v1/index.php');
      await http.delete(
        loginUrl,
        headers: {
          'Cookie': ?_cookie,
        },
      );
    } catch (e) {
      debugPrint('Aviso: não foi possível encerrar sessão no servidor: $e');
    }

    // 2. Limpa o estado local
    _cookie = null;
    _savedEmail = null;
    _savedPassword = null;
    _statusPrincipal = null;
    _statusPermitidos = null;
    _acessoLiberarSenhas = null;
    _clienteId = null;
    _rememberMe = false;

    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keySessionCookie);
    await prefs.remove(_keyClienteId);
    await prefs.remove(_keySavedEmail);
    await prefs.remove(_keySavedPassword);
    await prefs.remove(_keyStatusPrincipal);
    await prefs.remove(_keyStatusPermitidos);
    await prefs.remove(_keyAcessoSenhas);
    await prefs.setBool(_keyRememberMe, false);

    notifyListeners();
  }
}
