import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/validators/customer_name_validator.dart';
import 'package:nextpubli/features/main/home/viewmodels/create_ticket_viewmodel.dart';
import 'package:nextpubli/core/providers/session_provider.dart';
import 'package:nextpubli/core/components/ticket/check_boxes/check_box_count.dart';

class CreateTicketPopup extends StatefulWidget {
  const CreateTicketPopup({super.key});

  @override
  State<CreateTicketPopup> createState() => _CreateTicketPopupState();
}

class _CreateTicketPopupState extends State<CreateTicketPopup> {
  final TextEditingController _nomeController = TextEditingController();
  final TextEditingController _telefoneController = TextEditingController();
  int _qtdPessoas = 2;
  int _qtdCadeirantes = 0;
  int _qtdCriancas = 0;
  bool _cadeirantesHasError = false;
  bool _criancasHasError = false;
  String? _nomeError;
  bool _telefoneError = false;
  bool rememberMe = false;
  bool rememberMe2 = false;
  final nomeCheckBox1 = 'Cadeirantes';
  final nomeCheckBox2 = 'Crianças';

  void _setQtdCadeirantes(int value) {
    if (_qtdCadeirantes == value) return;
    setState(() => _qtdCadeirantes = value);
  }

  void _setCadeirantesError(bool hasError) {
    if (_cadeirantesHasError == hasError) return;
    setState(() => _cadeirantesHasError = hasError);
  }

  void _setQtdCriancas(int value) {
    if (_qtdCriancas == value) return;
    setState(() => _qtdCriancas = value);
  }

  void _setCriancasError(bool hasError) {
    if (_criancasHasError == hasError) return;
    setState(() => _criancasHasError = hasError);
  }

  Widget numCadeirantes() {
    if (rememberMe) {
      return CheckBox(
        initialCount: 1,
        nome: nomeCheckBox1,
        totalPessoas: _qtdPessoas,
        onChanged: _setQtdCadeirantes,
        onValidationChanged: _setCadeirantesError,
      );
    }
    return const SizedBox.shrink();
  }

  Widget numCriancas() {
    if (rememberMe2) {
      return CheckBox(
        initialCount: 1,
        nome: nomeCheckBox2,
        totalPessoas: _qtdPessoas,
        onChanged: _setQtdCriancas,
        onValidationChanged: _setCriancasError,
      );
    }
    return const SizedBox.shrink();
  }

  void _increment() {
    if (_qtdPessoas < 20) setState(() => _qtdPessoas++);
  }

  void _decrement() {
    if (_qtdPessoas > 1) setState(() => _qtdPessoas--);
  }

  @override
  void dispose() {
    _nomeController.dispose();
    _telefoneController.dispose();
    super.dispose();
  }

  bool get _isFormValid {
    final nomeValido =
        CustomerNameValidator.validate(_nomeController.text) == null;
    final telefoneValido = _telefoneController.text.trim().isNotEmpty;
    final qtdValida = _qtdPessoas >= 1;
    // Erros das checkboxes só bloqueiam se a checkbox estiver marcada
    final cadeirantesOk = !rememberMe || !_cadeirantesHasError;
    final criancasOk = !rememberMe2 || !_criancasHasError;

    return nomeValido &&
        telefoneValido &&
        qtdValida &&
        cadeirantesOk &&
        criancasOk;
  }

