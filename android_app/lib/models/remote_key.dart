enum RemoteKey {
  power('POWER', '116', 'Alimentation'),
  mute('MUTE', '113', 'Muet'),
  volUp('VOL+', '115', 'Volume +'),
  volDown('VOL-', '114', 'Volume -'),
  chUp('CH+', '402', 'Chaîne +'),
  chDown('CH-', '403', 'Chaîne -'),
  up('UP', '103', 'Haut'),
  down('DOWN', '108', 'Bas'),
  left('LEFT', '105', 'Gauche'),
  right('RIGHT', '106', 'Droite'),
  ok('OK', '352', 'OK'),
  menu('MENU', '139', 'Menu Accueil'),
  back('BACK', '158', 'Retour'),
  guide('PROG', '365', 'Guide TV'),
  vod('VOD', '393', 'VOD'),
  rec('REC', '167', 'Enregistrer'),
  playPause('PLAY/PAUSE', '164', 'Lecture / Pause'),
  fbwd('FBWD', '168', 'Retour Rapide'),
  ffwd('FFWD', '159', 'Avance Rapide'),
  direct('DIRECT', '166', 'Direct'),
  num0('0', '512', '0'),
  num1('1', '513', '1'),
  num2('2', '514', '2'),
  num3('3', '515', '3'),
  num4('4', '516', '4'),
  num5('5', '517', '5'),
  num6('6', '518', '6'),
  num7('7', '519', '7'),
  num8('8', '520', '8'),
  num9('9', '521', '9');

  final String keyName;
  final String keyCode;
  final String label;

  const RemoteKey(this.keyName, this.keyCode, this.label);
}
