# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import nuke
import os
import re
from .create_dialog import WriteNodePanel

# standard toolkit logger
logger = sgtk.platform.get_logger(__name__)


class NukeWriteNodeHandler(object):
    """
    Main application dialog window
    """

    def __init__(self):
        self.app = sgtk.platform.current_bundle()
        self.sg = self.app.shotgun

    def render_local(self, node):
        prepared_write = self.__prepare_write(node)
        if prepared_write:
            prepared_write["Render"].execute()
        else:
            nuke.message("Something went wrong.")

    def render_farm(self, node):
        prepared_write = self.__prepare_write(node)
        if prepared_write:
            import deadlineSubmission

            submit = deadlineSubmission.main(node.name())
            if submit:
                self.__increment_save()
        else:
            nuke.message("Something went wrong.")

    def create_writenode(self):
        write_nodes = self.get_all_write_nodes()
        write_names = []
        for node in write_nodes:
            node = nuke.toNode(node)
            write_names.append(node["output"].value())

        write_node_settings = self.__get_write_node_options()

        main_category_name = self.app.get_setting("main_category_name")
        main_write_name = self.app.get_setting("main_write_name")
        default_category = self.app.get_setting("default_category")

        write_node_data = WriteNodePanel(
            default_category, write_node_settings, main_category_name, main_write_name
        )
        write_node_data.setMinimumSize(200, 190)

        if write_node_data.showModalDialog():
            output_name = write_node_data.output_knob.value()
            if not len(output_name) > 0:
                nuke.message("No name specified, please specify a name.")
                return

            if output_name in write_names:
                nuke.message("Write node %s already existing." % output_name)
                self.go_to_write_node(output_name)
                return

            regex = re.compile(r"[a-zA-Z0-9]*$")

            # Validate name
            if not regex.match(output_name):
                nuke.message(
                    "Name contains illegal characters. Please only use letters and numbers. \n[a-zA-Z0-9]"
                )
                return

            category = write_node_data.category_knob.value()

            if category != main_category_name:
                if output_name == main_write_name:
                    nuke.message(
                        "Name %s only allowed on %s category."
                        % (output_name, main_category_name)
                    )
                    return

            write_data = write_node_data.data_knob.value()

            self.__create_write(write_node_settings, category, output_name, write_data)

    def read_from_selected(self):
        node = nuke.selectedNode()
        self.read_from_write(node)

    def read_from_write(self, node):
        with nuke.root():
            render_path = node["file"].value()

            if render_path == "":
                nuke.message(
                    "This write node has not rendered yet, please render before create a read from this write node."
                )
                return

            is_published = self.get_published_status(node)

            if is_published:
                render_path = self.__get_published_path(node, render_path)

            render_directory = os.path.dirname(render_path)
            frame_sequences = self.__get_frame_sequences(render_directory)

            for frame_sequence in frame_sequences:
                sequence_path = frame_sequence[0].replace(os.sep, "/")
                if sequence_path == render_path:
                    read_node = nuke.createNode("Read")

                    read_node["file"].fromUserText(render_path)

                    start_frame = int(min(frame_sequence[1]))
                    last_frame = int(max(frame_sequence[1]))

                    read_node["first"].setValue(start_frame)
                    read_node["origfirst"].setValue(start_frame)
                    read_node["last"].setValue(last_frame)
                    read_node["origlast"].setValue(last_frame)

                    xpos = node.xpos()
                    ypos = node.ypos() + 50

                    read_node["xpos"].setValue(xpos)
                    read_node["ypos"].setValue(ypos)

    def convert_placeholder_nodes(self):
        for placeholder_node in nuke.allNodes("ModifyMetaData"):
            if placeholder_node.name().startswith("ShotGridWriteNodePlaceholder"):
                write_node_settings = self.__get_write_node_options()

                metadata = placeholder_node.metadata()
                category = metadata.get("category")
                output_name = metadata.get("output")
                data_type = metadata.get("data_type")

                # Get data to replace node
                placeholder_xpos = placeholder_node.xpos()
                placeholder_ypos = placeholder_node.ypos()
                placeholder_input = placeholder_node.input(0).name()

                nuke.delete(placeholder_node)

                write_node = self.__create_write(
                    write_node_settings, category, output_name, data_type
                )

                write_node["xpos"].setValue(placeholder_xpos)
                write_node["ypos"].setValue(placeholder_ypos)
                write_node.setInput(0, nuke.toNode(placeholder_input))

            else:
                logger.debug(
                    "No ShotGrid Write Node placeholder node found, skipping conversion."
                )

    def add_callbacks(self):
        nuke.addOnScriptLoad(self.convert_placeholder_nodes, nodeClass="Root")

    def remove_callbacks(self):
        nuke.removeOnScriptLoad(self.convert_placeholder_nodes, nodeClass="Root")

    def update_read_nodes(self):
        write_nodes = self.get_all_write_nodes()

        image_sequences = {}
        for write_node in write_nodes:
            write_node = nuke.toNode(write_node)
            render_path = write_node["file"].value()
            image_sequences[render_path] = write_node

        all_nodes = nuke.allNodes()
        for node in all_nodes:
            if node.Class() == "Read":
                read_path = node["file"].value()
                if read_path in image_sequences.keys():
                    write_node = image_sequences.get(read_path)

                    published_path = self.__get_published_path(write_node, read_path)

                    node["file"].setValue(published_path)

    @staticmethod
    def get_all_write_nodes():
        all_nodes = nuke.allNodes()
        write_nodes = []
        for node in all_nodes:
            if node.Class() == "Group":
                if node["isShotGridWriteNode"]:
                    write_nodes.append(node.name())
        return write_nodes

    @staticmethod
    def go_to_write_node(output_name):
        all_nodes = nuke.allNodes()
        for node in all_nodes:
            if node.Class() == "Group":
                if node["isShotGridWriteNode"]:
                    if node["output"].value() == output_name:
                        nuke.zoom(3, [node.xpos(), node.ypos()])

    def get_node_render_template(self, node):
        configuration = self.__get_node_settings(node)
        render_template = configuration.get("render_template")
        render_template = self.app.get_template_by_name(render_template)
        return render_template

    def get_node_publish_template(self, node):
        configuration = self.__get_node_settings(node)
        publish_template = configuration.get("publish_template")
        publish_template = self.app.get_template_by_name(publish_template)
        return publish_template

    def get_published_status(self, node):
        # This function will check on ShotGrid if there is a publish with exactly the same name on the project. If
        # there is a publish existing it will return "True", otherwise return a "False" value
        sg = self.sg

        file_name = node["file"].value()
        file_name = os.path.basename(file_name)

        # Get current project ID
        current_engine = sgtk.platform.current_engine()
        current_context = current_engine.context
        project_id = current_context.project["id"]

        # Create the filter to search on ShotGrid for publishes with the same file name
        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
            ["code", "is", file_name],
        ]

        # Search on ShotGrid
        published_file = sg.find_one("PublishedFile", filters)

        # If there is no publish, it will return a None value. So set the variable is_published to "False"
        if published_file is None:
            is_published = False
        # If the value is not None, there is a publish with the same name. So set the variable is_published to "True"
        else:
            is_published = True

        return is_published

    @staticmethod
    def get_colorspace(node):
        with node:
            write_node = nuke.toNode("Write1")
            colorspace = write_node["colorspace"].value()
            return colorspace

    def __create_write(self, write_node_settings, category, output_name, data_type):
        created_write = nuke.createNode("sgWrite")
        created_write["output"].setValue(output_name)

        categories = []
        for key, value in write_node_settings.items():
            categories.append(key)
        created_write["category"].setValues(categories)
        created_write["category"].setValue(category)

        data_types = write_node_settings.get(category)
        created_write["dataType"].setValues(data_types)
        created_write["dataType"].setValue(data_type)

        # Initial setup of internal node
        configuration = self.__get_node_settings(created_write)
        created_write["tile_color"].setValue(configuration.get("tile_color"))
        settings = configuration.get("settings")
        with created_write:
            write_node = nuke.toNode("Write1")
            write_node["file_type"].setValue(configuration.get("file_type"))
            for knob, setting in settings.items():
                try:
                    write_node[knob].setValue(setting)
                except Exception as e:
                    logger.debug(
                        "Could not apply %s to the knob %s, because %s"
                        % (setting, knob, str(e))
                    )

        return created_write

    # This function will build a dictionary containing the category name and write node names
    def __get_write_node_options(self):
        categories = self.app.get_setting("categories")
        write_node_settings = {}
        for category in categories:
            # Get category name
            category_name = category.get("category_name")

            # Get write node names
            write_nodes = category.get("write_nodes")
            write_node_names = []
            for write_node in write_nodes:
                write_node_name = write_node.get("name")
                write_node_names.append(write_node_name)

            write_node_settings[category_name] = write_node_names

        return write_node_settings

    # This function will go trough the dictionary to find the configuration dictionary requested
    def __get_node_settings(self, node):
        write_category = node["category"].value()
        data_type = node["dataType"].value()

        categories = self.app.get_setting("categories")

        for category in categories:
            if category.get("category_name") == write_category:
                for write_node in category.get("write_nodes"):
                    if write_node.get("name") == data_type:
                        return write_node

    def __calculate_path(self, node, configuration):
        render_template = configuration.get("render_template")
        render_template = self.app.get_template_by_name(render_template)
        script_template = self.app.get_template("template_script_work")

        current_file = nuke.root().name()

        fields = script_template.get_fields(current_file)

        fields["SEQ"] = "FORMAT: %d"
        fields["output"] = node["output"].value()

        render_path = render_template.apply_fields(fields).replace(os.sep, "/")

        return render_path

    def __prepare_write(self, node):
        configuration = self.__get_node_settings(node)
        if configuration:
            render_path = self.__calculate_path(node, configuration)
            settings = configuration.get("settings")

            # Now we have all the parameters necessary, lets set them
            with node:
                write_node = nuke.toNode("Write1")
                write_node["file"].setValue(render_path)
                for knob, setting in settings.items():
                    # Prevent to change the channels knob
                    if not knob == "channels":
                        write_node[knob].setValue(setting)

            # Make sure directory exists
            render_directory = os.path.dirname(render_path)
            if not os.path.isdir(render_directory):
                os.makedirs(render_directory)

            return write_node

        else:
            nuke.message(
                "Could not found configuration for node %s" % node["name"].value()
            )
            return False

    def __increment_save(self):
        script_template = self.app.get_template("template_script_work")
        script_file = nuke.root().name()

        fields = script_template.get_fields(script_file)

        fields["version"] = fields["version"] + 1

        new_script_file = script_template.apply_fields(fields).replace(os.sep, "/")

        nuke.scriptSaveAs(new_script_file)

    def __get_published_path(self, node, path):
        render_template = self.get_node_render_template(node)
        render_fields = render_template.get_fields(path)

        publish_template = self.get_node_publish_template(node)
        render_path = publish_template.apply_fields(render_fields).replace(os.sep, "/")

        return render_path

    @staticmethod
    def __get_frame_sequences(folder, extensions=None, frame_spec=None):
        #  Copied from the publisher app, and customized to return
        #  file sequences with frame lists instead of filenames
        FRAME_REGEX = re.compile(r"(.*)([._-])(\d+)\.([^.]+)$", re.IGNORECASE)

        # list of already processed file names
        processed_names = {}

        # examine the files in the folder
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if os.path.isdir(file_path):
                # ignore subfolders
                continue

            # see if there is a frame number
            frame_pattern_match = re.search(FRAME_REGEX, filename)

            if not frame_pattern_match:
                # no frame number detected. carry on.
                continue

            prefix = frame_pattern_match.group(1)
            frame_sep = frame_pattern_match.group(2)
            frame_str = frame_pattern_match.group(3)
            extension = frame_pattern_match.group(4) or ""

            # filename without a frame number.
            file_no_frame = "%s.%s" % (prefix, extension)

            if file_no_frame in processed_names:
                # already processed this sequence. add the framenumber to the list, later we can use this to
                # determine the framerange
                processed_names[file_no_frame]["frame_list"].append(frame_str)
                continue

            if extensions and extension not in extensions:
                # not one of the extensions supplied
                continue

            # make sure we maintain the same padding
            if not frame_spec:
                padding = len(frame_str)
                frame_spec = "%%0%dd" % (padding,)

            seq_filename = "%s%s%s" % (prefix, frame_sep, frame_spec)

            if extension:
                seq_filename = "%s.%s" % (seq_filename, extension)

            # build the path in the same folder
            seq_path = os.path.join(folder, seq_filename)

            # remember each seq path identified and a list of files matching the
            # seq pattern
            processed_names[file_no_frame] = {
                "sequence_path": seq_path,
                "frame_list": [frame_str],
            }

        # build the final list of sequence paths to return
        frame_sequences = []
        for file_no_frame in processed_names:
            seq_info = processed_names[file_no_frame]
            seq_path = seq_info["sequence_path"]

            frame_sequences.append((seq_path, seq_info["frame_list"]))

        return frame_sequences
