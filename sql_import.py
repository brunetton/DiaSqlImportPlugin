# -*- coding: utf-8 -*-

###
#
#  Dia plugin to selectively import PostgreSql tables to a Dia schema.
#  https://github.com/brunetton/DiaSqlImportPlugin
#
#  Inspired from the work of Chris Daley for his postgres.py plugin
#
###

import math
import gtk
import pygtk
import sqlalchemy


class Gui:

    def __init__(self):
        self.connection = None
        self.connection_dialog = None
        self.import_dialog = None
        self.show_connection_dialog()

        # DEBUG
        # self.connection = db_connect("postgres://webserver:webserver@localhost:5432/test")
        # self.show_import_dialog(get_tables_names(self.connection))

    def main(self):
        if self.connection:
            self.connection_dialog.destroy()
            # self.connection_dialog.hide()
            tables_names = get_tables_names(self.connection)
            self.show_import_dialog(tables_names)
        else:
            self.show_connection_dialog()

    def show_connection_dialog(self):
        if self.connection_dialog:
            return
        else:
            # Create self.connection_dialog
            dialog = gtk.Dialog(title='DB import')
            dialog.set_border_width(10)
            dialog.connect("delete_event", lambda w,e: self.connection_dialog.destroy())

            # Connection frame
            frame = gtk.Frame(label='DB Connection')
            vbox = gtk.VBox(spacing=5)
            ## label and entry
            hbox = gtk.HBox(spacing=5)
            ### label
            elem = gtk.Label('Database url')
            hbox.pack_start(elem, expand=False, fill=False, padding=5)
            ### entry
            elem = gtk.Entry()
            elem. set_width_chars(50)
            self.db_connection_string_widget = elem
            hbox.pack_start(elem, expand=False, fill=False, padding=5)
            ### pack
            vbox.pack_start(hbox, expand=False, fill=False, padding=5)
            ## help message
            elem = gtk.Label("Example: postgres://user:password@localhost:5432/mydb\n(look at Sqlalchemy's database-urls for more details)")
            elem.set_selectable(True)
            elem.set_can_focus(False)
            vbox.pack_start(elem, expand=False, fill=False, padding=5)

            # Finaly
            frame.add(vbox)
            dialog.vbox.pack_start(frame, expand=False, fill=False, padding=5)

            # Buttons
            button = gtk.Button(stock=gtk.STOCK_CLOSE)
            button.connect("clicked", lambda w: gtk.main_quit())
            dialog.action_area.pack_end(button, expand=False, fill=False, padding=5)
            button = gtk.Button('_Connection')
            button.connect("clicked", self.on_connect_clicked)
            dialog.action_area.pack_end(button, expand=False, fill=False, padding=5)

            dialog.show_all()
            self.connection_dialog = dialog

    def on_connect_clicked(self, widget):
        # self.connection_dialog.hide()
        self.connection = db_connect(self.db_connection_string_widget.get_text())
        # dia.message(2, "show_connection_dialog")
        self.main()

    def show_import_dialog(self, tables_names):
        if self.import_dialog:
            return
        else:
            # Create self.import_dialog
            dialog = gtk.Dialog(title='Tables options')
            dialog.set_border_width(10)
            dialog.set_default_size(500, 400)
            dialog.connect("delete_event", lambda w,e: dialog.destroy())

            # Radios
            self.import_all_radio = gtk.RadioButton(None, "Import all {} tables".format(len(tables_names)))
            radio2 = gtk.RadioButton(self.import_all_radio, "Select tables to be imported")
            dialog.vbox.pack_start(self.import_all_radio, expand=False, fill=False, padding=5)
            dialog.vbox.pack_start(radio2, expand=False, fill=False, padding=5)
            # Synchronize toggle state with "sensitive" state of treeview
            radio2.connect('toggled', lambda w: self.toggle_frame.set_sensitive(w.get_active()))
            self.tables_filter_toggle = radio2

            # Frame containing tables list and bottom toggle
            frame = gtk.Frame()
            frame_vBox = gtk.VBox()
            frame.add(frame_vBox)
            # Tabels list
            model = gtk.ListStore(str, bool)
            self.model = model
            # Add tables names to model
            for e in get_tables_names(self.connection):
                model.append([e, True])
            treeview = gtk.TreeView(model=model)
            column = gtk.TreeViewColumn("Table", gtk.CellRendererText(), text=0)
            column.set_expand(True)
            column.set_sort_column_id(0)
            treeview.append_column(column)
            cell = gtk.CellRendererToggle()
            cell.connect("toggled", self.on_cell_toggled, model)  # When clicked, reflect click on model
            column = gtk.TreeViewColumn("Import", cell, active=1)
            treeview.append_column(column)
            treeview.connect('key-press-event', self.on_treeview_keypress)

            # Let it scrollable
            scroll = gtk.ScrolledWindow()
            scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scroll.add(treeview)
            # Pack
            frame_vBox.pack_start(scroll, expand=True, fill=True, padding=5)

            # "check/uncheck all" checkbox
            checkbox = gtk.CheckButton("Check/uncheck all")
            checkbox.connect("toggled", self.on_bottom_check_toggled)
            frame_vBox.pack_start(checkbox, expand=False, fill=False, padding=0)

            # Pack
            dialog.vbox.pack_start(frame, expand=True, fill=True, padding=5)

            # Buttons
            button = gtk.Button(stock=gtk.STOCK_OK)
            button.connect("clicked", self.on_ok_clicked)
            dialog.action_area.pack_end(button, expand=False, fill=False, padding=5)

            # Finaly
            self.toggle_frame = frame
            self.toggle_frame.set_sensitive(False)
            dialog.show_all()
            self.import_dialog = dialog

    def on_cell_toggled(self, cell, path, model, *ignore):
        self.model[path][1] = not self.model[path][1]

    def on_bottom_check_toggled(self, widget, data=None):
        state = widget.get_active()
        for e in self.model:
            e[1] = state

    def on_treeview_keypress(self, widget, ev, data=None):
        if ev.state == 0:  # No modifiers
            if ev.keyval in [gtk.gdk.keyval_from_name('Return'), gtk.gdk.keyval_from_name('space')]:
                path = widget.get_selection().get_selected_rows()[1][0]
                self.model[path][1] = not self.model[path][1]

    def on_ok_clicked(self, widget):
        # Final step
        if not self.import_all_radio.get_active():
            selected_tables = []
            self.model.foreach(
                lambda model, path, iter:
                    selected_tables.append(model[path][0]) if model[path][1] else None
            )
            if len(selected_tables) == 0:
                error_message('No tables selected. Select at least one table in order to begin.')
                return
        else:
            selected_tables = []
            self.model.foreach(lambda model, path, iter: selected_tables.append(model[path][0]))  # There should be a more Pythonic way to write it
        self.import_dialog.destroy()
        generate_diagram(self.connection, selected_tables)


