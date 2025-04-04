import sys
import re

def calculate_routing_percentage(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        
    # Split into individual paths
    paths = content.split('#Path')[1:]  # Skip the header
    
    for path_num, path in enumerate(paths, 1):
        # Find all CHANX and CHANY lines and extract their incremental delays
        routing_delays = re.findall(r'\|\s+\(CHAN[XY]:.+?\s+([0-9]+\.[0-9]+)', path)
        # total_routing_delay = sum(float(delay) for _, delay in routing_delays)
        total_routing_delay = sum(float(delay) for delay in routing_delays)
        
        # Find slack value
        slack_match = re.search(r'slack \(VIOLATED\).*?(-[0-9]+\.[0-9]+)', path)
        if slack_match:
            slack = abs(float(slack_match.group(1)))
            routing_percentage = (total_routing_delay / slack) * 100
            print(f"Path {path_num}: {routing_percentage:.2f}% of critical path delay is due to routing")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <timing_report_file>")
        sys.exit(1)
    
    calculate_routing_percentage(sys.argv[1])