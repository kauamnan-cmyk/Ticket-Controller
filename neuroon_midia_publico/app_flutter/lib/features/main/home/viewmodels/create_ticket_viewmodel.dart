import 'package:flutter/material.dart';
import 'package:nextpubli/core/validators/customer_name_validator.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class CreateTicketViewModel extends ChangeNotifier {
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }

  final Uri uri = Uri.parse(
    '${dotenv.env['URL_BASE']}controle_acesso/v1/adicionar.php',
  );

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  Future<bool> cancel({
    required String clienteNome,
    required int clienteId,
    required String telefone,
    required int qtdPessoas,
    required int qtdCadeirantes,
    required int qtdCriancas,
    required BuildContext context,
  }) async {
    final nameError = CustomerNameValidator.validate(clienteNome);
    if (nameError != null) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(nameError)));
      }
      return false;
    }

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
          'cliente_nome': CustomerNameValidator.normalize(clienteNome),
          'cliente_id': clienteId,
          'telefone': telefone,
          'qtd_pessoas': qtdPessoas,
          'qtd_cadeirantes': qtdCadeirantes,
          'qtd_criancas': qtdCriancas,
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;

        if (data['success'] == true) {
          return true;
        }

        if (data['success'] == false && context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(data['message'] ?? 'Erro ao adicionar senha'),
            ),
          );
        }

        if (data['success'] == false && response.statusCode == 401) {
          if (context.mounted) Navigator.of(context).pushNamed('/login');
        }

        return false;
      }

      debugPrint('Failed to create ticket: ${response.statusCode}');
      return false;
    } catch (e, st) {
      debugPrint('Error to crete ticket: $e\n$st');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
