import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'package:nextpubli/core/providers/session_provider.dart';

class ReturnLine extends ChangeNotifier {
  final Uri uri = Uri.parse('${dotenv.env['URL_BASE']}controle_acesso/v1/devolver_fila.php');

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  Future<bool> returnLine({
    required int usuarioId,
    required int clienteId,
    required int senhaId,
    required String? cookie,
    required SessionProvider sessionProvider,
    required BuildContext context,
  }) async {
    try {
      _isLoading = true;
      notifyListeners();

      final body = 'usuario_id=${usuarioId.toString()}&cliente_id=${clienteId.toString()}&id=${senhaId.toString()}';

      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'Cookie': ?cookie,
        },
        body: body,
      );

      if (response.statusCode == 200) {
        final data = _parseResponse(response.body);

        if (data['success'] == true) {
          final qtdChamadas = data['qtd_chamadas'];
          await sessionProvider.saveQtdChamadas(
            qtdChamadas is int ? qtdChamadas : null,
          );
          return true;
        }

        if (data['success'] == false && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(data['message'] ?? 'Erro ao devolver senha')),
          );
        }

        if (data['success'] == false && response.statusCode == 401) {
          if (context.mounted) Navigator.of(context).pushNamed('/login');
        }

        return false;
      }

      debugPrint('Failed to return ticket: ${response.statusCode}');
      return false;
    } catch (e, st) {
      debugPrint('Error returning ticket: $e\n$st');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Map<String, dynamic> _parseResponse(String body) {
    if (body.trim().isEmpty) {
      return {};
    }

    try {
      final decoded = json.decode(body);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
      if (decoded is Map) {
        return Map<String, dynamic>.from(decoded);
      }
    } catch (e) {
      debugPrint('Error parsing return ticket response: $e');
    }

    return {};
  }
}