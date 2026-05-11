import pandas as pd
import numpy as np
from datetime import datetime
from Utils.DateFolder import get_date_folder

def display_peak(figure_manager, peak, g2g, drop_end, peak_center, save_data, filename="peak_data"):
    """
    Displays the peak using the figure manager.
    """
    def plot(ax):
        ax.set_xlim(0, len(peak) + 10)
        ax.plot(peak, label='peak')
        ax.plot(g2g, label ='2g')
        ax.scatter(drop_end, peak[drop_end], marker='x', label='End of drop', color='black')
        ax.legend(loc='upper right')
        ax.set_title(f"Peak at {peak_center}")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Value")
    
    if save_data:
        df = pd.DataFrame({"Peak": peak, "G2G": g2g})
        filename1 = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        df.to_csv(f'../saved_data/{get_date_folder()}/' + filename + '_' + filename1 + '.csv', index=False)
        

    figure_manager.display(plot)

    figure_manager.add_text_box("Enter Spike Selection: ", [0.15, 0.05, 0.1, 0.05], 'spike')
    figure_manager.add_button("Confirm", [0.26, 0.05, 0.1, 0.05])

    input_values = figure_manager.wait_for_valid_inputs()
    return int(input_values["Enter Spike Selection: "])

def display_decel_vel_dep(figure_manager, depth, deceleration, velocity, save_data, filename="decel_vel_dep"):
    """
    Displays the deceleration, velocity, and depth data in one plot.
    """
    def plot(ax):
        ax.invert_yaxis()
        ax.set_ylim(max(depth * 100), 0)
        ax.set_xlim(0, max(max(deceleration), max(velocity)))
        ax.plot(deceleration, depth * 100, linestyle='-', label='Deceleration')
        ax.plot(velocity, depth * 100, linestyle='--', label='Velocity')
        ax.set_ylabel('Depth [CM]')
        ax.set_xlabel('Deceleration [g] // Velocity [m/s]')
        ax.legend(loc='upper right')

    if save_data:
        df = pd.DataFrame({"Deceleration": deceleration, "Velocity": velocity, "Depth (CM)": depth * 100})
        filename1 = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        df.to_csv(f'../saved_data/{get_date_folder()}/' + filename + '_' + filename1 + '.csv', index=False)

    figure_manager.display(plot)
    figure_manager.add_text_box("Enter Correction Type: ", [0.15, 0.01, 0.1, 0.05], 'correction')
    figure_manager.add_button("Confirm", [0.26, 0.01, 0.1, 0.05])
    figure_manager.add_info_text("1 for Log, 2 for Asinh, 3 for Beta", 0.02, 0.07, 0.34)
    figure_manager.add_radio([0.85, 0.02, 0.05, 0.08])
    figure_manager.add_info_text("In water?", 0.72, 0.03, 0.12)
    input_values = figure_manager.wait_for_valid_inputs()
    return int(input_values["Enter Correction Type: "]), figure_manager.radio_result

def display_QSBC_for_K(figure_manager, qsbc_for_k, save_data, filename="bearing_capacity"):
    """
    Displays the quasi static bearing capacity
    """
    def plot(ax):
        ax.set_xlim(0, len(qsbc_for_k) + 10)
        ax.plot(qsbc_for_k, label='QSBC')
        ax.set_xlabel('Bearing Capacity')
        ax.set_ylabel('Depth')
        ax.set_title('Depth x Bearing Capacity')
        ax.legend(loc='upper right')

    if save_data:
        df = pd.DataFrame({"QSBC": qsbc_for_k})
        filename1 = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        df.to_csv(f'../saved_data/{get_date_folder()}/' + filename + '_' + filename1 + '.csv', index=False)

    figure_manager.display(plot)

    # for input colection
    figure_manager.add_text_box("Enter Start Time: ", [0.15, 0.07, 0.1, 0.05], 't_start', time_range=qsbc_for_k)
    figure_manager.add_text_box("Enter End Time: ", [0.15, 0.01, 0.1, 0.05], 't_end', time_range=qsbc_for_k)
    figure_manager.add_button("Confirm", [0.26, 0.03, 0.1, 0.05])
    input_values = figure_manager.wait_for_valid_inputs()
    start = int(input_values["Enter Start Time: "])
    end = int(input_values["Enter End Time: "])
    return start, end


