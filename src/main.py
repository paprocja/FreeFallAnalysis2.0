#!/usr/bin/python3
import os
from Data.SoilParameterization import SoilParameterization
import UI.FileSelectUI as FileSelectUI
from UI.Figures.PeakDisplay import *
from UI.Figures.PorePressureDisplay import *
from UI.Figures.PenetrometerDataDisplay import display_initial_data
from UI.Figures.ClayFrameworkDisplay import display_Su_for_K, redisplay_corrected_qsbc
from Data.TiltCalculator import calculate_tilt
from UI.FigureManager import FigureManager
from Data.PenetrometerData import PenetrometerData
from Data.Peak import Peak
from Data.PorePressure import PorePressure
from Data.ClayFramework import ClayFramework
from datetime import datetime
from Data.RelativeDensity import calculate_relative_densities
from Utils.DateFolder import set_date_folder
from Data.FrictionAngle import AlbatalFrictionAngle
from Data.FrictionAngle import DurgunogluMitchellFrictionAngle


#from Utils.io_utils import prompt_user_for_val, confirm_input_range, confirm_input_spike

# penetrometer_data object with parsed data from binary file
penetrometer_data = None

# flag to mark the first run with a set of files
original_run = None

# FigureManager Object to handle all of our plot figures
fig_manager = FigureManager()

# Create a penetrometer_data object once a file has been selected by the UI component 
def on_select_file(file_paths, penetrometer_id):
    """
    Creates a penetrometer_data object from the selected file    
    """
    global penetrometer_data
    global original_run
    if original_run is None:
        penetrometer_data = PenetrometerData(file_paths, penetrometer_id)
        original_run = [file_paths, penetrometer_id]
    
# This function creates a saved_data folder and a dated time stamped folder for the created csv files
# The parameter is the peak number the user selected so the dated folder has the selected peak and file along with timestamp
def save_to_csv(selected_peak):
    """
    Writes output of binary data to CSV file
    """
    # Allows main to be executed from ui-ffp or ui-ffp/src folders
    if not os.path.exists('../saved_data'):
        os.makedirs('../saved_data', exist_ok=True)

    # create dated and time stamped folder with name of the selected data file 
    selected_data_file = os.path.splitext(os.path.basename(original_run[0][0]))[0]
    date_folder = f"{selected_data_file}_Peak{selected_peak}_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    set_date_folder(date_folder)
    full_dir = os.path.join("../saved_data", date_folder)
    if not os.path.exists(full_dir):
        os.makedirs(full_dir, exist_ok=True)
    
    penetrometer_data.save_data(f'../saved_data/{date_folder}/' + 'raw_data_' + datetime.now().strftime("%Y-%m-%d_%H%M%S") + '.csv')

def restart() -> bool:
    """
    if the user selected it will restart the program. 
    If yes, will create a new figure window and keep the old one in the background.
    """
    print("Loading original data...")
    global original_run
    if not original_run is None:
        global penetrometer_data
        penetrometer_data = PenetrometerData(original_run[0], original_run[1])
        print("Loaded original data successfully!")
        print("Creating figure manager for new window...")
        global fig_manager
        fig_manager = FigureManager()
        print("Created new figure manager successfully!\n")
        return True
    else:
        print("Failed to load original data! Please restart the program and reselect the file.\n")
        return False
    


