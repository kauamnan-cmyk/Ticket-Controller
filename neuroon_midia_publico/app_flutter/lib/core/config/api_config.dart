import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
class ReturnStatusHome extends ChangeNotifier {
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }
  final Uri uri = Uri.parse('${dotenv.env['URL_BASE']}');

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  Future<String> returnWaiting({
    required int usuarioId,
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
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        if (data['success'] == false) {
          return data['status'];
        }
        return data['status'];
      }

      debugPrint('Failed to return status filter: ${response.statusCode}');
        return '';
    } catch (e, st) {
      debugPrint('Error returning status filter: $e\n$st');
      return '';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
