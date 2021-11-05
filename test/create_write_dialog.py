import nukescripts
import nuke

types = {
    "main": ["exr (dwaa 16bit)"],
    "prerender": ["exr (zip 16bit)", "exr (zip 32bit)", "exr (dwaa 16bit)"],
    "mattepainting": ["tiff (deflate 16bit)"],
}

default_mode = "prerender"


class WriteNodePanel(nukescripts.PythonPanel):
    def __init__(self, default_mode, types):
        nukescripts.PythonPanel.__init__(self, "Create SG writenode")

        # Create knobs
        self.output_knob = nuke.String_Knob("output", "output", "")
        self.error_knob = nuke.Text_Knob("", "example message")
        self.divider1 = nuke.Text_Knob("divider1", "")
        self.mode_knob = nuke.Enumeration_Knob("mode", "mode", list(types.keys()))
        self.data_knob = nuke.Enumeration_Knob("data", "data", [])
        self.divider2 = nuke.Text_Knob("divider2", "")

        # Add knobs
        knobs = [self.output_knob, self.error_knob, self.divider1, self.mode_knob, self.data_knob, self.divider2]
        for knob in knobs:
            self.addKnob(knob)

        # Set default values
        self.mode_knob.setValue(default_mode)
        data_modes = types.get(default_mode)
        self.data_knob.setValues(data_modes)

        # Set tooltips
        self.output_knob.setTooltip('Set the output name for the render node.')
        self.mode_knob.setTooltip('Select the mode to set the render node to.')
        self.data_knob.setTooltip('Set the data type to render.')


    def knobChanged(self, knob):
        if knob.name() == 'mode':
            if knob.value() == 'main':
                self.output_knob.setValue('main')
                self.output_knob.setEnabled(False)
                self.data_knob.setEnabled(False)
            else:
                if self.output_knob.value() == 'main':
                    self.output_knob.setValue('')

                self.output_knob.setEnabled(True)
                self.data_knob.setEnabled(True)
            data_modes = types.get(knob.value())
            self.data_knob.setValues(data_modes)
            self.data_knob.setValue(data_modes[0])



write_node_data = WriteNodePanel(default_mode, types)
write_node_data.setMinimumSize(200, 50)
if write_node_data.showModalDialog():
    output_name = write_node_data.output_knob.value()
    mode = write_node_data.mode_knob.value()
    data_type = write_node_data.data_knob.value()

