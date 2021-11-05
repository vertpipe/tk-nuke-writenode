# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


from sgtk.platform import Application
import nuke
import os


class TkNukeWriteNode(Application):
    """
    The tk_nuke_writenode entry point. This class is responsible for initializing and tearing down
    the application, handle menu registration etc.
    """

    def init_app(self):
        """
        Called as the application is being initialized
        """

        self.tk_nuke_writenode = self.import_module("tk_nuke_writenode")
        self.handler = self.tk_nuke_writenode.NukeWriteNodeHandler()

        create_write_node = lambda: self.handler.create_writenode()
        self.engine.register_command(
            "NFA ShotGrid Write Node",
            create_write_node,
            dict(
                type="node",
                icon="Write.png",
                hotkey="w",
                context=self.context,
            ),
        )

        read_from_write = lambda: self.handler.read_from_selected()
        self.engine.register_command(
            "Create Read from Write",
            read_from_write,
            dict(
                type="menu",
                icon="Read.png",
                hotkey="ctrl+r",
                context=self.context,
            ),
        )

        self.handler.add_callbacks()

    def destroy_app(self):
        self.log_debug("Destroying tk-nuke-writenode app")

        self.handler.remove_callbacks()

    def render_local(self, node):
        self.handler.render_local(node)

    def render_farm(self, node):
        self.handler.render_farm(node)

    def read_from_write(self, node):
        self.handler.read_from_write(node)

    def get_all_write_nodes(self):
        write_nodes = self.handler.get_all_write_nodes()
        return write_nodes

    def get_node_render_template(self, node):
        render_template = self.handler.get_node_render_template(node)
        return render_template

    def get_node_publish_template(self, node):
        publish_template = self.handler.get_node_publish_template(node)
        return publish_template

    def get_published_status(self, node):
        is_published = self.handler.get_published_status(node)
        return is_published

    def get_colorspace(self, node):
        colorspace = self.handler.get_colorspace(node)
        return colorspace

    def update_read_nodes(self):
        self.handler.update_read_nodes()

    def convert_placeholder_nodes(self):
        self.handler.convert_placeholder_nodes()

    @staticmethod
    def get_write_nodes():
        # Empty function for legacy reasons to reset all render paths on file save, which is not what we want :)
        return []