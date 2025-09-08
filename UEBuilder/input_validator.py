import UEBuilder.ui as ui

YES_VALUES = ['y', 'yes', 'ok']
COOK_VALID_VALUES = [1, 2, 3, 4]
CONFIG_VALID_VALUES = [1, 2, 3, 4]

def is_selected_option_valid(input, valid_values):
    try:
        val = int(input)
        if val in valid_values:
            return True
        else:
            ui.print_error("invalid value entered")
            return False
    except ValueError:
        ui.print_error("non-integer value entered")
        return False

def did_user_select_yes(input):
    return input.lower() in YES_VALUES