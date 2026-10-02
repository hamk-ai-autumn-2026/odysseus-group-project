def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total


class PriceSummary:
    def __init__(self, values):
        self.values = values

    def total(self):
        return calculate_total(self.values)


if __name__ == "__main__":
    result = PriceSummary([10, 20, 30]).total()
    print(f"Total: {result}")