def display_corrected_QSBC(figure_manager, corrected_qsbc_lines,
                            depth, depth_midpoints, velocity, deceleration, qdyn, averaged_qdyn, start, end, do_pore, albatal_rel_density, white_rel_density, save_data, framework, correction_type, filename="corrected_qsbc"):
    """
    Displays the corrected quasi static bearing capacity
    """
    corrected_depth = depth[start:end+1]*100
    corrected_depth_midpoints = depth_midpoints[start:end+1]*100
    if correction_type != 3:
        k_or_beta = "k"
    else:
        k_or_beta = "β"
    
    def plot(ax):
        #plot the decel and velocity to the left side of figure
        ax[0].invert_yaxis()
        ax[0].set_ylim(max(depth * 100), 0)
        ax[0].set_xlim(0, max(max(deceleration), max(velocity)))
        ax[0].plot(deceleration, depth * 100, linestyle='-', label='Deceleration')
        ax[0].plot(velocity, depth * 100, linestyle='--', label='Velocity')
        ax[0].set_ylabel('Depth [CM]')
        ax[0].set_xlabel('Deceleration [g] // Velocity [m/s]')
        ax[0].legend(loc='upper right')
        

        #Plot the Correction averages and the dynamic on the right side of figure
        ax[1].invert_yaxis()
        ax[1].set_ylim(max(corrected_depth), 0)
        xlim_max = max(corrected_qsbc_lines[0].ave)
        for line in corrected_qsbc_lines:
            xlim_max = max(xlim_max, max(line.ave))
        xlim_max = max(xlim_max, max(qdyn[start:end+1])/1000)
        ax[1].set_xlim(0, xlim_max)
        
        # plot the corrected QSBC lines
        k_line_labels = ['QSBC(av) k = 1.0 & 1.5', 'QSBC(av) k = 0.2 & 0.4']
        beta_line_labels = ['QSBC(av) β = 0.035 & 0.085']
        for i in range(0, len(corrected_qsbc_lines)):
            if correction_type != 3:
                line_label = k_line_labels[i]
            else:
                line_label = beta_line_labels[i]
            ax[1].plot(corrected_qsbc_lines[i].ave, corrected_depth, label=line_label)
            ax[1].fill_betweenx(corrected_depth, corrected_qsbc_lines[i].low, corrected_qsbc_lines[i].high, color='grey', alpha=0.3)
        
        #plot the dynamic bearing capacity
        ax[1].plot(qdyn[start:end+1]/1000, corrected_depth, label='Qdyn')
        _, unique_indices = np.unique(corrected_depth_midpoints, return_index=True)
        unique_indices = np.sort(unique_indices)
        ax[1].plot(averaged_qdyn[start:end+1][unique_indices]/1000, corrected_depth_midpoints[unique_indices], label='Qdyn average')
        
        ax[1].set_xlabel('QSBC [kPa]')
        ax[1].set_ylabel('Depth [CM]')
        ax[1].set_title('QSBC corrections & Q_dynamic')
        ax[1].legend(loc='upper right')

    if save_data:
        #Save area and strain-rate correction factor
        df = pd.DataFrame({"Dynamic Bearing Capacity": qdyn[start:end+1] / 1000, "Depth(CM)": corrected_depth})
        filename1 = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        df.to_csv(f'../saved_data/{get_date_folder()}/' + filename + '_' + filename1 + '.csv', index=False)

    figure_manager.display(lambda axs :plot(axs), nrows=1, ncols = 2)
    figure_manager.add_button("Save as PNG", [0.05, 0.05, 0.1, 0.05])
    # Checks and adds relative density text + what the peak is 
    rel_dens_str = ''
    check_alb_dens: bool = 0 <= albatal_rel_density <= 100
    check_alb_dens_interest_bounds: bool = 20 < albatal_rel_density < 55
    check_white_dens: bool = 0 <= white_rel_density <= 100
    if framework == 'sand':
        if check_alb_dens:
            if not check_alb_dens_interest_bounds:
                rel_dens_str += f' -- Peak Relative Density: Albatal: *{albatal_rel_density}%'
            else:
                rel_dens_str += f' -- Peak Relative Density: Albatal: {albatal_rel_density}%'
        if check_white_dens:
            rel_dens_str += f', White: {white_rel_density}%'
        else:
            rel_dens_str += f', White: ERR - NO SOLUTION'
    peak_info = "This peak is a " + f"{framework}" + rel_dens_str
    figure_manager.add_info_text(peak_info, 0.16, 0, 0.64)
    
    # input box for k value 
    figure_manager.add_text_box(f"Select a {k_or_beta} value:", [0.77, 0.05, 0.1, 0.05], 'k_value')
    figure_manager.add_button("Confirm", [0.88, 0.05, 0.1, 0.05])
    input_values = figure_manager.wait_for_valid_inputs()
    k_value = float(input_values[f"Select a {k_or_beta} value:"])
    return k_value

