import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;

/// Nom affiché dans la page de licences pour le crédit du projet Python
/// d'origine (Orange-Livebox-TV-UHD-4K-python-controller, Léo d'Antoni /
/// DalFanajin).
const originalProjectLicenseName =
    "Orange-Livebox-TV-UHD-4K-python-controller (projet Python d'origine)";

/// Enregistre le crédit du projet Python d'origine dans la page de licences
/// native de Flutter (LicenseRegistry), aux côtés des licences des
/// dépendances pub collectées automatiquement au build.
///
/// Le texte vient d'un instantané figé (assets/licenses/), volontairement
/// indépendant du LICENSE de ce fork : ce dernier peut être modifié à
/// l'avenir, alors que le crédit dû à l'auteur d'origine doit rester fixe.
void registerOriginalProjectLicense() {
  LicenseRegistry.addLicense(() async* {
    final text = await rootBundle.loadString(
      'assets/licenses/original_project_license.txt',
    );
    yield LicenseEntryWithLineBreaks([originalProjectLicenseName], text);
  });
}
