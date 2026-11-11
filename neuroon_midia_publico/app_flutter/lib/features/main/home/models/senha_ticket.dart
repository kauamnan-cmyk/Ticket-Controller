class SenhaTicket {
  final int id;
  final int clienteId;
  final String senha;
  final String clienteNome;
  final int status; // 1=Aguardando, 2=Chamado, 3=Aceito, 4=Confirmado, 5=Cancelado
  final String gerada;
  final String telefone;
  final int qtdPessoas;
  final int qtdCadeirantes;
  final int qtdCriancas;
  final String? chamadoEm;
  final String? canceladoEm;
  final String? confirmadoEm;
  final int chamadasTotal;

  SenhaTicket({
    required this.id,
    required this.clienteId,
    required this.senha,
    required this.clienteNome,
    required this.status,
    required this.gerada,
    required this.telefone,
    required this.qtdPessoas,
    required this.qtdCadeirantes,
    required this.qtdCriancas,
    this.chamadoEm,
    this.canceladoEm,
    this.confirmadoEm,
    this.chamadasTotal = 0,
  });

  factory SenhaTicket.fromJson(Map<String, dynamic> json) {
    return SenhaTicket(
      id: _parseInt(json['id']),
      clienteId: _parseInt(json['cliente_id']),
      senha: json['senha']?.toString() ?? '',
      clienteNome: json['cliente_nome']?.toString() ?? '',
      status: _parseInt(json['status']),
      gerada: json['gerada']?.toString() ?? '',
      telefone: json['telefone']?.toString() ?? '',
      qtdPessoas: _parseInt(json['qtd_pessoas']),
      qtdCadeirantes: _parseInt(json['qtd_cadeirantes']),
      qtdCriancas: _parseInt(json['qtd_criancas']),
      chamadoEm: json['chamado_em']?.toString(),
      canceladoEm: json['cancelado_em']?.toString(),
      confirmadoEm: json['confirmado_em']?.toString(),
      chamadasTotal: _parseInt(json['chamadas_total']),
    );
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    return int.tryParse(value.toString()) ?? 0;
  }

  String get entradaFila {
    final parts = gerada.split(' ');
    if (parts.length < 2) return gerada;
    final timeParts = parts[1].split(':');
    if (timeParts.length < 2) return parts[1];
    return '${timeParts[0]}:${timeParts[1]}';
  }

  String get tempoEspera {
    try {
      final geradaEm = DateTime.parse(gerada);
      final diferenca = DateTime.now().difference(geradaEm);

      if (diferenca.inMinutes < 60) {
        return '${diferenca.inMinutes} min';
      } else {
        final horas = diferenca.inHours;
        final minutosRestantes = diferenca.inMinutes % 60;
        return '${horas}h ${minutosRestantes}min';
      }
    } catch (_) {
      return '--';
    }
  }

  bool matchesSearch(String query) {
    if (query.isEmpty) return true;

    final q = query.toLowerCase();
    return senha.toLowerCase().contains(q) ||
        clienteNome.toLowerCase().contains(q) ||
        telefone.toLowerCase().contains(q);
  }
}