def display_user_selected_QSBC(figure_manager, corrected_qsbc_line, depth, depth_midpoints, qdyn, averaged_qdyn, start, end, tilt_x, tilt_y, k_value, albatal_fa, white_fa, durg_mitch_fa, do_pore, save_data, framework, correction_type, filename="corrected_qsbc"):
    corrected_depth = depth[start:end+1]*100
    corrected_depth_midpoints = depth_midpoints[start:end+1]*100
    if correction_type != 3:
        k_or_beta = "k"
    else:
        k_or_beta = "β"
    
    def plot(ax):
        #Plot the Correction averages and the dynamic on the right side of figure
        ax[0].invert_yaxis()
        ax[0].set_ylim(max(corrected_depth), 0)
        xlim_max = max(max(corrected_qsbc_line.ave), max(qdyn[start:end+1])/1000)
        ax[0].set_xlim(0, xlim_max)
        
        # plot the corrected QSBC lines
        line_label = f'QSBC(av) {k_or_beta} = {k_value}'
        ax[0].plot(corrected_qsbc_line.ave, corrected_depth, label=line_label)
        ax[0].fill_betweenx(corrected_depth, corrected_qsbc_line.low, corrected_qsbc_line.high, color='grey', alpha=0.3)
            
        
        #plot the dynamic bearing capacity
        _, unique_indices = np.unique(corrected_depth_midpoints, return_index=True)
        unique_indices = np.sort(unique_indices)
        ax[0].plot(averaged_qdyn[start:end+1][unique_indices]/1000, corrected_depth_midpoints[unique_indices], label='Qdyn average')
        
        ax[0].set_xlabel('QSBC [kPa]')
        ax[0].set_ylabel('Depth [CM]')
        ax[0].set_title('QSBC corrections & Q_dynamic')
        ax[0].legend(loc='upper right')

        # other plots here
    
    figure_manager.display(lambda axs :plot(axs), nrows=1, ncols=3)

    # adds save png button
    figure_manager.add_button("Save as PNG", [0.01, 0, 0.1, 0.05])

    # adds text box displaying user selected k
    figure_manager.add_info_text(f"User-selected value for {k_or_beta}: {k_value}", 0.01, 0.05, 0.22)

    # adds friction angle and tilt text
    tilt_text = f'Tilt x:  {tilt_x:.3f}\u00b0, Tilt y: {tilt_y:.3f}\u00b0'
    fa_text = f'Peak Friction Angle: Albatal: {albatal_fa:.1f}\u00b0, White: {white_fa:.1f}\u00b0, D/M: {durg_mitch_fa:.1f}\u00b0'
    figure_manager.add_info_text(tilt_text, 0.12, 0, 0.22)
    figure_manager.add_info_text(fa_text, 0.35, 0, 0.43)

    # adds a text box asking the user to update k, exit, or continue
    figure_manager.add_text_box("Enter a command [update k, exit, continue]:", [0.50, 0.05, 0.1, 0.05], 'command')
    figure_manager.add_button("Confirm", [0.61, 0.05, 0.1, 0.05])

    # saves user input as command var
    input_values = figure_manager.wait_for_valid_inputs()
    command = str(input_values["Enter a command [update k, exit, continue]:"])

    # checks the command and does corresponding logic
    if command == "update k":
        # adds update k text box 
        figure_manager.add_text_box(f"{k_or_beta} value:", [0.77, 0.05, 0.1, 0.05], 'k_value')
        figure_manager.add_button("Update", [0.88, 0.05, 0.1, 0.05])
        input_values = figure_manager.wait_for_valid_inputs()
        k_beta_update = float(input_values[f"{k_or_beta} value:"])
        return k_beta_update
    elif command == "exit":
        return -1
    elif command == "continue":
        return 0

#Have each field represent a portion of display to allow this to be re-used for each graph
def display_selected_peak(figure_manager, val, peak):
    """
    Displays the peak using the figure manager.
    """
    def plot(ax):
        ax.set_xlim(0, len(peak.peak) + 10)
        ax.plot(peak.peak, label='peak')
        ax.plot(peak.g2g, label ='2g')
        ax.scatter(peak.end_of_drop, peak.peak[peak.end_of_drop], marker='x', label='End of drop', color='black')
        ax.legend(loc='upper right')
        ax.set_title(f"Peak at {peak.peak_center}")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Value")
        ax.plot(val, peak.peak[val], 'rx')
    
    figure_manager.display(plot)

def display_selected_range(figure_manager, qsbc_for_k, valStart, valEnd):
    def plot(ax):
        ax.set_xlim(0, len(qsbc_for_k) + 10)
        ax.plot(qsbc_for_k, label='QSBC')
        ax.set_xlabel('Bearing Capacity')
        ax.set_ylabel('Depth')
        ax.set_title('Depth x Bearing Capacity')
        ax.legend(loc='upper right')
        ax.plot(valStart, qsbc_for_k[valStart], 'rx')
        ax.plot(valEnd, qsbc_for_k[valEnd], 'rx')
    figure_manager.display(plot)
