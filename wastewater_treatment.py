## 📄 Complete Code

### wastewater_treatment.py
```python
"""
Electrochemical Treatment of Industrial Wastewater
Simulation and Analysis of Pollutant Removal Efficiency
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.integrate import odeint
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 12

class ElectrochemicalTreatment:
    """
    Electrochemical Wastewater Treatment System Simulation
    """
    
    def __init__(self, volume=1.0, electrode_area=0.1):
        """
        Initialize treatment system
        
        Args:
            volume: Treatment volume in m³
            electrode_area: Electrode surface area in m²
        """
        self.volume = volume  # m³
        self.electrode_area = electrode_area  # m²
        self.F = 96485  # Faraday constant (C/mol)
        
        # Typical parameters
        self.current_density = 50  # mA/cm²
        self.current = self.current_density * electrode_area * 1e3  # A
        self.voltage = 5  # V
        
        # Initial conditions
        self.COD_initial = 2000  # mg/L
        self.BOD_initial = 800  # mg/L
        self.TOC_initial = 600  # mg/L
        self.TSS_initial = 500  # mg/L
        self.pH = 7.0
        self.temperature = 25  # °C
    
    def first_order_kinetics(self, C0, k, t):
        """
        First order reaction kinetics
        C(t) = C0 * exp(-k * t)
        """
        return C0 * np.exp(-k * t)
    
    def second_order_kinetics(self, C0, k, t):
        """
        Second order reaction kinetics
        1/C(t) = 1/C0 + k * t
        """
        return 1 / (1/C0 + k * t)
    
    def cod_removal_model(self, t, k=0.015):
        """
        COD removal over time using first-order kinetics
        """
        return self.first_order_kinetics(self.COD_initial, k, t)
    
    def reaction_rate_temperature(self, k_ref, Ea=20000, T_ref=298, T=298):
        """
        Arrhenius equation for temperature effect on reaction rate
        k = k_ref * exp(Ea/R * (1/T_ref - 1/T))
        """
        R = 8.314  # Gas constant (J/mol·K)
        return k_ref * np.exp(Ea/R * (1/T_ref - 1/T))
    
    def energy_consumption(self, treatment_time_min):
        """
        Calculate energy consumption in kWh/m³
        
        Args:
            treatment_time_min: Treatment time in minutes
        
        Returns:
            Energy consumption in kWh/m³
        """
        treatment_time_hours = treatment_time_min / 60
        power = self.voltage * self.current  # Watts
        energy_kWh = power * treatment_time_hours / 1000
        return energy_kWh / self.volume  # kWh/m³
    
    def current_efficiency(self, COD_removed_mgL, treatment_time_min):
        """
        Calculate current efficiency for COD removal
        
        Args:
            COD_removed_mgL: Amount of COD removed in mg/L
            treatment_time_min: Treatment time in minutes
        
        Returns:
            Current efficiency (%)
        """
        # Oxygen equivalent for COD (2 electrons per O atom)
        n = 4  # electrons per O2 molecule
        COD_removed_kg = COD_removed_mgL * self.volume * 1e-3  # kg
        
        # Theoretical charge required (Coulombs)
        Q_theoretical = (COD_removed_kg * n * self.F) / 32000  # 32 g O2 = 1 mol
        Q_actual = self.current * treatment_time_min * 60  # Coulombs
        
        return (Q_theoretical / Q_actual) * 100 if Q_actual > 0 else 0
    
    def simulate_treatment(self, time_minutes=120, current_density=50):
        """
        Simulate the entire treatment process
        
        Args:
            time_minutes: Total treatment time in minutes
            current_density: Current density in mA/cm²
        
        Returns:
            DataFrame with simulation results
        """
        self.current_density = current_density  # mA/cm²
        self.current = self.current_density * self.electrode_area * 1e3  # A
        
        # Time array (minutes)
        t = np.linspace(0, time_minutes, 100)
        
        # Apply temperature effect on rate constant
        k_ref = 0.015  # Reference rate constant at 298K
        k = self.reaction_rate_temperature(k_ref, T=self.temperature + 273)
        
        # Calculate removal for each parameter
        COD = self.first_order_kinetics(self.COD_initial, k, t)
        BOD = self.first_order_kinetics(self.BOD_initial, k, t)
        TOC = self.first_order_kinetics(self.TOC_initial, k, t)
        TSS = self.first_order_kinetics(self.TSS_initial, k*1.2, t)  # TSS removes faster
        
        # Calculate energy consumption at each time point
        energy = [self.energy_consumption(ti) for ti in t]
        
        # Calculate removal efficiency
        COD_removal_efficiency = (1 - COD/self.COD_initial) * 100
        BOD_removal_efficiency = (1 - BOD/self.BOD_initial) * 100
        
        # Create results dataframe
        results = pd.DataFrame({
            'Time_min': t,
            'COD_mgL': COD,
            'BOD_mgL': BOD,
            'TOC_mgL': TOC,
            'TSS_mgL': TSS,
            'COD_Removal_%': COD_removal_efficiency,
            'BOD_Removal_%': BOD_removal_efficiency,
            'Energy_kWh_per_m3': energy
        })
        
        return results
    
    def optimize_current_density(self, time_minutes):
        """
        Find optimal current density for maximum removal efficiency
        
        Args:
            time_minutes: Treatment time in minutes
        
        Returns:
            Optimal current density and corresponding removal
        """
        current_densities = np.arange(10, 200, 10)  # mA/cm²
        removal_efficiencies = []
        energy_costs = []
        
        for cd in current_densities:
            results = self.simulate_treatment(time_minutes, cd)
            final_removal = results['COD_Removal_%'].iloc[-1]
            removal_efficiencies.append(final_removal)
            
            # Energy consumption at this current density
            energy = self.energy_consumption(time_minutes)
            energy_costs.append(energy)
        
        # Create DataFrame
        opt_df = pd.DataFrame({
            'Current_Density_mA_per_cm2': current_densities,
            'COD_Removal_%': removal_efficiencies,
            'Energy_kWh_per_m3': energy_costs
        })
        
        # Calculate cost-benefit ratio (removal per kWh)
        opt_df['Removal_per_kWh'] = opt_df['COD_Removal_%'] / (opt_df['Energy_kWh_per_m3'] + 0.01)
        
        # Find optimal
        optimal_idx = opt_df['Removal_per_kWh'].idxmax()
        optimal_cd = opt_df.loc[optimal_idx, 'Current_Density_mA_per_cm2']
        optimal_removal = opt_df.loc[optimal_idx, 'COD_Removal_%']
        
        return optimal_cd, optimal_removal, opt_df
    
    def cost_analysis(self, treatment_time_min, current_density):
        """
        Calculate treatment costs
        
        Args:
            treatment_time_min: Treatment time in minutes
            current_density: Current density in mA/cm²
        
        Returns:
            Dictionary with cost breakdown
        """
        results = self.simulate_treatment(treatment_time_min, current_density)
        final_removal = results['COD_Removal_%'].iloc[-1]
        
        # Energy cost (assuming $0.12 per kWh)
        energy = self.energy_consumption(treatment_time_min)
        energy_cost = energy * 0.12  # USD per m³
        
        # Electrode consumption (assuming $5 per m² per year)
        electrode_cost = 5 * self.electrode_area / 365  # USD per day
        
        # Labor and maintenance (estimate)
        labor_cost = 2.0  # USD per m³
        
        # Chemical additives (if any)
        chemical_cost = 0.5  # USD per m³
        
        total_cost = energy_cost + electrode_cost + labor_cost + chemical_cost
        
        return {
            'Treatment_Time_min': treatment_time_min,
            'Current_Density_mA_per_cm2': current_density,
            'COD_Removal_%': final_removal,
            'Energy_Consumption_kWh_per_m3': energy,
            'Energy_Cost_USD_per_m3': energy_cost,
            'Electrode_Cost_USD_per_m3': electrode_cost,
            'Labor_Cost_USD_per_m3': labor_cost,
            'Chemical_Cost_USD_per_m3': chemical_cost,
            'Total_Cost_USD_per_m3': total_cost,
            'Cost_per_kg_COD_Removed': total_cost * self.volume / (results['COD_mgL'].iloc[0] - results['COD_mgL'].iloc[-1]) * 1000
        }
    
    def plot_treatment_results(self, results):
        """
        Plot treatment simulation results
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Pollutant concentration over time
        axes[0, 0].plot(results['Time_min'], results['COD_mgL'], 'b-', linewidth=2, label='COD')
        axes[0, 0].plot(results['Time_min'], results['BOD_mgL'], 'g-', linewidth=2, label='BOD')
        axes[0, 0].plot(results['Time_min'], results['TOC_mgL'], 'r-', linewidth=2, label='TOC')
        axes[0, 0].plot(results['Time_min'], results['TSS_mgL'], 'orange', linewidth=2, label='TSS')
        axes[0, 0].set_xlabel('Time (minutes)')
        axes[0, 0].set_ylabel('Concentration (mg/L)')
        axes[0, 0].set_title('Pollutant Concentration vs Treatment Time')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Removal efficiency
        axes[0, 1].plot(results['Time_min'], results['COD_Removal_%'], 'b-', linewidth=2, label='COD Removal')
        axes[0, 1].plot(results['Time_min'], results['BOD_Removal_%'], 'g-', linewidth=2, label='BOD Removal')
        axes[0, 1].fill_between(results['Time_min'], results['COD_Removal_%'], alpha=0.3, color='blue')
        axes[0, 1].set_xlabel('Time (minutes)')
        axes[0, 1].set_ylabel('Removal Efficiency (%)')
        axes[0, 1].set_title('Pollutant Removal Efficiency vs Time')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(y=80, color='r', linestyle='--', label='80% Target')
        
        # Plot 3: Energy consumption
        axes[1, 0].plot(results['Time_min'], results['Energy_kWh_per_m3'], 'purple', linewidth=2)
        axes[1, 0].fill_between(results['Time_min'], results['Energy_kWh_per_m3'], alpha=0.3, color='purple')
        axes[1, 0].set_xlabel('Time (minutes)')
        axes[1, 0].set_ylabel('Energy (kWh/m³)')
        axes[1, 0].set_title('Energy Consumption vs Treatment Time')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Rate of removal
        removal_rate = np.gradient(results['COD_Removal_%'], results['Time_min'])
        axes[1, 1].plot(results['Time_min'], removal_rate, 'red', linewidth=2)
        axes[1, 1].set_xlabel('Time (minutes)')
        axes[1, 1].set_ylabel('Removal Rate (%/min)')
        axes[1, 1].set_title('COD Removal Rate vs Time')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axhline(y=0, color='k', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig('plots/treatment_simulation.png', dpi=150, bbox_inches='tight')
        plt.show()
    
    def plot_optimization_results(self, opt_df):
        """
        Plot optimization results
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Removal efficiency vs current density
        axes[0].plot(opt_df['Current_Density_mA_per_cm2'], opt_df['COD_Removal_%'], 'bo-', linewidth=2, markersize=8)
        axes[0].set_xlabel('Current Density (mA/cm²)')
        axes[0].set_ylabel('COD Removal Efficiency (%)')
        axes[0].set_title('Effect of Current Density on Removal Efficiency')
        axes[0].grid(True, alpha=0.3)
        
        # Optimal point
        optimal_idx = opt_df['Removal_per_kWh'].idxmax()
        axes[0].plot(opt_df.loc[optimal_idx, 'Current_Density_mA_per_cm2'], 
                    opt_df.loc[optimal_idx, 'COD_Removal_%'], 'r*', markersize=15, 
                    label='Optimal Point')
        axes[0].legend()
        
        # Cost-benefit analysis
        axes[1].plot(opt_df['Current_Density_mA_per_cm2'], opt_df['Removal_per_kWh'], 'g-', linewidth=2)
        axes[1].set_xlabel('Current Density (mA/cm²)')
        axes[1].set_ylabel('Removal per kWh (%/kWh)')
        axes[1].set_title('Cost-Benefit Analysis')
        axes[1].grid(True, alpha=0.3)
        axes[1].axvline(x=opt_df.loc[optimal_idx, 'Current_Density_mA_per_cm2'], 
                       color='r', linestyle='--', alpha=0.7, label='Optimal')
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig('plots/optimization_results.png', dpi=150, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, results, cost_analysis):
        """
        Generate treatment report
        """
        report = f"""
        ======================================================================
                    ELECTROCHEMICAL WASTEWATER TREATMENT REPORT
        ======================================================================
        
        TREATMENT PARAMETERS
        --------------------
        Volume Treated: {self.volume} m³
        Electrode Area: {self.electrode_area} m²
        Current Density: {self.current_density} mA/cm²
        Applied Current: {self.current:.2f} A
        Applied Voltage: {self.voltage} V
        Treatment Time: {results['Time_min'].iloc[-1]} minutes
        Temperature: {self.temperature}°C
        Initial pH: {self.pH}
        
        INITIAL CONDITIONS
        ------------------
        Initial COD: {self.COD_initial} mg/L
        Initial BOD: {self.BOD_initial} mg/L
        Initial TOC: {self.TOC_initial} mg/L
        Initial TSS: {self.TSS_initial} mg/L
        
        FINAL CONDITIONS
        ----------------
        Final COD: {results['COD_mgL'].iloc[-1]:.1f} mg/L
        Final BOD: {results['BOD_mgL'].iloc[-1]:.1f} mg/L
        Final TOC: {results['TOC_mgL'].iloc[-1]:.1f} mg/L
        Final TSS: {results['TSS_mgL'].iloc[-1]:.1f} mg/L
        
        REMOVAL EFFICIENCIES
        --------------------
        COD Removal: {results['COD_Removal_%'].iloc[-1]:.1f}%
        BOD Removal: {results['BOD_Removal_%'].iloc[-1]:.1f}%
        
        ENERGY AND COST ANALYSIS
        ------------------------
        Energy Consumption: {cost_analysis['Energy_Consumption_kWh_per_m3']:.2f} kWh/m³
        Energy Cost: ${cost_analysis['Energy_Cost_USD_per_m3']:.3f} per m³
        Electrode Cost: ${cost_analysis['Electrode_Cost_USD_per_m3']:.3f} per m³
        Labor Cost: ${cost_analysis['Labor_Cost_USD_per_m3']:.2f} per m³
        Chemical Cost: ${cost_analysis['Chemical_Cost_USD_per_m3']:.2f} per m³
        ----------------------------------------------------------------------
        TOTAL COST: ${cost_analysis['Total_Cost_USD_per_m3']:.3f} per m³
        Cost per kg COD Removed: ${cost_analysis['Cost_per_kg_COD_Removed']:.2f}
        
        REGULATORY COMPLIANCE
        ---------------------
        Discharge Standard (COD < 250 mg/L): {'✓ PASS' if results['COD_mgL'].iloc[-1] < 250 else '✗ FAIL'}
        Discharge Standard (BOD < 30 mg/L): {'✓ PASS' if results['BOD_mgL'].iloc[-1] < 30 else '✗ FAIL'}
        
        RECOMMENDATIONS
        ---------------
        - Optimal current density for this application: {self.current_density} mA/cm²
        - Recommended treatment time: {results['Time_min'].iloc[-1]} minutes
        - Consider post-treatment filtration for residual TSS
        
        ======================================================================
        Report generated by Electrochemical Wastewater Treatment System
        ======================================================================
        """
        
        # Save report
        with open('treatment_report.txt', 'w') as f:
            f.write(report)
        
        print(report)
        return report


def compare_with_conventional_methods():
    """
    Compare electrochemical treatment with conventional methods
    """
    methods = ['Electrochemical', 'Activated Sludge', 'Chemical Coagulation', 'Membrane Filtration']
    cod_removal = [92, 85, 75, 95]
    treatment_time = [120, 480, 90, 60]
    energy_consumption = [15, 8, 5, 20]
    operating_cost = [0.85, 0.60, 0.70, 1.20]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # COD Removal
    axes[0, 0].bar(methods, cod_removal, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'])
    axes[0, 0].set_ylabel('COD Removal (%)')
    axes[0, 0].set_title('Treatment Efficiency Comparison')
    axes[0, 0].set_ylim(0, 100)
    for i, v in enumerate(cod_removal):
        axes[0, 0].text(i, v + 2, str(v), ha='center')
    
    # Treatment Time
    axes[0, 1].bar(methods, treatment_time, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'])
    axes[0, 1].set_ylabel('Time (minutes)')
    axes[0, 1].set_title('Treatment Time Comparison')
    
    # Energy Consumption
    axes[1, 0].bar(methods, energy_consumption, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'])
    axes[1, 0].set_ylabel('Energy (kWh/m³)')
    axes[1, 0].set_title('Energy Consumption Comparison')
    
    # Operating Cost
    axes[1, 1].bar(methods, operating_cost, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'])
    axes[1, 1].set_ylabel('Cost (USD/m³)')
    axes[1, 1].set_title('Operating Cost Comparison')
    
    plt.tight_layout()
    plt.savefig('plots/method_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("ELECTROCHEMICAL WASTEWATER TREATMENT SYSTEM")
    print("Simulation and Analysis Platform")
    print("="*60)
    
    # Initialize treatment system
    treatment = ElectrochemicalTreatment(volume=1.0, electrode_area=0.1)
    
    # Display initial configuration
    print("\n📊 SYSTEM CONFIGURATION")
    print("-"*40)
    print(f"Volume: {treatment.volume} m³")
    print(f"Electrode Area: {treatment.electrode_area} m²")
    print(f"Initial COD: {treatment.COD_initial} mg/L")
    print(f"Initial BOD: {treatment.BOD_initial} mg/L")
    
    # Run simulation
    print("\n🔄 RUNNING TREATMENT SIMULATION...")
    results = treatment.simulate_treatment(time_minutes=120, current_density=50)
    
    # Plot results
    treatment.plot_treatment_results(results)
    
    # Optimization
    print("\n⚡ OPTIMIZING CURRENT DENSITY...")
    optimal_cd, optimal_removal, opt_df = treatment.optimize_current_density(120)
    print(f"Optimal Current Density: {optimal_cd} mA/cm²")
    print(f"Expected COD Removal: {optimal_removal:.1f}%")
    
    treatment.plot_optimization_results(opt_df)
    
    # Cost analysis
    print("\n💰 COST ANALYSIS")
    print("-"*40)
    costs = treatment.cost_analysis(120, optimal_cd)
    for key, value in costs.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")
    
    # Generate report
    treatment.generate_report(results, costs)
    
    # Compare with conventional methods
    print("\n📊 COMPARING WITH CONVENTIONAL METHODS...")
    compare_with_conventional_methods()
    
    # Parameter sensitivity analysis
    print("\n🔬 PARAMETER SENSITIVITY ANALYSIS")
    print("-"*40)
    
    temp_range = np.arange(15, 45, 5)
    removal_at_temp = []
    for temp in temp_range:
        treatment.temperature = temp
        results_temp = treatment.simulate_treatment(120, 50)
        removal_at_temp.append(results_temp['COD_Removal_%'].iloc[-1])
    
    plt.figure(figsize=(8, 5))
    plt.plot(temp_range, removal_at_temp, 'ro-', linewidth=2, markersize=8)
    plt.xlabel('Temperature (°C)')
    plt.ylabel('COD Removal Efficiency (%)')
    plt.title('Effect of Temperature on Treatment Efficiency')
    plt.grid(True, alpha=0.3)
    plt.savefig('plots/temperature_sensitivity.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\n✅ Simulation complete! Check 'plots/' directory for visualizations.")
    print("📄 Report saved as 'treatment_report.txt'")


if __name__ == "__main__":
    main()
