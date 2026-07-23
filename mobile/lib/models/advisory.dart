class Advisory {
  final String id;
  final String advisoryType;
  final String titleEn;
  final String? titleHi;
  final String? titleTa;
  final String bodyEn;
  final String? bodyHi;
  final String? bodyTa;
  final String? voiceUrlEn;
  final String? voiceUrlHi;
  final String? voiceUrlTa;
  final String priority;
  final String isRead;
  final String createdAt;

  const Advisory({
    required this.id,
    required this.advisoryType,
    required this.titleEn,
    required this.bodyEn,
    required this.priority,
    required this.isRead,
    required this.createdAt,
    this.titleHi,
    this.titleTa,
    this.bodyHi,
    this.bodyTa,
    this.voiceUrlEn,
    this.voiceUrlHi,
    this.voiceUrlTa,
  });

  String getTitle(String lang) {
    if (lang == 'hi' && titleHi != null) return titleHi!;
    if (lang == 'ta' && titleTa != null) return titleTa!;
    return titleEn;
  }

  String getBody(String lang) {
    if (lang == 'hi' && bodyHi != null) return bodyHi!;
    if (lang == 'ta' && bodyTa != null) return bodyTa!;
    return bodyEn;
  }

  factory Advisory.fromJson(Map<String, dynamic> json) {
    return Advisory(
      id: json['id']?.toString() ?? '',
      advisoryType: json['advisory_type']?.toString() ?? 'general',
      titleEn: json['title_en']?.toString() ?? '',
      titleHi: json['title_hi']?.toString(),
      titleTa: json['title_ta']?.toString(),
      bodyEn: json['body_en']?.toString() ?? '',
      bodyHi: json['body_hi']?.toString(),
      bodyTa: json['body_ta']?.toString(),
      voiceUrlEn: json['voice_url_en']?.toString(),
      voiceUrlHi: json['voice_url_hi']?.toString(),
      voiceUrlTa: json['voice_url_ta']?.toString(),
      priority: json['priority']?.toString() ?? 'normal',
      isRead: json['is_read']?.toString() ?? 'false',
      createdAt: json['created_at']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'advisory_type': advisoryType,
    'title_en': titleEn,
    'body_en': bodyEn,
    'priority': priority,
    'is_read': isRead,
    'created_at': createdAt,
  };
}
