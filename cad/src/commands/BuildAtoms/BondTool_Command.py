# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""

@author: Ninad
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details.
@version:$Id$

History:
2008-07-30: Created to refactor Build Chunks command (currently called
BuildAtoms_Command).  

TODO:

- Classes created to refactor BuildAtoms_Command (rather 'BuildChunks' command)
to be revised further. 
- document
- REVIEW: _reusePropMgr_of_parentCommand -- this is an experimental method 
that will fit in the NEW command API (2008-07-30) . to be revised/ renamed. 
e.g. command_reuse_PM etc.
"""

from commands.BuildAtoms.BuildAtoms_Command import BuildAtoms_Command
from commands.BuildAtoms.BondTool_GraphicsMode import DeleteBondTool_GraphicsMode
from commands.BuildAtoms.BondTool_GraphicsMode import BondTool_GraphicsMode
from model.bond_constants import V_SINGLE, V_DOUBLE, V_TRIPLE, V_AROMATIC, V_CARBOMERIC, V_GRAPHITE
from utilities.constants import CL_SUBCOMMAND
from model.elements import Singlet
import foundation.env as env
from utilities.Log import orangemsg
from utilities.debug import print_compact_stack, print_compact_traceback

class BondTool_Command(BuildAtoms_Command):
    """
    Each of the subclass of this class represent a temporary command that 
    will act like 'activating a tool'. Example: when user clicks on single Bonds 
    tool, it will enter Single Bond Tool command. , suspending the Build Chunks
    default command.
    """
    GraphicsMode_class = BondTool_GraphicsMode
    commandName = 'BOND_TOOL'
    
    command_can_be_suspended = False
    command_should_resume_prevMode = True
    command_has_its_own_gui = False
    
    currentActiveTool = 'BONDS_TOOL'
    
    _supress_apply_bondTool_on_selected_atoms = False
    
    
    #class constants for the NEW COMMAND API -- 2008-07-30
    command_level = CL_SUBCOMMAND
    command_parent = 'DEPOSIT'
    
    
    def Enter(self):
        BuildAtoms_Command.Enter(self)
        #REVIEW: NEW COMMAND API SHOULD REVISE THIS METHOD -- 2008-07-30
        self.command_enter_PM()     
        self._apply_bondTool_on_selected_atoms()
        
        name = self.getBondTypeString()
        if name:
            msg = "Click bonds or bondpoints to make them %ss." % name 
        else:
            msg = "Select a bond tool and then click on bonds or "\
                "bondpoints to convert them to a specific bond type."
        self.propMgr.updateMessage(msg)
        
        self.command_enter_flyout()
        
    def command_enter_flyout(self):
        """
        REUSE the flyout toolbar from the parent_command (BuildAtoms_command 
        in this case)
        @TODO: 
        - may need cleanup in command stack refactoring. But the method name is 
        such that it fits the new method names in command API.         
        """
        self._reuse_attr_of_parentCommand('flyoutToolbar')
    
    def _reuse_attr_of_parentCommand(self, attr_name = ''): 
        """
        Reuse the given attr of the parent command. 
        Example: reuse 'flyoutToolbar' or 'propMgr' attrs in self. 
        @see: self.command_enter_flyout()
        """
        # WARNING: this code is duplicated in other places.
        # For comments about it, see one of them.
        
        if not attr_name:
            print_compact_stack("bug: trying to set an attr with no name "
                                "in this command: ")
            return
        
        previousCommand = self.find_parent_command_named( self.command_parent)
        
        if previousCommand:
            try:
                parent_attr = getattr(previousCommand, attr_name)
            except:
                msg = "bug: parent command %s doesn't have an " \
                      "attr named %r" % (previousCommand, attr_name)
                print_compact_traceback( msg + ": " )
                return                
                
            setattr(self, attr_name, parent_attr)

        else:
            msg = "bug: parent command %s not found" % self.command_parent
            print_compact_stack( msg + ": " )
        return

    def command_enter_PM(self):
        """
        #REVIEW: NEW COMMAND API SHOULD REVISE THIS METHOD -- 2008-07-30
        """
        self._reuse_attr_of_parentCommand('propMgr')
        
    
    def init_gui(self):
        pass
    
    def restore_gui(self):
        pass
    
    def getBondType(self):
        return V_SINGLE
    
    def getBondTypeString(self):
        """
        Overridden in subclasses. 
        """
        return ''
    
    
    def _apply_bondTool_on_selected_atoms(self):
        """
        Converts the bonds between the selected atoms to one specified by
        self.graphicsMode..bondclick_v6. Example: When user selects all atoms in 
        a nanotube and clicks 'graphitic' bond button, it converts all the 
        bonds between the selected atoms to graphitic bonds. 
        @see: self.activateBondsTool()
        @see: self.changeBondTool()
        @see: bond_utils.apply_btype_to_bond()
        @see: BuildAtoms_GraphicsMode.bond_change_type()
        """
        #Method written on 2008-05-04 to support NFR bug 2832. This need to 
        #be reviewed for further optimization (not urgent) -- Ninad
        #This flag is set while activating the bond tool. 
        #see self.activateBondsTool()
        if self._supress_apply_bondTool_on_selected_atoms:
            return
        
        bondTypeString = self.getBondTypeString()
                
               
        #For the history message
        converted_bonds = 0
        non_converted_bonds = 0
        deleted_bonds = 0
        #We wil check the bond dictionary to see if a bond between the 
        #selected atoms is already operated on.
        bondDict = {}
        
        bondList = [] 
        #all selected atoms 
        atoms = self.win.assy.selatoms.values()
        for a in atoms:
            for b in a.bonds[:]:
                #If bond 'b' is already in the bondDict, skip this 
                #iteration.
                if bondDict.has_key(id(b)):
                    continue
                else:
                    bondDict[id(b)] = b
                #neigbor atom of the atom 'a'    
                neighbor = b.other(a)
                
                if neighbor.element != Singlet and neighbor.picked: 
                    bond_type_changed = self.graphicsMode.bond_change_type(
                        b, 
                        allow_remake_bondpoints = True,
                        supress_history_message = True
                    )
                    if bond_type_changed:
                        converted_bonds += 1
                    else:
                        non_converted_bonds += 1
                                           
                             
        msg = "%d bonds between selected atoms "\
            "converted to %s" %(converted_bonds, 
                                bondTypeString)
        msg2 = ''
        if non_converted_bonds:
            msg2 = orangemsg(" [Unable to convert %d "\
                             "bonds to %s]"%(non_converted_bonds, 
                                             bondTypeString))
        if msg2:
            msg += msg2
            
        if msg:
            env.history.message(msg)
            
        self.glpane.gl_update()
            
            
    
    #TEMPORARILY override the is*ToolActive methods in BuildAtoms_Command. 
    #These methods will go away when BuildAtoms command starts treating 
    #each tool as a subcommand. 
    def isAtomsToolActive(self):
        """
        Tells whether the Atoms Tool is active (boolean)          
        """        
        return False
    
    def isBondsToolActive(self):
        """
        Tells whether the Bonds Tool is active (boolean)          
        """        
        return True
    
    def isDeletBondsToolActive(self):
        """
        Tells whether the Delete Bonds Tool is active (boolean)          
        """        
        return False
    
#####################

#classes need to be in their own module
class SingleBondTool(BondTool_Command):
    commandName = 'SINGLE_BOND_TOOL'            
    def getBondType(self):
        return V_SINGLE
    
    def getBondTypeString(self):
        """
        Overrides superclass method. 
        """
        return 'Single Bond'

class DoubleBondTool(BondTool_Command):
    commandName = 'DOUBLE_BOND_TOOL'
    def getBondType(self):
        return V_DOUBLE
    
    def getBondTypeString(self):
        """
        Overridden in subclasses. 
        """
        return 'Double Bond'

class TripleBondTool(BondTool_Command):
    commandName = 'TRIPLE_BOND_TOOL'
    def getBondType(self):
        return V_TRIPLE
    
    def getBondTypeString(self):
        """
        Overridden in subclasses. 
        """
        return 'Triple Bond'
    
class AromaticBondTool(BondTool_Command):
    commandName = 'AROMATIC_BOND_TOOL'
    
    def getBondType(self):
        return V_AROMATIC
    
    def getBondTypeString(self):
        """
        Overridden in subclasses. 
        """
        return 'Aromatic Bond'

class GraphiticBondTool(BondTool_Command):
    commandName = 'GRAPHITIC_BOND_TOOL'
    
    def getBondType(self):
        return V_GRAPHITE
    
    def getBondTypeString(self):
        """
        Overridden in subclasses. 
        """
        return 'Graphitic Bond'

class DeleteBondTool(BondTool_Command):
    GraphicsMode_class = DeleteBondTool_GraphicsMode
    commandName = 'DELETE_BOND_TOOL'
    
    def _apply_bondTool_on_selected_atoms(self):
        """
        Converts the bonds between the selected atoms to one specified by
        self.graphicsMode..bondclick_v6. Example: When user selects all atoms in 
        a nanotube and clicks 'graphitic' bond button, it converts all the 
        bonds between the selected atoms to graphitic bonds. 
        @see: self.activateBondsTool()
        @see: self.changeBondTool()
        @see: bond_utils.apply_btype_to_bond()
        @see: BuildAtoms_GraphicsMode.bond_change_type()
        """
        #Method written on 2008-05-04 to support NFR bug 2832. This need to 
        #be reviewed for further optimization (not urgent) -- Ninad
        #This flag is set while activating the bond tool. 
        #see self.activateBondsTool()
        if self._supress_apply_bondTool_on_selected_atoms:
            return
                      
        deleted_bonds = 0
        #We wil check the bond dictionary to see if a bond between the 
        #selected atoms is already operated on.
        bondDict = {}
        bondList = [] 
        #all selected atoms 
        atoms = self.win.assy.selatoms.values()
        for a in atoms:
            for b in a.bonds[:]:
                #If bond 'b' is already in the bondDict, skip this 
                #iteration.
                if bondDict.has_key(id(b)):
                    continue
                else:
                    bondDict[id(b)] = b
                #neigbor atom of the atom 'a'    
                neighbor = b.other(a)
                
                if neighbor.element != Singlet and neighbor.picked:  
                    b.bust()
                    deleted_bonds += 1
                    
        msg = "Deleted %d bonds between selected atoms"%deleted_bonds
        env.history.message(msg)  
        self.glpane.gl_update()