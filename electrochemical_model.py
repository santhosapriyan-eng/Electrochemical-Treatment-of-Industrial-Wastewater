"""
Electrochemical Treatment Mathematical Models
Advanced kinetic and mass transfer models
"""

import numpy as np
from scipy.integrate import odeint

class ElectrochemicalKinetics:
    """
    Electrochemical reaction kinetics models
    """
    
    def __init__(self):
        self.F = 96485  # Faraday constant (C/mol)
        self.R = 8.314  # Gas constant (J/mol·K)
        
    def butler_volmer(self, eta, i0, alpha=0.5, T=298):
        """
        Butler-Volmer equation for electrode kinetics
        i = i0 * [exp(alpha * F * eta / RT) - exp(-(1-alpha) * F * eta / RT)]
        """
        f = self.F / (self.R * T)
        return i0 * (np.exp(alpha * f * eta) - np.exp(-(1-alpha) * f * eta))
    
    def limiting_current(self, C_bulk, D, delta, n):
        """
        Limiting current density for mass transfer
        i_L = n * F * D * C_bulk / delta
        """
        return n * self.F * D * C_bulk / delta
    
    def reaction_rate_constant(self, k0, Ea, T):
        """
        Arrhenius temperature dependence
        """
        return k0 * np.exp(-Ea / (self.R * T))


class MassTransferModel:
    """
    Mass transfer modeling in electrochemical reactors
    """
    
    def sherwood_number(self, Re, Sc, L, type='laminar'):
        """
        Calculate Sherwood number for different flow regimes
        Sh = k * L / D
        """
        if type == 'laminar':
            return 1.85 * (Re * Sc * (self.L / L))**(1/3)
        elif type == 'turbulent':
            return 0.023 * Re**0.83 * Sc**0.33
        else:
            return 2 + 0.6 * Re**0.5 * Sc**0.33
    
    def mass_transfer_coefficient(self, Sh, D, L):
        """
        Calculate mass transfer coefficient
        """
        return Sh * D / L


class ReactorDesign:
    """
    Electrochemical reactor design calculations
    """
    
    def residence_time_distribution(self, V, Q, model='CSTR'):
        """
        Calculate residence time distribution
        """
        tau = V / Q
        if model == 'CSTR':
            t = np.linspace(0, 5*tau, 100)
            E = (1/tau) * np.exp(-t/tau)
            return t, E
        else:  # PFR
            t = np.array([tau])
            E = np.array([1])
            return t, E
    
    def electrode_area_requirement(self, I, i):
        """
        Calculate required electrode area
        A = I / i
        """
        return I / i
    
    def cell_voltage(self, E_eq, eta_a, eta_c, iR):
        """
        Calculate cell voltage
        V_cell = E_eq + |eta_a| + |eta_c| + iR
        """
        return E_eq + abs(eta_a) + abs(eta_c) + iR


def main():
    """Demo the electrochemical models"""
    print("Electrochemical Kinetics Models")
    print("="*40)
    
    ek = ElectrochemicalKinetics()
    
    # Test Butler-Volmer
    eta = np.linspace(-0.5, 0.5, 100)
    i_density = ek.butler_volmer(eta, i0=0.01)
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 5))
    plt.plot(eta, i_density, 'b-', linewidth=2)
    plt.xlabel('Overpotential (V)')
    plt.ylabel('Current Density (A/m²)')
    plt.title('Butler-Volmer Kinetics')
    plt.grid(True, alpha=0.3)
    plt.savefig('butler_volmer.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    main() 
