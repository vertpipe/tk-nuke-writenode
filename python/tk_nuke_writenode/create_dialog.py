import nuke
import nukescripts
import re


class WriteNodePanel(nukescripts.PythonPanel):
    def __init__(self, default_mode, types, main_category_name, main_write_name):
        nukescripts.PythonPanel.__init__(self, "Create SG Write Node")

        self.main_category_name = main_category_name
        self.main_write_name = main_write_name

        self.types = types

        # Create knobs
        self.output_knob = nuke.String_Knob("output", "output", "")
        self.error_knob = nuke.Text_Knob(
            "errorMessage", " ", '<p style="color:#FFA500">Invalid name</p>'
        )
        self.divider1 = nuke.Text_Knob("divider1", "")
        self.category_knob = nuke.Enumeration_Knob("mode", "mode", list(types.keys()))
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
        self.category_knob.setTooltip("Select the category to set the render node to.")
        self.data_knob.setTooltip("Set the data type to render.")

    def knobChanged(self, knob):
        if knob.name() == "mode":
            if knob.value() == self.main_category_name:
                self.output_knob.setValue(self.main_write_name)
                self.output_knob.setEnabled(False)
                self.data_knob.setEnabled(False)
            else:
                if self.output_knob.value() == "main":
                    self.output_knob.setValue("")

                self.output_knob.setEnabled(True)
                self.data_knob.setEnabled(True)
            data_modes = self.types.get(knob.value())
            self.data_knob.setValues(data_modes)
            self.data_knob.setValue(data_modes[0])

        if knob.name() == "output":
            regex = re.compile(r"[a-zA-Z0-9]*$")
            regex_match = regex.match(self.output_knob.value())
            self.error_knob.setVisible(not regex_match)
