class Brand {
  final int id;
  final String name;
  final String nameEn;
  final String logo;
  final String country;

  Brand({required this.id, required this.name, this.nameEn = '', this.logo = '', this.country = ''});

  factory Brand.fromJson(Map<String, dynamic> json) => Brand(
    id: json['id'],
    name: json['name'],
    nameEn: json['name_en'] ?? '',
    logo: json['logo'] ?? '',
    country: json['country'] ?? '',
  );
}

class ForkliftSeries {
  final int id;
  final int brandId;
  final String name;
  final String description;

  ForkliftSeries({required this.id, required this.brandId, required this.name, this.description = ''});

  factory ForkliftSeries.fromJson(Map<String, dynamic> json) => ForkliftSeries(
    id: json['id'],
    brandId: json['brand_id'],
    name: json['name'],
    description: json['description'] ?? '',
  );
}

class ForkliftModel {
  final int id;
  final int seriesId;
  final String name;
  final double? loadCapacityKg;
  final double? loadCapacityTon;
  final double? liftHeightMm;
  final double? weightKg;
  final double? lengthMm;
  final double? widthMm;
  final double? heightMm;
  final String fuelType;
  final String imageUrl;

  ForkliftModel({
    required this.id,
    required this.seriesId,
    required this.name,
    this.loadCapacityKg,
    this.loadCapacityTon,
    this.liftHeightMm,
    this.weightKg,
    this.lengthMm,
    this.widthMm,
    this.heightMm,
    this.fuelType = '',
    this.imageUrl = '',
  });

  factory ForkliftModel.fromJson(Map<String, dynamic> json) => ForkliftModel(
    id: json['id'],
    seriesId: json['series_id'],
    name: json['name'],
    loadCapacityKg: json['load_capacity_kg']?.toDouble(),
    loadCapacityTon: json['load_capacity_ton']?.toDouble(),
    liftHeightMm: json['lift_height_mm']?.toDouble(),
    weightKg: json['weight_kg']?.toDouble(),
    lengthMm: json['length_mm']?.toDouble(),
    widthMm: json['width_mm']?.toDouble(),
    heightMm: json['height_mm']?.toDouble(),
    fuelType: json['fuel_type'] ?? '',
    imageUrl: json['image_url'] ?? '',
  );
}

class EngineBrand {
  final int id;
  final String name;
  final String nameEn;
  final String country;

  EngineBrand({required this.id, required this.name, this.nameEn = '', this.country = ''});

  factory EngineBrand.fromJson(Map<String, dynamic> json) => EngineBrand(
    id: json['id'],
    name: json['name'],
    nameEn: json['name_en'] ?? '',
    country: json['country'] ?? '',
  );
}

class EngineModelItem {
  final int id;
  final int brandId;
  final String modelName;
  final String displacement;
  final double? powerKw;
  final double? powerHp;
  final int? cylinders;
  final String fuelType;

  EngineModelItem({
    required this.id,
    required this.brandId,
    required this.modelName,
    this.displacement = '',
    this.powerKw,
    this.powerHp,
    this.cylinders,
    this.fuelType = '',
  });

  factory EngineModelItem.fromJson(Map<String, dynamic> json) => EngineModelItem(
    id: json['id'],
    brandId: json['brand_id'],
    modelName: json['model_name'],
    displacement: json['displacement'] ?? '',
    powerKw: json['power_kw']?.toDouble(),
    powerHp: json['power_hp']?.toDouble(),
    cylinders: json['cylinders'],
    fuelType: json['fuel_type'] ?? '',
  );
}

class PartItem {
  final int id;
  final String oemNumber;
  final String name;
  final String category;
  final String specifications;
  final String brand;
  final double? priceReference;

  PartItem({
    required this.id,
    required this.oemNumber,
    required this.name,
    this.category = '',
    this.specifications = '',
    this.brand = '',
    this.priceReference,
  });

  factory PartItem.fromJson(Map<String, dynamic> json) => PartItem(
    id: json['id'],
    oemNumber: json['oem_number'],
    name: json['name'],
    category: json['category'] ?? '',
    specifications: json['specifications'] ?? '',
    brand: json['brand'] ?? '',
    priceReference: json['price_reference']?.toDouble(),
  );
}

class DiagramItem {
  final int id;
  final int? modelId;
  final String diagramType;
  final String systemType;
  final String title;
  final String imageUrl;

  DiagramItem({
    required this.id,
    this.modelId,
    required this.diagramType,
    this.systemType = '',
    this.title = '',
    required this.imageUrl,
  });

  factory DiagramItem.fromJson(Map<String, dynamic> json) => DiagramItem(
    id: json['id'],
    modelId: json['model_id'],
    diagramType: json['diagram_type'],
    systemType: json['system_type'] ?? '',
    title: json['title'] ?? '',
    imageUrl: json['image_url'],
  );
}

class UserForkliftItem {
  final int id;
  final int userId;
  final int? forkliftModelId;
  final String customerName;
  final String serialNumber;
  final String engineModel;
  final double currentHours;
  final String modelName;
  final String brandName;

  UserForkliftItem({
    required this.id,
    required this.userId,
    this.forkliftModelId,
    this.customerName = '',
    this.serialNumber = '',
    this.engineModel = '',
    this.currentHours = 0,
    this.modelName = '',
    this.brandName = '',
  });

  factory UserForkliftItem.fromJson(Map<String, dynamic> json) => UserForkliftItem(
    id: json['id'],
    userId: json['user_id'],
    forkliftModelId: json['forklift_model_id'],
    customerName: json['customer_name'] ?? '',
    serialNumber: json['serial_number'] ?? '',
    engineModel: json['engine_model'] ?? '',
    currentHours: (json['current_hours'] ?? 0).toDouble(),
    modelName: json['model_name'] ?? '',
    brandName: json['brand_name'] ?? '',
  );
}