class DiaSchema :

    def __init__(self):
        self.diagram = dia.active_display().diagram
        self.active_layer = self.diagram.data.active_layer
        self.active_layer

    def addTable(self, table_name, columns):
        oType = dia.get_object_type("UML - Class")
        o, h1, h2 = oType.create (0,0)  # New UML class object
        o.properties["name"] = table_name
        o.properties["visible_operations"] = False  # No operations for now
        attributes = []
        for name in columns :
            attributes.append((name, '', '', '', 0, 0, 0))   # (name,type,value,comment,visibility,abstract,class_scope)
        o.properties["attributes"] = attributes
        self.active_layer.add_object(o)

    # Directely copied from Chris Daley's postgres.py plugin
    def distribute_objects(self):
        width = 0.0
        height = 0.0
        for o in self.active_layer.objects :
            if str(o.type) != "UML - Constraint" :
                if width < o.properties["elem_width"].value :
                    width = o.properties["elem_width"].value
                if height < o.properties["elem_height"].value :
                    height = o.properties["elem_height"].value
        # add 20 % 'distance'
        width *= 1.2
        height *= 1.2
        area = len (self.active_layer.objects) * width * height
        max_width = math.sqrt (area)
        x = 0.0
        y = 0.0
        dy = 0.0 # used to pack small objects more tightly
        for o in self.active_layer.objects :
            if str(o.type) != "UML - Constraint" :
                if dy + o.properties["elem_height"].value * 1.2 > height :
                    x += width
                    dy = 0.0
                if x > max_width :
                    x = 0.0
                    y += height
                o.move (x, y + dy)
                dy += (o.properties["elem_height"].value * 1.2)
                if dy > .75 * height :
                    x += width
                    dy = 0.0
                if x > max_width :
                    x = 0.0
                    y += height
                self.diagram.update_connections(o)

    # Finalize diagram
    def finalize(self) :
        self.distribute_objects()
        if self.diagram:
            self.diagram.update_extents()
            dia.active_display().scroll(-1, -1)  # To make diagram displayed on screen


def error_message(message):
    msgbox = gtk.MessageDialog(
        type=gtk.DIALOG_MODAL,
        buttons=gtk.BUTTONS_CLOSE,
        message_format=message
    )
    msgbox.run()
    msgbox.destroy()

# Try to connect with given connection string; display an error message if connection problem.
# Return True if connected
def db_connect(connection_string):
    try:
        db = sqlalchemy.create_engine(connection_string)
        db.connect()
    except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.ArgumentError) as e:
        error_message("Error connecting to DB:\n{}".format(e.message))
        return False
    return db

# Return an array containing tables names
def get_tables_names(connection):
    result = connection.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")
    return [e[0] for e in result.fetchall()]

# Return an array of columns names for given table name
def get_columns_names(connection, table_name):
    result = connection.execute("SELECT column_name FROM information_schema.columns WHERE table_name='{}'".format(table_name))
    return [e[0] for e in result.fetchall()]

def test_callback(data, flags):
    generate_diagram(['table1'])

def import_callback(data, flags):
    try:
        Gui()
    except ImportError:
        dia.message(2, "Dialog creation failed. Missing pygtk ?")

def generate_diagram(connection, tables_names):
    diagram = DiaSchema()
    for table_name in tables_names:
        columns = get_columns_names(connection, table_name)
        diagram.addTable(table_name, columns)
    diagram.finalize()

if __name__ == "__main__":
    # Test gui display
    pygtk.require('2.0')
    Gui()
    gtk.main()
else:
    import dia
    dia.register_callback("-- test --", "<Display>/Tools/Test", test_callback)
    dia.register_callback("- Sql Import -", "<Display>/Tools/SqlImport", import_callback)
