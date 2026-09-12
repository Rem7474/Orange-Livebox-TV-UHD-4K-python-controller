class Channel {
  final String name;
  final int? number;
  final String epgId;
  bool isFavorite;

  Channel({
    required this.name,
    this.number,
    required this.epgId,
    this.isFavorite = false,
  });

  String get displayName => number != null ? '$number - $name' : name;

  Map<String, dynamic> toJson() => {
    'name': name,
    'number': number,
    'epgId': epgId,
    'isFavorite': isFavorite,
  };

  factory Channel.fromJson(Map<String, dynamic> json) => Channel(
    name: json['name'] as String,
    number: json['number'] as int?,
    epgId: json['epgId'] as String,
    isFavorite: json['isFavorite'] as bool? ?? false,
  );
}
