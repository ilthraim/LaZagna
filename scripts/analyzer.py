import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
from matplotlib.patches import FancyBboxPatch
import os

def plot_bar_with_gradient(csv_file, name_index=0, value_index=2, output_file="average_net_length_2d.png"):
    """
    Plots a bar chart with gradient coloring based on values from a CSV file.

    Parameters:
    - csv_file: str, path to the CSV file.
    - name_index: int, index of the column to use for names (default is 0).
    - value_index: int, index of the column to use for values (default is 2).
    - output_file: str, path to save the output plot image (default is 'average_net_length_2d.png').
    """
    # Read the CSV file
    data = pd.read_csv(csv_file)

    # Extract columns
    names = data.iloc[:-2, name_index]
    values = data.iloc[:-2, value_index]

    # Normalize the values to a range of 0.1 - 0.9 for the color gradient
    normalized_values = ((values - values.min()) / (values.max() - values.min())* 0.6) + 0.2

    # Generate colors: green (low) to red (high) using RGB interpolation
    colors = [(0.5 + v * 0.5, v * 0.647, 0.5 - v * 0.5)for v in normalized_values]

    # Create the bar plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, values, color=colors)

    average_value = values.mean()

    plt.axhline(y=average_value, color='blue', linestyle='--', linewidth=1.5, label=f'Average: {average_value:.2f}')


    # Add labels and title
    plt.xlabel("Names")
    plt.ylabel("Values")
    plt.title("Bar Plot with Gradient Coloring")

    # Rotate x-axis labels if they are too crowded
    plt.xticks(rotation=45, ha="right")

    # Add text on top of each bar
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # X-coordinate of the bar's center
            bar.get_height(),  # Y-coordinate just above the bar
            f"{value:.2f}",  # Format value with 2 decimal places
            ha="center", va="bottom", fontsize=10, color="black"
        )

    plt.legend(loc='upper left')

    # Save the plot to a file
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # Save the plot with high resolution
    plt.close()  # Close the plot to free up memory

    print(f"Plot saved to {output_file}")

def cartoony_plot_bar_with_gradient(csv_file, name_index=0, value_index=2, plot_title="Average Net Length", x_label="Names", y_label="Values", output_file="average_net_length_2d.png", include_bar_text=True):
    """
    Plots a bar chart with gradient coloring from purple to orange based on values from a CSV file and adds a horizontal line for the average.

    Parameters:
    - csv_file: str, path to the CSV file.
    - name_index: int, index of the column to use for names (default is 0).
    - value_index: int, index of the column to use for values (default is 2).
    - output_file: str, path to save the output plot image (default is 'average_net_length_2d.png').
    """
    # Use a more casual style
    plt.style.use('seaborn-v0_8-pastel')

    # Read the CSV file
    data = pd.read_csv(csv_file)
    data.sort_values(by='name', inplace=True)
    # Extract columns
    names = data.iloc[:, name_index]
    values = data.iloc[:, value_index]

    # Calculate the average value
    average_value = values.mean()

    # Normalize the values to a range of 0.1 - 0.9 for the color gradient
    normalized_values = ((values - values.min()) / (values.max() - values.min()) * 0.7) + 0.2

    # Generate colors: purple (low) to orange (high) using RGB interpolation
    colors = [(0.5 + v * 0.5, v * 0.647, 0.5 - v * 0.5) for v in normalized_values]

    # Create the bar plot
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(names, values, color=colors, edgecolor='black', linewidth=2, zorder=3)

    # Add a horizontal line for the average value
    ax.axhline(y=average_value, color='red', linestyle='--', linewidth=4, label=f'Average: {average_value:.2f}', zorder=4)
    # ax.plot([0, len(names) - 1], [average_value, average_value], color='blue', linestyle='--', linewidth=1.5, marker='o', markersize=5, label=f'Average: {average_value:.2f}', zorder=4)

    # Add labels and title with a casual font
    plt.xlabel(x_label, fontsize=14, fontname='Roboto Condensed', fontweight='bold')
    plt.ylabel(y_label, fontsize=14, fontname='Roboto Condensed', fontweight='bold')
    plt.title(plot_title, fontsize=16, fontname='Roboto Condensed', fontweight='bold')

    # Rotate x-axis labels if they are too crowded
    plt.xticks(rotation=45, ha="right", fontsize=12, fontname='Roboto Condensed')

    # Add text on top of each bar
    if include_bar_text:
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,  # X-coordinate of the bar's center
                bar.get_height(),  # Y-coordinate just above the bar
                f"{value:.2f}",  # Format value with 2 decimal places
                ha="center", va="bottom", fontsize=10, color="black", fontweight='bold' 
            )

    # Add legend
    # ax.legend(loc='upper right', fontsize=12, frameon=False)

    # Add a shadow effect
    for bar in bars:
        shadow = FancyBboxPatch((bar.get_x(), 0), bar.get_width(), bar.get_height(),
                                boxstyle="round,pad=0.1", linewidth=0, facecolor='gray', alpha=0.3, zorder=2)
        ax.add_patch(shadow)

    # Save the plot to a file
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # Save the plot with high resolution
    plt.close()  # Close the plot to free up memory

    print(f"Plot saved to {output_file}")

