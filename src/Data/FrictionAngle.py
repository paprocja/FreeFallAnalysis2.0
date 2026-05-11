from abc import ABC, abstractmethod
import Data.RelativeDensity
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from Data.Peak import Peak

class FrictionAngleCalculation(ABC):
    @abstractmethod
    def calc_friction_angle(self, relative_density, depth):
        pass

class AlbatalFrictionAngle(FrictionAngleCalculation):

    # Constants from document
    __A = 34
    __B = 10
    __C = 3
    __D = 2

    # No idea if this is right, need to verify
    __atomspheric_pressure = 101.325  # kPa

    def __init__(self, peak: Peak = None):
        self.peak = peak
    
    def calc_friction_angle(self, relative_density, depth):
        if self.peak is None:
            raise ValueError("Peak must be defined")

        relative_density = relative_density * .01 # convert to decimal

        A = self.__A
        B = self.__B
        C = self.__C
        D = self.__D
        atmospheric_pressure = self.__atomspheric_pressure

        return (A + (B * relative_density) - (C + (D * relative_density)) * math.log10((depth * (18.1 - 9.81)) / atmospheric_pressure))
    # 46.3 for albatal
    # 46.5 for white
    
class DurgunogluMitchellFrictionAngle(FrictionAngleCalculation):

    def __init__(self, peak: Peak):
        self.peak = peak

    def calc_friction_angle(self, relative_density, depth):
        if self.peak is None:
            raise ValueError("Peak must be defined")

        # Helper functions to mimic MATLAB's degree-based trig
        def tand(x): return np.tan(np.deg2rad(x))
        def sind(x): return np.sin(np.deg2rad(x))
        def cosd(x): return np.cos(np.deg2rad(x))

        alpha = 30  # constant
        DeltaPhi = 0.5  # constant
        phi = np.arange(25, 51)  # range of angles to check
        # phi = 50
        psi = 90 - alpha
        gamma = np.linspace(0, 100, 1000)  # range of gammas to check for (probably a more efficient way out there)

        D = max(self.peak.depth) # grab max depth of penetrometer from peak
        print(f"Using D = {D} for friction angle calculation")

        B = 0.0875  # constant

        one = np.zeros(len(phi))
        two = np.zeros(len(phi))
        three = np.zeros(len(phi))
        four = np.zeros(len(phi))
        five = np.zeros(len(phi))
        six = np.zeros(len(phi))
        seven = np.zeros(len(phi))
        eight = np.zeros(len(phi))
        Ngq = np.zeros(len(phi))

        m = D / B
        for c in range(len(phi)):
            delta = phi[c] * DeltaPhi

            # solving for gamma
            eqn = np.zeros(len(gamma))
            for a in range(len(gamma)):
                eqn[a] = tand(delta) * (1 + sind(phi[c]) * sind(2 * gamma[a] - phi[c])) - sind(phi[c]) * cosd(2 * gamma[a] - phi[c])

            gammaVal = gamma[np.argmin(np.abs(eqn))]

            beta = phi[c]  # initializing the beta value
            thetaNaught = 180 - (psi + gammaVal) + beta

            # next step checks in m' is less than m.
            if 0.5 * sind(beta) * cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(thetaNaught) * tand(phi[c])) / (cosd(psi) * cosd(phi[c])) < m:
                mPrime = 0.5 * sind(beta) * cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(thetaNaught) * tand(phi[c])) / (cosd(psi) * cosd(phi[c]))
            # process to find beta if m'>m
            else:
                eta = 180 - (gammaVal + psi)
                betaNaught = np.arctan(2 * m * cosd(phi[c]) * cosd(psi) / (cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(eta) * tand(phi[c]))))
                betaNaught = np.rad2deg(betaNaught)
                thetaNaught = 180 - (psi + gammaVal) + betaNaught

                betaNew = np.arcsin(2 * m * cosd(phi[c]) * cosd(psi) / (cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(thetaNaught) * tand(phi[c]))))
                betaNew = np.rad2deg(betaNew)

                while abs(betaNew - betaNaught) >= 0.1:
                    betaNaught = (betaNaught + betaNew) / 2
                    thetaNaught = 180 - (psi + gammaVal) + betaNaught

                    betaNew = np.arcsin(2 * m * cosd(phi[c]) * cosd(psi) / (cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(thetaNaught) * tand(phi[c]))))
                    betaNew = np.rad2deg(betaNew)

                beta = betaNew
                thetaNaught = 180 - (psi + gammaVal) + beta
                mPrime = 0.5 * sind(beta) * cosd(gammaVal - phi[c]) * np.exp(np.deg2rad(thetaNaught) * tand(phi[c])) / (cosd(psi) * cosd(phi[c]))

            Itheta = (1 / (1 + 9 * (tand(phi[c]) ** 2))) \
                * (3 * tand(phi[c])
                * (np.exp(3 * np.deg2rad(thetaNaught) * tand(phi[c]))
                    * cosd(beta)
                    - cosd(thetaNaught - beta)
                    ) + (np.exp(3 * np.deg2rad(thetaNaught) * tand(phi[c]))
                        * sind(beta)
                        + sind(thetaNaught - beta)))

            K = 1 - sind(phi[c])

            one[c] = cosd(psi - delta) / cosd(delta)
            two[c] = (1 + sind(phi[c]) * sind(2 * gammaVal - phi[c])) / (cosd(phi[c]) * cosd(gammaVal - phi[c]))
            three[c] = 0.25 * Itheta * (cosd(gammaVal - phi[c]) ** 2) / ((cosd(psi) ** 2) * (cosd(phi[c]) ** 2))
            four[c] = 0.75 * cosd(gammaVal - phi[c]) / (cosd(psi) * cosd(phi[c]))
            five[c] = (cosd(beta) ** 2) * np.exp(2 * np.deg2rad(thetaNaught) * tand(phi[c])) * (m - (2 / 3) * mPrime)
            six[c] = K * cosd(psi) * cosd(phi[c]) * (m ** 3) / cosd(gammaVal - phi[c])
            seven[c] = K * cosd(psi) * cosd(phi[c]) * ((m - mPrime) ** 2) * (m + 2 * mPrime) / cosd(gammaVal - phi[c])
            eight[c] = tand(psi) / 4

            Ngq[c] = one[c] * two[c] * (three[c] + four[c] * five[c] + six[c] - seven[c]) - eight[c]
        
        Xigq = (1.5 / (1 + (1.5 / (0.6 + (np.tan(np.radians(phi)))**6)))) + 0.6
        yAxisParameter = np.array(Ngq)*Xigq
        q_c_eq = max(self.peak.corrected_qsbc_lines[0].ave)
        gS = 18.1-9.81
        Locator = q_c_eq/(gS*B)

        print(f"q_c_eq = {q_c_eq}")

        # the code below implements the python equivalent of the polyxpoly line in the given matlab code
        # unfortunately, we needed a new library for this, which is kind of stinky
        # could have done it using numpy (according to gemini), but this made so much more sense. The numpy code to do this actually hurt my brain, and only
        # worked in this specific case becasue we have a constant as one of the lines, so we could subtract the constant from yAxisParameter and do some weird 
        # root finding with interpolation to get the proper intersection point.

        curve_coords = np.column_stack((phi, yAxisParameter)) 
        const_coords = np.column_stack((phi, np.full_like(phi, Locator)))
        curve = LineString(curve_coords)
        const = LineString(const_coords)
        intersection = curve.intersection(const)

        obt_angle = None

        if intersection.is_empty:
            obt_angle = None
        elif intersection.geom_type == 'Point':
            obt_angle = intersection.x
        elif intersection.geom_type == 'MultiPoint':
            obt_angle = None
        print(f"Obtained friction angle: {obt_angle} degrees")
        return obt_angle
    
