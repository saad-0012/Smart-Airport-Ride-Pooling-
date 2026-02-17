def calculate_dynamic_price(base_price: float, demand_factor: float, detour_km: float) -> float:
    # Dynamic Pricing Formula: Base + (Demand * Multiplier) - (Shared Discount)
    return round(base_price * demand_factor + (detour_km * 5), 2)