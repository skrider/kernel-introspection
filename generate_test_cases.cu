#include <iostream>
#include <stdlib.h> 
#include "cute/layout.hpp"

using namespace cute;

static constexpr int MAX_DIM = 3;
static constexpr int MAX_DEPTH = 3;
static constexpr int MAX_SIZE = 10;

#define RAND_MODE (rand() % MAX_SIZE)

template<typename A, typename B>
class LayoutTestCase {
    Layout<A, B> layout;
public:
    template<typename Shape, typename Stride>
    LayoutTestCase(Layout<Shape, Stride> layout) : layout(layout) {}
    
    LayoutTestCase(int rank, int depth) {
        // base case
        switch (rank) {
            case 1:
            layout = make_layout(make_shape(RAND_MODE));
            break;
            case 2:
            layout = make_layout(make_shape(RAND_MODE, RAND_MODE));
            break;
            case 3: 
            layout = make_layout(make_shape(RAND_MODE, RAND_MODE, RAND_MODE));
            break;
        }
    }

    void print() {
        print(layout);
    }
};

void generate_layout_test_cases(int n) {
    for (int rank = 0; rank <= MAX_DIM; rank++) {
        for (int i = 0; i < n; i++) {
            auto test_case = LayoutTestCase(rank, 1);
            test_case.print();
        }
    }
}

int main() {
    srand(0);
    generate_layout_test_cases(10);
    return 0;
}
