

def adjust_options(message = None, default_names = None, default_values = None):
    import Rhino

    # Initialize default values for the options
    collected_values = default_values

    # Create an instance of GetOption
    go = Rhino.Input.Custom.GetOption()
    go.SetCommandPrompt(message)
    option_numbers = []
    # Add options with default values
    for i,l in zip(default_names,default_values):
        option_number = Rhino.Input.Custom.OptionDouble(l)
        option_numbers.append(option_number)
        go.AddOptionDouble(i, option_number)

    # Get the result from the user input
    while True:
        get_result = go.Get()

        if get_result == Rhino.Input.GetResult.Option:
            collected_values = []
            for i in option_numbers:
                collected_values.append(i.CurrentValue)
            pairs = [f'{name}: {value}' for name, value in zip(default_names, collected_values)]
            print(', '.join(pairs))
            continue  # This will continue to show the options until the user cancels

        break  # Exit the loop if the user cancels or closes the options dialog
    return collected_values


p1 = problem.gravity()
p2 = problem.displacement()

p1_values = problem.analyse(p1) # elements attributes -> interactions dictionary
p2_values = problem.analyse(p2)
