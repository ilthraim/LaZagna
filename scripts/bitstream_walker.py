def process_binary_string():
    # Get initial binary string
    current_string = "1010"
    
    # Validate input
    if not all(c in '01' for c in current_string):
        print("Invalid input. Please use only 1s and 0s.")
        return
    
    # Store original string
    original_string = current_string
    
    while True:
        try:
            # Get user input
            user_input = input(f"Current string: {current_string if current_string != original_string else '' }\nEnter indices (space-separated) or -1 to reset: ")
            
            # Check for reset condition
            if user_input == "-1":
                current_string = original_string
                continue
            
            # Parse indices
            start, end = map(int, user_input.split())
            
            # Validate indices
            if start < 0 or end > len(current_string) or start >= end:
                print("Invalid indices. Please try again.")
                continue
            
            # Update current string based on indices
            current_string = current_string[start:end + 1]
            print(f"Output: {current_string}")
            
        except ValueError:
            print("Invalid input format. Please enter two space-separated numbers or -1.")
        except KeyboardInterrupt:
            print("\nExiting program.")
            break

if __name__ == "__main__":
    process_binary_string()