  void _handleSubmit() async {
    setState(() {
      _nomeError = CustomerNameValidator.validate(_nomeController.text);
      _telefoneError = _telefoneController.text.trim().isEmpty;
    });

    if (_nomeError != null || _telefoneError) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Por favor, preencha os campos obrigatórios'),
        ),
      );
      return;
    }

    final viewModel = context.read<CreateTicketViewModel>();
    final session = context.read<SessionProvider>();
    final clienteId = session.clienteId;

    if (clienteId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Erro: cliente não identificado. Faça login novamente.',
          ),
        ),
      );
      return;
    }

    viewModel.updateSession(session.cookie);

    final success = await viewModel.cancel(
      clienteNome: CustomerNameValidator.normalize(_nomeController.text),
      clienteId: clienteId,
      telefone: _telefoneController.text,
      qtdPessoas: _qtdPessoas,
      context: context,
      qtdCadeirantes: _qtdCadeirantes,
      qtdCriancas: _qtdCriancas,
    );

    if (success && mounted) {
      Navigator.of(context).pop(true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Senha adicionada com sucesso!')),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Erro ao adicionar senha')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: EdgeInsets.zero,
      backgroundColor: Colors.transparent,
      child: Container(
        color: const Color(0xFF03050C),
        width: double.infinity,
        height: double.infinity,
        child: SafeArea(
          child: Column(
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16.0,
                  vertical: 16.0,
                ),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(
                        Icons.arrow_back,
                        color: Colors.white,
                        size: 28,
                      ),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Para começar, precisamos de alguns dados:',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          height: 1.2,
                        ),
                      ),
                      const SizedBox(height: 32),

                      // Nome Completo
                      const Text(
                        'Nome ou apelido',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _nomeController,
                        keyboardType: TextInputType.name,
                        textCapitalization: TextCapitalization.words,
                        onChanged: (value) {
                          setState(() {
                            _nomeError = CustomerNameValidator.validate(value);
                          });
                        },
                        style: const TextStyle(
                          color: Colors.black,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Ex: João, Bia ou Ana-Maria',
                          errorText: _nomeError,
                          errorMaxLines: 3,
                          hintStyle: TextStyle(
                            color: Colors.black.withValues(alpha: 0.5),
                          ),
                          filled: true,
                          fillColor: const Color(0xFFE8F0FE),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 16,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide.none,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // WhatsApp
                      const Text(
                        'WhatsApp (COM DDD)',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _telefoneController,
                        keyboardType: TextInputType.phone,
                        onChanged: (value) {
                          setState(() => _telefoneError = false);
                        },
                        inputFormatters: [TelefoneInputFormatter()],
                        style: const TextStyle(
                          color: Colors.black,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Ex: (31) 99665-8209',
                          errorText: _telefoneError
                              ? 'O WhatsApp é obrigatório'
                              : null,
                          hintStyle: TextStyle(
                            color: Colors.black.withValues(alpha: 0.5),
                          ),
                          filled: true,
                          fillColor: const Color(0xFFE8F0FE),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 16,
                          ),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide.none,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Usaremos este número para avisar quando sua mesa estiver pronta.',
                        style: TextStyle(
                          color: Color(0xFF8A94A6),
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 32),

                      // Quantidade de Pessoas
                      const Text(
                        'Quantidade de Pessoas',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        height: 60,
                        decoration: BoxDecoration(
                          color: const Color(0xFF131722),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFF2A2F45)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12.0,
                              ),
                              child: InkWell(
                                onTap: _decrement,
                                borderRadius: BorderRadius.circular(20),
                                child: Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: const Color(
                                        0xFFFF20BD,
                                      ).withValues(alpha: 0.5),
                                    ),
                                  ),
                                  child: const Icon(
                                    Icons.remove,
                                    color: Color(0xFFFF20BD),
                                  ),
                                ),
                              ),
                            ),
                            Text(
                              '$_qtdPessoas',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12.0,
                              ),
                              child: InkWell(
                                onTap: _increment,
                                borderRadius: BorderRadius.circular(20),
                                child: Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: const Color(
                                        0xFF00A3FF,
                                      ).withValues(alpha: 0.5),
                                    ),
                                  ),
                                  child: const Icon(
                                    Icons.add,
                                    color: Color(0xFF00A3FF),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Mínimo 1 pessoa • Máximo 20 pessoas',
                        style: TextStyle(
                          color: Color(0xFF8A94A6),
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 40),
                      Row(
                        children: [
                          Theme(
                            data: Theme.of(context).copyWith(
                              unselectedWidgetColor: const Color(0xFFF2F4F7),
                            ),
                            child: Checkbox(
                              value: rememberMe,
                              onChanged: (value) {
                                setState(() {
                                  rememberMe = value ?? false;
                                  if (!rememberMe) {
                                    _qtdCadeirantes = 0;
                                    _cadeirantesHasError = false;
                                  }
                                });
                              },
                              activeColor: const Color(0xFFFF20BD),
                              checkColor: Colors.white,
                              side: const BorderSide(color: Color(0xFFF2F4F7)),
                            ),
                          ),
                          const Expanded(
                            child: Text(
                              'Desejo informar a quantidade de cadeirantes',
                              style: TextStyle(
                                color: Color(0xFFF2F4F7),
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                      numCadeirantes(),

                      Row(
                        children: [
                          Theme(
                            data: Theme.of(context).copyWith(
                              unselectedWidgetColor: const Color(0xFFF2F4F7),
                            ),
                            child: Checkbox(
                              value: rememberMe2,
                              onChanged: (value) {
                                setState(() {
                                  rememberMe2 = value ?? false;
                                  if (!rememberMe2) {
                                    _qtdCriancas = 0;
                                    _criancasHasError = false;
                                  }
                                });
                              },
                              activeColor: const Color(0xFFFF20BD),
                              checkColor: Colors.white,
                              side: const BorderSide(color: Color(0xFFF2F4F7)),
                            ),
                          ),
                          const Expanded(
                            child: Text(
                              'Desejo informar a quantidade de crianças até 2 anos',
                              style: TextStyle(
                                color: Color(0xFFF2F4F7),
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                      numCriancas(),
                      // BotÃ£o Entrar na Fila
                      Consumer<CreateTicketViewModel>(
                        builder: (context, viewModel, child) {
                          final isButtonEnabled =
                              _isFormValid && !viewModel.isLoading;

                          return GestureDetector(
                            onTap: isButtonEnabled ? _handleSubmit : null,
                            child: Opacity(
                              opacity: isButtonEnabled ? 1.0 : 0.6,
                              child: Container(
                                height: 56,
                                decoration: BoxDecoration(
                                  color: isButtonEnabled
                                      ? null
                                      : const Color(0xFF6C757D),
                                  gradient: isButtonEnabled
                                      ? const LinearGradient(
                                          colors: [
                                            Color(0xFFFF20BD),
                                            Color(0xFF00A3FF),
                                          ],
                                          begin: Alignment.centerLeft,
                                          end: Alignment.centerRight,
                                        )
                                      : null,
                                  borderRadius: BorderRadius.circular(16),
                                  boxShadow: isButtonEnabled
                                      ? [
                                          BoxShadow(
                                            color: const Color(
                                              0xFFFF20BD,
                                            ).withAlpha(128),
                                            blurRadius: 12,
                                            offset: const Offset(0, 4),
                                          ),
                                        ]
                                      : null,
                                ),
                                child: Center(
                                  child: viewModel.isLoading
                                      ? const CircularProgressIndicator(
                                          color: Colors.white,
                                        )
                                      : const Text(
                                          'ENTRAR NA FILA',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 40),

                      // Logo
                      Center(
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 24.0),
                          child: Image.asset(
                            'assets/images/logo_login.png',
                            height: 240,
                            width: 240,
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class TelefoneInputFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    var text = newValue.text.replaceAll(RegExp(r'[^\d]'), '');

    if (text.length > 11) {
      text = text.substring(0, 11);
    }

    var formatted = '';
    if (text.isNotEmpty) {
      formatted = '(';
      if (text.length > 2) {
        formatted += '${text.substring(0, 2)}) ';
        if (text.length > 7) {
          if (text.length == 11) {
            formatted += '${text.substring(2, 7)}-${text.substring(7, 11)}';
          } else {
            formatted +=
                '${text.substring(2, 6)}-${text.substring(6, text.length)}';
          }
        } else {
          formatted += text.substring(2, text.length);
        }
      } else {
        formatted += text;
      }
    }

    // Se o usuário estiver apagando caracteres e a nova string for menor,
    // tentamos manter a posição original do cursor ou ir para o final.
    int selectionIndex = formatted.length;
    if (newValue.selection.end < newValue.text.length && oldValue.text.length > newValue.text.length) {
       // simplificação: ir para o final sempre é aceitável para máscaras simples, 
       // mas se for apagando no meio pode pular pro final. Para resolver isso perfeitamente,
       // exigiria uma lógica complexa de mapeamento de cursor.
    }

    return TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
  }
}

// ainda desenvolvendo nao fiz nenhuma mudanca
