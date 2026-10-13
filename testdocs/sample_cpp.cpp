#include <iostream>
#include <vector>

int calculate_total(const std::vector<int>& values) {
    int total = 0;
    for (int value : values) {
        total += value;
    }
    return total;
}

int main() {
    std::vector<int> values = {10, 20, 30};
    int total = calculate_total(values);
    std::cout << "Total: " << total << std::endl;
    return 0;
}
