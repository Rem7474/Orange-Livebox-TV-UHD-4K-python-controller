import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:android_app/licenses.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('registerOriginalProjectLicense enregistre une entrée avec le crédit '
      "du projet Python d'origine", () async {
    LicenseRegistry.reset();
    registerOriginalProjectLicense();

    final entries = await LicenseRegistry.licenses.toList();
    final entry = entries.singleWhere(
      (e) => e.packages.contains(originalProjectLicenseName),
    );

    final text = entry.paragraphs.map((p) => p.text).join('\n');
    expect(text, contains('MIT License'));
    expect(text, contains("Léo d'Antoni"));
  });
}
