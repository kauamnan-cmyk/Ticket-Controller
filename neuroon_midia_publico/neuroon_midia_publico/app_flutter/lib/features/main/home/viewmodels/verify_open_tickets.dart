import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
class VerifyOpenTickets extends ChangeNotifier {
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }
  Future<bool> verifyStatus() async {
    try {
      final verifyUri = Uri.parse('${dotenv.env['URL_BASE']}controle_acesso/v1/verificar_abertura.php');
      final response = await http.get(
        verifyUri,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Cookie': ?_cookie,
        },
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        
        if (data['success'] == true) {
          if (data.containsKey('abertura') && data['abertura'] != null) {
            final abertura = data['abertura'] as Map<String, dynamic>;
            final status = int.tryParse(abertura['status']?.toString() ?? '');
            final qtdLimite = int.tryParse(abertura['qtd_limite']?.toString() ?? '');
            final qtdGeradas = int.tryParse(abertura['qtd_geradas']?.toString() ?? '');

            // Se atingiu o limite de senhas geradas
            if (qtdLimite != null && qtdGeradas != null && qtdLimite == qtdGeradas) {
              return false; // Retorna falso para exibir cadeado vermelho
            }

            // Se o status for 1 (fechado manualmente ou de outra forma)
            if (status == 1) {
              return false; // Retorna falso para exibir cadeado vermelho
            }

            // Se o status for 0 (senhas abertas)
            if (status == 0) {
              return true; // Retorna verdadeiro para exibir cadeado verde
            }
          }
          
          // Fallback se 'abertura' não estiver presente
          return data['liberado'] == true;
        }
      }
    } catch (e, st) {
      debugPrint('Error verifying tickets status: $e\n$st');
    }
    return false;
  }
}