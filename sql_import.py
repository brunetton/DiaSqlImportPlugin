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
            radio1 = gtk.RadioButton(None, "Import all {} tables".format(len(tables_names)))
            radio2 = gtk.RadioButton(radio1, "Select tables to be imported")
            dialog.vbox.pack_start(radio1, expand=False, fill=False, padding=5)
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

            # Let it scrollable
            scroll = gtk.ScrolledWindow()
            scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scroll.add(treeview)
            # Add it to frame
            # frame_vBox.pack_start(scroll, expand=False, fill=False, padding=5)
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

def test_callback(data, flags):
    dia.message(0, "Hello, coucou !\n")
    log("test")

def import_callback(data, flags):
    try:
        Gui()
    except ImportError:
        dia.message(2, "Dialog creation failed. Missing pygtk ?")

if __name__ == "__main__":
    # Test gui display
    pygtk.require('2.0')
    Gui()
    gtk.main()
else:
    import dia
    dia.register_callback("-- test --", "<Display>/Tools/Test", test_callback)
    dia.register_callback("- Sql Import -", "<Display>/Tools/SqlImport", import_callback)
