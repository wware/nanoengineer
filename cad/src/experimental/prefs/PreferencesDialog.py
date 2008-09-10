# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
PreferencesDialog.py

This is experimental.

To run, type:

python PreferencesDialog.py
"""

import sys
from PyQt4.Qt import *
from PyQt4 import QtCore, QtGui
from Ui_PreferencesDialog import Ui_PreferencesDialog

# imports for testing
from PM.PM_ComboBox              import PM_ComboBox
from PM.PM_ColorComboBox         import PM_ColorComboBox
from PM.PM_CheckBox              import PM_CheckBox
from PM.PM_GroupBox              import PM_GroupBox
from PM.PM_CoordinateSpinBoxes   import PM_CoordinateSpinBoxes
from PM.PM_LineEdit              import PM_LineEdit
from PM.PM_PushButton            import PM_PushButton
from PM.PM_RadioButton           import PM_RadioButton
from PM.PM_RadioButtonList       import PM_RadioButtonList
from PM.PM_Slider                import PM_Slider
from PM.PM_TableWidget           import PM_TableWidget
from PM.PM_TextEdit              import PM_TextEdit
from PM.PM_ToolButton            import PM_ToolButton
from PM.PM_DoubleSpinBox         import PM_DoubleSpinBox
from PM.PM_Dial                  import PM_Dial
from PM.PM_SpinBox               import PM_SpinBox
from PM.PM_FileChooser           import PM_FileChooser
from PM.PM_WidgetRow             import PM_WidgetRow
from PM.PM_DockWidget            import PM_DockWidget
from PM.PM_PushButton            import PM_PushButton
from PM.PM_LabelRow              import PM_LabelRow

from PM.PM_Constants import PM_MAINVBOXLAYOUT_MARGIN
from PM.PM_Constants import PM_MAINVBOXLAYOUT_SPACING
from PM.PM_Constants import PM_HEADER_FRAME_MARGIN
from PM.PM_Constants import PM_HEADER_FRAME_SPACING
from PM.PM_Constants import PM_HEADER_FONT
from PM.PM_Constants import PM_HEADER_FONT_POINT_SIZE
from PM.PM_Constants import PM_HEADER_FONT_BOLD
from PM.PM_Constants import PM_SPONSOR_FRAME_MARGIN
from PM.PM_Constants import PM_SPONSOR_FRAME_SPACING
from PM.PM_Constants import PM_TOPROWBUTTONS_MARGIN
from PM.PM_Constants import PM_TOPROWBUTTONS_SPACING
from PM.PM_Constants import PM_LABEL_LEFT_ALIGNMENT, PM_LABEL_RIGHT_ALIGNMENT
   
from PM.PM_Constants import PM_ALL_BUTTONS
from PM.PM_Constants import PM_DONE_BUTTON
from PM.PM_Constants import PM_CANCEL_BUTTON
from PM.PM_Constants import PM_RESTORE_DEFAULTS_BUTTON
from PM.PM_Constants import PM_PREVIEW_BUTTON
from PM.PM_Constants import PM_WHATS_THIS_BUTTON

DEBUG = True

class ContainerWidget(QFrame):
    """
    The container widget class for use in PageWidget.
    """

    _rowCount = 0
    _widgetList = []
    _groupBoxCount = 0
    _lastGroupBox = None
    
    def __init__(self, name):
        """
        Creates a container widget within the page widget
        """
        QFrame.__init__(self)
        self.name = name
        self.setObjectName(name)
        if DEBUG:
            self.setFrameShape(QFrame.Box)

        # Create vertical box layout
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setMargin(0)
        self.vBoxLayout.setSpacing(0)

        # Create grid layout
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setMargin(2)
        self.gridLayout.setSpacing(2)

        # Insert grid layout in its own vBoxLayout
        self.vBoxLayout.addLayout(self.gridLayout)

        # Vertical spacer
        #vSpacer = QtGui.QSpacerItem(1, 1, 
                                    #QSizePolicy.Preferred, 
                                    #QSizePolicy.Expanding)
        #self.vBoxLayout.addItem(vSpacer)
        return

    def addQtWidget(self, qtWidget, column = 0, spanWidth = False):
        """
        Add a Qt widget to this page.

        @param qtWidget: The Qt widget to add.
        @type  qtWidget: QWidget
        """
        # Set the widget's row and column parameters.
        widgetRow      = self._rowCount
        widgetColumn   = column
        if spanWidth:
            widgetSpanCols = 2
        else:
            widgetSpanCols = 1

        self.gridLayout.addWidget( qtWidget,
                                   widgetRow, 
                                   widgetColumn,
                                   1, 
                                   widgetSpanCols )

        self._rowCount += 1
        return
    
    def getPmWidgetPlacementParameters(self, pmWidget):
        """
        Returns all the layout parameters needed to place 
        a PM_Widget in the group box grid layout.
        
        @param pmWidget: The PM widget.
        @type  pmWidget: PM_Widget
        """
        
        row = self._rowCount
        
        #PM_CheckBox doesn't have a label. So do the following to decide the 
        #placement of the checkbox. (can be placed either in column 0 or 1 , 
        #This also needs to be implemented for PM_RadioButton, but at present 
        #the following code doesn't support PM_RadioButton. 
        if isinstance(pmWidget, PM_CheckBox):
            spanWidth = pmWidget.spanWidth
            
            if not spanWidth:
                # Set the widget's row and column parameters.
                widgetRow      = row
                widgetColumn   = pmWidget.widgetColumn
                widgetSpanCols = 1
                widgetAlignment = PM_LABEL_LEFT_ALIGNMENT
                rowIncrement   = 1
                #set a virtual label
                labelRow       = row
                labelSpanCols  = 1
                labelAlignment = PM_LABEL_RIGHT_ALIGNMENT
                            
                if widgetColumn == 0:
                    labelColumn   = 1                              
                elif widgetColumn == 1:
                    labelColumn   = 0
            else:                
                # Set the widget's row and column parameters.
                widgetRow      = row
                widgetColumn   = pmWidget.widgetColumn
                widgetSpanCols = 2
                widgetAlignment = PM_LABEL_LEFT_ALIGNMENT
                rowIncrement   = 1
                #no label 
                labelRow       = 0
                labelColumn    = 0
                labelSpanCols  = 0
                labelAlignment = PM_LABEL_RIGHT_ALIGNMENT
                
            
            return widgetRow, \
               widgetColumn, \
               widgetSpanCols, \
               widgetAlignment, \
               rowIncrement, \
               labelRow, \
               labelColumn, \
               labelSpanCols, \
               labelAlignment
        
       
        label       = pmWidget.label            
        labelColumn = pmWidget.labelColumn
        spanWidth   = pmWidget.spanWidth
        
        if not spanWidth: 
            # This widget and its label are on the same row
            labelRow       = row
            labelSpanCols  = 1
            labelAlignment = PM_LABEL_RIGHT_ALIGNMENT
            # Set the widget's row and column parameters.
            widgetRow      = row
            widgetColumn   = 1
            widgetSpanCols = 1
            widgetAlignment = PM_LABEL_LEFT_ALIGNMENT
            rowIncrement   = 1
            
            if labelColumn == 1:
                widgetColumn   = 0
                labelAlignment = PM_LABEL_LEFT_ALIGNMENT
                widgetAlignment = PM_LABEL_RIGHT_ALIGNMENT
                        
        else: 
                      
            # This widget spans the full width of the groupbox           
            if label: 
                # The label and widget are on separate rows.
                # Set the label's row, column and alignment.
                labelRow       = row
                labelColumn    = 0
                labelSpanCols  = 2
                    
                # Set this widget's row and column parameters.
                widgetRow      = row + 1 # Widget is below the label.
                widgetColumn   = 0
                widgetSpanCols = 2
                
                rowIncrement   = 2
            else:  # No label. Just the widget.
                labelRow       = 0
                labelColumn    = 0
                labelSpanCols  = 0

                # Set the widget's row and column parameters.
                widgetRow      = row
                widgetColumn   = 0
                widgetSpanCols = 2
                rowIncrement   = 1
                
            labelAlignment = PM_LABEL_LEFT_ALIGNMENT
            widgetAlignment = PM_LABEL_LEFT_ALIGNMENT
                
        return widgetRow, \
               widgetColumn, \
               widgetSpanCols, \
               widgetAlignment, \
               rowIncrement, \
               labelRow, \
               labelColumn, \
               labelSpanCols, \
               labelAlignment

    def addPmWidget(self, pmWidget):
        """
        This is a reminder to Derrick and Mark to review the PM_Group class
        and its addPmWidget() method, since we want to support PM widget 
        classes.
        """
        """
        Add a PM widget and its label to this group box.

        @param pmWidget: The PM widget to add.
        @type  pmWidget: PM_Widget
        """

        # Get all the widget and label layout parameters.
        widgetRow, \
                 widgetColumn, \
                 widgetSpanCols, \
                 widgetAlignment, \
                 rowIncrement, \
                 labelRow, \
                 labelColumn, \
                 labelSpanCols, \
                 labelAlignment = \
                 self.getPmWidgetPlacementParameters(pmWidget)

        if pmWidget.labelWidget: 
            #Create Label as a pixmap (instead of text) if a valid icon path 
            #is provided
            labelPath = str(pmWidget.label)
            if labelPath and labelPath.startswith("ui/"): #bruce 080325 revised
                labelPixmap = getpixmap(labelPath)
                if not labelPixmap.isNull():
                    pmWidget.labelWidget.setPixmap(labelPixmap)
                    pmWidget.labelWidget.setText('')

            self.gridLayout.addWidget( pmWidget.labelWidget,
                                       labelRow, 
                                       labelColumn,
                                       1, 
                                       labelSpanCols,
                                       labelAlignment )


        # The following is a workaround for a Qt bug. If addWidth()'s 
        # <alignment> argument is not supplied, the widget spans the full 
        # column width of the grid cell containing it. If <alignment> 
        # is supplied, this desired behavior is lost and there is no 
        # value that can be supplied to maintain the behavior (0 doesn't 
        # work). The workaround is to call addWidget() without the <alignment>
        # argument. Mark 2007-07-27.

        if widgetAlignment == PM_LABEL_LEFT_ALIGNMENT:
            self.gridLayout.addWidget( pmWidget,
                                       widgetRow, 
                                       widgetColumn,
                                       1, 
                                       widgetSpanCols) 
                                        # aligment = 0 doesn't work.
        else:
            self.gridLayout.addWidget( pmWidget,
                                       widgetRow, 
                                       widgetColumn,
                                       1, 
                                       widgetSpanCols,
                                       widgetAlignment
                                       )

        self._widgetList.append(pmWidget)

        self._rowCount += rowIncrement
        return

# End of ContainerWidget class

    
class PageWidget(QWidget):
    """
    The page widget base class.
    """

    def __init__(self, name):
        """
        Creates a page widget named name.

        param name: The page name. It will be used as the tree item
        """
        QWidget.__init__(self)
        self.name = name
        self.setObjectName(name)
        self.containerList = []

        # Horizontal spacer
        hSpacer = QtGui.QSpacerItem(1, 1, 
                                    QSizePolicy.Expanding, 
                                    QSizePolicy.Preferred)

        self.hBoxLayout = QtGui.QHBoxLayout(self)
        self.hBoxLayout.setMargin(0)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.addItem(hSpacer)
        # add the base container widget
        container = self.addContainer(name + "_1")
#        print container
#        scrollArea = QScrollArea()
#        scrollArea.setWidget(container)
#        container.scrollarea = scrollArea

        return

    def insertContainer(self, containerName = None, indx = -1):
        """
        inserts a container class named containerName in the place specified 
        by indx
        """
        # set indx to append to the end of the list if indx is not passed
        if indx < 0:
            indx = len(self.containerList)
        # create some theoretically unique name if None is given
        if containerName == None:
            containerName = self.name + "_" + str((len(self.containerList) + 1))
        # create the container and name it
        _containerWidget = ContainerWidget(containerName)
        _containerWidget.setObjectName(containerName)
        # add the container into the page
        self.containerList.insert(indx, _containerWidget)
        self.hBoxLayout.insertWidget(indx,_containerWidget)
        return _containerWidget
    
    def addContainer(self, containerName = None):
        """
        Adds a container to the end of the list and returns the 
        container's handle
        """
        _groupBoxCount = 0
        _containerWidget = self.insertContainer(containerName)
        return _containerWidget
            
    def getPageContainers(self, containerKey = None):
        """
        Returns a list of containers which the page owns.
        Always returns a list for consistancy.  The list can be restricted to
        only those that have containerKey in the name.  If there's only one, the 
        programmer can do list = list[0]
        """

        # See if we are asking for a specific container
        if containerKey == None:
            # return the whole list
            containers = self.containerList
        else:
            # return only the container(s) where containerKey is in the name.
            # this is a list comprehension search.
            # Also, the condition can be modified with a startswith depending
            # on the implementation of naming the containers.
            containers = [ x for x in self.containerList \
                           if x.objectName().find(containerKey) >= 0 ]
        return containers

# End of PageWidget class

class PreferencesDialog(QDialog, Ui_PreferencesDialog):
    """
    The Preferences dialog class.

    This is experimental.
    
    pagenameList[0] always has to be a singular item, it cannot be a list.
    All sub-lists are interpreted as being children of the item preceding it.
    """
    pagenameList = ["General", 
                    "Graphics Area", 
                    ["Zoom, Pan and Rotate", "Rulers"],
                    "Atoms",
                    "Bonds",
                    "DNA",
                    ["Minor groove error indicator", 
                     "Base orientation indicator"],
                    "Adjust",
                    "Lighting",
                    "Plug-ins",
                    "Undo",
                    "Window",
                    "Reports",
                    "Tooltips"]
    
    #NOTE: when creating the function names for populating the pages with 
    # widgets...  Create the function name by replacing all spaces with 
    # underscores and removing all characters that are not ascii 
    # letters or numbers, and appending the result to "populate_"
    # ex. "Zoom, Pan and Rotate" has the function:
    #     populate_Zoom_Pan_and_Rotate()
    
    pagenameDict = {}

    def __init__(self):
        """
        Constructor for the prefs dialog.
        """
        QDialog.__init__(self)
        self.setupUi(self)
        self._setupDialog_TopLevelWidgets()
        self._addPages(self.pagenameList)
        self.populatePages()
        return

    def _setupDialog_TopLevelWidgets(self):
        """
        Setup all the main dialog widgets and their signal-slot connection(s).
        """

        #self.setWindowIcon(geticon("ui/actions/Tools/Options.png"))

        # This connects the "itemSelectedChanged" signal generated when the
        # user selects an item in the "Category" QTreeWidget on the left
        # side of the Preferences dialog (inside the "Systems Option" tab)
        # to the slot for turning to the correct page in the QStackedWidget
        # on the right side.
        self.connect(self.categoriesTreeWidget, SIGNAL("itemSelectionChanged()"), self.showPage)

        # Connections for OK and What's This buttons at the bottom of the dialog.
        self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
        self.connect(self.whatsThisToolButton, SIGNAL("clicked()"),QWhatsThis.enterWhatsThisMode)

        #self.whatsThisToolButton.setIcon(
        #    geticon("ui/actions/Properties Manager/WhatsThis.png"))
        #self.whatsThisToolButton.setIconSize(QSize(22, 22))
        self.whatsThisToolButton.setToolTip('Enter "What\'s This?" help mode')
        return

    #def addScrollArea(self):
        #self.propertyManagerScrollArea = QScrollArea(self.categoriesTreeWidget)
        #self.propertyManagerScrollArea.setObjectName("propertyManagerScrollArea")
        #self.propertyManagerScrollArea.setWidget(self.categoriesTreeWidget)
        #self.propertyManagerScrollArea.setWidgetResizable(True)
    
    def _addPages(self, pagenameList, myparent = None):
        """
        Creates all page widgets in pagenameList and add them 
        to the Preferences dialog.
        """

        if (type(pagenameList[0]) == list or \
            type(pagenameList[0]) == tuple):
            print "Invalid tree structure with no root page."
            return
        # Run through the list and add the pages into the tree.
        # This is recursive so that it interpretes nested sublists based on
        # the structure of the list.
        x=-1
        while x < len(pagenameList) - 1:
            x = x + 1
            name = pagenameList[x]
            if DEBUG:
                print name
            page_widget = PageWidget(name)
            # Create a dictionary entry for the page name and it's index
            self.pagenameDict[name] = len(self.pagenameDict)
            page_tree_slot = self.addPage(page_widget, myparent)
            # Check if the next level is a sub-list
            if x + 1 <= len(pagenameList) - 1 and \
               (type(pagenameList[x+1]) == list or \
               type(pagenameList[x+1]) == tuple):
                # If so, call addPages again using the sublist and the current
                # item as the parent
                self._addPages(pagenameList[x+1], page_tree_slot)
                x = x + 1

        return

    def addPage(self, page, myparent = None):
        """
        Adds page into this preferences dialog at position index.
        If index is negative, the page is added at the end. 

        param page: Page widget.
        type  page: L{PageWidget}
        """

        # Add page to the stacked widget
        self.prefsStackedWidget.addWidget(page)

        # Add a QTreeWidgetItem to the categories QTreeWidget.
        # The label (text) of the item is the page name.
        if not myparent:
            _item = QtGui.QTreeWidgetItem(self.categoriesTreeWidget)
        else:
            _item = QtGui.QTreeWidgetItem(myparent)
        _item.setText(0, 
                      QtGui.QApplication.translate("PreferencesDialog", 
                                                   page.name, 
                                                   None, 
                                                   QtGui.QApplication.UnicodeUTF8))

        return _item

    def _addPageTestWidgets(self, page_widget):
        """
        This creates a set of test widgets for page_widget.
        """
        _label = QtGui.QLabel(page_widget)
        _label.setText(page_widget.name)
        page_widget.addQtWidget(_label)
        _checkbox = QtGui.QCheckBox(page_widget.name, page_widget)
        page_widget.addQtWidget(_checkbox)
        _pushbutton = QtGui.QPushButton(page_widget.name, page_widget)
        page_widget.addQtWidget(_pushbutton)
        _label = QtGui.QLabel(page_widget)
        _choices = ['choice a', 'choice b' ]
        _pref_ComboBox = PM_ComboBox( page_widget, label =  "choices:", 
                                      choices = _choices, setAsDefault = True)
        _pref_color = PM_ColorComboBox(page_widget, spanWidth = True)
        _pref_CheckBox = PM_CheckBox(page_widget, text ="nothing interesting", \
                                     widgetColumn = 1)
        #N means this PM widget currently does not work.
        _pmGroupBox1 = PM_GroupBox( page_widget, title = "Test of GB",
                                    connectTitleButton = False)
#N        _endPoint1SpinBoxes = PM_CoordinateSpinBoxes(_pmGroupBox1)
#        duplexLengthLineEdit  =  \
#            PM_LineEdit(page_widget, label =  "something\non the next line",
#                         text          =  "default text",
#                         setAsDefault  =  False)
        pushbtn = PM_PushButton(page_widget, label = "Click here",
                                 text = "here")
        radio1 = PM_RadioButton(page_widget, text = "self button1")
        radio2 = PM_RadioButton(page_widget, text = "self button2")
        radiobtns = PM_RadioButtonList (_pmGroupBox1, title = "junk", 
                                        label = "junk2", 
                                        buttonList = [[ 1, "btn1", "btn1"],
                                                      [ 2, "btn2", "btn2"]])
        slider1 = PM_Slider(page_widget, label = "slider 1:")
#        table1 = PM_TableWidget(page_widget, label = "table:")
#        TE1 = PM_TextEdit(page_widget, label = "QMX")
#N        TB1 = PM_ToolButton(_pmGroupBox1, label = "tb1", text = "text1")
        radio3 = PM_RadioButton(page_widget, text = "self button3")
#        SB = PM_SpinBox(page_widget, label = "SB", suffix = "x2")
#        DBS = PM_DoubleSpinBox(page_widget, label = "test", suffix = "x3", singleStep = .1)
#        Dial = PM_Dial( page_widget, label = "Direction", suffix = "degrees")

        return
        
    def getPage(self, pagename):
        """
        Returns the page widget for pagename.
        """
        if not pagename in self.pagenameDict:
            msg = 'Preferences page unknown: pagename =%s\n' \
                'pagename must be one of the following:\n%r\n' \
                % (pagename, self.pagenameList)
            print_compact_traceback(msg)
            return
        return self.prefsStackedWidget.widget(self.pagenameDict[pagename])
    
    def populatePages(self):
        import string
        for name in self.pagenameDict:
            # create the function name by replacing spaces with "_" and 
            # removing everything that is not an _, ascii letter, or number
            # and appending that to populate_
            fname = "populate_%s" % "".join([ x for x in name.replace(" ","_") \
                                              if (x in string.ascii_letters or\
                                                  x in string.digits \
                                                  or x == "_") ])
            # Make sure the class has that object defined before calling it.
            if hasattr(self, fname):
                fcall = getattr(self, fname)
                if callable(fcall):
                    if DEBUG:
                        print "method defined: %s" % fname
                    fcall(name)
                else:
                    print "Attribute %s exists, but is not a callable method."
            else:
                if DEBUG:
                    print "method missing: %s" % fname
        return

    def showPage(self, pagename = ""):
        """
        Show the current page of the Preferences dialog. If no page is
        selected from the Category tree widget, show the "General" page.

        @param pagename: Name of the Preferences page. Default is "General".
                         Only names found in self.pagenameList are allowed.
        @type  pagename: string

        @note: This is the slot method for the "Categories" QTreeWidget.
        """

        if not pagename:
            selectedItemsList = self.categoriesTreeWidget.selectedItems()
            if selectedItemsList:
                selectedItem = selectedItemsList[0]
                pagename = str(selectedItem.text(0))
            else:
                pagename = 'General'

        if not pagename in self.pagenameDict:
            msg = 'Preferences page unknown: pagename =%s\n' \
                'pagename must be one of the following:\n%r\n' \
                % (pagename, self.pagenameList)
            print_compact_traceback(msg)

        try:
            # Show page.  Use the dictionary to get the index.
            self.prefsStackedWidget.setCurrentIndex(self.pagenameDict[pagename])
        except:
            print_compact_traceback("Bug in showPage() ignored.")

        self.setWindowTitle("Preferences - %s" % pagename)
        #containers = self.getPage(pagename).getPageContainers()
        #print containers
        return

    def populate_General(self, pagename):
        """
        Populate the General page
        """
        print "populate_General: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        logosGroupBox = PM_GroupBox( _pageContainer, 
                                     title = "Sponsor logos download permission",
                                     connectTitleButton = False)
        radiobtns = PM_RadioButtonList (logosGroupBox,
                                        buttonList = [[ 1, "Always ask before downloading", "always_ask"],
                                                      [ 2, "Never ask before downloading", "never_ask"],
                                                      [ 3, "Never download", "never_download"] ])
        
        buildChunksGroupBox = PM_GroupBox( _pageContainer, 
                                     title = "Build Chunks Settings",
                                     connectTitleButton = False)
        autobondCheckBox = PM_CheckBox(buildChunksGroupBox, text ="Autobond")
        hoverHighlightCheckBox = PM_CheckBox(buildChunksGroupBox, text ="Hover highlighting")
        waterCheckBox = PM_CheckBox(buildChunksGroupBox, text ="Water")
        autoSelectAtomsCheckBox = PM_CheckBox(buildChunksGroupBox, text ="Auto select atoms of deposited objects")

        offsetFactorPastingGroupBox = PM_GroupBox( _pageContainer, 
                                     title = "Offset factor for pasting objects",
                                     connectTitleButton = False)
        pasteOffsetForChunks_doublespinbox = PM_DoubleSpinBox(offsetFactorPastingGroupBox, label = "Chunk Objects", singleStep = 1)
        pasteOffsetForDNA_doublespinbox = PM_DoubleSpinBox(offsetFactorPastingGroupBox, label = "DNA Objects", singleStep = 1)
      
        return

    def populate_Tooltips(self, pagename):
        print "populate_Tooltips: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        slider2 = PM_Slider(_pageContainer, label = "slider 2:")
        return
    
    def populate_Reports(self, pagename):
        print "populate_Reports: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_DNA(self, pagename):
        print "populate_DNA: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        DNA_default_values_GroupBox = PM_GroupBox(_pageContainer,
                                                  title = "DNA default values",
                                                  connectTitleButton = False)
        _choices = ["B-DNA"]
        conformation_ComboBox = PM_ComboBox(DNA_default_values_GroupBox, 
                                      label =  "Conformation:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        bases_per_turn_DoubleSpinBox = PM_DoubleSpinBox(DNA_default_values_GroupBox,
                                                         label = "Bases per turn:", 
                                                         suffix = "", 
                                                         singleStep = 1,
                                                         )
        rise_DoubleSpinBox = PM_DoubleSpinBox(DNA_default_values_GroupBox,
                                                         label = "Rise:", 
                                                         suffix = "Angstroms", 
                                                         singleStep = 10,
                                                         )
        strand1_ColorComboBox = PM_ColorComboBox(DNA_default_values_GroupBox,
                                                           label = "Strand 1:")
        strand2_ColorComboBox = PM_ColorComboBox(DNA_default_values_GroupBox,
                                                           label = "Strand 2:")
        segment_ColorComboBox = PM_ColorComboBox(DNA_default_values_GroupBox,
                                                           label = "Segment:")
        restore_DNA_colors_PushButton = PM_PushButton(DNA_default_values_GroupBox,
                                                      text = "Restore Default Colors",
                                                      spanWidth = False)
        buttonList = [["QSpacerItem", 40, 0, 0], ["PushButton", restore_DNA_colors_PushButton, 1]]
        buttonPlacer = PM_WidgetRow(DNA_default_values_GroupBox,
                                 spanWidth = True,
                                 widgetList = buttonList)
        strand_arrowhead_display_options_GroupBox = PM_GroupBox(_pageContainer,
                                                  title = "Strand arrowhead display options",
                                                  connectTitleButton = False)
        show_arrows_on_backbones_CheckBox = PM_CheckBox(strand_arrowhead_display_options_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show arrows on backbones")
        show_arrows_on_3prime_ends_CheckBox = PM_CheckBox(strand_arrowhead_display_options_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show arrows on 3' ends")
        show_arrows_on_5prime_ends_CheckBox = PM_CheckBox(strand_arrowhead_display_options_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show arrows on 5' ends")
        three_prime_end_custom_ColorComboBox = PM_ColorComboBox(strand_arrowhead_display_options_GroupBox,
                                                           label = "3' end custom color:")
        five_prime_end_custom_ColorComboBox = PM_ColorComboBox(strand_arrowhead_display_options_GroupBox,
                                                           label = "5' end custom color:")
        
        return
    
    def populate_Bonds(self, pagename):
        print "populate_Bonds: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        bond_colors_GroupBox = PM_GroupBox(_pageContainer,
                                           title = "Colors",
                                           connectTitleButton = False)
        bond_highlighting_ColorComboBox = PM_ColorComboBox(bond_colors_GroupBox,
                                                           label = "Bond highlighting:")
        ball_and_stick_cylinder_ColorComboBox = PM_ColorComboBox(bond_colors_GroupBox,
                                                           label = "Ball and stick cylinder:")
        bond_stretch_ColorComboBox = PM_ColorComboBox(bond_colors_GroupBox,
                                                           label = "Bond stretch:")
        Vane_Ribbon_ColorComboBox = PM_ColorComboBox(bond_colors_GroupBox,
                                                           label = "Vane/Ribbon:")
        restore_bond_colors_PushButton = PM_PushButton(bond_colors_GroupBox,
                                                      text = "Restore Default Colors",
                                                      spanWidth = False)
        buttonList = [["QSpacerItem", 40, 0, 0], ["PushButton", restore_bond_colors_PushButton, 1]]
        buttonPlacer = PM_WidgetRow(bond_colors_GroupBox,
                                 spanWidth = True,
                                 widgetList = buttonList)
        
        misc_bond_settings_GroupBox = PM_GroupBox(_pageContainer,
                                                  title = "Miscellaneous bond settings",
                                                  connectTitleButton = False)
        ball_and_stick_bond_scale_SpinBox = PM_SpinBox(misc_bond_settings_GroupBox,
                                                       label = "Ball and stick bond scale:",
                                                       suffix = "%")
        bond_line_thickness_SpinBox = PM_SpinBox(misc_bond_settings_GroupBox,
                                                       label = "Bond line thickness:",
                                                       suffix = "pixels")
        high_order_bonds_GroupBox = PM_GroupBox(misc_bond_settings_GroupBox,
                                                title = "High order bonds",
                                                connectTitleButton = False)
        high_order_bonds_RadioButtonList = PM_RadioButtonList(high_order_bonds_GroupBox,
                                        buttonList = [[ 1, "Multiple cylinders", "cylinders"],
                                                      [ 2, "Vanes", "vanes"],
                                                      [ 3, "Ribbons", "ribbons"] ])
        show_bond_type_letters_CheckBox = PM_CheckBox(misc_bond_settings_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show bond type letters")
        show_valence_errors_CheckBox = PM_CheckBox(misc_bond_settings_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show valence errors")
        show_bond_stretch_indicators_CheckBox = PM_CheckBox(misc_bond_settings_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Show bond stretch indicators")
        return
    
    def populate_Rulers(self, pagename):
        print "populate_Rules: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]

        rulers_GroupBox = PM_GroupBox(_pageContainer,
                                      title = "Rulers",
                                      connectTitleButton = False)
        _choices = ["Both rulers", "Verticle ruler only", "Horizontal ruler only"]
        display_rulers_ComboBox = PM_ComboBox(rulers_GroupBox, 
                                      label =  "Display:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        _choices = ["Lower left", "Upper left", "Lower right", "Upper right"]
        origin_rulers_ComboBox = PM_ComboBox(rulers_GroupBox, 
                                      label =  "Origin:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        rulor_color_ColorComboBox = PM_ColorComboBox(rulers_GroupBox,
                                                      label = "Color:")
        ruler_opacity_SpinBox = PM_SpinBox(rulers_GroupBox,
                                           label = "Opacity",
                                           suffix = "%")
        show_rulers_in_perspective_view_CheckBox = PM_CheckBox(rulers_GroupBox,
                                                               text ="Show rulers in perspective view",
                                                               spanWidth = True,
                                                               widgetColumn = 0)
        return
    
    def populate_Plugins(self, pagename):
        print "populate_Plugins: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        pluginList = [ "QuteMolX", 
                       "POV-Ray", 
                       "MegaPOV", 
                       "POV include dir",
                       "GROMACS",
                       "cpp"]
        #if DEBUG:
            #self._addPageTestWidgets(_pageContainer)
        executablesGroupBox = PM_GroupBox( _pageContainer, 
                                           title = "Location of Executables",
                                           connectTitleButton = False)
        checkboxes = {}
        choosers = {}
        for name in pluginList:
            
            checkboxes[name] = PM_CheckBox(executablesGroupBox, text = name+'  ')
            choosers[name] = PM_FileChooser(executablesGroupBox,
                                label     = ' ',
                                text      = 'test path' ,
                                filter    = "All Files (*.*)",
                                spanWidth = True,
                                labelColumn = 1
                                )
            aWidgetList = [ ("PM_CheckBox", checkboxes[name], 0),
                            ("PM_FileChooser", choosers[name], 1) ]
                            
            widgetRow = PM_WidgetRow(executablesGroupBox,
                             title     = '',
                             widgetList = aWidgetList,
                             label = " ",
                             labelColumn  = 0,
                             )
        if DEBUG:
            print checkboxes
            print choosers
        return
    
    def populate_Adjust(self, pagename):
        print "populate_Adjust: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_Atoms(self, pagename):
        print "populate_Atoms: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        atom_colors_GroupBox = PM_GroupBox(_pageContainer,
                                           title = "Colors",
                                           connectTitleButton = False)
        change_element_colors_PushButton = PM_PushButton(atom_colors_GroupBox,
                                                      text = "Change Element Colors...",
                                                      spanWidth = False)
        buttonList = [["QSpacerItem", 40, 0, 0], ["PushButton", change_element_colors_PushButton, 0]]
        buttonPlacer = PM_WidgetRow(atom_colors_GroupBox,
                                 spanWidth = True,
                                 widgetList = buttonList)
        atom_colors_sub_GroupBox = PM_GroupBox(atom_colors_GroupBox,
                                               connectTitleButton = False)
        atom_highlighting_ColorComboBox = PM_ColorComboBox(atom_colors_sub_GroupBox,
                                                      label = "Atom Highlighting:")
        bondpoint_highlighting_ColorComboBox = PM_ColorComboBox(atom_colors_sub_GroupBox,
                                                      label = "Bondpoint Highlighting:")
        bondpoint_hotspots_ColorComboBox = PM_ColorComboBox(atom_colors_sub_GroupBox,
                                                      label = "Bondpoint hotspots:")
        restore_element_colors_PushButton = PM_PushButton(atom_colors_sub_GroupBox,
                                                      text = "Restore Default Colors",
                                                      spanWidth = False)
        buttonList = [["QSpacerItem", 40, 0, 0], ["PushButton", restore_element_colors_PushButton, 1]]
        buttonPlacer = PM_WidgetRow(atom_colors_GroupBox,
                                 spanWidth = True,
                                 widgetList = buttonList)
        misc_atom_settings_GroupBox = PM_GroupBox(_pageContainer,
                                                  title = "Miscellaneous atom options",
                                                  connectTitleButton = False)
        _choices = ["Low", "Medium", "High", "Variable"]
        detail_level_ComboBox = PM_ComboBox(misc_atom_settings_GroupBox, 
                                      label =  "Level of detail:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        ball_and_stick_atom_scale_SpinBox = PM_SpinBox(misc_atom_settings_GroupBox,
                                                       label = "Ball and stick atom scale",
                                                       suffix = "%")
        CPK_atom_scale_SpinBox = PM_SpinBox(misc_atom_settings_GroupBox,
                                            label = "CPK atom scale",
                                            suffix = "%")
        overlapping_atom_indicators_CheckBox = PM_CheckBox(misc_atom_settings_GroupBox,
                                                           spanWidth = True,
                                                           widgetColumn = 0,
                                                           text ="Overlapping atom indicators")
        force_to_keep_bonds_during_transmute_CheckBox = PM_CheckBox(misc_atom_settings_GroupBox,
                                                                    spanWidth = True,
                                                                    widgetColumn = 0,
                                                                    text ="Force to keep bonds during transmute:")
        return
    
    def populate_Window(self, pagename):
        print "populate_Window: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_Graphics_Area(self, pagename):
        print "populate_Graphics_Area: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        _choices = ["Lines", "Tubes", "Ball and Stick", "CPK", "DNA Cylinder"]
        globalDisplayStyleStartupComboBox = PM_ComboBox(_pageContainer, 
                                      label =  "Global display style at start-up:", 
                                      choices = _choices, setAsDefault = False)
        compassGroupBox = PM_GroupBox(_pageContainer, 
                                       title = "Compass display settings",
                                       connectTitleButton = False)
        display_compass_CheckBox = PM_CheckBox(compassGroupBox, 
                                               text = "Display compass: ",
                                               widgetColumn = 0)
        _choices = ["Upper right", "Upper left", "Lower left", "Lower right"]
        globalDisplayStyleStartupComboBox = PM_ComboBox(compassGroupBox, 
                                      label =  "Compass Location:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        display_compass_labels_checkbox = PM_CheckBox(compassGroupBox, 
                                               text = "Display compass labels ",
                                               spanWidth = True,
                                               widgetColumn = 0)
        axesGroupBox = PM_GroupBox(_pageContainer, 
                                   title = "Axes",
                                   connectTitleButton = False)
        display_origin_axix_checkbox = PM_CheckBox(axesGroupBox, 
                                               text = "Display origin axis",
                                               widgetColumn = 0)
        display_pov_axis_checkbox = PM_CheckBox(axesGroupBox, 
                                               text = "Display point of view (POV) axis ",
                                               spanWidth = True,
                                               widgetColumn = 0)
        cursor_text_GroupBox = PM_GroupBox(_pageContainer, 
                                       title = "Cursor text settings",
                                       connectTitleButton = False)
        cursor_text_CheckBox = PM_CheckBox(cursor_text_GroupBox, 
                                           text = "Cursor text",
                                           widgetColumn = 0)
        cursor_text_font_size_SpinBox = PM_DoubleSpinBox(cursor_text_GroupBox,
                                                         label = "Font Size", 
                                                         suffix = "pt", 
                                                         singleStep = 1,
                                                         )
        cursor_text_reset_Button = PM_PushButton(cursor_text_GroupBox, 
                                                 text = "reset")
        aWidgetList = [ ("PM_DoubleSpinBox", cursor_text_font_size_SpinBox, 0),
                        ("PM_PushButton", cursor_text_reset_Button, 1) ]
                            
        widgetRow = PM_WidgetRow(cursor_text_GroupBox,
                         title     = '',
                         spanWidth = True,
                         widgetList = aWidgetList)

        cursor_text_color_ComboBox = PM_ColorComboBox(cursor_text_GroupBox,
                                                      label = "Cursor Text color:",
                                                      spanWidth = True)
        misc_graphics_GroupBox = PM_GroupBox(_pageContainer, 
                                       title = "Other graphics options",
                                       connectTitleButton = False)
        display_confirmation_corner_CheckBox = PM_CheckBox(misc_graphics_GroupBox, 
                                           text = "Display confirmation corner",
                                           widgetColumn = 0)
        anti_aliasing_CheckBox = PM_CheckBox(misc_graphics_GroupBox, 
                                           text = "Enable anti-aliasing (next session)",
                                           widgetColumn = 0)
        
        return
    
    def populate_Base_orientation_indicator(self, pagename):
        print "populate_Base_orientation_indicator: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_Undo(self, pagename):
        print "populate_Undo: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_Zoom_Pan_and_Rotate(self, pagename):
        print "populate_Zoom_Pan_and_Rotate: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        view_rotation_settings_GroupBox = PM_GroupBox(_pageContainer, 
                                                      title = "View rotation settings",
                                                      connectTitleButton = False)
        animate_views_CheckBox = PM_CheckBox(view_rotation_settings_GroupBox, 
                                             text = "Animate between views",
                                             widgetColumn = 0)
        view_animation_speed_Slider = PM_Slider(view_rotation_settings_GroupBox,
                                                label = "View animation speed: ",
                                                spanWidth = True)
        labelList = [["QLabel", "slow", 0], ["QSpacerItem", 0, 0, 1], ["QLabel", "fast", 2]]
        SF1_Label = PM_WidgetRow(view_rotation_settings_GroupBox,
                                 spanWidth = True,
                                 widgetList = labelList)
        mouse_rotation_speed_Slider = PM_Slider(view_rotation_settings_GroupBox,
                                                label = "Mouse rotation speed: ",
                                                spanWidth = True)
        SF2_Label = PM_WidgetRow(view_rotation_settings_GroupBox,
                                 spanWidth = True,
                                 widgetList = labelList)
        mouse_zoom_settings_GroupBox = PM_GroupBox(_pageContainer,
                                                   title = "Mouse wheel zoom settings",
                                                   connectTitleButton = False)
        
        _choices = ["Pull/push wheel to zoom in/out", "Push/pull wheel to zoom in/out"]
        zoom_directon_ComboBox = PM_ComboBox(mouse_zoom_settings_GroupBox, 
                                      label =  "Direction:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        _choices = ["Center about cursor postion", "Center about screen"]
        zoom_in_center_ComboBox = PM_ComboBox(mouse_zoom_settings_GroupBox, 
                                      label =  "Zoom in:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        _choices = ["Pull/push wheel to zoom in/out", "Push/pull wheel to zoom in/out"]
        zoom_out_center_ComboBox = PM_ComboBox(mouse_zoom_settings_GroupBox, 
                                      label =  "Zoom out:", labelColumn = 0,
                                      choices = _choices, 
                                      setAsDefault = False)
        hover_highlighting_timeout_SpinBox = PM_DoubleSpinBox(mouse_zoom_settings_GroupBox,
                                                         label = "Hover highlighting\ntimeout interval", 
                                                         suffix = "seconds",
#                                                         spanWidth = True,
                                                         singleStep = .1)
        return
    
    def populate_Lighting(self, pagename):
        print "populate_Lighting: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    
    def populate_Minor_groove_error_indicator(self, pagename):
        print "populate_Minor_groove_error_indicator: %s" % pagename
        page_widget = self.getPage(pagename)
        _pageContainer = page_widget.getPageContainers()
        _pageContainer = _pageContainer[0]
        if DEBUG:
            self._addPageTestWidgets(_pageContainer)
            #page_widget.addContainer()
        return
    

# End of PreferencesDialog class

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    pd = PreferencesDialog()
    pd.show()
    sys.exit(app.exec_())