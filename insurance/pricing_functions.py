def calculate_premium_for_mtpl(policy_duration: int, driver_experience: int, make: str) -> float:
    base_price = 100
    risk_factor = 1

    if make == "BMW":
        risk_factor *= 1.5

    if driver_experience == 0:
        risk_factor *= 3
    elif driver_experience == 1:
        risk_factor *= 2
    elif driver_experience == 2:
        risk_factor *= 1.5
    elif driver_experience == 3:
        risk_factor *= 1.25
    elif driver_experience == 4:
        risk_factor *= 1.1
    elif driver_experience == 5:
        risk_factor *= 1
    elif driver_experience <= 10:
        risk_factor *= 0.9
    elif driver_experience <= 15:
        risk_factor *= 0.8
    elif driver_experience <= 20:
        risk_factor *= 0.75
    else:
        risk_factor *= 0.7

    ins_premium = base_price * risk_factor * policy_duration / 365.25
    return round(ins_premium, 2)


def calculate_premium_for_casco(policy_duration: int, driver_experience: int, make: str, car_alarm: bool) -> float:
    base_price = 1000
    risk_factor = 1

    if make == "BMW":
        risk_factor *= 1.5

    if driver_experience == 0:
        risk_factor *= 3
    elif driver_experience == 1:
        risk_factor *= 2
    elif driver_experience == 2:
        risk_factor *= 1.5
    elif driver_experience == 3:
        risk_factor *= 1.25
    elif driver_experience == 4:
        risk_factor *= 1.1
    elif driver_experience == 5:
        risk_factor *= 1
    elif driver_experience <= 10:
        risk_factor *= 0.9
    elif driver_experience <= 15:
        risk_factor *= 0.8
    elif driver_experience <= 20:
        risk_factor *= 0.75
    else:
        risk_factor *= 0.7

    if car_alarm:
        risk_factor *= 0.9

    ins_premium = base_price * risk_factor * policy_duration / 365.25
    return round(ins_premium, 2)


def calculate_premium_for_property(policy_duration: int, building_purpose: str, construction: str, selected_risks: list) -> float:
    base_price = 100
    risk_factor = 1
    factor_of_prop_risks = 1

    if construction == "brick/concrete":
        risk_factor *= 1
    elif construction == "wood":
        risk_factor *= 2
    elif construction == "logs":
        risk_factor *= 1.8
    elif construction == "mixed":
        risk_factor *= 1.5

    if building_purpose == "apartment":
        risk_factor *= 1.5
    elif building_purpose == "garden house":
        risk_factor *= 1.7
    elif building_purpose == "summerhouse":
        risk_factor *= 1.7
    elif building_purpose == "house of other purpose":
        risk_factor *= 1.4
    else:
        risk_factor *= 1

    for _ in selected_risks:  # Galima ir su len.
        factor_of_prop_risks += 0.1

    ins_premium = base_price * risk_factor * factor_of_prop_risks * policy_duration / 365.25
    return round(ins_premium, 2)
