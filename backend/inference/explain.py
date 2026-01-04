
def explain_feature(name, value, delta, reason):
    if value is None or delta == 0:
        return None
    sign = "+" if delta > 0 else ""
    return f"{reason} ({sign}{delta:.1f})"


def generate_explanations(contributions):
    explanations = []
    for item in contributions:
        if item:
            explanations.append(item)
    return explanations
