import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
class BlockViewModel extends ChangeNotifier {
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }
  final Uri uri = Uri.parse(
    '${dotenv.env['URL_BASE']}controle_acesso/v1/abertura_senhas.php',
  );

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  Future<bool> open({
    required int quantidade,
    required BuildContext context,
  }) async {
    try {
      _isLoading = true;
      notifyListeners();

      final cookie = _cookie;

      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Cookie': ?cookie,
        },
        body: jsonEncode({'qtd': quantidade, 'acao': 'bloquear'}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        if (data['success'] == false) {
          if (context.mounted) Navigator.of(context).pushNamed('/login');
          return false;
        }
        return data['success'] == true;
      }

      debugPrint('Failed to open tickets: ${response.statusCode}');
      return false;
    } catch (e, st) {
      debugPrint('Error opening tickets: $e\n$st');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
