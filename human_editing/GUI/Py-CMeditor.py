"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Description**

GUI application for hand editing Bathymetry data.
Brook Tozer, SIO IGPP 2018.

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

# IMPORT MODULES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# to-do vtk.vtkRadiusOutlierRemoval
import sys
import matplotlib as mpl
mpl.use('WXAgg')
from matplotlib import pyplot as plt
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import wx.py as py
import wx.lib.agw.aui as aui
from wx.lib.buttons import GenBitmapButton
import numpy as np
from numpy import size
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy
import glob
import os
import webbrowser
import folium
from folium import features
from wx import html
from wx import html2
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PyCMeditor(wx.Frame):
    """
    Master class for program.
    Most functions are contained in this Class.
    Sets GUI display panels, sizer's and event bindings.
    Additional classes are used for "pop out" windows (Dialog boxes).
    Objects are passed between the master class and Dialog boxes.
    """

    '# %DIR CONTAINING PROGRAM ICONS'
    gui_icons_dir = os.path.dirname(os.path.realpath(__file__)) + '/icons/'

    # INITALIZE GUI~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Py-CMeditor', size=(1800, 1050))

        '# %START AUI WINDOW MANAGER'
        self.mgr = aui.AuiManager()

        '# %TELL AUI WHICH FRAME TO USE'
        self.mgr.SetManagedWindow(self)

        '# %SET SPLITTER WINDOW TOGGLE IMAGES'
        images = wx.ImageList(16, 16)
        top = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_MENU, (16, 16))
        bottom = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_MENU, (16, 16))
        images.Add(top)
        images.Add(bottom)

        '# %CREATE PANEL TO FILL WITH CONTROLS'
        self.leftPanel = wx.SplitterWindow(self, wx.ID_ANY, size=(115, 1000), style=wx.SP_NOBORDER | wx.EXPAND)
        self.leftPanel.SetMinimumPaneSize(1)
        self.leftPanel.SetBackgroundColour('white')

        self.leftPanel_top = wx.Panel(self.leftPanel, -1, size=(115, 100), style=wx.ALIGN_RIGHT)
        self.leftPanel_bottom = wx.Panel(self.leftPanel, -1, size=(115, 900), style=wx.ALIGN_RIGHT)

        self.leftPanel.SplitHorizontally(self.leftPanel_top, self.leftPanel_bottom, 100)

        '# %CREATE PANEL TO FILL WITH COORDINATE INFORMATION'
        self.rightPaneltop = wx.Panel(self, -1, size=(1800, 50), style=wx.ALIGN_RIGHT)
        self.rightPaneltop.SetBackgroundColour('white')

        '# %CREATE PANEL TO FILL WITH MATPLOTLIB INTERACTIVE FIGURE (MAIN NAVIGATION FRAME)'
        self.rightPanelbottom = wx.Panel(self, -1, size=(1700, 900), style=wx.ALIGN_RIGHT)
        self.rightPanelbottom.SetBackgroundColour('white')

        '# %CREATE PANEL FOR PYTHON CONSOLE (USED FOR DEBUGGING AND CUSTOM USAGES)'
        self.ConsolePanel = wx.Panel(self, -1, size=(1800, 100), style=wx.ALIGN_LEFT | wx.BORDER_RAISED | wx.EXPAND)
        intro = "###############################################################\r" \
                "!USE import sys; then sys.Gmg.OBJECT TO ACCESS PROGRAM OBJECTS \r" \
                "ctrl+up FOR COMMAND HISTORY                                    \r" \
                "###############################################################"
        py_local = {'__app__': 'gmg Application'}
        sys.Gmg = self
        self.win = py.shell.Shell(self.ConsolePanel, -1, size=(2200, 1100), locals=py_local, introText=intro)

        '# %ADD THE PANES TO THE AUI MANAGER'
        self.mgr.AddPane(self.leftPanel, aui.AuiPaneInfo().Name('left').Left().Caption("Controls"))
        self.mgr.AddPane(self.rightPaneltop, aui.AuiPaneInfo().Name('righttop').Top())
        self.mgr.AddPane(self.rightPanelbottom, aui.AuiPaneInfo().Name('rightbottom').CenterPane())
        self.mgr.AddPane(self.ConsolePanel, aui.AuiPaneInfo().Name('console').Bottom().Caption("Console"))
        # self.mgr.GetPaneByName('console').Hide()  # HIDE PYTHON CONSOLE BY DEFAULT
        self.mgr.Update()

        '# %CREATE PROGRAM MENUBAR & TOOLBAR (PLACED AT TOP OF FRAME)'
        self.create_menu()
        self.create_toolbar()

        '# %CREATE STATUS BAR'
        self.statusbar = self.CreateStatusBar(3, style=wx.NO_BORDER)
        self.controls_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'redock_2.png'),
                                               pos=(0, -5), style=wx.NO_BORDER)
        # self.Bind(wx.EVT_BUTTON, self.show_controls, self.controls_button)

        '# %PYTHON CONSOLE'
        self.console_button = GenBitmapButton(self.statusbar, -1, wx.Bitmap(self.gui_icons_dir + 'python_16.png'),
                                              pos=(24, -5), style=wx.NO_BORDER)
        # self.Bind(wx.EVT_BUTTON, self.show_console, self.console_button)

        self.status_text = " || Current file: %s "
        self.statusbar.SetStatusWidths([-1, -1, 1700])
        self.statusbar.SetStatusText(self.status_text, 2)
        self.statusbar.SetSize((1800, 24))

        '# %INITALISE NAV FRAME'
        self.draw_navigation_window()

        '# %SET PROGRAM STATUS'
        self.connect_mpl_events()

        '# %SET PROGRAM STATUS'
        self.saved = False

        '# %BIND PROGRAM EXIT BUTTON WITH EXIT FUNCTION'
        self.Bind(wx.EVT_CLOSE, self.on_close_button)

        '# %MAXIMIZE FRAME'
        self.Maximize(True)

    def create_menu(self):
        """# %CREATES GUI MENUBAR"""
        self.menubar = wx.MenuBar()  # MAIN MENUBAR

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# % FILE MENU'
        self.file = wx.Menu()  # CREATE MENUBAR ITEM

        m_open_cm_file = self.file.Append(-1, "Open \tCtrl-L", "Open")
        self.Bind(wx.EVT_MENU, self.open_cm_file, m_open_cm_file)

        self.file.AppendSeparator()

        m_exit = self.file.Append(-1, "Exit...\tCtrl-X", "Exit...")
        self.Bind(wx.EVT_MENU, self.exit, m_exit)

        self.file.AppendSeparator()

        #m_3d = self.file.Append(-1, "plot\tCtrl-p", "Plot")
        #self.Bind(wx.EVT_MENU, self.plot_surface, m_3d)

        self.menubar.Append(self.file, "&File")  # %DRAW FILE MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %EDIT MENU'
        self.edit = wx.Menu()  # CREATE MENUBAR ITEM

        self.menubar.Append(self.edit, "&Edit")  # %DRAW EDIT MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %FIND MENU'  # CREATE MENUBAR ITEM
        self.find = wx.Menu()

        self.menubar.Append(self.find, "&Find")  # % DRAW FIND MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %VIEW MENU'  # CREATE MENUBAR ITEM
        self.view = wx.Menu()

        self.menubar.Append(self.view, "&View")  # % DRAW VIEW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %GO MENU'  # CREATE MENUBAR ITEM
        self.go = wx.Menu()

        self.menubar.Append(self.go, "&Go")  # % DRAW GO MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %TOOLS MENU'  # CREATE MENUBAR ITEM
        self.tools = wx.Menu()

        self.menubar.Append(self.tools, "&Tools")  # % DRAW TOOLS MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %WINDOW MENU'  # CREATE MENUBAR ITEM
        self.window = wx.Menu()

        self.menubar.Append(self.window, "&Window")  # % DRAW WINDOW MENU

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '# %SET MENUBAR'
        self.SetMenuBar(self.menubar)

    def create_toolbar(self):
        '# %TOOLBAR - (THIS IS THE ICON BAR BELOW THE MENU BAR)'
        self.toolbar = self.CreateToolBar()

        t_save_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                                 wx.Bitmap(self.gui_icons_dir + 'save_24.png'))
        # self.Bind(wx.EVT_TOOL, self.save_model, t_save_model)

        t_load_model = self.toolbar.AddTool(wx.ID_ANY, 'Load model',
                                                 wx.Bitmap(self.gui_icons_dir + 'load_24.png'))
        # self.Bind(wx.EVT_TOOL, self.load_model, t_load_model)

        t_calc_model_bott = self.toolbar.AddTool(wx.ID_ANY, 'calculate-gravity',
                                                      wx.Bitmap(self.gui_icons_dir + 'G_24.png'))
        # self.Bind(wx.EVT_TOOL, self.calc_grav_switch, t_calc_model_bott)

        t_capture_coordinates = self.toolbar.AddTool(wx.ID_ANY, 't_capture_coordinates',
                                                          wx.Bitmap(self.gui_icons_dir + 'C_24.png'))
        # self.Bind(wx.EVT_TOOL, self.capture_coordinates, t_capture_coordinates)

        t_aspect_increase = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-up',
                                                      wx.Bitmap(self.gui_icons_dir + 'large_up_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_increase, t_aspect_increase)

        t_aspect_decrease = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-down',
                                                      wx.Bitmap(self.gui_icons_dir + 'large_down_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_decrease, t_aspect_decrease)

        t_aspect_increase2 = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-up-2',
                                                       wx.Bitmap(self.gui_icons_dir + 'small_up_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_increase2, t_aspect_increase2)

        t_aspect_decrease2 = self.toolbar.AddTool(wx.ID_ANY, 'aspect-ratio-down-2',
                                                       wx.Bitmap(self.gui_icons_dir + 'small_down_24.png'))
        self.Bind(wx.EVT_TOOL, self.aspect_decrease2, t_aspect_decrease2)

        t_zoom = self.toolbar.AddTool(wx.ID_ANY, 'zoom',
                                           wx.Bitmap(self.gui_icons_dir + 'zoom_in_24.png'))
        self.Bind(wx.EVT_TOOL, self.zoom, t_zoom)

        t_zoom_out = self.toolbar.AddTool(wx.ID_ANY, 'zoom out',
                                               wx.Bitmap(self.gui_icons_dir + 'zoom_out_24.png'))
        self.Bind(wx.EVT_TOOL, self.zoom_out, t_zoom_out)

        t_full_extent = self.toolbar.AddTool(wx.ID_ANY, 'full_extent',
                                                  wx.Bitmap(self.gui_icons_dir + 'full_extent_24.png'))
        self.Bind(wx.EVT_TOOL, self.full_extent, t_full_extent, id=604)

        t_pan = self.toolbar.AddTool(wx.ID_ANY, 'pan',
                                          wx.Bitmap(self.gui_icons_dir + 'pan_24.png'))
        self.Bind(wx.EVT_TOOL, self.pan, t_pan)
        #
        # t_transparency_down = self.toolbar.AddTool(wx.ID_ANY, 'transparency_down',
        #                                                 wx.Bitmap(self.gui_icons_dir + 'large_left_24.png'))
        # self.Bind(wx.EVT_TOOL, self.transparency_decrease, t_transparency_down)
        #
        # t_transparency_up = self.toolbar.AddTool(wx.ID_ANY, 'transparency_up',
        #                                               wx.Bitmap(self.gui_icons_dir + 'large_right_24.png'))
        # self.Bind(wx.EVT_TOOL, self.transparency_increase, t_transparency_up)
        #
        self.toolbar.Realize()
        self.toolbar.SetSize((1790, 36))

    def draw_navigation_window(self):
        """# %INITALISE OBSERVED DATA AND LAYERS"""

        # self.tile = 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}.png'

        self.folium_map = folium.Map(location=[0.0, -180.0],
                                zoom_start=2,
                                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}.png',
                                attr='My Data Attribution')

        # self.folium_map.TitleLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}.png')


        self.folium_map.save("my_map.html")

        self.browser = wx.html2.WebView.New(self.rightPanelbottom, -1)
        self.browser.LoadURL('/Users/brook/Bathymetry/human_editing/GUI/my_map.html')

        """# %CREATE MPL FIGURE CANVAS"""
        mpl.rcParams['toolbar'] = 'None'

        # self.fig = plt.figure()  # %CREATE MPL FIGURE
        # self.fig = Basemap(projection='robin', lon_0=0.5 * (lons[0] + lons[-1]))

        # self.canvas = FigureCanvas(self.rightPanelbottom, -1, self.fig)  # %CREATE FIGURE CANVAS
        # self.nav_toolbar = NavigationToolbar(self.canvas)  # %CREATE NAVIGATION TOOLBAR
        # self.nav_toolbar.Hide()

        '#% SET DRAW COMMAND WHICH CAN BE CALLED TO REDRAW THE FIGURE'
        # self.draw = self.fig.canvas.draw

        '#% GET THE MODEL DIMENSIONS AND SAMPLE LOCATIONS'
        self.x1 = -90.
        self.x2 = 90.
        self.y1 = -180.
        self.y2 = 180.
        self.aspect = 1.

        '#% DRAW MAIN PROGRAM WINDOW'
        self.draw_main_frame()

        '#% DRAW BUTTON WINDOW'
        self.draw_button_and_list_frame()

        '#%CONNECT MPL FUNCTIONS'
        # self.connect_mpl_events()

        '#% UPDATE DISPLAY'
        # self.display_info()
        self.size_handler()

        '#% REFRESH SIZER POSITIONS'
        self.Hide()
        self.Show()

    def draw_main_frame(self):
        """# %DRAW THE PROGRAM CANVASES"""

        '#% CURRENT COORDINATES'
        self.window_font = wx.Font(16, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)  # % SET FONT
        '#  % SET LONGITUDE'
        self.longitude_text = wx.StaticText(self.rightPaneltop, -1, "Longitude (x):", style=wx.ALIGN_CENTER)
        self.longitude_text.SetFont(self.window_font)
        self.longitude = wx.TextCtrl(self.rightPaneltop, -1)

        '#  % SET LATITUDE'
        self.latitude_text = wx.StaticText(self.rightPaneltop, -1, "Latitude (y):")
        self.latitude_text.SetFont(self.window_font)
        self.latitude = wx.TextCtrl(self.rightPaneltop, -1)

        '#  % SET T VALUE'
        self.T_text = wx.StaticText(self.rightPaneltop, -1, "t:")
        self.T_text.SetFont(self.window_font)

        self.T = wx.TextCtrl(self.rightPaneltop, -1)

        '#%NAV CANVAS'
        # self.nav_canvas = plt.subplot2grid((20, 20), (2, 2), rowspan=17, colspan=17)
        # self.nav_canvas.set_xlabel("Longitude (dec. Degrees)")
        # self.nav_canvas.set_ylabel("Latitude (dec. Degrees)")
        # self.nav_canvas.set_xlim(-180., 180.)  # % SET X LIMITS
        # self.nav_canvas.set_ylim(-90, 90.)  # % SET Y LIMITS
        # self.nav_canvas.grid()
        # self.fig.subplots_adjust(top=1.05, left=-0.045, right=1.02, bottom=0.02,
        #                          hspace=0.5)
        # self.error = 0.
        # self.last_layer = 0

        '#% UPDATE INFO BAR'
        # self.display_info()

        '#%DRAW MAIN'
        # self.draw()

    def draw_button_and_list_frame(self):
        """#% CREATE LEFT HAND BUTTON MENU"""

        '# %BUTTON ONE'
        self.button_one = wx.Button(self.leftPanel_top, -1, "Load cm", style=wx.ALIGN_CENTER)

        '# %BUTTON TWO'
        self.button_two = wx.Button(self.leftPanel_top, -1, "Load Xcm", style=wx.ALIGN_CENTER)

        '# %BUTTON THREE'
        self.button_three = wx.Button(self.leftPanel_top, -1, "Load Predicted", style=wx.ALIGN_CENTER)

        '# %BUTTON THREE'
        self.button_four = wx.Button(self.leftPanel_top, -1, "3D Viewer", style=wx.ALIGN_CENTER)

        self.file_list_ctrl = wx.ListCtrl(self.leftPanel_bottom, -1, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_item_selected, self.file_list_ctrl)
        self.file_list_ctrl.InsertColumn(0, 'cm Files')

    def size_handler(self):
        """# %CREATE AND FIT BOX SIZERS (GUI LAYOUT)"""

        '# %ADD CURRENT COORDINATE BOXES'
        self.coordinate_box_sizer = wx.FlexGridSizer(cols=6, hgap=7, vgap=1)
        self.coordinate_box_sizer.AddMany([self.longitude_text, self.longitude, self.latitude_text, self.latitude,
                                           self.T_text, self.T])

        '# %ADD LIVE COORDINATE DATA BOX'
        self.box_right_top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_top_sizer.Add(self.coordinate_box_sizer, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        '# %ADD MAIN COORDINATE MAP BOX'
        self.box_right_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_right_bottom_sizer.Add(self.browser, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)
        # self.box_right_bottom_sizer.Add(self.canvas, 1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, border=2)

        '# %CREATE LAYER BUTTON BOX'
        self.left_box_top_sizer = wx.FlexGridSizer(cols=1, rows=4, hgap=8, vgap=8)
        self.left_box_top_sizer.AddMany([self.button_one, self.button_two, self.button_three, self.button_four])

        '# %CREATE FILE LIST BOX'
        self.left_box_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_box_bottom_sizer.Add(self.file_list_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        '# %CREATE LEFT SPLITTER PANEL SIZE (POPULATED WITH BUTTON BOX AND FILE LIST BOX)'
        self.splitter_left_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.splitter_left_panel_sizer.Add(self.leftPanel, 1, wx.EXPAND)

        '# %PLACE BOX SIZERS IN CORRECT PANELS'
        self.leftPanel_top.SetSizerAndFit(self.left_box_top_sizer)
        self.leftPanel_bottom.SetSizerAndFit(self.left_box_bottom_sizer)
        self.leftPanel.SetSizer(self.splitter_left_panel_sizer)
        self.rightPaneltop.SetSizerAndFit(self.box_right_top_sizer)
        self.rightPanelbottom.SetSizerAndFit(self.box_right_bottom_sizer)
        self.rightPaneltop.SetSize(self.GetSize())
        self.rightPanelbottom.SetSize(self.GetSize())

    def connect_mpl_events(self):
        """#% CONNECT MOUSE AND EVENT BINDINGS"""
        # self.fig.canvas.mpl_connect('button_press_event', self.button_press)
        # self.fig.canvas.mpl_connect('motion_notify_event', self.move)
        # self.fig.canvas.mpl_connect('button_release_event', self.button_release)
        # self.fig.canvas.mpl_connect('key_press_event', self.key_press)
        # self.fig.canvas.mpl_connect('pick_event', self.on_pick)

        self.button_one.Bind(wx.EVT_BUTTON, self.open_cm_file)
        self.button_two.Bind(wx.EVT_BUTTON, self.open_cm_directory)
        self.button_three.Bind(wx.EVT_BUTTON, self.open_predicted_cm_file)
        self.button_four.Bind(wx.EVT_BUTTON, self.plot_threed)

    # FIGURE DISPLAY FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def zoom(self, event):
        self.nav_toolbar.zoom()
        self.draw()

    def zoom_out(self, event):
        self.nav_toolbar.back()
        self.draw()

    def full_extent(self, event):
        """# %REDRAW MODEL FRAME WITH FULL EXTENT"""
        '#% SET CANVAS LIMITS'
        self.nav_canvas.set_xlim(self.cm[:, 1].min() - 0.2, self.cm[:, 1].max() + 0.2)
        self.nav_canvas.set_ylim(self.cm[:, 2].min() - 0.2, self.cm[:, 2].max() + 0.2)
        self.draw()

    def pan(self, event):
        """# %PAN MODEL VIEW USING MOUSE DRAG"""
        self.nav_toolbar.pan()
        self.draw()

    def aspect_increase(self, event):
        if self.aspect >= 1:
            self.aspect = self.aspect + 1
            self.set_nav_aspect()
            self.draw()
        elif 1.0 > self.aspect >= 0.1:
            self.aspect = self.aspect + 0.1
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def aspect_decrease(self, event):
        if self.aspect >= 2:
            self.aspect = self.aspect - 1
            self.set_nav_aspect()
            self.draw()
        elif 1.0 >= self.aspect >= 0.2:
            self.aspect = self.aspect - 0.1
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def aspect_increase2(self, event):
        self.aspect = self.aspect + 2
        self.set_nav_aspect()
        self.draw()

    def aspect_decrease2(self, event):
        if self.aspect >= 3:
            self.aspect = self.aspect - 2
            self.set_nav_aspect()
            self.draw()
        else:
            pass

    def set_nav_aspect(self):
        self.nav_canvas.set_aspect(self.aspect)

    # GUI INTERACTION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def access_sql(self):
        pass

    def open_cm_file(self, event):
        """# %GET CM FILE TO LOAD"""
        open_file_dialog = wx.FileDialog(self, "Open XY file", "", "", "All files (*.cm)|*.*", wx.FD_OPEN |
                                         wx.FD_FILE_MUST_EXIST)
        if open_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # %THE USER CHANGED THEIR MIND
        else:
            '# % IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
            try:
                self.cm_plot
            except AttributeError:
                pass
            else:
                self.delete_cm_file()

            '# % GET THE FILE NAME FROM FileDialog WINDOW'
            self.cm_file = open_file_dialog.GetPath()
            self.cm_filename = open_file_dialog.Filename  # % ASSIGN FILE

            '# % NOW LOAD THE DATA'
            self.load_cm_file()

    def color(self, input_elev):
        """SET COLOR FOR POINT PLOTTING"""
        color_input = -(float(input_elev) / 10000.)
        cmap = plt.cm.get_cmap('RdYlBu')
        norm = mpl.colors.Normalize(vmin=-10000.0, vmax=0.0)
        rgb = cmap(color_input)[:3]
        return (mpl.colors.rgb2hex(rgb))

    def load_cm_file(self):
        """LOAD .cm FILE DATA INTO PROGRAM"""
        try:
            self.colorbar = plt.cm.get_cmap('RdYlBu')
            self.cm = np.genfromtxt(self.cm_file, delimiter=' ', dtype=float, filling_values=-9999)  # % LOAD FILE
            # self.cm_plot = self.nav_canvas.scatter(self.cm[:, 1], self.cm[:, 2], marker='o', s=1, c=self.cm[:, 3],
            #                                        cmap=self.colorbar, label=self.cm[:, 3])

            # myStyle = {
            #     "color": "#ff7800",
            #     "weight": 5,
            #     "opacity": 0.65
            # }
            #
            # data = {
            #     'type': 'FeatureCollection',
            #     'features': [
            #         {
            #             'type': 'Feature',
            #             'geometry': {
            #                 'type': 'MultiPoint',
            #                 'coordinates': [[lon, lat] for (lat, lon) in zip(self.cm[:, 2], self.cm[:, 1])],
            #             },
            #             'properties': {'prop0': 'value0'}
            #         },
            #     ],
            # }
            # self.folium_map.add_child(features.GeoJson(data, style=myStyle))

            fg = folium.FeatureGroup(name="cm_file")

            for lat, lon, elev, name in zip(self.cm[:, 2], self.cm[:, 1], self.cm[:, 3], self.cm[:, 4]):
                folium.CircleMarker(location=[lat, lon], radius=1, popup=None, fill=True,
                                    color=self.color(elev)).add_to(fg)

            self.folium_map.add_child(fg)

            self.folium_map.save("my_map.html")
            self.browser.LoadURL('/Users/brook/Bathymetry/human_editing/GUI/my_map.html')

            # '# % SET WINDOW DIMENSIONS TO FIT CURRENT SURVEY'
            # self.nav_canvas.set_xlim(self.cm[:, 1].min()-0.2, self.cm[:, 1].max()+0.2)
            # self.nav_canvas.set_ylim(self.cm[:, 2].min()-0.2, self.cm[:, 2].max()+0.2)

        except IndexError:
            error_message = "ERROR IN LOADING PROCESS - FILE MUST BE ASCII SPACE DELIMITED"
            wx.MessageDialog(self, -1, error_message, "Load Error")
            raise

        '# %GET DATA AS cm FILE DATA AS NUMPY ARRAYS'
        self.xyz = self.cm[:, 1:4]
        self.xyz = np.divide(self.xyz, (1.0, 1.0, 10000.0))  # % DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X&Z
        self.xyz_cm_id = self.cm[:, 0].astype(int)  # % GET CM FILE IDs
        self.xyz_width = self.cm.shape[1]
        self.xyz_meta_data = self.cm[:, 4:self.xyz_width]
        self.xyz_point_flags = np.zeros(shape=(1, len(self.xyz)))
        self.xyz_cm_line_number = np.linspace(0, len(self.xyz), (len(self.xyz)+1))

        '# % If THREE DIMENSIONAL VIEWER IS OPEN, THEN CLOSE IT AND REOPEN WITH NEW .cm FILE'
        try:
            self.tdv
        except AttributeError:
            pass
        else:
            self.reload_threed()

        '# %UPDATE MPL CANVAS'
        # self.draw()

    def delete_cm_file(self):
        """" # %DELETE CURRENT .cm FILE SO THE NEWLY SELECTED .cm FILE CAN BE LOADED INTO THE VIEWERS"""

        '# % REMOVE .cm DATA from MAP FRAME'
        del self.cm_file
        del self.cm
        self.cm_plot.set_visible(False)
        self.cm_plot.remove()
        del self.cm_plot

        '# % REMOVE .cm DATA from MAP FRAME'
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
        self.active_dir = folder_path  # % SET .cm DIR
        paths = glob.glob(folder_path + "/*.cm")  # % GET ALL .cm file names
        for index, path in enumerate(paths):
            self.file_list_ctrl.InsertItem(index, os.path.basename(path))
        dlg.Destroy()

    def list_item_selected(self, event):
        """ACTIVATED WHEN A FILE FROM THE LIST CONTROL IS SELECTED"""

        file = event.GetText()
        self.selected_file = str(self.active_dir)+"/"+str(file)
        print(self.selected_file)

        '# % IF A .cm FILE IS ALREADY LOADED THEN REMOVE IT BEFORE LOADING THE CURRENT FILE'
        try:
            self.cm_plot
        except AttributeError:
            pass
        else:
            self.delete_cm_file()

        '# %LOAD NEW .cm FILE DATA INTO VIEWERS'
        self.cm_file = self.selected_file
        self.load_cm_file()

    def open_predicted_cm_file(self, event):
        """# %LOAD & PLOT XY DATA E.G. EQ HYPOCENTERS"""

        open_file_dialog = wx.FileDialog(self, "Open XY file", "", "", "All files (*.cm)|*.*", wx.FD_OPEN |
                                         wx.FD_FILE_MUST_EXIST)
        if open_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # %THE USER CHANGED THEIR MIND
        else:
            predicted_cm_file = open_file_dialog.GetPath()
            self.predicted_cm_filename = open_file_dialog.Filename  # % ASSIGN FILE

        try:
            self.predicted_cm = np.genfromtxt(predicted_cm_file, delimiter=' ', dtype=float, filling_values=-9999)
            self.predicted_cm_plot = self.nav_canvas.scatter(self.predicted_cm[:, 1], self.predicted_cm[:, 2],
                                                             marker='o', s=0.5, c=self.predicted_cm[:, 3],
                                                             cmap=self.colorbar)

            #  % SET WINDOW DIMENSIONS TO FIT CURRENT SURVEY
            self.nav_canvas.set_xlim(self.cm[:, 1].min()-0.2, self.cm[:, 1].max()+0.2)
            self.nav_canvas.set_ylim(self.cm[:, 2].min()-0.2, self.cm[:, 2].max()+0.2)
        except IndexError:
            error_message = "ERROR IN LOADING PROCESS - FILE MUST BE ASCII SPACE DELIMITED"
            wx.MessageDialog(self, -1, error_message, "Load Error")
            raise

        self.draw()
        self.aspect = 1
        self.set_nav_aspect()
        self.draw()

        '# %GET DATA AS cm FILE DATA AS NUMPY ARRAYS'
        self.predicted_xyz = self.predicted_cm[:, 1:4]
        self.predicted_xyz = np.divide(self.predicted_xyz, (1.0, 1.0, 10000.0))  # %DIVIDE TO MAKE Z SCALE ON SAME
        '# %ORDER OF MAG AS X&Z'
        self.id = self.predicted_xyz[:, 0]  # %GET CM FILE IDs
        self.predicted_xyz_width = self.predicted_cm.shape[1]
        self.predicted_xyz_meta_data = self.predicted_cm[:, 4:self.xyz_width]

    def button_three(self, event):
        self.plot_threed()
        # self.SetTitle("STL File Viewer: " + self.p1.filename)
        # self.statusbar.SetStatusText("Use W,S,F,R keys and mouse to interact with the model ")

    def plot_threed(self, event):
        """PLOT 3D VIEW OF DATA"""

        '# %ATTEMPT TO OPEN PREDICTED XYZ BATHYMETRY DATA'
        try:
            self.predicted_xyz = self.predicted_cm[:, 1:4]
            self.predicted_xyz = np.divide(self.predicted_xyz, (1.0, 1.0, 10000.0))
        except AttributeError:
            self.predicted_xyz = None

        '# %OPEN A vtk 3D VIEWER WINDOW AND CREATE A RENDER'
        self.tdv = ThreeDimViewer(self, -1, 'Modify Current Model', self.cm, self.xyz, self.xyz_cm_id, self.xyz_meta_data,
                                  self.xyz_point_flags, self.xyz_cm_line_number, self.predicted_xyz)
        self.tdv.Show(True)

    def reload_threed(self):
        """REMOVE 3D VIEWER AND REPLACE WITH NEWLY LOADED DATA"""
        self.tdv.Show(False)
        del self.tdv
        self.plot_threed(self)

    # DOCUMENTATION~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def open_documentation(self, event):
        """# %OPENS DOCUMENTATION HTML"""
        new = 2
        doc_url = os.path.dirname(__file__) + '/docs/_build/html/manual.html'
        webbrowser.open(doc_url, new=new)

    def about_pycmeditor(self, event):
        """# %SHOW SOFTWARE INFORMATION"""
        about = "About PyCMeditor"
        dlg = wx.MessageDialog(self, about, "About", wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

    def legal(self, event):
        """# %SHOW LICENCE"""
        licence = ["Copyright 2018 Brook Tozer \n\nRedistribution and use in source and binary forms, with or "
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
        """# %SHUTDOWN APP (FROM FILE MENU)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

    def on_close_button(self, event):
        """# %SHUTDOWN APP (X BUTTON)"""
        dlg = wx.MessageDialog(self, "Do you really want to exit", "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.Destroy()
            wx.GetApp().ExitMainLoop()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ThreeDimViewer(wx.Frame):
    def __init__(self, parent, id, title, cm, xyz, xyz_cm_id, xyz_meta_data, xyz_point_flags,
                                                                    xyz_cm_line_number, predicted_xyz_file):
        wx.Frame.__init__(self, None, wx.ID_ANY, '3D Viewer', size=(1500, 1100))

        '# %START AUI WINDOW MANAGER'
        self.tdv_mgr = aui.AuiManager()

        '# %TELL AUI WHICH FRAME TO USE'
        self.tdv_mgr.SetManagedWindow(self)

        '# %CREATE PANEL TO FILL WITH COORDINATE INFORMATION'
        self.tdv_top_panel = wx.Panel(self, -1, size=(1350, 1100), style=wx.ALIGN_RIGHT | wx.BORDER_RAISED | wx.EXPAND)
        self.tdv_top_panel.SetBackgroundColour('blue')

        '# %CREATE PANEL TO FILL WITH MATPLOTLIB INTERACTIVE FIGURE (MAIN NAVIGATION FRAME)'
        self.tdv_left_panel = wx.Panel(self, -1, size=(150, 1100), style=wx.ALIGN_RIGHT | wx.BORDER_RAISED)
        self.tdv_left_panel.SetBackgroundColour('grey')

        '# %ADD THE PANES TO THE AUI MANAGER'
        self.tdv_mgr.AddPane(self.tdv_top_panel, aui.AuiPaneInfo().Name('top').CenterPane())
        self.tdv_mgr.AddPane(self.tdv_left_panel, aui.AuiPaneInfo().Name('left').Left())
        self.tdv_mgr.Update()

        ' # % SET Renderer AS OBJECT'
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.8, 0.8, 0.8)

        '# % ASSIGN RENDER WINDOW OBJECTS'
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        self.Interactor = wxVTKRenderWindowInteractor(self.tdv_top_panel, -1)
        self.Interactor.SetRenderWindow(self.renderWindow)
        # self.Interactor.RemoveObservers('KeyPressEvent')
        self.Interactor.RemoveObservers('CharEvent')

        '# % SET VTK OBSERVERS'
        self.Interactor.AddObserver("KeyPressEvent", self.keyPressEvent)

        '# % SET RENDERER CAMERA AS OBJECT'
        self.cam = vtk.vtkCamera()
        self.renderer.SetActiveCamera(self.cam)

        '# % SET DEFAULT INTERACTION STYLE'
        self.base_style = vtk.vtkInteractorStyleTrackballCamera()
        self.Interactor.SetInteractorStyle(self.base_style)
        self.current_style = str('base_style')

        ' # % ADD Interactor WINDOW TO TOP BOX'
        self.box_top = wx.BoxSizer(wx.VERTICAL)
        self.box_top.Add(self.Interactor, 1, wx.ALIGN_CENTRE | wx.EXPAND)

        '# % ADD MOUSE INTERACTION TOOLS --------------------------------------------------------'
        # PASS

        '# % CREATE TOOL BUTTONS ----------------------------------------------------------------'

        '# % PICKER BUTTON'
        self.picker_button = wx.Button(self.tdv_left_panel, -1, "Picking mode", size=(150, 20),
                                       style=wx.ALIGN_CENTRE)
        self.picker_button.Bind(wx.EVT_BUTTON, self.rubber_picker)

        '# % X SCALE SIZER SLIDER'
        self.x_scale_text = wx.StaticText(self.tdv_left_panel, -1, "X-scale", style=wx.ALIGN_CENTRE)
        self.x_scale_slider = wx.Slider(self.tdv_left_panel, value=2.0, minValue=1.0, maxValue=20., size=(150, 20),
                                         style=wx.SL_HORIZONTAL)
        self.x_scale_slider.Bind(wx.EVT_SLIDER, self.set_x_scale)

        '# % Y SCALE SIZER SLIDER'
        self.y_scale_text = wx.StaticText(self.tdv_left_panel, -1, "Y-scale", style=wx.ALIGN_CENTRE)
        self.y_scale_slider = wx.Slider(self.tdv_left_panel, value=2.0, minValue=1.0, maxValue=20., size=(150, 20),
                                         style=wx.SL_HORIZONTAL)
        self.y_scale_slider.Bind(wx.EVT_SLIDER, self.set_y_scale)

        '# % Z SCALE SIZER SLIDER'
        self.z_scale_text = wx.StaticText(self.tdv_left_panel, -1, "Z-scale", style=wx.ALIGN_CENTRE)
        self.z_scale_slider = wx.Slider(self.tdv_left_panel, value=2.0, minValue=1.0, maxValue=20., size=(150, 20),
                                         style=wx.SL_HORIZONTAL)
        self.z_scale_slider.Bind(wx.EVT_SLIDER, self.set_z_scale)

        '# % POINT SIZER SLIDER'
        self.size_text = wx.StaticText(self.tdv_left_panel, -1, "Point size", style=wx.ALIGN_CENTRE)
        self.size_slider = wx.Slider(self.tdv_left_panel, value=4.0, minValue=1.0, maxValue=10., size=(150, 20),
                                         style=wx.SL_HORIZONTAL)
        self.size_slider.Bind(wx.EVT_SLIDER, self.set_point_size)

        '# % ADD FLAG BUTTON'
        self.flag_button = wx.Button(self.tdv_left_panel, -1, "Set Flag", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.flag_button.Bind(wx.EVT_BUTTON, self.set_flag)

        '# % ADD DELAUNAY BUTTON'
        self.delaunay_button = wx.Button(self.tdv_left_panel, -1, "Grid", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.delaunay_button.Bind(wx.EVT_BUTTON, self.delaunay)

        '# % ADD PREDICTED DELAUNAY BUTTON'
        self.predicted_delaunay_button = wx.Button(self.tdv_left_panel, -1, "Grid Predicted", size=(150, 20),
                                                   style=wx.ALIGN_CENTRE)
        self.predicted_delaunay_button.Bind(wx.EVT_BUTTON, self.render_predicted)

        '# % ADD DELETE SELECTED BUTTON'
        self.delete_selected_button = wx.Button(self.tdv_left_panel, -1, "Delete", size=(150, 20),
                                                style=wx.ALIGN_CENTRE)
        self.delete_selected_button.Bind(wx.EVT_BUTTON, self.delete_selected)

        '# % ADD SAVE CM BUTTON'
        self.save_cm_button = wx.Button(self.tdv_left_panel, -1, "Save .cm", size=(150, 20), style=wx.ALIGN_CENTRE)
        self.save_cm_button.Bind(wx.EVT_BUTTON, self.save_cm)

        ' #% ADD BUTTONS ETC TO LEFT BOX'
        self.left_box = wx.FlexGridSizer(cols=1, rows=15, hgap=5, vgap=5)
        self.left_box.AddMany([self.picker_button, self.x_scale_text, self.x_scale_slider, self.y_scale_text,
                               self.y_scale_slider, self.z_scale_text, self.z_scale_slider, self.size_text,
                               self.size_slider, self.flag_button, self.delaunay_button, self.predicted_delaunay_button,
                               self.delete_selected_button, self.save_cm_button])

        '# % RENDER THE XYZ DATA IN 3D'
        self.cm = cm
        self.xyz = xyz
        self.xyz_cm_id = xyz_cm_id
        self.xyz_meta_data = xyz_meta_data
        self.xyz_point_flags = xyz_point_flags
        self.xyz_cm_line_number = xyz_cm_line_number
        '# % DO THE RENDER OF THE PONIT DATA'
        self.do_point_render()

        '#  % MAKE THE PREDICTED XYZ DATA AN OBJECT'
        self.predicted_xyz_file = predicted_xyz_file

        '# % SET SIZERS'
        # self.tdv_sizer()

        # '# % CREATE VTK PICKER OBJECTS'
        # self.cell_picker = vtk.vtkCellPicker()
        # self.node_picker = vtk.vtkPointPicker()
        # self.cell_picker.SetTolerance(0.001)
        # self.node_picker.SetTolerance(0.001)
        #
        # self.area_picker = vtk.vtkAreaPicker()  # vtkRenderedAreaPicker?
        # self.rubber_band_style = vtk.vtkInteractorStyleRubberBandPick()

        '# % SET PICKER STYLE - SO LEFT MOUSE CLICK ALLOWS SELECTION OF A SINGLE POINT'
        # self.picker_style = MouseInteractorHighLightActor(self.renderWindow, self.pointcloud)
        # self.picker_style.SetDefaultRenderer(self.renderer)
        # self.Interactor.SetInteractorStyle(self.picker_style)
        # self.Interactor.AddObserver("LeftButtonPressEvent", self.picker_style.leftButtonPressEvent)        self.area_picker = vtk.vtkAreaPicker()

        '#PLACE BOX SIZERS IN CORRECT PANELS'
        self.tdv_top_panel.SetSizerAndFit(self.box_top)
        self.tdv_left_panel.SetSizerAndFit(self.left_box)
        self.tdv_top_panel.SetSize(self.GetSize())
        self.tdv_left_panel.SetSize(self.GetSize())

        '# % INITIZE SWITCHES'
        self.grid_created = 0

        '# % UPDATE AUI MANGER'
        self.tdv_mgr.Update()

    def do_point_render(self):
        """
        # % RENDER 3D POINTS
        *** arg1 = XYZ NUMPY ARRAY
        """

        '  # %Render XYZ POINTS'
        self.x_scale = 1
        self.y_scale = 1
        self.z_scale = 1  # SET SCALE VALUE FOR Z-AXIS (CAN BE MODIFIED IN VIEWER USING SLIDING BAR)
        self.pointcloud = VtkPointCloud(self.xyz, self.xyz_cm_id, self.xyz_meta_data,
                                        self.xyz_cm_line_number, self.xyz_point_flags, self.cm)
        for k in range(len(self.xyz)):
            point = self.xyz[k]
            xyz_cm_id = self.xyz_cm_id[k]
            xyz_cm_line_number = self.xyz_cm_line_number[k]
            self.pointcloud.addPoint(point, xyz_cm_id, xyz_cm_line_number)

        '# % ADD ACTOR TO RENDER'
        self.renderer.AddActor(self.pointcloud.vtkActor)

        '# % SET POINT SIZE'
        self.pointcloud.vtkActor.GetProperty().SetPointSize(4)

        '# % Add 3D AXES WIDGET'
        self.axesactor = vtk.vtkAxesActor()
        self.axes = vtk.vtkOrientationMarkerWidget()
        self.axes.SetOrientationMarker(self.axesactor)
        self.axes.SetInteractor(self.Interactor)
        self.axes.EnabledOn()
        self.axes.InteractiveOn()
        self.renderer.ResetCamera()

        '#  % CREATE SCALE BAR'
        self.cb_mapper = self.pointcloud.vtkActor.GetMapper()
        self.cb_mapper.SetScalarRange(self.xyz[:,2].min(), self.xyz[:,2].max())

        self.sb = vtk.vtkScalarBarActor()
        self.sb.SetLookupTable(self.cb_mapper.GetLookupTable())
        self.renderer.AddActor(self.sb)
        self.sb.SetAnnotationTextScaling(100)
        self.sb.SetTitle("Depth (m)")
        self.sb.SetLabelFormat("%0.1f")
        self.sb.SetOrientationToHorizontal()
        self.sb.SetWidth(0.3)
        self.sb.SetHeight(0.05)
        self.sb.GetPositionCoordinate().SetValue(0.7, 0.05)

        '#  % CREATE XYZ OUTLINE AXES GRID'
        self.outlineMapper = self.pointcloud.vtkActor.GetMapper()
        self.outlineActor = vtk.vtkCubeAxesActor()
        self.outlineActor.SetBounds(self.xyz[:, 0].min(), self.xyz[:, 0].max(),
                                    self.xyz[:, 1].min(), self.xyz[:, 1].max(),
                                    self.xyz[:, 2].min(), self.xyz[:, 2].max())

        self.outlineActor.SetCamera(self.renderer.GetActiveCamera())
        self.outlineActor.SetMapper(self.outlineMapper)
        self.outlineActor.DrawXGridlinesOn()
        self.outlineActor.DrawYGridlinesOn()
        self.outlineActor.DrawZGridlinesOn()
        self.renderer.AddActor(self.outlineActor)

        # '#  % CREATE BALLOON INFO WIDGET'
        # self.balloonRep = vtk.vtkBalloonRepresentation()
        # self.balloonRep.SetBalloonLayoutToImageRight()
        # self.balloonWidget = vtk.vtkBalloonWidget()
        # self.balloonWidget.SetInteractor(self.Interactor)
        # self.balloonWidget.SetRepresentation(self.balloonRep)
        # self.balloonWidget.AddBalloon(self.pointcloud.vtkActor, self.pointcloud.cm_poly_data.GetPoints().GetPoint())

    def delaunay(self, event):
        """CREATE 3D GRID"""
        if self.grid_created == 1:
            if self.meshActor.GetVisibility() == 1:
                self.meshActor.SetVisibility(False)
            else:
                self.meshActor.SetVisibility(True)
            self.renderWindow.Render()
            print("meshActor exists")
        else:
            self.grid_created = 1
            self.cell_array = vtk.vtkCellArray()
            self.boundary = self.pointcloud.cm_poly_data
            self.boundary.SetPoints(self.pointcloud.cm_poly_data.GetPoints())
            self.boundary.SetPolys(self.cell_array)

            self.delaunay = vtk.vtkDelaunay2D()

            self.delaunay.SetInputData(self.pointcloud.cm_poly_data)
            self.delaunay.SetSourceData(self.boundary)

            self.delaunay.Update()

            self.meshMapper = vtk.vtkPolyDataMapper()
            self.meshMapper.SetInputData(self.pointcloud.cm_poly_data)
            self.meshMapper.SetColorModeToDefault()
            self.meshMapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
            self.meshMapper.SetScalarVisibility(1)
            self.meshMapper.SetInputConnection(self.delaunay.GetOutputPort())
            self.meshActor = vtk.vtkActor()
            self.meshActor.SetMapper(self.meshMapper)
            # self.meshActor.GetProperty().SetEdgeColor(0, 0, 1)
            self.meshActor.GetProperty().SetInterpolationToFlat()
            # self.meshActor.GetProperty().SetRepresentationToWireframe()

            self.renderer.AddActor(self.meshActor)
            self.renderWindow.Render()

    def render_predicted(self, event):

        if self.predicted_xyz_file is not None:
            '  # %Render XYZ POINTS'
            self.predicted_pointcloud = VtkPointCloud(self.predicted_xyz_file)
            for k in range(size(self.predicted_xyz_file, 0)):
                point = self.predicted_xyz_file[k]
                self.predicted_pointcloud.addPoint(point)

            # self.renderer.AddActor(self.predicted_pointcloud.vtkActor)

            self.delaunay_predicted()

            self.renderWindow.Render()

    def delaunay_predicted(self):
        """CREATE GRID OF PREDICTED BATHYMETRY"""
        try:
            if self.predicted_meshActor.GetVisibility() == 1:
                self.predicted_meshActor.SetVisibility(False)
            else:
                self.predicted_meshActor.SetVisibility(True)
            self.renderWindow.Render()
            print("predicted_meshActor exists")
        except AttributeError:
            self.cell_array = vtk.vtkCellArray()
            self.boundary = self.predicted_pointcloud.cm_poly_data
            self.boundary.SetPoints(self.predicted_pointcloud.cm_poly_data.GetPoints())
            self.boundary.SetPolys(self.cell_array)

            self.delaunay = vtk.vtkDelaunay2D()
            if vtk.VTK_MAJOR_VERSION <= 5:
                self.delaunay.SetInput(self.predicted_pointcloud.cm_poly_data.GetOutput())
                self.delaunay.SetSource(self.boundary)
            else:
                self.delaunay.SetInputData(self.predicted_pointcloud.cm_poly_data)
                self.delaunay.SetSourceData(self.boundary)

            self.delaunay.Update()

            self.meshMapper = vtk.vtkPolyDataMapper()
            self.meshMapper.SetInputData(self.predicted_pointcloud.cm_poly_data)
            self.meshMapper.SetColorModeToDefault()
            self.meshMapper.SetScalarRange(self.predicted_xyz_file[:, 2].min(), self.predicted_xyz_file[:, 2].max())
            self.meshMapper.SetScalarVisibility(1)
            self.meshMapper.SetInputConnection(self.delaunay.GetOutputPort())
            self.predicted_meshActor = vtk.vtkActor()
            self.predicted_meshActor.SetMapper(self.meshMapper)
            self.predicted_meshActor.GetProperty().SetInterpolationToFlat()

            self.renderer.AddActor(self.predicted_meshActor)
            self.renderWindow.Render()

    def set_point_size(self, value):
        self.size = float(self.size_slider.GetValue())
        self.pointcloud.vtkActor.GetProperty().SetPointSize(self.size)
        self.pointcloud.vtkActor.Modified()
        self.renderWindow.Render()
        return

    def set_z_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        '#% GET THE NEW SCALE VALUE'
        self.z_scale = float(self.z_scale_slider.GetValue())

        '# % REPLACE CURRENT RENDER WITH NEW DATA'
        self.re_render()

        self.pointcloud.vtkActor.Modified()
        self.renderWindow.Render()
        return

    def set_x_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        '#% GET THE NEW SCALE VALUE'
        self.x_scale = float(self.x_scale_slider.GetValue())

        '# % REPLACE CURRENT RENDER WITH NEW DATA'
        self.re_render()

        self.pointcloud.vtkActor.Modified()
        self.renderWindow.Render()
        return

    def set_y_scale(self, value):
        """RESCALE THE Z-AXIS OF THE 3D PLOT"""

        '#% GET THE NEW SCALE VALUE'
        self.y_scale = float(self.y_scale_slider.GetValue())

        '# % REPLACE CURRENT RENDER WITH NEW DATA'
        self.re_render()

        self.pointcloud.vtkActor.Modified()
        self.renderWindow.Render()
        return

    def rubber_picker(self, event):
        # print("r key pressed")
        print("current style = %s" % self.current_style)

        if self.current_style is 'rubber_band':
            '# % REMOVE THE CURRENT HIGHLIGHT ACTOR (IF THERE IS ONE) FROM SCREEN'
            if self.rubber_style.selected_actor:
                self.renderer.RemoveActor(self.rubber_style.selected_actor)
                del self.rubber_style.selected_actor

            print('setting style as base_style')
            self.Interactor.SetInteractorStyle(self.base_style)
            self.current_style = str('base_style')

            self.cam.SetFocalPoint(self.focal_point)
            self.cam.SetPosition(self.positon)
            self.cam.SetViewUp(self.view_up)
            self.cam.SetViewAngle(self.view_angle)
            self.cam.SetParallelProjection(self.parallel_projection)
            self.cam.SetParallelScale(self.parallel_scale)
            self.cam.SetClippingRange(self.clip)

            self.renderer.Render()
            self.renderWindow.Render()

        else:
            print('setting style as rubber_band')
            self.area_picker = vtk.vtkAreaPicker()
            self.Interactor.SetPicker(self.area_picker)
            self.rubber_style = RubberBand(self.renderWindow, self.renderer, self.pointcloud, self.Interactor,
                                           self.area_picker, self.cm)
            self.Interactor.SetInteractorStyle(self.rubber_style)
            self.current_style = str('rubber_band')

    def delete_selected(self, event):
        """CREATES A NEW NUMPY ARRAY of the cm FILE WITH SELECTED NODES REMOVED"""
        print("Deleting")
        try:
            '# % DELETE SELECTED VALUES'
            self.selected_cm_line_number = vtk_to_numpy(
                                    self.rubber_style.selected.GetPointData().GetArray("cm_line_number")).astype(int)
            self.new_cm = np.delete(self.cm, self.selected_cm_line_number, 0)
            self.cm = self.new_cm

            '# % REPLACE CURRENT RENDER WITH NEW DATA'
            self.renderer.RemoveActor(self.rubber_style.selected_actor)
            self.re_render()

            '# % UPDATE RENDER'
            self.renderWindow.Render()

        except AttributeError:
            print("attr error")
            pass

    def set_flag(self, event):
        """SETS FLAG FOR SELECTED NODES"""
        print("SETTING FLAG")
        try:
            '# % DELETE SELECTED VALUES'
            self.selected_cm_line_number = vtk_to_numpy(
                                    self.rubber_style.selected.GetPointData().GetArray("cm_line_number")).astype(int)

            '# % CLONE CURRENT cm file'
            self.new_cm = np.copy(self.cm)

            '# %SET FLAG AS 1 FOR ALL SELECTED NODES'
            flag_column_index = np.shape(self.cm)[1]
            for x in range(len(self.selected_cm_line_number)):
                index = self.selected_cm_line_number[x]  # % GET INDEX VALUE
                self.new_cm[index, 4] = 1  # % INSERT FLAG IN COL 1

            '# % REMOVE SELECTED ACTOR'
            self.renderer.RemoveActor(self.rubber_style.selected_actor)

            '# % DRAW FLAGGED ACTOR'
            self.rubber_style.flagged_mapper = vtk.vtkDataSetMapper()
            self.rubber_style.flagged_actor = vtk.vtkActor()
            self.rubber_style.flagged_actor.SetMapper(self.rubber_style.flagged_mapper)
            self.rubber_style.flagged_mapper.SetInputData(self.rubber_style.selected)
            self.rubber_style.flagged_actor.GetMapper().ScalarVisibilityOff()
            self.rubber_style.flagged_actor.GetProperty().SetColor(0, 0, 0)  # (R, G, B)
            self.rubber_style.flagged_actor.GetProperty().SetPointSize(10)
            self.renderer.AddActor(self.rubber_style.flagged_actor)

            '# % REPLACE CURRENT RENDER WITH NEW DATA'
            self.re_render()

            '# % UPDATE LIVE RENDER'
            self.renderWindow.Render()

        except AttributeError:
            print("attr error")
            pass

    def save_cm(self, event):
        """# %SET OUTPUT FILE NAME AND DIR"""
        save_file_dialog = wx.FileDialog(self, "Save edited .cm file", "", "", ".cm file (*.cm)|*.cm",
                                         wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if save_file_dialog.ShowModal() == wx.ID_CANCEL:
            return  # %THE USER CHANGED THEIR MIND

        '# %SAVE TO DISC'
        outputfile = save_file_dialog.GetPath()
        np.savetxt(outputfile, self.cm, delimiter=" ")

    def re_render(self):
        """
        # % RE RENDER 3D POINTS AFTER REMOVING SELECTION
        """
        print("re rendering")
        self.renderer.RemoveActor(self.pointcloud.vtkActor)
        del self.pointcloud.vtkActor

        self.xyz = self.cm[:, 1:4]
        self.xyz = np.divide(self.xyz, (1.0/self.x_scale, 1.0/self.y_scale, 10000.0/self.z_scale))  # % DIVIDE TO MAKE Z SCALE ON SAME ORDER OF MAG AS X&Z
        self.xyz_cm_id = self.cm[:, 0].astype(int)  # % GET CM FILE IDs
        self.xyz_width = self.cm.shape[1]
        self.xyz_meta_data = self.cm[:, 4:self.xyz_width]
        self.xyz_point_flags = np.zeros(shape=(1, len(self.xyz)))
        self.xyz_cm_line_number = np.linspace(0, len(self.xyz), (len(self.xyz)+1))

        '  # %Render XYZ POINTS'
        del self.pointcloud
        self.pointcloud = VtkPointCloud(self.xyz, self.xyz_cm_id, self.xyz_meta_data,
                                        self.xyz_cm_line_number, self.xyz_point_flags, self.cm)
        for k in range(len(self.xyz)):
            point = self.xyz[k]
            xyz_cm_id = self.xyz_cm_id[k]
            xyz_cm_line_number = self.xyz_cm_line_number[k]
            self.pointcloud.addPoint(point, xyz_cm_id, xyz_cm_line_number)

        self.renderer.AddActor(self.pointcloud.vtkActor)
        self.set_point_size(float(self.size_slider.GetValue()))

        '#% CHECK IF GRID ACTOR IS ON'
        if self.grid_created == 1:
            self.grid_created = 0
            self.renderer.AddActor(self.meshActor)

        '# % SET ACTIVE CAM'
        self.renderer.SetActiveCamera(self.cam)

        '#% RESCALE THE AXIS OUTLINE'
        self.outlineActor.SetBounds(self.xyz[:, 0].min(), self.xyz[:, 0].max(),
                                    self.xyz[:, 1].min(), self.xyz[:, 1].max(),
                                    self.xyz[:, 2].min(), self.xyz[:, 2].max())

        # self.Interactor.RemoveObservers('KeyPressEvent')
        # self.Interactor.RemoveObservers('CharEvent')

    def keyPressEvent(self, obj, event):
        key = self.Interactor.GetKeyCode()
        # key = self.Interactor.GetKeySym()
        '''# %ACTIVATE POINT PICKER'''
        if key == 'r':
            print("!!!!!!!")
            print("get cam")
            print("!!!!!!!!")
            self.focal_point = self.cam.GetFocalPoint()
            self.positon = self.cam.GetPosition()
            self.view_up = self.cam.GetViewUp()
            self.view_angle = self.cam.GetViewAngle()
            self.parallel_projection = self.cam.GetParallelProjection()
            self.parallel_scale = self.cam.GetParallelScale()
            self.clip = self.cam.GetClippingRange()
            print(self.focal_point)
            print(self.positon)
            print(self.view_up)
            print(self.view_angle)
            print(self.parallel_projection)
            print(self.parallel_scale)
            print(self.clip)
            self.rubber_picker(obj)

            self.set_cam()

        if key == 'd':
            self.delete_selected(obj)

        if key == 'c':
            self.set_cam()
    # def middleButtonPressEvent(self, obj, event):
    #     print("Middle Button pressed")
    #     self.OnMiddleButtonDown()
    #     return
    #
    # def middleButtonReleaseEvent(self, obj, event):
    #     print("Middle Button released")
    #     self.OnMiddleButtonUp()
    #     return

    def set_cam(self):
        print("##########")
        print("set_cam")
        print("##########")
        print(self.focal_point)
        print(self.positon)
        print(self.view_up)
        print(self.view_angle)
        print(self.parallel_projection)
        print(self.parallel_scale)
        print(self.clip)

        self.cam.SetFocalPoint(self.focal_point)
        self.cam.SetPosition(self.positon)
        self.cam.SetViewUp(self.view_up)
        self.cam.SetViewAngle(self.view_angle)
        self.cam.SetParallelProjection(self.parallel_projection)
        self.cam.SetParallelScale(self.parallel_scale)
        self.cam.SetClippingRange(self.clip)


class VtkPointCloud:
    def __init__(self, xyz, xyz_cm_id, xyz_meta_data, xyz_cm_line_number, xyz_point_flags, cm,
                 maxNumPoints=10e6):
        """CREATE vtk PointCloud (XYZ SCATTER PLOT OF BATHYMETRY DATA"""

        '# %INITIALISE POINT DATA'
        self.cm = cm
        self.xyz = xyz  # % THIS IS THE XYZ DATA
        self.xyz_cm_id = xyz_cm_id  # % THIS IS THE .cm ID
        self.xyz_meta_data = xyz_meta_data  # % THIS CONTAINS ALL ADDITIONAL COLUMNS
        self.xyz_cm_line_number = xyz_cm_line_number
        self.xyz_point_flags = xyz_point_flags
        self.maxNumPoints = maxNumPoints

        '# %CREATE vtkPolyData OBJECT'
        self.cm_poly_data = vtk.vtkPolyData()

        self.xyz_points = vtk.vtkPoints()
        self.cm_poly_data.SetPoints(self.xyz_points)

        '# %CREATE vtkPolyData VERTICES'
        self.xyz_cells = vtk.vtkCellArray()
        self.cm_poly_data.SetVerts(self.xyz_cells)
        # self.xyz_cells.SetName('XYArray')

        '# %CREATE vtkPolyData SCALAR VALUES'

        '# % SCALAR 1 = cm file line number - This is used for numpy array data manipulation'
        self.cm_line_number = vtk.vtkDoubleArray()
        self.cm_line_number.SetName('cm_line_number')
        self.cm_poly_data.GetPointData().AddArray(self.cm_line_number)

        '# % SCALAR 2 = cm file id'
        self.cm_id = vtk.vtkDoubleArray()
        self.cm_id.SetName('cm_id')
        self.cm_poly_data.GetPointData().AddArray(self.cm_id)

        '# % SCALAR 3 = DEPTH'
        self.xyz_depth = vtk.vtkDoubleArray()
        self.xyz_depth.SetName('Z')
        self.cm_poly_data.GetPointData().AddArray(self.xyz_depth)
        self.cm_poly_data.GetPointData().SetScalars(self.xyz_depth)
        self.cm_poly_data.GetPointData().SetActiveScalars('Z')
        # self.cm_poly_data.GetPointData().SetActiveScalars('cm_id')

        '# % SET COLOR MAPPER'
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputData(self.cm_poly_data)
        self.mapper.SetColorModeToDefault()
        self.mapper.SetScalarRange(self.xyz[:, 2].min(), self.xyz[:, 2].max())
        self.mapper.SetScalarVisibility(1)
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(self.mapper)

    def addPoint(self, point, xyz_cm_id, xyz_cm_line_number):

        if self.xyz_points.GetNumberOfPoints() < self.maxNumPoints:
            pointId = self.xyz_points.InsertNextPoint(point[:])
            self.xyz_depth.InsertNextValue(point[2])
            self.xyz_cells.InsertNextCell(1)
            self.xyz_cells.InsertCellPoint(pointId)
            self.cm_id.InsertNextValue(xyz_cm_id)
            self.cm_line_number.InsertNextValue(xyz_cm_line_number)
        else:
            print("ERROR: MORE THAN 10e6 POINTS IN FILE")
            return

class RubberBand(vtk.vtkInteractorStyleRubberBandPick):
    def __init__(self, renderWindow, renderer, pointcloud, interactor, area_picker, cm):
        print("entering rubber band mode")
        self.cm = cm
        self.renderWindow = renderWindow
        self.renderer = renderer
        self.pointcloud = pointcloud
        self.Interactor = interactor
        self.selected_mapper = vtk.vtkDataSetMapper()
        self.selected_actor = vtk.vtkActor()
        self.selected_actor.SetMapper(self.selected_mapper)
        self.area_picker = area_picker

        '# % SET VTK OBSERVERS'
        self.Interactor.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.Interactor.AddObserver("LeftButtonReleaseEvent", self.LeftButtonReleaseEvent)

    def leftButtonPressEvent(self, obj, event):
        print("LEFT BUTTON PRESSED")
        self.OnLeftButtonDown()
        '# % REMOVE THE CURRENT HIGHLIGHT ACTOR (IF THERE IS ONE) FROM SCREEN'
        try:
            self.renderer.RemoveActor(self.selected_actor)
        except AttributeError:
            pass
        self.renderWindow.Render()

    def LeftButtonReleaseEvent(self, obj, event):
        print("LEFT BUTTON RELEASED")
        self.OnLeftButtonUp()

        self.frustum = self.area_picker.GetFrustum()

        self.extract_geometry = vtk.vtkExtractGeometry()
        self.extract_geometry.SetImplicitFunction(self.frustum)
        self.extract_geometry.SetInputData(self.pointcloud.cm_poly_data)
        self.extract_geometry.Update()

        self.glyph_filter = vtk.vtkVertexGlyphFilter()
        self.glyph_filter.SetInputConnection(self.extract_geometry.GetOutputPort())
        self.glyph_filter.Update()

        self.selected = self.glyph_filter.GetOutput()
        self.p1 = self.selected.GetNumberOfPoints()
        self.p2 = self.selected.GetNumberOfCells()
        print("Number of points = %s" % self.p1)
        print("Number of cells = %s" % self.p2)

        '# % COLOR SELECTED POINTS RED'
        self.selected_mapper.SetInputData(self.selected)
        try:
            self.selected_actor.GetProperty().SetPointSize(10)
            self.selected_actor.GetProperty().SetColor(0, 0, 0)  # (R, G, B)
            self.color_picked()
        except AttributeError:
            pass

    def save_output(self):
        """CREATES A NEW NUMPY ARRAY of the cm FILE WITH SELECTED NODES REMOVED"""
        pass
        # np.column_stack((self.selected_cm_ids, self.selected_xyz))

    def color_picked(self):
        try:
            self.renderer.AddActor(self.selected_actor)
            self.renderWindow.Render()
        except AttributeError:
            pass
        # self.selected_actor.GetProperty().Get

        # '# % CREATE ID FOR EACH SELECTED POINT'
        # self.ids = vtk.vtkIdFilter()
        # self.ids.SetInputData(self.selected)
        # self.ids.SetIdsArrayName("Ids")  # % SET Id ARRAY NAME AS 'Ids'
        # print("self.ids =")
        # print(self.ids)
        # print("")
        #
        # self.cell_ids = self.ids.GetCellIds()
        # self.cell_ids = vtk_to_numpy(self.cells.GetArray('Ids'))


        # print(self.cell_ids)
        # print("")
        #
        # self.selected_frustrum = vtk.vtkExtractSelectedFrustum()
        # self.selected_frustrum.SetFrustum(self.frustum)
        # self.selected_frustrum.PreserveTopologyOff()
        # self.selected_frustrum.SetInputConnection(self.ids.GetOutputPort())  # was grid?
        # self.selected_frustrum.Update()
        # self.ugrid = self.selected_frustrum.GetOutput()
        # self.cells = self.ugrid.GetCellData()
        #
        # print("self.cells =")
        # print(self.cells)
        # print("")



        # print("self.cell_ids =")
        # print(self.cell_ids)
        # print("")

        # sys.Gmg.tdv.pointcloud.cm_poly_data.GetPoints().GetPoint(id)

        # self.point_data
        # self.ids = vtk.vtkIdTypeArray.SafeDownCast(self.selected.GetPointData().GetArray("OriginalIds"))
        # print(self.ids)
        # self.count = self.ids.GetTypedTuple()
        # for i in range(self.ids.GetTypedTuple()):
        #     print("Id %s : %s" % (i, self.ids.GetValue(i)))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''# %START SOFTWARE'''
if __name__ == "__main__":
    app = wx.App(False)
    fr = wx.Frame(None, title='Py-CMeditor')
    app.frame = PyCMeditor()
    app.frame.CenterOnScreen()
    app.frame.Show()
    app.MainLoop()