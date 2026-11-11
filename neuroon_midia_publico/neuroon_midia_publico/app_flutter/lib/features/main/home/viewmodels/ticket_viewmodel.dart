import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'package:nextpubli/features/main/home/models/senha_ticket.dart';
import 'dart:convert';

class TicketViewModel extends ChangeNotifier {
  List<SenhaTicket> _tickets = [];
  int? _usuarioId;
  int? _clienteId;
  bool _isLoading = false;
  String? _errorMessage;
  String? _cookie;

  void updateSession(String? cookie) {
    _cookie = cookie;
  }

  List<SenhaTicket> get tickets => _tickets;
  int? get usuarioId => _usuarioId;
  int? get clienteId => _clienteId;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  int get totalTickets => _tickets.length;
  int get waitingCount => _tickets.where((t) => t.status == 1).length;
  int get callingCount => _tickets.where((t) => t.status == 2).length;

  // Busca os dados brutos da API (lógica HTTP centralizada aqui)
  Future<Map<String, dynamic>> _fetchRaw() async {
    final url = Uri.parse(
        '${dotenv.env['URL_BASE']}controle_acesso/v1/senhas.php');

    final response = await http.get(url, headers: {'Cookie': _cookie ?? ''});
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // Carga inicial: exibe loading, substitui a lista completa
  Future<Map<String, dynamic>> buscarSenhas() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final data = await _fetchRaw();

      if (data['success'] == true) {
        final usuario = data['usuario'] as Map<String, dynamic>?;
        _usuarioId = usuario?['id'] as int?;
        _clienteId = usuario?['cliente_id'] as int?;

        final senhasJson = data['senhas'] as List<dynamic>? ?? [];
        _tickets = senhasJson
            .map((item) => SenhaTicket.fromJson(item as Map<String, dynamic>))
            .toList();

        _errorMessage = null;
      } else {
        _errorMessage = data['message'] ?? 'Erro ao buscar senhas';
      }

      return data;
    } catch (e) {
      _errorMessage = 'Erro ao carregar tickets: $e';
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Polling silencioso: sem loading, adiciona novos ao final e atualiza status
  Future<void> pollSenhas() async {
    try {
      final data = await _fetchRaw();

      if (data['success'] != true) return;

      // Atualiza usuário se ainda não tiver
      final usuario = data['usuario'] as Map<String, dynamic>?;
      _usuarioId ??= usuario?['id'] as int?;
      _clienteId ??= usuario?['cliente_id'] as int?;

      final senhasJson = data['senhas'] as List<dynamic>? ?? [];
      final fresh = senhasJson
          .map((item) => SenhaTicket.fromJson(item as Map<String, dynamic>))
          .toList();

      bool changed = false;

      // 1. Verifica se a quantidade mudou (ex: um ticket foi finalizado em outro celular e não vem mais na API)
      if (_tickets.length != fresh.length) {
        changed = true;
      } else {
        // 2. Se a quantidade for a mesma, verifica se houve alguma mudança de status ou ordem
        for (int i = 0; i < fresh.length; i++) {
          final t = _tickets[i];
          final f = fresh[i];
          if (t.id != f.id || t.status != f.status || t.chamadasTotal != f.chamadasTotal) {
            changed = true;
            break;
          }
        }
      }

      // Se algo mudou, sincroniza a lista local exatamente como a do servidor
      if (changed) {
        _tickets = fresh;
        notifyListeners();
      }
    } catch (_) {
      // Silencioso: erros de rede no polling não interrompem a UX
    }
  }
}