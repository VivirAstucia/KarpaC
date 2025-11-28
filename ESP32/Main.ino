#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

const int side1 = 8, side2 = 4;

int LED = 23;
int count = side1*side1*4;

const int H_IN[] = {15, 2, 4, 5};
const int H_OUT[] = {13, 12, 14, 27, 26, 25, 33, 32};


int hall_grid[side2][side1] = {
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0},
    {0, 0, 0, 0, 0, 0, 0, 0}
};


int square[side2][side1][4] = {
    {{0, 1, 30, 31}, {2, 3, 28, 29}, {4, 5, 26, 27}, {6, 7, 24, 25}, {8, 9, 22, 23}, {10, 11, 20, 21}, {12, 13, 18, 19}, {14, 15, 16, 17}},
    // {{16, 17, 30, 31}, {18, 19, 28, 29}, {20, 21, 26, 27}, {22, 23, 24, 25}},
    {{32, 33, 62, 63}, {34, 35, 60, 61}, {36, 37, 58, 59}, {38, 39, 56, 57}, {40, 41, 54, 55}, {42, 43, 52, 53}, {44, 45, 50, 51}, {46, 47, 48, 49}},
    // {{32, 33, 46, 47}, {34, 35, 44, 45}, {36, 37, 42, 43}, {38, 39, 40, 41}},
    {{64, 65, 94, 95}, {66, 67, 92, 93}, {68, 69, 90, 91}, {70, 71, 88, 89}, {72, 73, 86, 87}, {74, 75, 84, 85}, {76, 77, 82, 83}, {78, 79, 80, 81}},
    // {{48, 49, 62, 63}, {50, 51, 60, 61}, {52, 53, 58, 59}, {54, 55, 56, 57}}
    {{96, 97, 126, 127}, {98, 99, 124, 125}, {100, 101, 122, 123}, {102, 103, 120, 121}, {104, 105, 118, 119}, {106, 107, 116, 117}, {108, 109, 114, 115}, {110, 111, 112, 113}}
};


Adafruit_NeoPixel strip(count, LED, NEO_GRB + NEO_KHZ800);
auto yellow = strip.Color(255, 150, 0);
auto red = strip.Color(255, 0, 0);
auto blue = strip.Color(0, 0, 255);
auto green = strip.Color(0, 255, 0);
auto pink = strip.Color(255, 0, 255);
auto purple = strip.Color(75, 0, 130);
auto orange = strip.Color(255, 165, 0);



void read_hall_sensors() {
    for (int i = 0; i < side2; i++) {
        digitalWrite(H_IN[i], HIGH);
        delay(5);
        for (int j = 0; j < side1; j++) hall_grid[i][j] = digitalRead(H_OUT[j]);
        digitalWrite(H_IN[i], LOW);
    }

    Serial.println("Hall Sensor Grid: ");
    for (int i = 0; i < side2; i++) {
        for (int j = 0; j < side1; j++) {
            Serial.print(hall_grid[i][j]); Serial.print(" ");
        }
        Serial.println(); Serial.println();
    }
}

void update_leds() {
    strip.clear();
    for (int i = 0; i < side2; i++) {
        for (int j = 0; j < side1; j++) {
            auto set_color = hall_grid[i][j] ? red : blue;
            for (int led_idx : square[i][j]) strip.setPixelColor(led_idx, set_color);
        }
    }
    strip.show();
}

void led_test() {
    for (auto& square_row : square) {
        for (auto& leds : square_row) {
            strip.clear();
            for (int led_index : leds) {
                for (auto color: {red, green, blue, yellow}) {
                    strip.setPixelColor(led_index, color);
                    strip.show();
                    delay(500);
                }
            }
        }
    }
}

void led_test1(){
    // light up all leds changing color - R,G,B,Y,O,P,W,off, with 500 ms interval
    for (auto color : {red, green, blue, yellow, orange, pink, purple}) {
        strip.fill(color);
        strip.show();
        delay(500);
    }
}

void led_test2(){
    int x = 2;
    int y = 3;
    digitalWrite(H_IN[y], HIGH);
    int val = digitalRead(H_OUT[x]);
    if (val == 0) {
    // for (auto color : {red, green, blue, yellow, orange, pink, purple}) {
        for (int led_idx : square[y][x]) {
            strip.setPixelColor(led_idx, red);
        }
        strip.show();
    }
    else {
        for (int led_idx : square[y][x]) {
            strip.setPixelColor(led_idx, blue);
        }
        strip.show();
    }

    // }
}

void setup() {
    Serial.begin(115200);
    Serial.println("Test");

    strip.begin();
    strip.show();

    for (int pin : H_IN) {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW);
    }

    for (int pin : H_OUT) pinMode(pin, INPUT_PULLUP);
    // strip.setBrightness(70);
}

void loop() {
    read_hall_sensors();
    update_leds();
    delay(10);
    // led_test1();
    // delay(50);
}