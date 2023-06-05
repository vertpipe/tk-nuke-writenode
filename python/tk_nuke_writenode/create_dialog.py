import nuke
import nukescripts
import re


class WriteNodePanel(nukescripts.PythonPanel):
    def __init__(
        self, default_mode, types, main_category_name, main_write_name
    ):
        """Panel to create ShotGrid write node

        Args:
            default_mode (str): default mode to select when the panel is opened
            types (dict): containing all possible write nodes
            main_category_name (str): category name for the main output
            main_write_name (str): name for the main write node
        """
        nukescripts.PythonPanel.__init__(self, "Create SG Write Node")

        # Get variables
        self.main_category_name = main_category_name
        self.main_write_name = main_write_name

        self.types = types

        # Create knobs
        self.output_knob = nuke.String_Knob("output", "output", "")
        self.error_knob = nuke.Text_Knob(
            "errorMessage", " ", '<p style="color:#FFA500">Invalid name</p>'
        )
        self.divider1 = nuke.Text_Knob("divider1", "")
        self.category_knob = nuke.Enumeration_Knob(
            "mode", "mode", list(types.keys())
        )
        self.data_knob = nuke.Enumeration_Knob("data", "data", [])
        self.divider2 = nuke.Text_Knob("divider2", "")

        # Add knobs
        knobs = [
            self.output_knob,
            self.error_knob,
            self.divider1,
            self.category_knob,
            self.data_knob,
            self.divider2,
        ]
        for knob in knobs:
            self.addKnob(knob)

        # Set default values
        self.category_knob.setValue(default_mode)
        data_modes = types.get(default_mode)
        self.data_knob.setValues(data_modes)
        self.error_knob.setVisible(False)

        # Set tooltips
        self.output_knob.setTooltip("Set the output name for the render node.")
        self.category_knob.setTooltip(
            "Select the category to set the render node to."
        )
        self.data_knob.setTooltip("Set the data type to render.")

    def knobChanged(self, knob):
        """This function is called whenever any knob changes

        Args:
            knob (attribute): knob that has been changed
        """

        # If mode changes, we need to change datatype knob
        if knob.name() == "mode":

            # If it is the main category, we need to disable
            # changing of the name
            if knob.value() == self.main_category_name:
                self.output_knob.setValue(self.main_write_name)
                self.output_knob.setEnabled(False)
                self.data_knob.setEnabled(False)

            else:
                # Erase if main name was set by main category
                if self.output_knob.value() == "main":
                    self.output_knob.setValue("")

                # Allow changing again
                self.output_knob.setEnabled(True)
                self.data_knob.setEnabled(True)

            # Set corresponding data modes
            data_modes = self.types.get(knob.value())
            self.data_knob.setValues(data_modes)
            self.data_knob.setValue(data_modes[0])

        # Do a regex check whenever the output name is mad
        if knob.name() == "output":
            regex = re.compile(r"[a-zA-Z0-9]*$")
            regex_match = regex.match(self.output_knob.value())

            # Only set this knob visible if regex doesn't match
            self.error_knob.setVisible(not regex_match)
