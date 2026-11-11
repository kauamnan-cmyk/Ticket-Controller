import 'package:flutter_test/flutter_test.dart';
import 'package:nextpubli/core/validators/customer_name_validator.dart';

void main() {
  test('accepts short names, nicknames, accents and name separators', () {
    for (final name in [
      'Li',
      'Bia',
      'Zé',
      'João',
      'Ana Maria',
      'Ana-Maria',
      "D'Ávila",
      'O’Connor',
      'Jose\u0301',
      '张伟',
      'Jacinto',
      'Scunthorpe',
      '  Maria   da Silva  ',
    ]) {
      expect(CustomerNameValidator.validate(name), isNull, reason: name);
    }
  });

  test('rejects empty names, numbers, symbols and malformed separators', () {
    for (final name in [
      '',
      '   ',
      '123',
      'João123',
      'Maria @',
      'Bia😀',
      '<script>',
      '-Ana',
      'Ana-',
      "'Bia",
      'Ana--Maria',
      "Ana ' Maria",
      '\u0301Ana',
      'Ana\nMaria',
      'Ana\tMaria',
      'Ana\u0000',
      'Jo\u200Bao',
    ]) {
      expect(CustomerNameValidator.validate(name), isNotNull, reason: name);
    }
  });

  test('rejects explicit blocked words regardless of case and accents', () {
    for (final name in [
      'CARALHO',
      'Porra',
      'Cuzão',
      'Cuza\u0303o',
      'João Merda',
      'Foda-se',
      'Arrombada',
      "Ana'Puta",
      'Ana’Puta',
    ]) {
      expect(
        CustomerNameValidator.validate(name),
        contains('termo não permitido'),
        reason: name,
      );
    }
  });

  test('limits name length without truncating the submitted name', () {
    expect(CustomerNameValidator.validate('a' * 100), isNull);
    expect(CustomerNameValidator.validate('a' * 101), isNotNull);
  });

  test('normalizes spaces while preserving spelling and capitalization', () {
    expect(
      CustomerNameValidator.normalize('  João   D’Ávila  '),
      'João D’Ávila',
    );
  });
}