def plot_grouped_bars(names, values_list, labels_list, x_label="Names", y_label="Values", plot_title="Average Net Length", output_file="grouped_bar_plot.png"):
    plt.style.use('seaborn-v0_8-pastel')

    # Define the number of groups and the width of the bars
    num_groups = len(values_list)
    gap = 0.5
    x = np.arange(len(names)) * (1 + gap)  # the label locations
    width = 1 / num_groups  # Adjust width based on number of groups

    max_y = max(max(values) for values in values_list) * 1.2 # Adding 10% padding to the maximum value

    # Create the bar plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # print(x)

    # Adjusted background colors for each group
    for i in range(len(names)):
        background_color = 'white' if i % 2 == 0 else '#a9a9a9'  # Alternating light grey and white
        if i == 0:
            left_edge = x[i]
        else:
            left_edge = x[i] - ((width * num_groups) /2) - (gap / 2) - 0.1
        right_edge = x[i] + ((width * num_groups) / 2) + (gap / 2) - 0.1

        # print(left_edge, right_edge)

        ax.axvspan(left_edge, right_edge, facecolor=background_color, zorder=0)

    # Add background colors for each group
    for i in range(num_groups):
        # Set background color
        # background_color = 'white' if i % 2 == 0 else 'grey'
        # ax.axvspan(i - 0.5, i + 0.5, facecolor=background_color, zorder=0)

        # Create bars for each group
        bars = ax.bar(x + (i - num_groups / 2) * width, values_list[i], width, label=labels_list[i], edgecolor='black', linewidth=2, zorder=3)

        # Add shadow effect
        for bar in bars:
            shadow = FancyBboxPatch((bar.get_x(), 0), bar.get_width(), bar.get_height(),
                                    boxstyle="round,pad=0.1", linewidth=0, facecolor='gray', alpha=0.3, zorder=2)
            ax.add_patch(bar)

    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'cyan', 'magenta', 'yellow']

    # Add a horizontal line for the average value for each group and write the value to a CSV file
    for i in range(len(values_list)):
        average_value = np.mean(values_list[i])
        ax.axhline(y=average_value, color=colors[i % len(colors)], linestyle='--', linewidth=4, label=f'{labels_list[i]} Average: {average_value:.2f}', zorder=4)

    # Write the average values to a CSV file
    with open(plot_title + 'average_values.csv', 'w') as f:
        f.write('Label,Average\n')
        for i in range(len(values_list)):
            average_value = np.mean(values_list[i])
            f.write(f'{labels_list[i]},{average_value:.2f}\n')

        # Sort the values based on the average value in the CSV file
        f.write('Sorted by Average\n\n')
        sorted_values = sorted(zip(labels_list, [np.mean(values) for values in values_list]), key=lambda x: x[1])
        for label, value in sorted_values:
            f.write(f'{label},{value:.2f}\n')



    ax.set_ylim(0, max_y)

    # Add labels and title with a casual font
    plt.xlabel(x_label, fontsize=14, fontname='Roboto Condensed', fontweight='bold')
    plt.ylabel(y_label, fontsize=14, fontname='Roboto Condensed', fontweight='bold')
    plt.title(plot_title, fontsize=16, fontname='Roboto Condensed', fontweight='bold')

    # Rotate x-axis labels if they are too crowded
    plt.xticks(x, names, rotation=45, ha="right", fontsize=12, fontname='Roboto Condensed')

    # Add legend
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=12, frameon=False)

    # Save the plot to a file
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)  # Save the plot with high resolution
    plt.close()  # Close the plot to free up memory

    print(f"Plot saved to {output_file}")

def extract_unique_parts(strings):
    # Split each string into components based on '_'
    split_strings = [s.split('_') for s in strings]
    
    # Find the common prefix
    prefix_len = 0
    for i in range(len(split_strings[0])):
        if all(s[i] == split_strings[0][i] for s in split_strings):
            prefix_len += 1
        else:
            break
    
    # Find the common suffix
    suffix_len = 0
    for i in range(1, len(split_strings[0]) + 1):
        if all(s[-i] == split_strings[0][-i] for s in split_strings):
            suffix_len += 1
        else:
            break
    
    # Extract the unique middle part for each string
    unique_parts = [
        "_".join(s[prefix_len:len(s) - suffix_len]) for s in split_strings
    ]
    return [part.replace("_", " ") for part in unique_parts]  # Convert underscores to spaces

def create_grouped_csvs(original_path):

    results_dir = os.path.abspath(os.path.join(original_path, "..", "results"))

    print("results_dir", results_dir)

    for dirpath, dirnames, filenames in os.walk(results_dir):
        folder_name = os.path.basename(dirpath)
        
        if folder_name in ["results_csvs", "pngs"]:
            continue

        print(dirpath)
        command = ["python3", os.path.abspath(os.path.join(original_path, "csv_grouper.py")), dirpath]

        os.system(" ".join(command))

