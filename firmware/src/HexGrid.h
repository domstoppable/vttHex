#pragma once

#ifndef __HEX_GRID_H
#define __HEX_GRID_H

#include "Arduino.h"
#include "LRAArray.h"

#define R1  0
#define R2  1
#define R3  2
#define R4  3

#define G1  4
#define G2  5
#define G3  6
#define G4  7

#define B1  8
#define B2  9
#define B3 10
#define B4 11

const int activationMap[][2] = {
	{R1,R1}, {R1,G1}, {G1,G1}, {G1,B1}, {B1,B1}, {B1,R1},
	{R1,G2}, {R1,B2}, {G1,B2}, {G1,R2}, {R2,B1}, {B1,G2},
	{G2,B2}, {B2,B2}, {B2,R2}, {R2,R2}, {R2,G2}, {G2,G2},
	{G2,R3}, {R3,B2}, {B2,G3}, {G3,R2}, {R2,B3}, {B3,G2},
	{R3,R3}, {R3,G3}, {G3,G3}, {G3,B3}, {B3,B3}, {B3,R3},
	{G4,R3}, {R3,B4}, {B4,G3}, {G3,R4}, {R4,B3}, {B3,G4},
	{G4,B4}, {B4,B4}, {B4,R4}, {R4,R4}, {R4,G4}, {G4,G4},
};

const float easeFunc_linear[]     = { 0.000,0.012,0.024,0.036,0.048,0.060,0.071,0.083,0.095,0.107,0.119,0.131,0.143,0.155,0.167,0.179,0.190,0.202,0.214,0.226,0.238,0.250,0.262,0.274,0.286,0.298,0.310,0.321,0.333,0.345,0.357,0.369,0.381,0.393,0.405,0.417,0.429,0.440,0.452,0.464,0.476,0.488,0.500,0.512,0.524,0.536,0.548,0.560,0.571,0.583,0.595,0.607,0.619,0.631,0.643,0.655,0.667,0.679,0.690,0.702,0.714,0.726,0.738,0.750,0.762,0.774,0.786,0.798,0.810,0.821,0.833,0.845,0.857,0.869,0.881,0.893,0.905,0.917,0.929,0.940,0.952,0.964,0.976,0.988,1.000 };
const float easeFunc_expoIn[]     = { 0.000,0.001,0.001,0.001,0.001,0.002,0.002,0.002,0.002,0.002,0.002,0.003,0.003,0.003,0.003,0.004,0.004,0.004,0.005,0.005,0.005,0.006,0.006,0.007,0.008,0.008,0.009,0.010,0.010,0.011,0.012,0.013,0.014,0.016,0.017,0.018,0.020,0.022,0.023,0.025,0.028,0.030,0.033,0.035,0.038,0.042,0.045,0.049,0.053,0.058,0.063,0.068,0.074,0.080,0.087,0.094,0.102,0.111,0.120,0.130,0.141,0.153,0.166,0.180,0.196,0.212,0.230,0.250,0.271,0.294,0.319,0.346,0.376,0.408,0.442,0.480,0.521,0.565,0.613,0.665,0.722,0.783,0.850,0.922,1.000 };
const float easeFunc_cubicIn[]    = { 0.000,0.000,0.000,0.000,0.000,0.000,0.000,0.001,0.001,0.001,0.002,0.002,0.003,0.004,0.005,0.006,0.007,0.008,0.010,0.012,0.013,0.016,0.018,0.021,0.023,0.026,0.030,0.033,0.037,0.041,0.046,0.050,0.055,0.061,0.066,0.072,0.079,0.085,0.093,0.100,0.108,0.116,0.125,0.134,0.144,0.154,0.164,0.175,0.187,0.198,0.211,0.224,0.237,0.251,0.266,0.281,0.296,0.312,0.329,0.347,0.364,0.383,0.402,0.422,0.442,0.463,0.485,0.507,0.531,0.554,0.579,0.604,0.630,0.656,0.684,0.712,0.741,0.770,0.801,0.832,0.864,0.897,0.930,0.965,1.000 };
const float easeFunc_cubicInOut[] = { 0.000,0.000,0.000,0.000,0.000,0.001,0.001,0.002,0.003,0.005,0.007,0.009,0.012,0.015,0.019,0.023,0.028,0.033,0.039,0.046,0.054,0.063,0.072,0.082,0.093,0.105,0.119,0.133,0.148,0.165,0.182,0.201,0.221,0.243,0.265,0.289,0.315,0.342,0.370,0.400,0.432,0.465,0.500,0.535,0.568,0.600,0.630,0.658,0.685,0.711,0.735,0.757,0.779,0.799,0.818,0.835,0.852,0.867,0.881,0.895,0.907,0.918,0.928,0.938,0.946,0.954,0.961,0.967,0.972,0.977,0.981,0.985,0.988,0.991,0.993,0.995,0.997,0.998,0.999,0.999,1.000,1.000,1.000,1.000,1.000 };
typedef struct {
	int driver;
	int channel;
} DriverChannelPair;

class HexGrid{
	public:
		void setup();
		void testActuator(uint8_t actuatorID);
		void setActuatorIntensity(uint8_t actuatorID, uint8_t intensity);
		void enable(uint8_t cellID, uint8_t intensity, uint8_t pitch);
		void disable(uint8_t cellID);
		void calibrate();
		void disableAll();

		LRAArray actuators;

	protected:
		uint8_t currentCell = 255;

		void _setValue(uint8_t idA, uint8_t idB, uint8_t value);

};

#endif
