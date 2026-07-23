class Farmer {
  final String id;
  final String name;
  final String district;
  final String state;
  final double totalLandAcres;
  final String? soilHealthCardId;

  const Farmer({
    required this.id,
    required this.name,
    required this.district,
    required this.state,
    this.totalLandAcres = 0.0,
    this.soilHealthCardId,
  });

  factory Farmer.fromJson(Map<String, dynamic> json) {
    return Farmer(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      district: json['district'] as String? ?? '',
      state: json['state'] as String? ?? '',
      totalLandAcres: (json['total_land_acres'] as num?)?.toDouble() ?? 0.0,
      soilHealthCardId: json['soil_health_card_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'district': district,
        'state': state,
        'total_land_acres': totalLandAcres,
        'soil_health_card_id': soilHealthCardId,
      };
}
