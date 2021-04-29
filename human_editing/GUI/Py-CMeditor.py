import os
import sys
import glob
import subprocess
import webbrowser
import folium
import geojson
import json
import matplotlib as mpl
import numpy as np
import math as m
import wx
import wx.py as py
import wx.lib.agw.aui as aui
from matplotlib import pyplot as plt
from wx.lib.buttons import GenBitmapButton
from wx import html2
from three_dim_viewer import ThreeDimViewer
# from old_three_dim_viewer import ThreeDimViewer
from folium import LayerControl
from custom_folium_draw import Draw
from folium.plugins import MousePosition
from folium.plugins import FastMarkerCluster
import shapely.speedups
shapely.speedups.enable()
from shapely.geometry import Polygon
import geopandas as gpd

# to-do vtk.vtkRadiusOutlierRemoval
mpl.use('WXAgg')

"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Description**

GUI application for viewing/editing bathymetry data.
Brook Tozer, SIO IGPP 2018-2020.

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Dependencies**

NumPy
Matplotlib
pylab
wxpython
VTK

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**References**

***

***

***

***

***
Icons where designed using the Free icon Maker.
https://freeiconmaker.com/
***

***
Documentation created using Sphinx.
***

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PyCMeditor(wx.Frame):
    """
    Master class for program.
    Most functions are contained in this Class.
    Sets GUI display panels, sizer's and event bindings.
    Contains functions for preforming software tasks.
    """

    # INITIALISE GUI ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Py-CMeditor', size=(1800, 1050))

        # GET CURRENT WORKING DIR
        self.cwd = os.path.dirname(os.path.realpath(__file__))

        # DIR CONTAINING PROGRAM ICONS
        self.gui_icons_dir = self.cwd + '/icons/'

        # START AUI WINDOW MANAGER
        self.mgr = aui.AuiManager()

        # TELL AUI WHICH FRAME TO USE
        self.mgr.SetManagedWindow(self)

        # SET SPLITTER WINDOW TOGGLE IMAGES
        images = wx.ImageList(16, 16)
        top = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_MENU, (16, 16))
        bottom = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_MENU, (16, 16))
        images.Add(top)
        images.Add(bottom)

        # CREATE PANEL TO FILL WITH CONTROLS
        self.left_panel = wx.SplitterWindow(self, wx.ID_ANY, size=(115, 1000), style=wx.SP_NOBORDER | wx.EXPAND)
        self.left_panel.SetMinimumPaneSize(1)
        self.left_panel.SetBackgroundColour('white')

        self.left_panel_top = wx.Panel(self.left_panel, -1, size=(115, 100), style=wx.ALIGN_RIGHT)
        self.left_panel_bottom = wx.Panel(self.left_panel, -1, size=(115, 900), style=wx.ALIGN_RIGHT)

        self.left_panel.SplitHorizontally(self.left_panel_top, self.left_panel_bottom, 100)

        # CREATE PANEL TO FILL WITH INTERACTIVE MAP
        self.right_panel_bottom = wx.Panel(self, -1, size=(1700, 900), style=wx.ALIGN_RIGHT)
        self.right_panel_bottom.SetBackgroundColour('white')

        # CREATE PANEL FOR PYTHON CONSOLE (USED FOR DEBUGGING AND CUSTOM USAGES)
        self.ConsolePanel = wx.Panel(self, -1, size=(1700, 50), style=wx.ALIGN_LEFT | wx.BORDER_RAISED | wx.EXPAND)
        intro = "###############################################################\r" \
                "!USE import sys; then sys.t.OBJECT TO ACCESS PROGRAM OBJECTS \r" \
                "ctrl+up FOR COMMAND HISTORY                                    \r" \
                "###############################################################"
        py_local = {'__app__': 'gmg Application'}
        sys.t = self
        self.win = py.shell.Shell(self.ConsolePanel, -1, size=(2200, 1100),
                                  locals=py_local, introText=intro)

        # ADD THE PANES TO THE AUI MANAGER
        self.mgr.AddPane(self.left_panel, aui.AuiPaneInfo().Name('left').Left().Caption("Controls"))
        self.mgr.AddPane(self.right_panel_bottom, aui.AuiPaneInfo().Name('rightbottom').CenterPane().Caption(""))
        self.mgr.AddPane(self.ConsolePanel, aui.AuiPaneInfo().Name('console').Bottom().Caption("Console"))
        # self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE BY DEFAULT
        self.mgr.Update()

        # CREATE PROGRAM MENUBAR & TOOLBAR (PLACED AT TOP OF FRAME)
        self.create_menu()
        self.create_toolbar()

        # CREATE STATUS BAR
        self.statusbar = self.CreateStatusBar(3, style=wx.NO_BORDER)
        self.controls_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'redock_2.png'),
                                               pos=(0, -5), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.show_controls, self.controls_button)

        # PYTHON CONSOLE
        self.console_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'python_16.png'),
                                              pos=(24, -5), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.show_console, self.console_button)

        # self.status_text = " || Current file: %s "
        # self.statusbar.SetStatusWidths([-1, -1, 1700])
        # self.statusbar.SetStatusText(self.status_text, 2)
        # self.statusbar.SetSize((1800, 24))

        # INITIALISE NAV FRAME
        self.draw_map_window()
        self.export_click_count = 0

        # SET PROGRAM STATUS
        self.bind_button_events()

        # BIND PROGRAM EXIT BUTTON WITH EXIT FUNCTION
        self.Bind(wx.EVT_CLOSE, self.on_close_button)

        # MAXIMIZE FRAME
        #self.Maximize()

        # INITIALISE THREE DIMENSION VIEWER OBJECTS
        self.predicted_xyz = None
        self.difference_xyz = None

    def create_menu(self):
        """# CREATES GUI MENUBAR"""
        self.menubar = wx.MenuBar()  # MAIN MENUBAR

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # FILE MENU
        self.file = wx.Menu()  # CREATE MENUBAR ITEM

        m_open_cm_file = self.file.Append(-1, "Open \tCtrl-L", "Open")
        self.Bind(wx.EVT_MENU, self.open_cm_file, m_open_cm_file)

        self.file.AppendSeparator()

        m_exit = self.file.Append(-1, "Exit...\tCtrl-X", "Exit...")
        self.Bind(wx.EVT_MENU, self.exit, m_exit)

        self.file.AppendSeparator()

        self.menubar.Append(self.file, "&File")  # DRAW FILE MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # EDIT MENU
        self.edit = wx.Menu()  # CREATE MENUBAR ITEM

        self.menubar.Append(self.edit, "&Edit")  # DRAW EDIT MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # FIND MENU'  # CREATE MENUBAR ITEM
        self.find = wx.Menu()

        self.menubar.Append(self.find, "&Find")  # DRAW FIND MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # VIEW MENU'  # CREATE MENUBAR ITEM
        self.view = wx.Menu()

        self.menubar.Append(self.view, "&View")  # DRAW VIEW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # GO MENU'  # CREATE MENUBAR ITEM
        self.go = wx.Menu()

        self.menubar.Append(self.go, "&Go")  # DRAW GO MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # TOOLS MENU'  # CREATE MENUBAR ITEM
        self.tools = wx.Menu()

        self.menubar.Append(self.tools, "&Tools")  # DRAW TOOLS MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # WINDOW MENU'  # CREATE MENUBAR ITEM
        self.window = wx.Menu()

        self.menubar.Append(self.window, "&Window")  # DRAW WINDOW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # SET MENUBAR'
        self.SetMenuBar(self.menubar)

    def create_toolbar(self):
        """CREATE TOOLBAR"""
        # TOOLBAR - (THIS IS THE ICON BAR BELOW THE MENU BAR)
        self.toolbar = self.CreateToolBar()

        t_save_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'save_24.png'))
        # self.Bind(wx.EVT_TOOL, self.save_model, t_save_model)

        t_load_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                            wx.Bitmap(self.gui_icons_dir + 'load_24.png'))
        # self.Bind(wx.EVT_TOOL, self.load_model, t_load_model)

        self.toolbar.Realize()
        self.toolbar.SetSize((1790, 36))

    def draw_map_window(self):
        """INITIALISE FOLIUM INTERACTIVE MAP"""

        # CREATE MAP
        self.folium_map = folium.Map(location=[0.0, 0.0],
                                     zoom_start=1,
                                     attr='map',
                                     no_wrap=True,
                                     name='map',
                                     control_scale=True,
                                     tiles=None)

        # ADD SRTM15+ TILES
        #self.tiles = folium.TileLayer(tiles='/Volumes/External_B/SRTM_tiles/{z}/{x}/{y}.png',
        #                              name='SRTM15+V2.1', attr='SRTM15+V2.1', overlay=True, control=True, show=False)
        self.tiles = folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}.png',
                                      name='Test', attr='Test', overlay=True, control=True, show=True)
        self.tiles.add_to(self.folium_map)

        #self.regridded = folium.TileLayer(tiles='',  name='Regrid', attr='regridded', overlay=False, control=False)
        #self.regridded.add_to(self.folium_map)

        # LOAD DRAWING FUNCTIONALITY
        self.draw = Draw(filename='outpoint.geojson',
                         draw_options={'polyline': False, 'rectangle': False, 'circle': False, 'marker': False,
                                       'circlemarker': False},
                         edit_options={'poly': {'allowIntersection': False}},)

        self.draw.add_to(self.folium_map)

        # LOAD MOUSE POSITION FUNCTIONALITY
        self.mouse_position = MousePosition()
        self.mouse_position.add_to(self.folium_map)

        # CREATE FOLIUM SCATTER PLOT OBJECT - THIS IS USED FOR THE .cm FILE
        self.bad_fg = folium.FeatureGroup(name="Bad")
        self.uncertain_fg = folium.FeatureGroup(name="Uncertain")
        self.good_fg = folium.FeatureGroup(name="Good")

        self.bad_fg_depthdiff = folium.FeatureGroup(name="Bad (depth diff)", show=False)
        self.uncertain_fg_depthdiff = folium.FeatureGroup(name="Uncertain (depth diff)", show=False)
        self.good_fg_depthdiff = folium.FeatureGroup(name="Good (depth diff)", show=False)

        self.folium_map.add_child(self.bad_fg)
        self.folium_map.add_child(self.uncertain_fg)
        self.folium_map.add_child(self.good_fg)

        self.folium_map.add_child(self.bad_fg_depthdiff)
        self.folium_map.add_child(self.uncertain_fg_depthdiff)
        self.folium_map.add_child(self.good_fg_depthdiff)

        # ADD HIDE/SHOW FUNCTIONALITY FOR THE SCATTER POINT DATA
        self.controls = LayerControl(position='bottomright', collapsed=False)
        self.controls.add_to(self.folium_map)

        # SAVE MAP AS HTML
        self.folium_map.save("Py-CMeditor.html")

        # CREATE GUI HTML WINDOW
        # wx.html2.WebView.MSWSetEmulationLevel(wx.html2.WEBVIEWIE_EMU_IE11)
        self.browser = wx.html2.WebView.New(self.right_panel_bottom, -1)
        #self.browser.MSWSetEmulationLevel(level=wx.html2.WEBVIEWIE_EMU_IE11)
        #self.browser.Bind(wx.html2.EVT_HTML_LINK_CLICKED, self.on_import)
        # wx.html2.WebView.WEBVIEW_

        # LOAD FOLIUM MAP INTO WXPYTHON HTML WINDOW
        self.browser.LoadURL(self.cwd + '/Py-CMeditor.html')

        # SET MAIN MAP NAME
        self.main_map_url = str(self.browser.GetCurrentURL())

        # DRAW BUTTON WINDOW
        self.draw_button_and_list_frame()

        # UPDATE DISPLAY
        self.size_handler()

        # REFRESH SIZER POSITIONS
        self.Hide()
        self.Show()

    def draw_button_and_list_frame(self):
        """#% CREATE LEFT HAND BUTTON MENU"""

        # BUTTON - LOAD .cm FILE FROM DISC
        self.button_load_cm = wx.Button(self.left_panel_top, -1, "Load .cm", style=wx.ALIGN_CENTER)

        # BUTTON - LOAD ALL .cm FILES FROM DIR
        self.button_load_cm_dir = wx.Button(self.left_panel_top, -1, "Load .cm dir", style=wx.ALIGN_CENTER)

        # BUTTON - LAUNCH 3D VIEWER
        self.button_launch_3d_viewer = wx.Button(self.left_panel_top, -1, "3D viewer", style=wx.ALIGN_CENTER)

        # BUTTON SIX ADD EXPORT BUTTON FOR POLYGONS
        self.button_export_polygons = wx.Button(self.left_panel_top, -1, "Export polygons", pos=(0, 170),
                                                style=wx.ALIGN_CENTER)

        # BUTTON SEVEN ADD IMPORT BUTTON FOR POLYGONS
        self.button_import_polygons = wx.Button(self.left_panel_top, -1, "Import polygons", pos=(0, 220),
                                                style=wx.ALIGN_CENTER)

        # BUTTON EIGHT SET FLAGS BASED ON POLYGONS
        self.button_flag_points_using_polygons = wx.Button(self.left_panel_top, -1, "Set flags", pos=(0, 220),
                                                style=wx.ALIGN_CENTER)

        # BUTTON NINE SAVE CM FILE TO DISC
        self.button_save_cm_file = wx.Button(self.left_panel_top, -1, "Save .cm", pos=(0, 220),
                                                style=wx.ALIGN_CENTER)

        # BUTTON TEN: REGRID CURRENT DATA
        self.button_regrid = wx.Button(self.left_panel_top, -1, "Regrid", pos=(0, 220), style=wx.ALIGN_CENTER)

        self.file_list_ctrl = wx.ListCtrl(self.left_panel_bottom, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_item_selected, self.file_list_ctrl)
        self.file_list_ctrl.InsertColumn(0, 'cm Files')

    def size_handler(self):
        """CREATE AND FIT SIZERS (DO THE GUI LAYOUT)"""

        # ADD MAIN COORDINATE MAP BOX
        self.box_right_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_bottom_sizer.Add(self.browser, 1, wx.ALL | wx.EXPAND, border=2)
        #self.box_right_bottom_sizer.Add(self.right_panel_bottom, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        # CREATE LAYER BUTTON BOX
        self.left_box_top_sizer = wx.FlexGridSizer(cols=1, rows=8, hgap=8, vgap=8)
        self.left_box_top_sizer.AddMany([self.button_load_cm, self.button_load_cm_dir, self.button_launch_3d_viewer,
                                         self.button_regrid, self.button_export_polygons,
                                         self.button_import_polygons, self.button_flag_points_using_polygons,
                                         self.button_save_cm_file])

        # CREATE FILE LIST BOX
        self.left_box_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_box_bottom_sizer.Add(self.file_list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # PLACE BOX SIZERS IN CORRECT PANELS
        self.left_panel_top.SetSizerAndFit(self.left_box_top_sizer)
        self.left_panel_bottom.SetSizerAndFit(self.left_box_bottom_sizer)

        self.right_panel_bottom.SetSizerAndFit(self.box_right_bottom_sizer)
        self.right_panel_bottom.SetSize(self.GetSize())

    def bind_button_events(self):
        """CONNECT MOUSE AND EVENT BINDINGS"""
        self.button_load_cm.Bind(wx.EVT_BUTTON, self.open_cm_file)
        self.button_load_cm_dir.Bind(wx.EVT_BUTTON, self.open_cm_directory)
        self.button_launch_3d_viewer.Bind(wx.EVT_BUTTON, self.plot_three_dim)
        self.button_save_cm_file.Bind(wx.EVT_BUTTON, self.save_cm_file)
        self.button_regrid.Bind(wx.EVT_BUTTON, self.regrid)
        self.button_export_polygons.Bind(wx.EVT_BUTTON, self.on_wx_export_button)
        self.button_import_polygons.Bind(wx.EVT_BUTTON, self.on_wx_import_button)
        self.button_flag_points_using_polygons.Bind(wx.EVT_BUTTON, self.flag_points_using_polygons)
        self.button_save_cm_file.Bind(wx.EVT_BUTTON, self.save_cm_file)

    # GUI INTERACTION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def color_score(self, value):
        """SET COLOR FOR POINT PLOTTING"""
        if value != -9999:
            cmap = plt.cm.get_cmap('RdYlBu')
            norm = plt.Normalize(0.0, 1.0)
            rgb = cmap(norm(value))[:3]
        else:
            rgb = (0, 0, 0)  # SET FLAGGED NODES AS BLACK
        return (mpl.colors.rgb2hex(rgb))

    def color_depth(self, value):
        """SET COLOR FOR POINT PLOTTING"""
        cmap = plt.cm.get_cmap('viridis')
        norm = plt.Normalize(-10000.0, 0.0)
        rgb = cmap(norm(value))[:3]
        return (mpl.colors.rgb2hex(rgb))

    def open_cm_file(self, event):
        """GET CM FILE TO LOAD"""

        # OPEN THE DIALOG BOX TO ENTER THE THRESHOLD VALUES
        open_cm_dialogbox = OpenCmDialog(self, -1, 'Loading a single .cm file')
        open_cm_dialogbox.ShowModal()

        # OPEN THE .cm FILE
        if open_cm_dialogbox.regular_load_button is True or open_cm_dialogbox.cluster_load_button is True:

            # 1. SET THE THRESHOLD VALUES
            self.bad_th = float(open_cm_dialogbox.bad_th_value)
            self.uncertain_th = float(open_cm_dialogbox.uncertain_th_value)

            # 2. OPEN THE FILE
            open_file_dialog = wx.FileDialog(self, "Open XY file", "", "", "All files (*.cm)|*.*", wx.FD_OPEN |
                                             wx.FD_FILE_MUST_EXIST)
            if open_file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # USER CHANGED THEIR MIND
            else:
                #  IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE
                try:
                    self.cm_plot
                except AttributeError:
                    pass
                else:
                    self.delete_cm_file()

                #  GET THE FILE NAME FROM FileDialog WINDOW
                self.cm_file = open_file_dialog.GetPath()
                self.cm_filename = open_file_dialog.Filename
                self.cm_dir = open_file_dialog.Directory

                # SET THE CLUSTER ZOOM LEVEL TERMINATION
                if open_cm_dialogbox.regular_load_button is True:
                    self.zoom_level = 1
                else:
                    self.zoom_level = 8

                # LOAD THE DATA
                self.load_cm_file_as_cluster(self.bad_th, self.uncertain_th)

    def load_cm_file_as_cluster(self, bad_th, uncertain_th):
        """LOAD .cm FILE AND PLOT AS CLUSTERS"""
        # CM format: ID, Lon, Lat, Depth, SIG H, SIG D, SID, pred, score
        try:
            # 1.0 OPEN THE .cm FILE USING NUMPY
            self.cm = np.genfromtxt(self.cm_file, delimiter=' ', filling_values=-9999)

            ## 1.1 SAVE XYZ FOR 3D VIEWER
            self.xyz = self.cm[:, 1:4]
            self.xyz_cm_id = self.cm[:, 0].astype(int)
            self.xyz_width = self.cm.shape[1]
            self.xyz_meta_data = self.cm[:, 4:self.xyz_width]
            self.xyz_point_flags = np.zeros(shape=(1, len(self.xyz)))
            self.xyz_cm_line_number = np.linspace(0, len(self.xyz), (len(self.xyz) + 1))
            self.score_xyz = self.cm[:, [1, 2, 8]]  # ML SCORE

            # 2.0 GENERATE COLORS FOR THE DEPTHS AND SCORES
            colors = np.empty(shape=[self.cm.shape[0], 2], dtype=object)
            for i in range(0, self.cm.shape[0]):
                colors[i, 0] = self.color_score(self.cm[i, 8])
                colors[i, 1] = self.color_depth(self.cm[i, 3])

            # 2.1 ADD COLORS TO CM ARRAY
            self.cm = np.column_stack((self.cm, colors))

            # 3.0 DIVIDE RECORDS INTO BAD, UNCERTAIN, GOOD (BASED ON ML SCORE)

            # 3.1 MAKE NUMPY ARRAY WITH BAD SCORES
            scored_bad = self.cm[self.cm[:, 8] <= bad_th]

            # 3.2 MAKE NUMPY ARRAY WITH UNCERTAIN SCORES
            scored_uncertain = self.cm[self.cm[:, 8] > bad_th]
            scored_uncertain = scored_uncertain[scored_uncertain[:, 8] <= uncertain_th]

            # 3.3 MAKE NUMPY ARRAY WITH GOOD SCORES
            scored_good = self.cm[self.cm[:, 8] > uncertain_th]

            # 4.0 LOAD CM DATA INTO THE HTML WINDOW

            # 4.1 CUSTOM JAVA SCRIPT FOR CREATING CIRCLE MARKERS & COLORING WITH SCORE VALUE
            callback = ('function (input) {'
                        'var circle = L.circle(new L.LatLng(input[0], input[1]), '
                        '{color: input[2],  radius: 10,  opacity: 0.5});'
                        'return circle};')

            callback2 = ('function (input) {'
                         'var circle = L.circle(new L.LatLng(input[0], input[1]), '
                         '{color: input[2],  radius: 10,  opacity: 0.5});'
                         "var popup = L.popup({maxWidth: '300'});"
                         "const display_text = {text: input[3]};"
                         "var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; "
                         "height: 100.0%;'> ${display_text.text}</div>`)[0];"
                         "popup.setContent(mytext);"
                         "circle.bindPopup(popup);"
                         'return circle};')

            # CREATE CLUSTER OBJECTS
            self.bad_fg.add_child(FastMarkerCluster((scored_bad[:, (2, 1, 9)]).tolist(),
                                                    callback=callback, disableClusteringAtZoom=self.zoom_level))

            self.uncertain_fg.add_child(FastMarkerCluster((scored_uncertain[:, (2, 1, 9)]).tolist(),
                                                          callback=callback, disableClusteringAtZoom=self.zoom_level))

            self.good_fg.add_child(FastMarkerCluster((scored_good[:, (2, 1, 9)]).tolist(),
                                                     callback=callback, disableClusteringAtZoom=self.zoom_level))

            # CREATE DEPTH DIFFERENCE CLUSTER OBJECTS
            self.bad_fg_depthdiff.add_child(FastMarkerCluster((scored_bad[:, (2, 1, 10, 7)]).tolist(),
                                                              callback=callback2,
                                                              disableClusteringAtZoom=self.zoom_level))

            self.uncertain_fg_depthdiff.add_child(FastMarkerCluster((scored_uncertain[:, (2, 1, 10, 7)]).tolist(),
                                                                    callback=callback2,
                                                                    disableClusteringAtZoom=self.zoom_level))

            self.good_fg_depthdiff.add_child(FastMarkerCluster((scored_good[:, (2, 1, 10, 7)]).tolist(),
                                                               callback=callback2,
                                                               disableClusteringAtZoom=self.zoom_level))

            # IMPORT PREDICTED GRID
            lon, lat = self.get_centeroid(self.cm[:, 1:3])
            epsg_code = self.convert_wgs_to_utm_epsg_code(lon, lat)
            self.get_predicted(epsg_code)

            # SAVE AND DISPLAY THE NEW FOLIUM MAP (INCLUDING THE .cm FILE)
            self.set_map_location()
            self.folium_map.save("Py-CMeditor.html")
            self.browser.Reload()


        except IndexError:
            error_message = "ERROR IN LOADING PROCESS - FILE MUST BE ASCII SPACE DELIMITED"
            wx.MessageDialog(self, -1, error_message, "Load Error")
            raise

    def set_map_location(self):
        map_name = self.folium_map.get_name()
        r, lt = self.browser.RunScript(str(map_name) + '.getCenter()[\'lat\']')
        r, ln = self.browser.RunScript(str(map_name) + '.getCenter()[\'lng\']')
        r, zoom = self.browser.RunScript(str(map_name) + '.getZoom()')
        self.folium_map.options['zoom'] = zoom
        self.folium_map.location = [lt, ln]


    def get_centeroid(self, arr):
        length = arr.shape[0]
        sum_x = np.sum(arr[:, 0])
        sum_y = np.sum(arr[:, 1])
        return sum_x/length, sum_y/length

    def convert_wgs_to_utm_epsg_code(self, lon, lat):
        utm_band = str((m.floor((lon + 180) / 6) % 60) + 1)
        if len(utm_band) == 1:
            utm_band = '0' + utm_band
        if lat >= 0:
            epsg_code = '326' + utm_band
        else:
            epsg_code = '327' + utm_band
        return epsg_code

    def get_predicted(self, epsg_code):
        msg = "Please wait while we process your request..."
        self.busyDlg = wx.BusyInfo(msg)

        try:
            #  SAVE CM AS INPUT XYZ FOR BASH SCRIPT'
            cm_file = self.cm[:, 1:4]
            np.savetxt('input.xyz', cm_file, delimiter=" ", fmt="%10.6f %10.6f %10.6f")

            # RUN BASH SCRIPT
            subprocess.run(["bash", self.cwd + '/' + 'get_predicted.sh', self.cm_dir + '/' + self.cm_filename, epsg_code])

            # LOAD CURRENT GRID XYZ POINTS
            self.predicted_xyz = np.genfromtxt('predicted.xyz', delimiter=' ', dtype=float, filling_values=-9999)

            # LOAD DIFFERENCE CM
            self.difference_xyz = np.genfromtxt('difference.xyz', delimiter=' ', dtype=float, filling_values=-9999)

        except AttributeError:
            print("ERROR: no .cm file loaded")
        self.busyDlg = None

    def delete_cm_file(self):
        """
        DELETE CURRENT .cm FILE SO THE NEWLY SELECTED .cm FILE CAN BE LOADED INTO THE VIEWERS
        """

        #  REMOVE .cm DATA from MAP FRAME
        del self.cm_file
        del self.cm
        self.cm_plot.set_visible(False)
        self.cm_plot.remove()
        del self.cm_plot

        #  REMOVE .cm DATA from MAP FRAME
        del self.xyz
        del self.xyz_cm_id
        del self.xyz_width
        del self.xyz_meta_data
        del self.xyz_point_flags
        del self.xyz_cm_line_number

        self.draw()

    def open_cm_directory(self, event):
        """
        Update the listctrl with the file names in the passed in folder
        """
        dlg = wx.DirDialog(self, "Choose a directory:")
        if dlg.ShowModal() == wx.ID_OK:
            folder_path = dlg.GetPath()
        self.active_dir = folder_path  # SET .cm DIR
        paths = glob.glob(folder_path + "/*.cm")  # GET ALL .cm file names
        for index, path in enumerate(paths):
            self.file_list_ctrl.InsertItem(index, os.path.basename(path))
        dlg.Destroy()

    def save_cm_file(self, event):
        """SAVE THE CURRENTLY OPEN .cm FILE TO DISC (INCLUDING EDITS)"""

        # 1.0 OPEN A FILE NAV WINDOW AND SELECT THE OUTPUT FILE
        save_file_dialog = wx.FileDialog(self, "Save model file", "", "", "Model files (*.cm)|*.cm", wx.FD_SAVE
                                         | wx.FD_OVERWRITE_PROMPT)
        if save_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # USER CHANGED THEIR MIND

        # 2.0 GET FILE NAME
        output_filename = save_file_dialog.GetPath()

        # 3.0 SAVE .cm TO DISC
        print(self.cm[1, :])
        np.savetxt(output_filename, self.cm[:, 0:9], fmt="%1d %4.6f %4.6f %4.16f %1d %1d %1d %1.1f %1.1f")

    def list_item_selected(self, event):
        """ACTIVATED WHEN A FILE FROM THE LIST CONTROL IS SELECTED"""

        file = event.GetText()
        self.selected_file = str(self.active_dir) + "/" + str(file)
        print(self.selected_file)

        #  IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
        try:
            self.cm_plot
        except AttributeError:
            pass
        else:
            self.delete_cm_file()

        # LOAD NEW .cm FILE DATA INTO VIEWERS'
        self.cm_file = self.selected_file
        self.load_cm_file()

    def open_predicted_cm_file(self, event):
        pass

    def regrid(self, event):
        # STEP 1: WRITE OUT TMP CM FILE
        self.cm_out= np.copy(self.cm)
        self.cm_out
        np.savetxt('current_cm.tmp', self.cm_out[:, 0:8], fmt="%1d %4.6f %4.6f %4.16f %1d %1d %1d %1.1f")

        # RUN BASH SCRIPT FOR REGRIDDING
        subprocess.run(["bash", self.cwd + '/' + 'regrid.sh', self.cwd + '/' + 'current_cm.tmp'])

        # LOAD NEW GRID
        self.regridded.tiles = '/Users/brook/PROJECTS/ML/Bathymetry/human_editing/GUI/TMP_RESTORED/{z}/{x}/{y}.png'
        self.regridded.overlay = True
        self.regridded.control = True
        # SAVE AND DISPLAY THE NEW FOLIUM MAP (INCLUDING THE .cm FILE)
        self.folium_map.save("Py-CMeditor.html")
        self.browser.Reload()

    def on_wx_import_button(self, event):
        """
        IMPORTING POLYGONS
        """

        # 1.0 OPEN A FILE NAV WINDOW AND SELECT THE FILE TO OPEN
        open_file_dialog = wx.FileDialog(self, "Open model file", "", "", "Model files (*.geojson)|*.geojson",
                                         wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if open_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # USER CHANGED THEIR MIND

        with open(open_file_dialog.GetPath(), 'rb') as input_file:
            self.imported_data = json.load(input_file)

        # 2.0 CONVERT STR TO GEOJSON
        self.fc = geojson.FeatureCollection(eval(str(self.imported_data)))

        # 3.0 GET NUMBER OF LAYERS
        number_of_layers = len(self.fc['features']['id']['features'])
        print(number_of_layers)

        # 4.0 LOOP THROUGH LAYERS AND EXTRACT THE COORDINATES
        for i in range(number_of_layers):
            # 4.1 GET COORDINATES
            layer_coords = self.fc['features']['id']['features'][i]['geometry']['coordinates'][0]
            # 4.2 CHECK FOR LONGS > 180 AND REFORMAT TO -180<->180
            # for c in range(len(layer_coords)):
            #     if layer_coords[0, c] > 180.:
            #         layer_coords[0, c] -= 360.
            # 4.3 REVERSE ORDER OF COORDINATES AS REQUIRED FOR INPUT
            layer_coords = [elem[::-1] for elem in layer_coords]
            # 4.4 ADD LAYER TO CURRENT MAP
            self.browser.RunScript("L.polygon(%s).addTo(drawnItems)" % layer_coords)

    def on_wx_export_button(self, event):
        """
        FIRERS WHEN EXPORT BUTTON IS PRESSED
        """
        print("EXPORT BUTTON PRESSED")

        # 1.0 GET THE POLYGON DATA FRM THE FOLIUM JAVASCRIPT
        success, text = self.browser.RunScript("drawnItems.toGeoJSON()")
        self.fc = geojson.FeatureCollection(eval(text))

        # 2.0 OPEN A FILE NAV WINDOW AND SELECT THE OUTPUT FILE
        save_file_dialog = wx.FileDialog(self, "Save model file", "", "", "Model files (*.txt)|*.txt", wx.FD_SAVE
                                         | wx.FD_OVERWRITE_PROMPT)
        if save_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # USER CHANGED THEIR MIND

        # 3.0 GET FILE NAME
        output_filename = save_file_dialog.GetPath()
        output_prefix = output_filename.split('.')[0]

        # 4.0 WRITE DATA TO ASCII TEXT FILE
        with open(output_filename, 'wb') as output_f:
            for i in range(len(self.fc.features)):
                spacer = np.array([['>>', 'Polygon ' + str(i)]]).astype(str)
                np.savetxt(output_f, spacer, fmt='%2s')
                coords = list(geojson.utils.coords(self.fc.features[i]))
                output_coords = np.array(coords).astype(str)
                np.savetxt(output_f, output_coords, fmt='%10s')

        # 5.0 WRITE OUT THE POLYGONS AS A GEOJSON FORMATTED FILE (WHICH CAN BE LOADED BACK LATER)
        output_geojson_file = geojson.Feature(eval(text))
        with open(output_prefix+'.geojson', 'w') as f:
            geojson.dump(output_geojson_file, f)

    def plot_three_dim(self, event):
        """
        PLOT 3D VIEW OF DATA

        inputs::

        self.cm =
        self.xyz =
        self.xyz_cm_id =
        self.xyz_meta_data =
        self.xyz_cm_line_number =
        self.predicted_xyz =
        self.difference_xyz =
        self.score_xyz =
        """

        # OPEN A vtk 3D VIEWER WINDOW AND CREATE A RENDER'
        self.tdv = ThreeDimViewer(self, -1, 'Modify Current Model', self.cm, self.xyz, self.xyz_cm_id,
                                  self.xyz_meta_data, self.xyz_cm_line_number, self.predicted_xyz,
                                  self.difference_xyz, self.score_xyz)
        self.tdv.Show(True)

    def reload_three_dim(self):
        """REMOVE 3D VIEWER AND REPLACE WITH NEWLY LOADED DATA"""
        self.tdv.Show(False)
        del self.tdv
        self.plot_three_dim(self)

    def show_controls(self, event):
        pass

    def show_console(self, event):
        """SHOW/HIDE PYTHON CONSOLE"""
        if self.mgr.GetPaneByName('console').Hide:
            self.mgr.GetPaneByName('console').Show()  # SHOW PYTHON CONSOLE
        else:
            self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE

    def flag_points_using_polygons(self, event):
        """Flag all points that fall within the user defined polygons"""

        # 1.0 STEP UP INPUT POINTS
        self.input_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(self.cm[:, 1], self.cm[:, 2]))

        # 2.0 GET POLYGONS
        success, self.text = self.browser.RunScript("drawnItems.toGeoJSON()")
        self.fc = geojson.FeatureCollection(eval(self.text))

        # 3.0 CREATE OUTPUT ARRAY
        self.output_result = np.zeros(shape=(len(self.input_points), len(self.fc.features))).astype(str)

        # 4.0 LOOP THROUGH POLYGONS
        for i in range(len(self.fc.features)):
            # 3.1 GET POLYGON COORDINATES
            self.polygon = Polygon(self.fc.features[i]['geometry']['coordinates'][0])
            # 3.2 LOOP OVER EACH INPUT POINT
            self.output_result[:, i] = self.input_points.within(self.polygon)

        # 5.0 CHECK IF A POINT IS IN ANY OF THE POLYGONS. IF TRUE THEN SET THE POINT FLAG AS A 1
        for i in range(len(self.output_result)):
            for p in range(np.shape(self.output_result)[1]):
                if self.output_result[i, p] == 'True':
                    self.cm[i, 5] = -9999


    # DOCUMENTATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_documentation(self, event):
        """# OPENS DOCUMENTATION HTML"""
        new = 2
        doc_url = os.path.dirname(__file__) + '/docs/_build/html/manual.html'
        webbrowser.open(doc_url, new=new)

    def about_pycmeditor(self, event):
        """# SHOW SOFTWARE INFORMATION"""
        about = "About PyCMeditor"
        dlg = wx.MessageDialog(self, about, "About", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def legal(self, event):
        """# SHOW LICENCE"""
        licence = ["Copyright 2020 Brook Tozer \n\nRedistribution and use in source and binary forms, with or "
                   "without modification, are permitted provided that the following conditions are met: \n \n"
                   "1. Redistributions of source code must retain the above copyright notice, this list of conditions "
                   "and the following disclaimer. \n\n2. Redistributions in binary form must reproduce the above "
                   "copyright notice, this list of conditions and the following disclaimer in the documentation and/or "
                   "other materials provided with the distribution. \n\n3. Neither the name of the copyright holder "
                   "nor the names of its contributors may be used to endorse or promote products  derived from this "
                   "software without specific prior written permission. \n\nTHIS SOFTWARE IS PROVIDED BY THE "
                   "COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT "
                   "NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE "
                   "DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, "
                   "INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, "
                   "PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS "
                   "INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,"
                   " OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, "
                   "EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."]

        dlg = wx.MessageDialog(self, licence[0], "BSD-3-Clause Licence", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    # EXIT FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def exit(self, event):
        """# SHUTDOWN APP (FROM FILE MENU)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

    def on_close_button(self, event):
        """# SHUTDOWN APP (X BUTTON)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()


# DIALOGS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class OpenCmDialog(wx.Dialog):
    """
    OPEN A CM FILE AND SET THE THRESHOLDS FOR THE SCORES
    """

    def __init__(self, parent, id, title, m_x1=None, m_x2=None, m_z1=None, m_z2=None):
        """DIALOG BOX USED TO GATHER USER INPUT FOR CREATING A NEW MODEL"""
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.OK | wx.CANCEL
                                                          | wx.BORDER_RAISED)
        self.floating_panel = wx.Panel(self, -1)

        # SET BUTTON VALUES
        self.regular_load_button = False
        self.cluster_load_button = False

        # MAIN BOX SIZER
        self.main_box = wx.BoxSizer(wx.HORIZONTAL)

        # 1. ADD TEXT
        self.title_text = wx.StaticText(self.floating_panel, -1, "Set the scoring thresholds for dividing these data",
                                        style=wx.ALIGN_CENTRE_HORIZONTAL)

        # 2. THRESHOLD TEXT DESCRIPTIONS
        self.bad_scores_text = wx.StaticText(self.floating_panel, -1, "Bad threshold: ")
        self.uncertain_scores_text = wx.StaticText(self.floating_panel, -1, "Uncertain threshold: ")

        # 3. THRESHOLD INPUT BOXES
        self.bad_th_text = wx.TextCtrl(self.floating_panel, -1, "0.1", size=(100, -1))
        self.uncertain_th_text = wx.TextCtrl(self.floating_panel, -1, "0.2", size=(100, -1))

        # 4. LINE SPACER 2
        self.line2 = (wx.StaticLine(self.floating_panel), 0, wx.ALL | wx.EXPAND, 5)

        # 5. LOAD REGULAR BUTTON
        self.b_regular_button = wx.Button(self.floating_panel, -1, "Load as regular points")
        self.Bind(wx.EVT_BUTTON, self.open_regular_button, self.b_regular_button)

        # 6. LOAD CLUSTER BUTTON
        self.b_cluster_button = wx.Button(self.floating_panel, -1, "Load as clustered points")
        self.Bind(wx.EVT_BUTTON, self.open_cluster_button, self.b_cluster_button)

        # 7. ADD FOOTER TEXT
        self.footer_text = wx.StaticText(self.floating_panel, -1,
                                         "NB. Using Cluster mode is recommended when the\n"
                                         "data set is geographically sparse and/or contains.\n"
                                         "> 50,000 records. This will help prevent lagging\n"
                                         "when rendering the point data.")

        # CREATE SIZER TO HOST THE FEATURES
        self.sizer = wx.GridBagSizer(4, 3)
        self.sizer.Add(self.title_text, pos=(0, 0), span=(1, 3), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.bad_scores_text, pos=(1, 0), flag=wx.LEFT)
        self.sizer.Add(self.bad_th_text, pos=(1, 1), flag=wx.LEFT)
        self.sizer.Add(self.uncertain_scores_text, pos=(2, 0), flag=wx.LEFT)
        self.sizer.Add(self.uncertain_th_text, pos=(2, 1), flag=wx.LEFT)
        self.sizer.Add(self.b_regular_button, pos=(3, 0), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.b_cluster_button, pos=(3, 1), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.footer_text, pos=(4, 0), span=(1, 3), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=5)

        # ADD SIZER TO MAIN FRAME
        self.main_box.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        self.floating_panel.SetSizerAndFit(self.main_box)
        self.main_box.Fit(self)

    def open_regular_button(self, event):
        """WHEN THE "Load as regular points" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.regular_load_button = True
        self.cluster_load_button = False
        self.EndModal(1)

    def open_cluster_button(self, event):
        """WHEN THE "Load as clustered points" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.cluster_load_button = True
        self.regular_load_button = False
        self.EndModal(1)

    def redraw(self):
        """REDRAW THE CM POINT DATA ON THEE MAP AFTER APPLYING FLAGS TO THE DATA WITHIN USER DERIVED POLYGONS"""
        # 1.0 GENERATE NEW COLORS FOR THE DEPTHS (FLAGGED= -9999)
        colors = np.empty(shape=[self.cm.shape[0], 1], dtype=object)
        for i in range(0, self.cm.shape[0]):
            colors[i, 1] = self.color_depth(self.cm[i, 3])

        # 1.1 ADD COLORS TO CM ARRAY
        self.cm[:, 7] = colors

        # 3.0 DIVIDE RECORDS INTO BAD, UNCERTAIN, GOOD (BASED ON ML SCORE)
        scored_bad = self.cm[self.cm[:, 6] <= self.bad_th]
        bad_list = scored_bad[:, (2, 1, 9, 6)].tolist()

        scored_uncertain = self.cm[self.cm[:, 6] > self.bad_th]
        scored_uncertain = scored_uncertain[scored_uncertain[:, 6] <= self.uncertain_th]
        uncertain_list = scored_uncertain[:, (2, 1, 9, 6)].tolist()

        # 3.3 MAKE NUMPY ARRAY WITH GOOD SCORES
        scored_good = self.cm[self.cm[:, 6] > self.uncertain_th]
        scored_good = scored_good[:, (2, 1, 9, 6)].tolist()

        # 4.0 GET THE CURRENT JAVA SCRIPT OBJECTS DATA POINTERS
        bad_fg_data_java_pointer = self.bad_fg._children[list(self.bad_fg._children.keys())[0]].data
        uncertain_fg_java_pointer = self.uncertain_fg._children[list(self.uncertain_fg._children.keys())[0]].data
        good_fg_java_pointer = self.good_fg._children[list(self.good_fg._children.keys())[0]].data

        # CREATE NEW DATA ARRAY
        new_bad_data = [list(i) for i in zip(g.cm[:, 2], g.cm[:, 3], g.cm[:, 4], g.cm[:, 9])]

        # INSET NEW DATA INTO JAVA OBJECT
        self.bad_fg._children[list(self.bad_fg._children.keys())[0]].data = new_bad_data

class SavePolygonsDialog(wx.Dialog):
    """
    DIALOG TO SELECT/CREATE THE ASCII TEXT FILE TO SAVE POLYGON COORDINATES INTO
    """

    def __init__(self, parent, id, title):
        """DIALOG BOX USED TO USE FOR ASSIGNING A FILE NAME FOR THE TEXT FILE TO SAVE POLYGONS"""
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE | wx.MAXIMIZE_BOX | wx.OK | wx.CANCEL
                                                          | wx.BORDER_RAISED)
        self.floating_panel = wx.Panel(self, -1)

        # SET BUTTON VALUES
        self.regular_load_button = False
        self.cluster_load_button = False

        # MAIN BOX SIZER
        self.main_box = wx.BoxSizer(wx.HORIZONTAL)

        # 1. ADD TEXT
        self.title_text = wx.StaticText(self.floating_panel, -1, "Set the scoring thresholds for dividing these data",
                                        style=wx.ALIGN_CENTRE_HORIZONTAL)

        # 2. THRESHOLD TEXT DESCRIPTIONS
        self.bad_scores_text = wx.StaticText(self.floating_panel, -1, "Bad threshold: ")
        self.uncertain_scores_text = wx.StaticText(self.floating_panel, -1, "Uncertain threshold: ")

        # 3. THRESHOLD INPUT BOXES
        self.bad_th_text = wx.TextCtrl(self.floating_panel, -1, "0", size=(100, -1))
        self.uncertain_th_text = wx.TextCtrl(self.floating_panel, -1, "0", size=(100, -1))

        # 4. LINE SPACER 2
        self.line2 = (wx.StaticLine(self.floating_panel), 0, wx.ALL | wx.EXPAND, 5)

        # 5. LOAD REGULAR BUTTON
        self.b_regular_button = wx.Button(self.floating_panel, -1, "Load as regular points")
        self.Bind(wx.EVT_BUTTON, self.open_regular_button, self.b_regular_button)

        # 6. LOAD CLUSTER BUTTON
        self.b_cluster_button = wx.Button(self.floating_panel, -1, "Load as clustered points")
        self.Bind(wx.EVT_BUTTON, self.open_cluster_button, self.b_cluster_button)

        # 7. ADD FOOTER TEXT
        self.footer_text = wx.StaticText(self.floating_panel, -1,
                                         "NB. Using Cluster mode is recommended when the\n"
                                         "data set is geographically sparse and/or contains.\n"
                                         "> 50,000 records. This will help prevent lagging\n"
                                         "when rendering the point data.")

        # CREATE SIZER TO HOST THE FEATURES
        self.sizer = wx.GridBagSizer(4, 3)
        self.sizer.Add(self.title_text, pos=(0, 0), span=(1, 3), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.bad_scores_text, pos=(1, 0), flag=wx.LEFT)
        self.sizer.Add(self.bad_th_text, pos=(1, 1), flag=wx.LEFT)
        self.sizer.Add(self.uncertain_scores_text, pos=(2, 0), flag=wx.LEFT)
        self.sizer.Add(self.uncertain_th_text, pos=(2, 1), flag=wx.LEFT)
        self.sizer.Add(self.b_regular_button, pos=(3, 0), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.b_cluster_button, pos=(3, 1), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=10)
        self.sizer.Add(self.footer_text, pos=(4, 0), span=(1, 3), flag=wx.TOP | wx.CENTER | wx.BOTTOM, border=5)

        # ADD SIZER TO MAIN FRAME
        self.main_box.Add(self.sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        self.floating_panel.SetSizerAndFit(self.main_box)
        self.main_box.Fit(self)

    def open_regular_button(self, event):
        """WHEN THE "Load as regular points" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.regular_load_button = True
        self.cluster_load_button = False
        self.EndModal(1)

    def open_cluster_button(self, event):
        """WHEN THE "Load as clustered points" BUTTON IS PRESSED"""
        self.bad_th_value = float(self.bad_th_text.GetValue())
        self.uncertain_th_value = float(self.uncertain_th_text.GetValue())
        self.cluster_load_button = True
        self.regular_load_button = False
        self.EndModal(1)


class MessageDialog(wx.MessageDialog):
    """GENERIC MESSAGE DIALOG BOX. USED TO POPULATE MESSAGES IN THE GUI"""

    def __init__(self, parent, id, message_text, title):
        wx.MessageDialog.__init__(self, parent, message_text, title)
        dlg = wx.MessageDialog(self, message_text, title, wx.OK)
        answer = dlg.ShowModal()
        dlg.Destroy()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# START SOFTWARE
if __name__ == "__main__":
    app = wx.App(False)
    fr = wx.Frame(None, title='Py-CMeditor')
    app.frame = PyCMeditor()
    app.frame.CenterOnScreen()
    app.frame.Show()
    app.MainLoop()