def main():
    # Starts file selection UI
    file_select = FileSelectUI.FileSelectUI(on_select_file)
    file_select.create_ui()

    # ensures penetrometer_data exists and has peaks
    if penetrometer_data is None or penetrometer_data.number_peaks == 0:
        print("No peaks found. Exiting Program.")
        return
    
    running = True
    while running:
        #display the initial plot through the figure manager
        peak_number, do_calculate_pore_pressure = display_initial_data(fig_manager, penetrometer_data.g2g, penetrometer_data.g18g, penetrometer_data.g50g, penetrometer_data.g200g, penetrometer_data.g250g,
                                                                       penetrometer_data.peaks, penetrometer_data.heights, penetrometer_data.number_peaks)
        save_to_csv(peak_number)

        # Prompt user to select a peak
        peak = Peak(peak_num=peak_number-1, penetrometer_data=penetrometer_data)

        # Determine if this peak will be used to calculate pore pressure
        # Once peak is selected, prompt user to select a spike within the peak
        spike = display_peak(fig_manager, peak.peak, peak.g2g, peak.end_of_drop, peak.peak_center, True) 
        peak.integrate_spike(spike)

        soil_parameterization = SoilParameterization(peak)

        # Get input for type of correction log, asinh, or beta
        # Once spike is selected, prompt user to select a QSBC correction equation
        correction_type, in_water = display_decel_vel_dep(fig_manager, peak.depth, peak.deceleration, peak.velocity, True)

        # TODO Make iot so that correction factor and tip type can be selected from JSON
        correction_factor = 1.5
        tip_type = 'c'

        initial_qsbc = peak.calculate_QSBC_for_K(correction_type, correction_factor, tip_type, in_water)

        # Will also need to pass in the tip type when not using default to c
        
        # Tuple used to find start and end values. Could be changed so parameters are not needed for average calculation
        start, end = display_QSBC_for_K(fig_manager, initial_qsbc, True)
        
        corrected_qsbc_lines = peak.calculate_corrected_qsbc(correction_type, start, end, in_water)

        # Get the tilt in the x and y directions
        tilt_x, tilt_y = calculate_tilt(spike, peak.end_of_drop, peak.gX55g, peak.gY55g)

        # Handles calculating relative density and friction angle and creates variables for displaying them 
        albatal_density, white_density = (-1, None), (-1, None)
        albatal_fa, white_fa, durg_mitch_fa = -1, -1, -1
        if soil_parameterization.framework == 'sand':
            albatal_density, white_density = calculate_relative_densities(peak)
            friction_angle = AlbatalFrictionAngle(peak)
            albatal_fa = friction_angle.calc_friction_angle(albatal_density[0], albatal_density[1].get_rd_depth())
            white_fa = friction_angle.calc_friction_angle(white_density[0], white_density[1].get_rd_depth())
            friction_angle = DurgunogluMitchellFrictionAngle(peak)
            durg_mitch_fa = friction_angle.calc_friction_angle(None, None)
        # Display corrected QSBC lines
        k_value = display_corrected_QSBC(fig_manager, corrected_qsbc_lines,
                               peak.depth, peak.depth_midpoints, peak.velocity, peak.deceleration, peak.qdyn, peak.averaged_qdyn, start, end, do_calculate_pore_pressure or (soil_parameterization.framework == 'clay'),
                               albatal_density[0], white_density[0], True, framework=soil_parameterization.framework, correction_type=correction_type)
        
        # Display three-plot screen with user-inputted value for QSBC plot, pore pressures, and soil behavior chart
        # needs to loop while user updates k
        running = True
        while True:
            user_selected_k_qsbc_line = peak.calculate_corrected_qsbc_given_k(correction_type, start, end, in_water, k_value)
            command = display_user_selected_QSBC(fig_manager, user_selected_k_qsbc_line, peak.depth, peak.depth_midpoints, peak.qdyn, peak.averaged_qdyn, start, end,
                                             tilt_x, tilt_y, k_value, albatal_fa, white_fa, durg_mitch_fa, do_calculate_pore_pressure or (soil_parameterization.framework == 'clay'), True, soil_parameterization.framework, correction_type)
            if command == 0:
                break
            elif command == -1:
                running = False
                break
            else:
                k_value = command

        if soil_parameterization.framework == 'clay':
            ntk = float(redisplay_corrected_qsbc(fig_manager, corrected_qsbc_lines, correction_type,
                                                 peak.depth, peak.velocity, peak.deceleration, peak.qdyn, start, end, tilt_x, tilt_y))
            print(ntk)
            framework = ClayFramework(peak, corrected_qsbc_lines[0].ave) # can be any corrected qsbc
            framework.select_ntk(ntk) # will output same as QSBC
            su = framework.proceed()
            running = display_Su_for_K(fig_manager, su, do_calculate_pore_pressure)
        else:
            print('Sand Framework not yet implemented.')

        # Determine if this is the first peak and if the user would like to calculate pore pressure for that peak
        if do_calculate_pore_pressure:
            
            # Get the bounds of the pore pressure for the first peak
            pore_pressure_start, pore_pressure_end = display_peaks_and_ppm(fig_manager, penetrometer_data)

            # Create PorePressure object calculate deceleration profile based on bounds
            pore_pressure = PorePressure(peak, penetrometer_data, pore_pressure_start, pore_pressure_end)

            pore_pressure.calculate_deceleration_profile()

            # Get the bounds of the deceleration profile
            profile_increase, profile_decrease = display_deceleration_profile(fig_manager, pore_pressure)

            # Calculate and display pore pressure based on profile bounds
            pore_pressure.calculate_pore_pressure(profile_increase, profile_decrease)

            running = display_pore_pressure(fig_manager, pore_pressure)

        if running:
            restart()

    print("Exiting program.")

if __name__ == "__main__":
    main()