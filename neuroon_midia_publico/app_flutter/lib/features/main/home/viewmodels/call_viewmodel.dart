import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
class CallViewModel extends ChangeNotifier {
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }
  final Uri uri = Uri.parse('${dotenv.env['URL_BASE']}controle_acesso/v1/chamar.php');

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  Future<bool> chamar({
    required int usuarioId,
    required int clienteId,
    required int senhaId,
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
        body: jsonEncode({
          'usuario_id': usuarioId,
          'cliente_id': clienteId,
          'id': senhaId,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;

        if (data['success'] == true) {
          return true;
        }

        if (data['success'] == false && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(data['message'] ?? 'Erro ao chamar senha')),
          );
        }

        if (data['success'] == false && response.statusCode == 401) {
          if (context.mounted) Navigator.of(context).pushNamed('/login');
        }

        return false;
      }

      debugPrint('Failed to call ticket: ${response.statusCode}');
      return false;
    } catch (e, st) {
      debugPrint('Error calling ticket: $e\n$st');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}