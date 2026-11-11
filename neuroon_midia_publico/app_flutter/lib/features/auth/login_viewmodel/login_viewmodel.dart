import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LoginViewModel extends ChangeNotifier {
  final Uri url = Uri.parse('${dotenv.env['URL_BASE']}login/v1/index.php');

  /// Faz login enviando email e senha via POST.
  /// Retorna um Map com 'success' e, em caso de erro, 'message'.
  Future<Map<String, dynamic>> loadLoginData(String email, String senha) async {
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'senha': senha}),
      );

      final data = json.decode(response.body) as Map<String, dynamic>;

      if (data['success'] == true) {
        // Captura o cookie de sessão (ex: "PHPSESSID=abc123; path=/; ...")
        final rawCookie = response.headers['set-cookie'];

        if (rawCookie != null) {
          final sessionCookie = rawCookie.split(
            ';',
          )[0]; // pega só "PHPSESSID=abc123"
          data['cookie'] = sessionCookie;
        } else {
          debugPrint(
            'Aviso: login OK, mas servidor não retornou cookie de sessão.',
          );
        }

        debugPrint('Login bem-sucedido');
        return data;
      } else {
        return {
          'success': false,
          'message': data['message'] ?? 'Email ou senha inválidos.',
        };
      }
    } catch (e) {
      debugPrint('Unexpected error: $e');
      return {'success': false, 'message': e.toString()};
    }
  }
}
