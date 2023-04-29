import os
import json

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMenu, QSplitter, QLabel, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QIcon

from config_reader import config_reader

from core_helper import core_helper
from core_manager import core_manager
from fs_helper import fs_helper

from widgets.s_tab import s_tab
from widgets.s_single_input_dialog import s_single_input_dialog
from widgets.s_search_bar import s_file_search_bar
from widgets.s_rich_text_editor.s_rich_text_editor import s_rich_text_editor
from widgets.s_file_tree import s_file_tree
from widgets.s_file_list import s_file_list

from widgets.s_file_searcher.s_file_searcher import s_file_searcher

class s_main_window(QMainWindow):
    
    def __init__(
            self, 
            parent=None
            ):
        super(s_main_window, self).__init__(parent)
        
        self._init_dialogs_ui()
        self._init_actions_ui()

        self.hl_fpath = []
        self.dangling_fpath = []

        self.left_panel = None
        self.right_panel = None

        self.central_splitter = None

        self.file_tree = None
        self.text_editors_map = {}
        
        self.tab = None

        self.c_helper = None

        self.c_config = { 
            'user': [],
            'ds_fpath_map': { }
        }

        self.c_manager = None


    def new_project(self):
        root_dir = QFileDialog().getExistingDirectory(            
            None,
            'Select a project folder:',
            '',
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
            )

        if root_dir == '':
            return
        

        self.c_config['root_dir'] = root_dir        

        if self._prompt_project_config():
            try:
                self._dump_datasource_file(
                    self.c_config['project_name'], 
                    self.c_config['active_user'],
                    self.c_config['active_ds_fpath']
                    )    

            except Exception as e:
                self._show_config_file_create_failed_msg()
                print("Error occurred while writing data to file:", e)
                
                return 


            c_reader = config_reader(self.c_config['active_ds_fpath'])

            self.c_helper = core_helper(c_reader)

            self.text_editors_map[self.c_config['active_user']] = s_rich_text_editor()

            # Clean up previous widgets before init new widgets
            self._clean_up()

            self._init_core_ui()
            self._init_core_manager()

        else:
            self._show_config_file_create_failed_msg()
                

    def open_project(self):
        root_dir = QFileDialog().getExistingDirectory(            
            None,
            'Select a project folder:',
            '',
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
            )

        if root_dir == '':
            return
    

        self.c_config['root_dir'] = root_dir

        self.c_config['active_ds_fpath'] = QFileDialog().getOpenFileName(
            None, 
            "Open a datasource file", 
            "", 
            "JSON Files (*.json);;All Files (*)", 
            options= QFileDialog.Options() | QFileDialog.DontUseNativeDialog
            )[0]
        
        if self.c_config['active_ds_fpath'] == '':
            return
            

        c_reader = config_reader(self.c_config['active_ds_fpath'])

        if c_reader.is_valid:
            self.c_helper = core_helper(c_reader)

            self.c_config['project_name'] = c_reader.get_project_name()

            self.c_config['active_user'] = c_reader.get_user()
            self.c_config['ds_fpath_map'][self.c_config['active_user']] = self.c_config['active_ds_fpath']
            
            self.text_editors_map[self.c_config['active_user']] = s_rich_text_editor()

            # Clean up previous widgets before init new widgets    
            self._clean_up()

            self._init_core_ui()
            self._init_core_manager()

        else:
            self._show_config_file_not_valid_msg()


    def add_datasource_file(self):
        ds_fpath, _ = QFileDialog.getOpenFileName(
            None,
            "Select a JSON file",
            "",
            "JSON Files (*.json)",
            options=QFileDialog.Options() | QFileDialog.ReadOnly | QFileDialog.DontUseNativeDialog
            )

        c_reader = config_reader(ds_fpath)

        if c_reader.is_valid:
            if self.c_config['project_name'] != c_reader.get_project_name():
                self._show_missmtach_project_msg()
                return
            

            if c_reader.get_user() in self.c_config['ds_fpath_map']:
                self.text_editors_map[c_reader.get_user()].deleteLater()


            self.c_helper = core_helper(c_reader)

            self.c_config['active_ds_fpath'] = ds_fpath

            self.c_config['active_user'] = c_reader.get_user()
            self.c_config['ds_fpath_map'][self.c_config['active_user']] = self.c_config['active_ds_fpath']

            self.text_editors_map[self.c_config['active_user']] = s_rich_text_editor()

            self._update_core_ui()
            self._update_core_manager()

        else:
            self._show_config_file_not_valid_msg()


    def _init_dialogs_ui(self):
        self.dialog = s_single_input_dialog({
            'dialog_title': 'New Project',
            'dialog_var_1': 'project_name',
            'dialog_var_2': 'user',
            'dialog_var_3': 'dirpath',
            'dialog_msg_1': 'Enter a project name',
            'dialog_msg_2': 'Enter an username',
            'dialog_msg_3': 'Choose a datasource directory',
        })


    def _init_actions_ui(self):
        self.setWindowTitle('Code Meta')

        self._init_file_menu()

        self._init_new_project_action()
        self._init_open_project_action()
        self._init_add_datasource_file_action()

        self._init_auto_save_action()


    def _init_file_menu(self):
        self.file_menu = QMenu('File', self)

        self.menuBar().addMenu(self.file_menu)

    
    def _init_new_project_action(self):
        action = QAction(
            'New Project', 
            self
            )

        action.triggered.connect(self.new_project)
        self.file_menu.addAction(action)


    def _init_open_project_action(self):
        action = QAction(
            'Open Project', 
            self
            )

        action.triggered.connect(self.open_project)
        self.file_menu.addAction(action)


    def _init_add_datasource_file_action(self):
        action = QAction(
            'Add Datasource', 
            self
            )

        action.triggered.connect(self.add_datasource_file)
        self.file_menu.addAction(action)


    def _init_auto_save_action(self):
        action = QAction(
            QIcon(f"{os.environ['code_meta_dir']}/resources/check-solid.svg'"), 
            'Auto Save', 
            self
            )

        action.setCheckable(False)
        self.file_menu.addAction(action)


    def _prompt_project_config(self):
        if self.dialog.exec_() == QDialog.Accepted:
            self.c_config['project_name'] = self.dialog.get_config()['project_name']
            self.c_config['active_user'] = self.dialog.get_config()['user']

            # Generate datasource filename
            self.c_config['active_ds_fpath'] = f"{self.dialog.get_config()['dirpath']}/{self.c_config['project_name']}_{self.c_config['active_user']}_datasource.json"     

            self.c_config['ds_fpath_map'][self.c_config['active_user']] = self.c_config['active_ds_fpath']

            return True

        else:
            print("Project input dialog rejected")
            return False
        

    def _init_core_ui(self):
        self._init_left_panel()
        self._init_right_panel()

        self._init_central_widget()


    def _init_core_manager(self):
        self.c_manager = core_manager(
            self.file_tree, 
            self.file_searcher,
            self._get_active_text_editor(),
            self.c_helper
            )


    def _init_file_tree(self):
        all_fpaths = fs_helper.relativize_file_paths(
            fs_helper.get_all_filepaths(self.c_config['root_dir'])
            )

        hl_fpaths = self.c_helper.select_filepaths_with_non_empty_plain_text_note_by_filepaths_in(all_fpaths)
        
        hl_decorator = lambda item: item.setForeground(QBrush(QColor('green')))

        self.file_tree = s_file_tree(
            fs_helper.relativize_file_paths(hl_fpaths),
            hl_decorator
            )

        self.file_tree.setModel(
            self._populate_file_tree_model(self.c_config['root_dir'], self.c_config['project_name'])
            )
        self.file_tree.setMaximumWidth(300)


    def _init_file_searcher(self):
        all_fpaths = fs_helper.relativize_file_paths(
            fs_helper.get_all_filepaths(self.c_config['root_dir'])
            )

        fpaths = self.c_helper.select_filepaths_with_non_empty_plain_text_note_by_filepaths_not_in(all_fpaths)

        model = QStandardItemModel()

        for fpath in fpaths:
            item = QStandardItem(fpath)

            model.appendRow(item)


        self.search_title = QLabel('Dangling Notes')

        self.search_bar = s_file_search_bar()

        self.file_list = s_file_list(model)

        self.file_searcher = s_file_searcher(self.search_title, self.search_bar, self.file_list)


    def _init_tab(self):
        self.tab = s_tab()

        self.tab.addTab(
            self.text_editors_map[self.c_config['active_user']], 
            f"{self.c_config['active_user']}"
            )


    def _init_left_panel(self):
        self._init_file_tree()
        self._init_file_searcher()
    
        self.left_panel = QSplitter()

        self.left_panel.addWidget(self.file_tree)
        self.left_panel.addWidget(self.file_searcher)

        self.left_panel.setOrientation(Qt.Vertical)  
        self.left_panel.setSizes([600, 300])
    

    def _init_right_panel(self):
        self._init_tab()

        self.right_panel = self.tab
    

    def _get_active_text_editor(self):
        return self.text_editors_map[self.c_config['active_user']]


    def _on_tab_changed(self, index):
        # Get the tab widget that emitted the signal
        sender = self.tab.sender()
        # Get the current tab index
        current_tab_index = sender.currentIndex()

        # Get the text of the current tab
        current_tab_text = sender.tabText(current_tab_index)
        print("Clicked Tab Index:", current_tab_index)
        print("Clicked Tab Text:", current_tab_text)


    def _init_central_widget(self):
        self.central_splitter = QSplitter()

        self.central_splitter.addWidget(self.left_panel)
        self.central_splitter.addWidget(self.right_panel)

        self.setCentralWidget(self.central_splitter)
        

    def _update_core_manager(self):
        self.c_manager.update(
            self.file_tree, 
            self.file_searcher, 
            self._get_active_text_editor(), 
            self.c_helper
            )


    def _update_core_ui(self):
        self._update_tab()

        self._update_file_tree()
        self._update_file_searcher()


    def _update_tab(self):
        self.tab.upsert_widget_by_label(
            self.text_editors_map[self.c_config['active_user']], 
            self.c_config['active_user']
            )


    def _update_file_tree(self):
        all_fpaths = fs_helper.relativize_file_paths(
            fs_helper.get_all_filepaths(self.c_config['root_dir'])
            )

        hl_fpaths = self.c_helper.select_filepaths_with_non_empty_plain_text_note_by_filepaths_in(all_fpaths)

        self.file_tree.set_highlight_file_paths(
            fs_helper.relativize_file_paths(hl_fpaths)
            )


    def _update_file_searcher(self):
        all_fpaths = fs_helper.relativize_file_paths(
            fs_helper.get_all_filepaths(self.c_config['root_dir'])
            )

        fpaths = self.c_helper.select_filepaths_with_non_empty_plain_text_note_by_filepaths_not_in(all_fpaths)

        model = QStandardItemModel()

        for fpath in fpaths:
            item = QStandardItem(fpath)

            model.appendRow(item)


        self.file_list.update_model(model)

        self.file_searcher.update_file_list(self.file_list)


    def _show_config_file_existed_msg(self):
        QMessageBox.critical(
            None, 
            'Error', 
            'The selected directory already contain a configuration file.'
            )


    def _show_config_file_create_failed_msg(self):
        QMessageBox.critical(
            None, 
            'Error', 
            'Failed to create a configuration file.'
            )


    def _show_config_file_missing_msg(self):
        QMessageBox.critical(
            None, 
            'Error', 
            'The selected directory does not contain a configuration file.'
            )
        
    
    def _show_config_file_not_valid_msg(self):
        QMessageBox.critical(
            None, 
            'Error', 
            'The selected directory does not contain a valid configuration.'
            )

    def _show_missmtach_project_msg(self):
        QMessageBox.critical(
            None, 
            'Error', 
            'The selected project doesnt match existing project.'
            )


    def _clean_up(self):
        if self.central_splitter != None:
            self.central_splitter.deleteLater()

            # deleteLater() doesnt remove the reference  
            # and this removes reference manually
            self.central_splitter = None

            
    def _populate_file_tree_model(
            self, 
            root_dir,
            label
            ):
        # Special case
        root_item = QStandardItem('.')

        print(root_item.text())

        root_item.setData(QVariant([fs_helper.relativize_file_path(root_dir), True]), Qt.UserRole)

        model = QStandardItemModel()

        model.setHorizontalHeaderLabels([label])
        model.appendRow(root_item)

        self._add_files(root_item, root_dir)

        return model


    def _add_files(
            self, 
            parent, 
            path,
            ):
        
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)

            if not os.path.isdir(fpath):
                item = QStandardItem(fname)
                
                item.setData(QVariant([fs_helper.relativize_file_path(fpath), False]), Qt.UserRole)
                parent.appendRow(item)


            if os.path.isdir(fpath):
                item = QStandardItem(fname)

                item.setData(QVariant([fs_helper.relativize_file_path(fpath), True]), Qt.UserRole)
                parent.appendRow(item)

                self._add_files(item, fpath)


    def _dump_datasource_file(
            self,
            name, 
            user,
            fpath):
        print(fpath)
        json_data = {
          "name": name,
          "user": user,
          "file_paths": { }
        }

        with open(fpath, 'w') as outfile:
            json.dump(json_data, outfile)