def main():
    rcParams['font.family'] = 'Roboto Condensed'

    results_paths = []

    original_path = os.path.dirname(os.path.abspath(__file__))

    create_grouped_csvs(original_path)

    return

    datas = []
    labels = []

    csvs_path = os.path.abspath(os.path.join(original_path, "..", "results", "results_csvs"))

    for path in os.listdir(csvs_path):
        if path.endswith(".csv"):
            results_paths.append(f"{csvs_path}/{path}")

    #get basename

    os.makedirs("./pngs", exist_ok=True)

    for path in results_paths:
        # cartoony_plot_bar_with_gradient(path, name_index=0, value_index=2, output_file=f"pngs/{os.path.basename(path)}_average_net_length.png", plot_title="Average Net Length", x_label="Benchmark Name", y_label="")
        # cartoony_plot_bar_with_gradient(path, name_index=0, value_index=12, output_file=f"pngs/{os.path.basename(path)}_total_wire_length.png", plot_title="Total Wire Length", x_label="Benchmark Name", y_label="")

        datas.append(pd.read_csv(path))
        labels.append(path)

    #     print(f"Plots saved for {path}")

    labels = extract_unique_parts(labels)

    #reorder each data frame to match the order of the names
    for data in datas:
        data.sort_values(by='name', inplace=True)

    # Initialize a dictionary to hold the data
    data_dict = {}

    # Populate the dictionary with data for each label
    for i, label in enumerate(labels):
        # Extract the values for each metric based on name
        names = datas[i].iloc[:, 0].tolist()
        average_net_length_values = datas[i].iloc[:, 2].tolist()
        total_wire_length_values = datas[i].iloc[:, 12].tolist()
        total_time_values = datas[i].iloc[:, 1].tolist()
        
        # Store the data in the dictionary
        data_dict[label] = [names, average_net_length_values, total_wire_length_values, total_time_values]

    # Now decide which labels and data to use for plotting based on some condition
    selected_labels = []
    selected_average_net_length_values = []
    selected_total_wire_length_values = []
    selected_total_time_values = []
    selected_names = []

    for label, data in data_dict.items():
        names, average_net_length_values, total_wire_length_values, total_time_values = data
        print(label)
        # Example condition: Modify this according to your needs
        if True:  # Only select data with certain string in the label
            if selected_names == []:
                selected_names = names
            print(label, "selected")
            selected_labels.append(label)
            selected_average_net_length_values.append(average_net_length_values)
            selected_total_wire_length_values.append(total_wire_length_values)
            selected_total_time_values.append(total_time_values)

    print(selected_names)
    print(selected_labels)
    print(selected_average_net_length_values)
    print(selected_total_wire_length_values)
    print(selected_total_time_values)

    plot_grouped_bars(selected_names, values_list=selected_average_net_length_values, labels_list=selected_labels, output_file="average_net_length_compare.png", plot_title="Average Net Length Comparison", x_label="Benchmark Name", y_label="")
    plot_grouped_bars(selected_names, values_list=selected_total_wire_length_values, labels_list=selected_labels, output_file="total_wire_length_compare.png", plot_title="Total Wire Length Comparison", x_label="Benchmark Name", y_label="")
    plot_grouped_bars(selected_names, values_list=selected_total_time_values, labels_list=selected_labels, output_file="total_time_compare.png", plot_title="Total Time Comparison", x_label="Benchmark Name", y_label="Total Time (s)")


    time_values = []
    wire_length_values = []
    average_net_values = []

    # print the mean for each label in each selected data
    for label, data in data_dict.items():
        names, average_net_length_values, total_wire_length_values, total_time_values = data

        cur_time_values = []
        cur_wire_length_values = []
        cur_average_net_length_values = []

        if label in selected_labels:
            cur_average_net_length_values.append(np.float64(np.mean(average_net_length_values)))
            cur_wire_length_values.append(np.mean(total_wire_length_values))
            cur_time_values.append(np.mean(total_time_values))

            time_values.append(cur_time_values)
            wire_length_values.append(cur_wire_length_values)
            average_net_values.append(cur_average_net_length_values)

    #plot the average net length for each selected data

    time_label = ["Total Time"]
    wire_length_label = ["Total Wire Length"]
    average_net_length_label = ["Average Net Length"]

    print(time_values)
    print(wire_length_values)
    print(average_net_values)


    plot_grouped_bars(time_label, values_list=time_values, labels_list=selected_labels, output_file="time_mean_compare.png", plot_title="Total Time Comparison", x_label="Benchmark Name", y_label="Total Time (s)")
    plot_grouped_bars(wire_length_label, values_list=wire_length_values, labels_list=selected_labels, output_file="wire_length_mean_compare.png", plot_title="Total Wire Length Comparison", x_label="Benchmark Name", y_label="")
    plot_grouped_bars(average_net_length_label, values_list=average_net_values, labels_list=selected_labels, output_file="average_net_length_mean_compare.png", plot_title="Average Net Length Comparison", x_label="Benchmark Name", y_label="")

if __name__ == "__main__":
    main()
# plot the average net length for each selected data
