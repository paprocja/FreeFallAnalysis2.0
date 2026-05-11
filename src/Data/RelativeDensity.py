from abc import ABC, abstractmethod
from Data.Peak import Peak
import numpy as np
import math
from scipy.optimize import root_scalar

class RelativeDensityFunction(ABC):

    @abstractmethod
    def calculate_rd(self):
        pass

    @abstractmethod
    def get_rd_depth(self):
        pass

class AlbatalDensity(RelativeDensityFunction):

    #TODO: once we're done with the small test in this file (and move our testing to test.py), we should make the peak arg required
    def __init__(self, peak: Peak = None):
        self.peak = peak
        if self.peak is not None:
            decel, velo, depth = self.peak.get_decel_velo_depth_at_max_decel()
            self.deceleration = decel
            self.velocity = velo
            self.depth = depth

    def calculate_rd(self):
        if self.peak is None and self.deceleration is None:
            raise ValueError("Peak must be defined, or deceleration must be explicitly set by set_decel()")
        decel = self.deceleration

        return (-2.18 * pow(10, -4) * pow(decel, 3)) + (1.29 * pow(10, -2) * pow(decel, 2)) + (1.61 * decel) - 13.09
    
    def get_rd_depth(self):
        return self.depth

    # set_decel really only used for testing -- where we want to manually set decel to a specific number,
    # rather than calculating it from the given peak
    def set_decel(self, decel):
        self.deceleration = decel
        

# small test of Albatal density -- need to check this with Sponsor (Julie) to see if this value seems correct
if __name__ == "__main__":
    ad = AlbatalDensity()
    ad.set_decel(30)
    print("Albatal density @ a = 30 --> " + f"{ad.calculate_rd()}")


def calculate_relative_densities(peak: Peak = None):
    albatal_density = AlbatalDensity(peak)
    white_density = WhiteDensity(peak)
    return (round(albatal_density.calculate_rd(), 1), albatal_density), (round(white_density.calculate_rd(), 1), white_density)

# ======= notes/concerns for below implementation =======
#
# 1. It seems like the arrays of data in Peak don't necessarily line up -- e.g. they are different lengths -- best case scenario
# is that the additional values in some of the arrays are 'at the end' of the array (at larger depths)
# worse case is that additional values are at the beginning of array, or even worse, in the middle somehow -- need to figure that out
#
# 2. Right now the function only uses constant values -- need to implement parameters for whatever values she wants changed at some point -- fairly trivial


class WhiteDensity(RelativeDensityFunction):

    # Constants (c & p from matlab codes) (others can be input by user)
    __phicv = math.radians(32)
    __Q = 6
    __R = 1
    __V50 = 1 # constant
    __Nkt = 12
    __c0 = 300
    __c1 = 0.46
    __c2 = 2.96
    __gammap = 10  # in kN/m3
    __k0 = 0.5
    __chmin = .031
    __peak = None

    __depth_of_max_rd = None

    def __init__(self, peak: Peak):
        self.__peak = peak

        # added this so __depth_of_max_rd was not None and get_rd_depth() would stop returning -1 for
        # use in the friction angle calc
        if self.__peak is not None:
            __decel, __velo, __depth = self.__peak.get_decel_velo_depth_at_max_decel()
            self.__depth_of_max_rd = __depth
    
    # ------- Functions/terms reimplemented from matlab codes -------

    def __pm(self, depth: float):
        gammap = self.__gammap
        k0 = self.__k0
        return gammap * ((1 + 2*k0) / 3) * depth

    def __V(self, velocity: float):
        chmin = self.__chmin
        return (velocity * 0.0875) / chmin

    def __strainterm(self, velocity: float):
        V50 = self.__V50
        return 1 / (1 + (self.__V(velocity) / V50))
    
    # ------- chunking up of equation for organizational purposes -------

    # a repeated chunk of our equation
    def __A(self, x):
        Nkt = self.__Nkt
        phicv = self.__phicv
        Q = self.__Q
        return Nkt * 0.5 * ((6 * math.sin(phicv))/(3 - math.sin(phicv))) * math.exp(Q - (1/x))

    # another chunk of our equation (not repeated)
    def __B(self, depth: float, x):
        c0 = self.__c0
        c1 = self.__c1
        c2 = self.__c2
        pm = self.__pm(depth)
        return c0 * (pm**c1) * math.exp(x*c2)

    def calculate_rd_at_depth(self, depth):
        qdynr = (self.__peak.qdyn[depth]) / 1000
        v = self.__peak.velocity[depth]
        strainterm = self.__strainterm(v)
        def eqn(x): # our full equation that we want to solve, as a function of x (f(x)) --> passed to root_scalar function with a range where we think on is (0, 1)
            return qdynr - (self.__A(x) + strainterm * (self.__B(self.__peak.depth[depth], x) - self.__A(x)))
        try:
            res = root_scalar(eqn, bracket=[1e-2, 1.0]) # because we can't pass 0 to eqn (we get div. by 0 error), we want to pass a very small value (close to 0)
            rd = res.root
            if res.converged:
                return rd
            else:
                return None
        except ValueError as e:
            return None
    
    def calculate_rd(self):
        results = []
        dep_indices = [] # list of indices we found results at
        len_depth = len(self.__peak.depth)
        len_qdyn = len(self.__peak.qdyn)
        len_velocity = len(self.__peak.velocity)
        for i in range(10, min(len_depth, len_qdyn, len_velocity)):
            res = self.calculate_rd_at_depth(i)
            if res is not None:
                results.append(res * 100) # as a percentage
                dep_indices.append(i)
        if results is not None:
            ret = max(results) # the result we want to return
            index_rd = results.index(ret) # the index of that result in the array of results
            depth_index = dep_indices[index_rd] # the corresponding depth index of that result in the original depth array from the peak
            self.__depth_of_max_rd = self.__peak.depth[depth_index] # the actual value of the depth at that particular depth index (kind of confusing...)
            return ret
        else: 
            return -1 # pass an invalid value for printing purposes in PeakDisplay.py
    
    def get_rd_depth(self):
        if self.__depth_of_max_rd is not None:
            return self.__depth_of_max_rd
        else:
            return -1 # prone to changing this, maybe we just want to return None ? Jury's still out on that...