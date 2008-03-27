# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaDuplex.py -- DNA duplex generator helper classes, based on empirical data.

@author: Mark Sims
@version: $Id$
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details.

History:

Mark 2007-10-18:
- Created. Major rewrite of DnaGenHelper.py.
"""

import foundation.env as env
import os
import random

from math    import sin, cos, pi

from utilities.debug import print_compact_traceback, print_compact_stack

from platform.PlatformDependent import find_plugin_dir
from files.mmp.files_mmp import readmmp
from geometry.VQT import Q, V, angleBetween, cross, vlen
from commands.Fuse.fusechunksMode import fusechunksBase
from utilities.Log      import orangemsg
from command_support.GeneratorBaseClass import PluginBug
from utilities.constants import gensym, darkred, blue, orange, olive
from utilities.constants import diBALL, diTUBES
from utilities.prefs_constants import dnaDefaultSegmentColor_prefs_key

from dna.model.Dna_Constants import getDuplexBasesPerTurn

from simulation.sim_commandruns import adjustSinglet

from model.elements import PeriodicTable
from model.Line import Line

Element_Ae3 = PeriodicTable.getElement('Ae3')

from dna.model.Dna_Constants import basesDict, dnaDict

basepath_ok, basepath = find_plugin_dir("DNA")
if not basepath_ok:
    env.history.message(orangemsg("The cad/plugins/DNA directory is missing."))

RIGHT_HANDED = -1
LEFT_HANDED  =  1


from geometry.VQT import V, Q, norm, cross  
from geometry.VQT import  vlen
from Numeric import dot


class Dna:
    """
    Dna base class. It is inherited by B_Dna and Z_Dna subclasses.

    @ivar baseRise: The rise (spacing) between base-pairs along the helical
                    (Z) axis.
    @type baseRise: float

    @ivar handedness: Right-handed (B and A forms) or left-handed (Z form).
    @type handedness: int

    @ivar model: The model representation, where:
                    - "PAM3" = PAM-3 reduced model.
                    - "PAM5" = PAM-5 reduced model.

    @type model: str

    @ivar numberOfBasePairs: The number of base-pairs in the duplex.
    @type numberOfBasePairs: int

    @note: Atomistic models are not supported.
    @TODO: This classe's attribute 'assy' (self.assy) is determined in self.make
           Its okay because callers only call dna.make() first. If assy object 
           is going to remain constant,(hopefully is the case) the caller should
           pass it to the costructor of this class. (not defined as of 
           2008-03-17.

    """
    #initialize sel.assy to None. This is determined each time in self.make()
    #using the 'group' argument of that method. 
    assy = None
    #The following is a list bases inserted in to the model while generating
    #dna. see self.make()
    baseList = []

    strandA_atom_end1 = None

    def modify(self,
               group,
               ladderEndAxisAtom,
               numberOfBasePairs, 
               basesPerTurn, 
               duplexRise,
               endPoint1,
               endPoint2              
               ):
        """
        AVAILABLE AS A DEBUG PREFERENCE ONLY AS OF 2008-03-24. 
        NEED CLEANUP , LOTS OF DOCUMENTATION AND RENAMING. 
        """  
        self.assy               =  group.assy         
        assy                    =  group.assy
        #Make sure to clear self.baseList each time self.modify() is called
        self.baseList           =  []

        self.setNumberOfBasePairs(abs(numberOfBasePairs))
        self.setBaseRise(duplexRise)
        
        #@TODO: See a note in DnaSegment_EditCommand._createStructure(). Should 
        #the parentGroup object <group> be assigned properties such as
        #duplexRise, basesPerTurn in this method itself? to be decided 
        self.setBasesPerTurn(basesPerTurn)

        #End axis atom at end1. i.e. the first mouse click point from which 
        #user started resizing the dna duplex (rubberband line). This is initially
        #set to None. When we start creating the duplex and read in the first 
        #mmp file:  MiddleBasePair.mmp, we assign the appropriate atom to this 
        #variable. See self._determine_axis_and_strandA_endAtoms_at_end_1()
        self.axis_atom_end1 = None

        #The strand base atom of Strand-A, connected to the self.axis_atom_end1
        #The vector between self.axis_atom_end1 and self.strandA_atom_end1 
        #is used to determine the final orientation of the created duplex. 
        #that aligns this vector such that it is parallel to the screen. 
        #see self._orient_to_position_first_strandA_base_in_axis_plane() for 
        #more details.
        self.strandA_atom_end1 = None
        
        
        #The end strand base-atom of the original structure (segment) being 
        #resized. This and the corresponding axis end atom ot the original 
        #structure will be used to orient the new bases we will create and fuse
        #to the original structure. 
        self._original_structure_lastBaseAtom_strand1 = None
        
        #The axis end base atom of the original structure (at the resize end)
        self._original_structure_lastBaseAtom_axis = None
        
        #Do a safety check. If number of base pairs to add or subtract is 0, 
        #don't proceed further. 
        if numberOfBasePairs == 0:
            print "Duplex not created. The number of base pairs are unchanged"
            return
        
        #If the number of base pairs supplied by the caller are negative, it 
        #means the caller wants to delete those from the original structure
        #(duplex). 
        if numberOfBasePairs < 0:
            numberOfBasePairsToSubtract = abs(numberOfBasePairs)
            self._subtract_bases_from_duplex(group, 
                                             ladderEndAxisAtom,
                                             numberOfBasePairsToSubtract)
            return
        
        #Create a raw duplex first in Z direction. Using reference mmp basefiles
        #Later we will reorient this duplex and then fuse it with the original
        #duplex (which is being resized)
        self._create_raw_duplex(group, 
                                numberOfBasePairs, 
                                basesPerTurn, 
                                duplexRise )      
        
       
        # Orient the duplex.
        
        #Do the basic orientation so that axes of the newly created raw duplex
        #aligns with the original duplex
        self._orient(self.baseList, ladderEndAxisAtom.posn(), endPoint2)
        
        #Now determine the the strand1-end and axis-endAtoms at the resize 
        #end of the *original structure*. We will use this information 
        #for final orientation of the new duplex and also for fusing the new 
        #duplex with the original one. 
        
        #find out dna ladder to which the end axis atom of the original duplex
        #belongs to
        ladder = ladderEndAxisAtom.molecule.ladder 
        
        #list of end base atoms of the original duplex, at the resize end.
        #This list includes the axis end atom and strand end base atoms 
        #(so for a double stranded dna, this will return 3 atoms whereas
        #for a single stranded dna, it will return 2 atoms
        endBaseAtomList  = ladder.get_endBaseAtoms_containing_atom(ladderEndAxisAtom)        
        
        #As of 2008-03-26, we support onlu double stranded dna case
        #So endBaseAtomList should have atleast 3 atoms to proceed further. 
        if endBaseAtomList and len(endBaseAtomList) > 2:

            self._original_structure_lastBaseAtom_strand1 = endBaseAtomList[0]

            self._original_structure_lastBaseAtom_axis = endBaseAtomList[1]

            #Run full dna update so that the newly created duplex represents
            #one in dna data model. Do it before calling self._orient_for_modify
            #The dna updater run will help us use dna model features such as
            #dna ladder, rail. These will be used in final orientation 
            #of the new duplex and later fusing it with the original duplex
            #REVIEW: Wheather dna updater should be run without 
            #calling assy.update_parts... i.e. only running a local update 
            #than the whole on -- Ninad 2008-03-26
            self.assy.update_parts()
            
            #Do the final orientation of the new duplex. i.e rotate the new 
            #duplex around its own axis such that its then fusable with the
            #original duplex.
            self._orient_for_modify(endPoint1, endPoint2)
            
            #new_ladder is the dna ladder of the newly generated duplex.
            new_ladder = self.axis_atom_end1.molecule.ladder     
            
            #REFACTOR: Reset the dnaBaseNames of the atoms to 'X' 
            #replacing the original dnaBaseNames 'a' or 'b'. Do not do it 
            #inside self._postProcess because that method is also used by
            #self.make that calls self._create_atomLists_for_regrouping
            #after calling self._postProcess
            for m in new_ladder.all_chunks():
                for atm in m.atoms.values():
                    if atm.element.symbol in ('Ss3') and atm.getDnaBaseName() in ('a','b'):
                        atm.setDnaBaseName('X')
            
            #Find out the 'end' of the new ladder i.e. whether it is end0 or 
            #end1, that contains the first end axis base atom of the new duplex
            #i.e. atom self.axis_atom_end1)
            new_ladder_end = new_ladder.get_ladder_end(self.axis_atom_end1)
            
            #Find out three the end base atoms list of the new duplex 
            
            endBaseAtomList_generated_duplex = new_ladder.get_endBaseAtoms_containing_atom(self.axis_atom_end1)

            #strandA atom should be first in the list. If it is not, 
            #make sure that this list includes end atoms in this order: 
            #[strand1, axis, strand2] 
            if self.strandA_atom_end1 in endBaseAtomList_generated_duplex and \
               self.strandA_atom_end1 != endBaseAtomList_generated_duplex[0]:
                endBaseAtomList_generated_duplex.reverse()
                
            
            #Note that after orienting the duplex the first set of end base atoms 
            #in endBaseAtomList_generated_duplex will be killed. Why? because 
            #the corrsponding atoms are already present on the original duplex
            #We just used this new set for proper orientation. 

            
            #As we will be deleting the first set of 
            #endBaseAtomList_generated_duplex, et a set of base atoms connected 
            #to) the end base atoms in endBaseAtomList_generated_duplex. This 
            #will become our new end base atoms 
            
            new_endBaseAtomList = []
            for atm in endBaseAtomList_generated_duplex:
                rail = atm.molecule.get_ladder_rail()                        
                baseindex = rail.baseatoms.index(atm)

                next_atm = None
                if len(rail.baseatoms) == 1:
                    for bond_direction in (1, -1):
                        next_atm = atm.next_atom_in_bond_direction(bond_direction)
                else:                        
                    if new_ladder_end == 0:
                        #@@@BUG 2008-03-21. Handle special case when len(rail.baseatoms == 1)
                        next_atm = rail.baseatoms[1]
                    elif new_ladder_end == 1:
                        next_atm = rail.baseatoms[-2]

                assert next_atm is not None                        
                new_endBaseAtomList.append(next_atm)

            #@@REVIEW This doesn't invalidate the ladder. We just delete 
            #all the atoms and then the dna updater runs. 
            for atm in endBaseAtomList_generated_duplex:
                atm.kill()   

            #Run dna updater again
            self.assy.update_parts()

            self.axis_atom_end1 = None
            
            #FUSE new duplex with the original duplex
            chunkList1 = \
                       [ new_endBaseAtomList[0].molecule, 
                         self._original_structure_lastBaseAtom_strand1.molecule]

            chunkList2 = \
                       [ new_endBaseAtomList[1].molecule,
                          self._original_structure_lastBaseAtom_axis.molecule]

            chunkList3 = \
                       [new_endBaseAtomList[2].molecule,
                        endBaseAtomList[2].molecule]
            
            #Set the chunk color and chunk display of the new duplex such that
            #it matches with the original duplex chunk color and display
            #Actually, fusing the chunks should have taken care of this, but 
            #for some unknown reasons, its not happening. May be because 
            #chunks are not 'merged'?  ... Setting display and color for new 
            #duplex chunk is explicitely done below. Fixes bug 2711            
            for chunkPair in (chunkList1, chunkList2, chunkList3):
                display = chunkPair[1].display
                color   = chunkPair[1].color
                chunkPair[0].setDisplay(display)
                if color:
                    chunkPair[0].setcolor(color)
                
            
            
                
            

            self.fuseBasePairChunks(chunkList1)
            self.fuseBasePairChunks(chunkList2, fuseTolerance = 3.0)
            self.fuseBasePairChunks(chunkList3)


        self.assy.update_parts()
        
    
    def _subtract_bases_from_duplex(self,
                                    group, 
                                    ladderEndAxisAtom, 
                                    numberOfBasePairsToSubtract): 
        """
        AVAILABLE AS A DEBUG PREFERENCE ONLY AS OF 2008-03-26. Will be cleaned 
        up. 
        
        THIS IS BUGGY 
        """
        #TODO: See bug 2712
        #Use of wholechain.yield_rail_index_direction_counter
        #needs to be worked out. Looks like it reaches 
        #"#print "*** this direction doesn't work -- no atomB!"
        
        ladder = ladderEndAxisAtom.molecule.ladder
        
        atomsScheduledForDeletion = []
          
        atm = ladderEndAxisAtom    
        atomsScheduledForDeletion.extend(atm.strand_neighbors())
        
        #We have already considered the first set of atoms to delete (i.e.
        #the end strand atoms appended to atomsScheduledForDeletion above. 
        #So, only loop until it reaches 1 
        #NOTE: The following destructively modifies numberOfBasePairsToSubtract
        #as there is no use of this variable later. 
        while numberOfBasePairsToSubtract > 1:       
            
            rail = atm.molecule.get_ladder_rail()                
            baseindex = rail.baseatoms.index(atm)
            
            #Following copies some code from DnaMarker.py
            try_these = [
                            (rail, baseindex, 1),
                            (rail, baseindex, -1),
                         ]
            for item_rail, item_baseIndex, item_direction in try_these:
                pos = item_rail, item_baseIndex, item_direction
                pos_generator = atm.molecule.wholechain.yield_rail_index_direction_counter(
                            pos
                         )
                
                iter = 0
                pos_counter_A = pos_counter_B = None
                for pos_counter in pos_generator:
                    iter += 1
                    if iter == 1:
                        # should always happen
                        pos_counter_A = pos_counter
                    elif iter == 2:
                        # won't happen if we start at the end we scan towards
                        pos_counter_B = pos_counter
                        break
                    continue
                del pos_generator
                assert iter in (1, 2)
                railA, indexA, directionA, counter_junk = pos_counter_A
                assert (railA, indexA, directionA) == (item_rail, item_baseIndex, item_direction)
                atomB = None
                if iter < 2:
                    #print "*** this direction doesn't work -- no atomB!"
                    pass
                else:
                    # this direction works iff we found the right atom
                    railB, indexB, directionB, counter_junk = pos_counter_B
                    atomB = railB.baseatoms[indexB]
                    
                if atomB is not None:
                    atm = atomB
                    strand_neighbors = atomB.strand_neighbors()
                    for strand_atom in strand_neighbors:
                        if strand_atom not in atomsScheduledForDeletion:
                            atomsScheduledForDeletion.append(strand_atom)
                    break
                    
            numberOfBasePairsToSubtract = numberOfBasePairsToSubtract - 1
            
        for atm in atomsScheduledForDeletion:
            if atm:
                try:
                    atm.kill()
                except:
                    print_compact_traceback("bug in deleting atom while resizing the segment")
            
         
    def make(self, 
             group, 
             numberOfBasePairs, 
             basesPerTurn, 
             duplexRise,
             endPoint1,
             endPoint2,
             position = V(0, 0, 0)):
        """
        Makes a DNA duplex with the I{numberOfBase} base-pairs. 
        The duplex is oriented with its central axis coincident to the
        line (endPoint1, endPoint1), with its origin at endPoint1.

        @param assy: The assembly (part).
        @type  assy: L{assembly}

        @param group: The group node object containing the DNA. The caller
                      is responsible for creating an empty group and passing
                      it here. When finished, this group will contain the DNA
                      model.
        @type  group: L{Group}

        @param numberOfBasePairs: The number of base-pairs in the duplex.
        @type  numberOfBasePairs: int

        @param basesPerTurn: The number of bases per helical turn.
        @type  basesPerTurn: float

        @param duplexRise: The rise; the distance between adjacent bases.
        @type  duplexRise: float

        @param endPoint1: The origin of the duplex.
        @param endPoint1: L{V}

        @param endPoint2: The second point that defines central axis of 
                          the duplex.
        @param endPoint2: L{V}

        @param position: The position in 3d model space at which to create
                         the DNA strand. This should always be 0, 0, 0.
        @type position:  position

        @see: self.fuseBasePairChunks()
        @see:self._insertBasesFromMMP()
        @see: self._regroup()
        @see: self._postProcess()
        @see: self._orient()
        @see: self._rotateTranslateXYZ()
        """      

        self.assy               =  group.assy         
        assy                    =  group.assy
        #Make sure to clear self.baseList each time self.make() is called
        self.baseList           =  []

        self.setNumberOfBasePairs(numberOfBasePairs)
        self.setBaseRise(duplexRise)
        #See a note in DnaSegment_EditCommand._createStructure(). Should 
        #the parentGroup object <group> be assigned properties such as
        #duplexRise, basesPerTurn in this method itself? to be decided 
        #once dna data model is fully functional (and when this method is 
        #revised) -- Ninad 2008-03-05
        self.setBasesPerTurn(basesPerTurn)

        #End axis atom at end1. i.e. the first mouse click point from which 
        #user started drawing the dna duplex (rubberband line). This is initially
        #set to None. When we start creating the duplex and read in the first 
        #mmp file:  MiddleBasePair.mmp, we assign the appropriate atom to this 
        #variable. See self._determine_axis_and_strandA_endAtoms_at_end_1()
        self.axis_atom_end1 = None

        #The strand base atom of Strand-A, connected to the self.axis_atom_end1
        #The vector between self.axis_atom_end1 and self.strandA_atom_end1 
        #is used to determine the final orientation of the created duplex. 
        #that aligns this vector such that it is parallel to the screen. 
        #see self._orient_to_position_first_strandA_base_in_axis_plane() for more details.
        self.strandA_atom_end1 = None

        #Create a duplex by inserting basepairs from the mmp file. 
        self._create_raw_duplex(group, 
                                numberOfBasePairs, 
                                basesPerTurn, 
                                duplexRise,
                                position = position)


        # Orient the duplex.
        self._orient(self.baseList, endPoint1, endPoint2)

        #do further adjustments so that first base of strandA always lies
        #in the screen parallel plane, which is passing through the 
        #axis. 
        self._orient_to_position_first_strandA_base_in_axis_plane(self.baseList, 
                                                                  endPoint1, 
                                                                  endPoint2)

        # Regroup subgroup into strand and chunk groups
        self._regroup(group)
        return

    #START -- Helper methods used in generating dna (see self.make())===========

    def _create_raw_duplex(self,
                           group, 
                           numberOfBasePairs, 
                           basesPerTurn, 
                           duplexRise,
                           position = V(0, 0, 0)):
        """
        Create a raw dna duplex in the specified group. This will be created 
        along the Z axis. Later it will undergo more operations such as 
        orientation change anc chunk regrouping. 

        @return: A group object containing the 'raw dna duplex'
        @see: self.make()

        """
        # Make the duplex.
        subgroup = group
        subgroup.open = False    


        # Calculate the twist per base in radians.
        twistPerBase = (self.handedness * 2 * pi) / basesPerTurn
        theta = 0.0
        z     = 0.5 * duplexRise * (numberOfBasePairs - 1)

        # Create duplex.
        for i in range(numberOfBasePairs):
            basefile, zoffset, thetaOffset = self._strandAinfo(i)

            def tfm(v, theta = theta + thetaOffset, z1 = z + zoffset):
                return self._rotateTranslateXYZ(v, theta, z1)

            #Note that self.baseList gets updated in the the following method
            self._insertBaseFromMmp(basefile, 
                                    subgroup, 
                                    tfm, 
                                    self.baseList,
                                    position = position)

            if i == 0:
                #The chunk self.baseList[0] should always contain the information 
                #about the strand end and axis end atoms at end1 we are 
                #interested in. This chunk is obtained by reading in the 
                #first mmp file (at i =0) .

                #Note that we could have determined this after the for loop 
                #as well. But now harm in doing it here. This is also safe 
                #from any accidental modifications to the chunk after the for 
                #loop. Note that 'self.baseList' gets populated in 
                #sub 'def insertBasesFromMMP'.... Related TODO: The method 
                #'def make' itself needs reafcatoring so that all submethods are
                #direct methods of class Dna.
                #@see self._determine_axis_and_strandA_endAtoms_at_end_1() for 
                #more comments
                firstChunkInBaseList = self.baseList[0]
                self._determine_axis_and_strandA_endAtoms_at_end_1(self.baseList[0])

            theta -= twistPerBase
            z     -= duplexRise

        # Fuse the base-pair chunks together into continuous strands.
        self.fuseBasePairChunks(self.baseList)

        try:
            self._postProcess(self.baseList)
        except:
            if env.debug():
                print_compact_traceback( 
                    "debug: exception in %r._postProcess(self.baseList = %r) \
                    (reraising): " % (self, self.baseList,))
            raise



    def _insertBaseFromMmp(self,
                           filename, 
                           subgroup, 
                           tfm, 
                           baseList,
                           position = V(0, 0, 0) ):
        """
        Insert the atoms for a nucleic acid base from an MMP file into
        a single chunk.
         - If atomistic, the atoms for each base are in a separate chunk.
         - If PAM5, the pseudo atoms for each base-pair are together in a 
           chunk.

        @param filename: The mmp filename containing the base 
                         (or base-pair).
        @type  filename: str

        @param subgroup: The part group to add the atoms to.
        @type  subgroup: L{Group}

        @param tfm: Transform applied to all new base atoms.
        @type  tfm: V

        @param baseList: A list that maintains the bases inserted into the 
                         model Example self.baseList

        @param position: The origin in space of the DNA duplex, where the
                         3' end of strand A is 0, 0, 0.
        @type  position: L{V}

        """

        #@TODO: The argument baselist ACTUALLY MODIFIES self.baseList. Should we 
        #directly use self.baseList instead? Only comments are added for 
        #now. See also self.make()(the caller)
        try:
            grouplist = readmmp(self.assy, filename, isInsert = True)
        except IOError:
            raise PluginBug("Cannot read file: " + filename)
        if not grouplist:
            raise PluginBug("No atoms in DNA base? " + filename)

        viewdata, mainpart, shelf = grouplist

        for member in mainpart.members:
            # 'member' is a chunk containing a full set of 
            # base-pair pseudo atoms.

            for atm in member.atoms.values():                            
                atm._posn = tfm(atm._posn) + position

            member.name = "BasePairChunk"
            subgroup.addchild(member)

            #Append the 'member' to the baseList. Note that this actually 
            #modifies self.baseList. Should self.baseList be directly used here?
            baseList.append(member)

        # Clean up.
        del viewdata                
        shelf.kill()

    def _rotateTranslateXYZ(self, inXYZ, theta, z):
        """
        Returns the new XYZ coordinate rotated by I{theta} and 
        translated by I{z}.

        @param inXYZ: The original XYZ coordinate.
        @type  inXYZ: V

        @param theta: The base twist angle.
        @type  theta: float

        @param z: The base rise.
        @type  z: float

        @return: The new XYZ coordinate.
        @rtype:  V
        """
        c, s = cos(theta), sin(theta)
        x = c * inXYZ[0] + s * inXYZ[1]
        y = -s * inXYZ[0] + c * inXYZ[1]
        return V(x, y, inXYZ[2] + z)


    def fuseBasePairChunks(self, baseList, fuseTolerance = 1.5):
        """
        Fuse the base-pair chunks together into continuous strands.

        @param baseList: The list of bases inserted in the model. See self.make
                          (the caller) for an example.
        @see: self.make()
        @NOTE: self.assy is determined in self.make() so this method 
               must be called from that method only.
        """

        if self.assy is None:
            print_compact_stack("bug:self.assy not defined.Unable to fusebases")
            return 

        # Fuse the base-pair chunks together into continuous strands.
        fcb = fusechunksBase()
        fcb.tol = fuseTolerance
        
        for i in range(len(baseList) - 1):
            #Note that this is actually self.baseList that we are using. 
            #Example see self.make() which calls this method. 
            tol_string = fcb.find_bondable_pairs([baseList[i]], 
                                                 [baseList[i + 1]],
                                                 ignore_chunk_picked_state = True
                                             ) 
            fcb.make_bonds(self.assy)

    def _postProcess(self, baseList):
        return

    #END Helper methods used in dna generation (see self.make())================

    def _baseFileName(self, basename):
        """
        Returns the full pathname to the mmp file containing the atoms 
        of a nucleic acid base (or base-pair).

        Example: If I{basename} is "MidBasePair" and this is a PAM5 model of
        B-DNA, this returns:

          - "C:$HOME\cad\plugins\DNA\B-DNA\PAM5-bases\MidBasePair.mmp"

        @param basename: The basename of the mmp file without the extention
                         (i.e. "adenine", "MidBasePair", etc.).
        @type  basename: str

        @return: The full pathname to the mmp file.
        @rtype:  str
        """
        form    = self.form             # A-DNA, B-DNA or Z-DNA
        model   = self.model + '-bases' # PAM3 or PAM5
        return os.path.join(basepath, form, model, '%s.mmp' % basename)

    def _orient(self, baseList, pt1, pt2):
        """
        Orients the DNA duplex I{dnaGroup} based on two points. I{pt1} is
        the first endpoint (origin) of the duplex. The vector I{pt1}, I{pt2}
        defines the direction and central axis of the duplex.

        @param pt1: The starting endpoint (origin) of the DNA duplex.
        @type  pt1: L{V}

        @param pt2: The second point of a vector defining the direction
                    and central axis of the duplex.
        @type  pt2: L{V}
        """

        a = V(0.0, 0.0, -1.0)
        # <a> is the unit vector pointing down the center axis of the default
        # DNA structure which is aligned along the Z axis.
        bLine = pt2 - pt1
        bLength = vlen(bLine)
        b = bLine/bLength
        # <b> is the unit vector parallel to the line (i.e. pt1, pt2).
        axis = cross(a, b)
        # <axis> is the axis of rotation.

        theta = angleBetween(a, b)
        # <theta> is the angle (in degress) to rotate about <axis>.
        scalar = self.getBaseRise() * (self.getNumberOfBasePairs() - 1) * 0.5
        rawOffset = b * scalar

        if 0: # Debugging code.
            print "~~~~~~~~~~~~~~"
            print "uVector  a = ", a
            print "uVector  b = ", b
            print "cross(a,b) =", axis
            print "theta      =", theta
            print "baserise   =", self.getBaseRise()
            print "# of bases =", self.getNumberOfBasePairs()
            print "scalar     =", scalar
            print "rawOffset  =", rawOffset 

        if theta == 0.0 or theta == 180.0:
            axis = V(0, 1, 0)
            # print "Now cross(a,b) =", axis

        rot =  (pi / 180.0) * theta  # Convert to radians
        qrot = Q(axis, rot) # Quat for rotation delta.

        # Move and rotate the base chunks into final orientation.
        ##for m in dnaGroup.members:
        for m in baseList:
            if isinstance(m, self.assy.Chunk):        
                m.move(qrot.rot(m.center) - m.center + rawOffset + pt1)
                m.rot(qrot)



    def _determine_axis_and_strandA_endAtoms_at_end_1(self, chunk):
        """
        Overridden in subclasses. Default implementation does nothing. 

        @param chunk: The method itereates over chunk atoms to determine 
                      strand and axis end atoms at end 1. 
        @see: B_DNA_PAM3._determine_axis_and_strandA_endAtoms_at_end_1()
              for documentation and implementation. 
        """
        pass

    def _orient_for_modify(self, baseList, end1, end2):        
        pass

    def _orient_to_position_first_strandA_base_in_axis_plane(self, baseList, end1, end2):
        """
        Overridden in subclasses. Default implementation does nothing.

        The self._orient method orients the DNA duplex parallel to the screen
        (lengthwise) but it doesn't ensure align the vector
        through the strand end atom on StrandA and the corresponding axis end 
        atom  (at end1) , parallel to the screen. 

        This function does that ( it has some rare bugs which trigger where it
        doesn't do its job but overall works okay )

        What it does: After self._orient() is done orienting, it finds a Quat 
        that rotates between the 'desired vector' between strand and axis ends at
        end1(aligned to the screen)  and the actual vector based on the current
        positions of these atoms.  Using this quat we rotate all the chunks 
        (as a unit) around a common center. 

        @BUG: The last part 'rotating as a unit' uses a readymade method in 
        ops_motion.py -- 'rotateSpecifiedMovables' . This method itself may have
        some bugs because the axis of the dna duplex is slightly offset to the
        original axis. 

        @see: self._determine_axis_and_strandA_endAtoms_at_end_1()
        @see: self.make()

        @see: B_DNA_PAM3._orient_to_position_first_strandA_base_in_axis_plane

        """
        pass


    def _regroup(self, dnaGroup):
        """
        Regroups I{dnaGroup} into group containing three chunks: I{StrandA},
        I{StrandB} and I{Axis} of the DNA duplex.

        @param dnaGroup: The DNA group which contains the base-pair chunks
                         of the duplex.
        @type  dnaGroup: L{Group}

        @return: The new DNA group that contains the three chunks
                 I{StrandA}, I{StrandB} and I{Axis}.
        @rtype:  L{Group}
        """
            #Get the lists of atoms (two lists for two strands and one for the axis
            #for creating new chunks 

        _strandA_list, _strandB_list, _axis_list = \
                     self._create_atomLists_for_regrouping(dnaGroup)



        # Create strand and axis chunks from atom lists and add 
        # them to the dnaGroup.

        # [bruce 080111 add conditions to prevent bugs in PAM5 case
        #  which is not yet supported in the above code. It would be
        #  easy to support it if we added dnaBaseName assignments
        #  into the generator mmp files and generalized the above
        #  symbol names, and added a 2nd pass for Pl atoms.
        #  update, bruce 080311: it looks like something related to
        #  this has been done without this comment being updated.]

        if _strandA_list:
            strandAChunk = \
                         self.assy.makeChunkFromAtomList(
                             _strandA_list,
                             name = gensym("Strand"),
                             group = dnaGroup,
                             color = darkred)
        if _strandB_list:
            strandBChunk = \
                         self.assy.makeChunkFromAtomList(
                             _strandB_list,
                             name = gensym("Strand"),
                             group = dnaGroup,
                             color = blue)
        if _axis_list:
            axisChunk = \
                      self.assy.makeChunkFromAtomList(
                          _axis_list,
                          name = "Axis",
                          group = dnaGroup,
                          color = env.prefs[dnaDefaultSegmentColor_prefs_key])



        return

    def getBaseRise( self ):
        """
        Get the base rise (spacing) between base-pairs.
        """
        return float( self.baseRise )

    def setBaseRise( self, inBaseRise ):
        """
        Set the base rise (spacing) between base-pairs.

        @param inBaseRise: The base rise in Angstroms.
        @type  inBaseRise: float
        """
        self.baseRise  =  inBaseRise

    def getNumberOfBasePairs( self ):
        """
        Get the number of base-pairs in this duplex.
        """
        return self.numberOfBasePairs

    def setNumberOfBasePairs( self, inNumberOfBasePairs ):
        """
        Set the base rise (spacing) between base-pairs.

        @param inNumberOfBasePairs: The number of base-pairs.
        @type  inNumberOfBasePairs: int
        """
        self.numberOfBasePairs  =  inNumberOfBasePairs

    def setBasesPerTurn(self, basesPerTurn):
        """
        Sets the number of base pairs per turn
        @param basesPerTurn: Number of bases per turn
        @type  basesPerTurn: int
        """
        self.basesPerTurn = basesPerTurn

    def getBasesPerTurn(self):
        """
        returns the number of bases per turn in the duplex
        """
        return self.basesPerTurn

    pass

class A_Dna(Dna):
    """
    Provides an atomistic model of the A form of DNA.

    The geometry for A-DNA is very twisty and funky. We need to to research 
    the A form since it's not a simple helix (like B) or an alternating helix 
    (like Z).

    @attention: This class is not implemented yet.
    """
    form       =  "A-DNA"
    baseRise   =  dnaDict['A-DNA']['DuplexRise']
    handedness =  RIGHT_HANDED

class A_Dna_PAM5(A_Dna):
    """
    Provides a PAM-5 reduced model of the B form of DNA.

    @attention: This class is not implemented yet.
    """
    model = "PAM5"
    pass

class A_Dna_PAM3(A_Dna):
    """
    Provides a PAM-5 reduced model of the B form of DNA.

    @attention: This class is not implemented yet.
    """
    model = "PAM3"
    pass

class B_Dna(Dna):
    """
    Provides an atomistic model of the B form of DNA.
    """
    form       =  "B-DNA"
    baseRise   =  dnaDict['B-DNA']['DuplexRise']
    handedness =  RIGHT_HANDED

    basesPerTurn = getDuplexBasesPerTurn('B-DNA')   

    pass

class B_Dna_PAM5(B_Dna):
    """
    Provides a PAM-5 reduced model of the B form of DNA.
    """
    model = "PAM5"

    def _isStartPosition(self, index):
        """
        Returns True if I{index} points the first base-pair position (5').

        @param index: Base-pair index.
        @type  index: int

        @return: True if index is zero.
        @rtype : bool
        """
        if index == 0:
            return True
        else:
            return False

    def _isEndPosition(self, index):
        """
        Returns True if I{index} points the last base-pair position (3').

        @param index: Base-pair index.
        @type  index: int

        @return: True if index is zero.
        @rtype : bool
        """
        if index ==  self.getNumberOfBasePairs() - 1:
            return True
        else:
            return False

    def _strandAinfo(self, index):
        """
        Returns parameters needed to add a base, including its complement base,
        to strand A.

        @param index: Base-pair index.
        @type  index: int
        """
        zoffset      =  0.0
        thetaOffset  =  0.0
        basename     =  "MiddleBasePair"

        if self._isStartPosition(index):
            basename = "StartBasePair"

        if self._isEndPosition(index):
            basename = "EndBasePair"

        if self.getNumberOfBasePairs() == 1:
            basename = "SingleBasePair"

        basefile     =  self._baseFileName(basename)
        return (basefile, zoffset, thetaOffset)

    def _postProcess(self, baseList): # bruce 070414
        """
        Set bond direction on the backbone bonds.

        @param baseList: List of basepair chunks that make up the duplex.
        @type  baseList: list
        """
        # This implem depends on the specifics of how the end-representations
        # are terminated. If that's changed, it might stop working or it might
        # start giving wrong results. In the current representation, 
        # baseList[0] (a chunk) has two bonds whose directions we must set,
        # which will determine the directions of their strands: 
        #   Ss5 -> Sh5, and Ss5 <- Pe5.
        # Just find those bonds and set the strand directions (until such time
        # as they can be present to start with in the end1 mmp file).
        # (If we were instead passed all the atoms, we could be correct if we 
        # just did this to the first Pe5 and Sh5 we saw, or to both of each if 
        # setting the same direction twice is allowed.)
        atoms = baseList[0].atoms.values()
        Pe_list = filter( lambda atom: atom.element.symbol in ('Pe5'), atoms)
        Sh_list = filter( lambda atom: atom.element.symbol in ('Sh5'), atoms)

        if len(Pe_list) == len(Sh_list) == 1:
            for atom in Pe_list:
                assert len(atom.bonds) == 1
                atom.bonds[0].set_bond_direction_from(atom, 1, propogate = True)
            for atom in Sh_list:
                assert len(atom.bonds) == 1
                atom.bonds[0].set_bond_direction_from(atom, -1, propogate = True)
        else:
            #bruce 070604 mitigate bug in above code when number of bases == 1
            # by not raising an exception when it fails.
            msg = "Warning: strand not terminated, bond direction not set \
                (too short)"
            env.history.message( orangemsg( msg))

            # Note: It turns out this bug is caused by a bug in the rest of the
            # generator (which I didn't try to diagnose) -- for number of 
            # bases == 1 it doesn't terminate the strands, so the above code
            # can't find the termination atoms (which is how it figures out
            # what to do without depending on intimate knowledge of the base 
            # mmp file contents).

            # print "baseList = %r, its len = %r, atoms in [0] = %r" % \
            #       (baseList, len(baseList), atoms)
            ## baseList = [<molecule 'unknown' (11 atoms) at 0xb3d6f58>],
            ## its len = 1, atoms in [0] = [Ax1, X2, X3, Ss4, Pl5, X6, X7, Ss8, Pl9, X10, X11]

            # It would be a mistake to fix this here (by giving it that
            # intimate knowledge) -- instead we need to find and fix the bug 
            # in the rest of generator when number of bases == 1.
        return

    def _create_atomLists_for_regrouping(self, dnaGroup):
        """
        Creates and returns the atom lists that will be used to regroup the 
        chunks  within the DnaGroup. 

        @param dnaGroup: The DnaGroup whose atoms will be filtered and put into 
                         individual strand A or strandB or axis atom lists.
        @return: Returns a tuple containing three atom lists 
                 -- two atom lists for strand chunks and one for axis chunk. 
        @see: self._regroup()
        """
        _strandA_list  =  []
        _strandB_list  =  []
        _axis_list     =  []
        # Build strand and chunk atom lists.
        for m in dnaGroup.members:
            for atom in m.atoms.values():                
                if atom.element.symbol in ('Pl5', 'Pe5'):
                    if atom.getDnaStrandId_for_generators() == 'Strand1':                        
                        _strandA_list.append(atom)
                        # Following makes sure that the info record 
                        #'dnaStrandId_for_generators' won't be written for 
                        #this atom that the dna generator outputs. i.e.
                        #the info record 'dnaStrandId_for_generators' is only 
                        #required while generating the dna from scratch
                        #(by reading in the strand base files in 'cad/plugins'
                        #see more comments in Atom.getDnaStrandId_for_generators
                        atom.setDnaStrandId_for_generators('')
                    elif atom.getDnaStrandId_for_generators() == 'Strand2':
                        atom.setDnaStrandId_for_generators('')
                        _strandB_list.append(atom)                        
                if atom.element.symbol in ('Ss5', 'Sh5'):
                    if atom.getDnaBaseName() == 'a':
                        _strandA_list.append(atom)
                        #Now reset the DnaBaseName for the added atom 
                        # to 'unassigned' base i.e. 'X'
                        atom.setDnaBaseName('X')
                    elif atom.getDnaBaseName() == 'b':
                        _strandB_list.append(atom)
                        #Now reset the DnaBaseName for the added atom 
                        # to 'unassigned' base i.e. 'X'
                        atom.setDnaBaseName('X')
                    else:
                        msg = "Ss5 or Sh5 atom not assigned to strand 'a' or 'b'."
                        raise PluginBug(msg)
                elif atom.element.symbol in ('Ax5', 'Ae5', 'Gv5', 'Gr5'):
                    _axis_list.append(atom)

        return (_strandA_list, _strandB_list, _axis_list)

class B_Dna_PAM3(B_Dna_PAM5):
    """
    Provides a PAM-3 reduced model of the B form of DNA.
    """
    model = "PAM3"

    strandA_atom_end1 = None

    def _strandAinfo(self, index):
        """
        Returns parameters needed to add the next base-pair to the duplex 
        build built.

        @param index: Base-pair index.
        @type  index: int
        """

        zoffset      =  0.0
        thetaOffset  =  0.0
        basename     =  "MiddleBasePair"
        basefile     =  self._baseFileName(basename)
        return (basefile, zoffset, thetaOffset)
    



    def _postProcess(self, baseList):
        """
        Final tweaks on the DNA chunk, including:

          - Transmute Ax3 atoms on each end into Ae3.
          - Adjust open bond singlets.

        @param baseList: List of basepair chunks that make up the duplex.
        @type  baseList: list

        @note: baseList must contain at least two base-pair chunks.
        """
        
        if len(baseList) < 1:
            print_compact_stack("bug? (ignoring) DnaDuplex._postProcess called but "\
                                " baseList is empty. May be dna_updater was "\
                                "run? ")
            return

        start_basepair_atoms = baseList[0].atoms.values()
        end_basepair_atoms = baseList[-1].atoms.values()

        Ax_caps = filter( lambda atom: atom.element.symbol in ('Ax3'), 
                          start_basepair_atoms)
        Ax_caps += filter( lambda atom: atom.element.symbol in ('Ax3'), 
                           end_basepair_atoms)

        # Transmute Ax3 caps to Ae3 atoms. 
        # Note: this leaves two "killed singlets" hanging around,  
        #       one from each Ax3 cap.
        #
        # REVIEW: is it safe to simply not do this when dna_updater_is_enabled()?
        # [bruce 080320 question]
        for atom in Ax_caps:
            atom.Transmute(Element_Ae3)

        # X_List will contain 6 singlets, 2 of which are killed (non-bonded).
        # The other 4 are the 2 pair of strand open bond singlets.
        X_List = filter( lambda atom: atom.element.symbol in ('X'), 
                         start_basepair_atoms)
        X_List += filter( lambda atom: atom.element.symbol in ('X'), 
                          end_basepair_atoms)

        # Adjust the 4 open bond singlets.
        for singlet in X_List:
            if singlet.killed():
                # Skip the 2 killed singlets.
                continue
            adjustSinglet(singlet)
            
 
        return

    def _determine_axis_and_strandA_endAtoms_at_end_1(self, chunk):
        """
        Determine the axis end atom and the strand atom on strand 1 
        connected to it , at end1 . i.e. the first mouse click point from which 
        user started drawing the dna duplex (rubberband line)

        These are initially set to None. 

        The strand base atom of Strand-A, connected to the self.axis_atom_end1
        The vector between self.axis_atom_end1 and self.strandA_atom_end1 
        is used to determine the final orientation of the created duplex
        done in self._orient_to_position_first_strandA_base_in_axis_plane()

        This vector is aligned such that it is parallel to the screen. 

        i.e. StrandA end Atom and corresponding axis end atom are coplaner and 
        parallel to the screen.   

        @NOTE:The caller should make sure that the appropriate chunk is passed 
              as an argument to this method. This function itself only finds 
              and assigns the axis ('Ax3') and strand ('Ss3' atom and on StrandA)
              atoms it sees first to the  respective attributes. (and which pass
              other necessary tests)        

        @see: self.make() where this function is called
        @see: self._orient_to_position_first_strandA_base_in_axis_plane()
        """
        for atm in chunk.atoms.itervalues():
            if self.axis_atom_end1 is None:
                if atm.element.symbol == 'Ax3':
                    self.axis_atom_end1 = atm
            if self.strandA_atom_end1 is None:
                if atm.element.symbol == 'Ss3' and atm.getDnaBaseName() == 'a':
                    self.strandA_atom_end1 = atm

    def _orient_for_modify(self, end1, end2):    
        

        original_ladder = self._original_structure_lastBaseAtom_axis.molecule.ladder
        original_ladder_end = original_ladder.get_ladder_end(self._original_structure_lastBaseAtom_axis)

        rail_for_strandA_of_original_duplex = self._original_structure_lastBaseAtom_strand1.molecule.get_ladder_rail()      

        rail_bond_direction_of_strandA_of_original_duplex = rail_for_strandA_of_original_duplex.bond_direction()

        b = norm(end2 - end1)
        new_ladder =   self.axis_atom_end1.molecule.ladder
        new_ladder_end = new_ladder.get_ladder_end(self.axis_atom_end1)

        chunkListForRotation = new_ladder.all_chunks()

        endBaseAtomList  = new_ladder.get_endBaseAtoms_containing_atom(self.axis_atom_end1)
        
        endStrandbaseAtoms = (endBaseAtomList[0], endBaseAtomList[2])        

        self.strandA_atom_end1 = None
        for atm in endStrandbaseAtoms:
            rail = atm.molecule.get_ladder_rail()

            bond_direction = rail.bond_direction()

            if new_ladder_end == original_ladder_end:                
                if bond_direction != rail_bond_direction_of_strandA_of_original_duplex:
                    self.strandA_atom_end1 = atm
            else:
                if bond_direction == rail_bond_direction_of_strandA_of_original_duplex:
                    self.strandA_atom_end1 = atm 
                    

        axis_strand_vector = (self.strandA_atom_end1.posn() - \
                              self.axis_atom_end1.posn())


        vectorAlongLadderStep =  self._original_structure_lastBaseAtom_strand1.posn() - \
                              self._original_structure_lastBaseAtom_axis.posn()

        unitVectorAlongLadderStep = norm(vectorAlongLadderStep)

        self.final_pos_strand_end_atom = \
            self.axis_atom_end1.posn() + \
            vlen(axis_strand_vector)*unitVectorAlongLadderStep

        expected_vec = self.final_pos_strand_end_atom - self.axis_atom_end1.posn()
        
        DEBUG_BY_DRAWING_LINES = 0

        if DEBUG_BY_DRAWING_LINES:
            pointList1 = (self.strandA_atom_end1.posn() ,
                          self.axis_atom_end1.posn())
            line1 = Line(self.assy.w, pointList = pointList1)

            pointList2 = (self._original_structure_lastBaseAtom_strand1.posn(),
                          self._original_structure_lastBaseAtom_axis.posn())
            line2 = Line(self.assy.w, pointList = pointList2)

            pointList3 = (self.final_pos_strand_end_atom, self.axis_atom_end1.posn())
            line3 = Line(self.assy.w, pointList = pointList3)

            pointList4 = (end1, end2)
            line4 = Line(self.assy.w, pointList = pointList4)
            print "~~~~~~~~~~~~~~~~~~~~"
            print "***self.strandA_atom_end1 =", self.strandA_atom_end1
            print "***%s vector before orientation" %(line1.name)
            print "***%s orientation of the last duplex"%(line2.name)
            print "***%s expected orientation of new duplex"%(line3.name)
            print "***%s end1  to end2"%(line4.name)
            print "~~~~~~~~~~~~~~~~~~~~"

        
        q_new = Q(axis_strand_vector, vectorAlongLadderStep)

        if dot(axis_strand_vector, cross(vectorAlongLadderStep, b)) < 0:
            q_new2 = Q(b, -q_new.angle)
        else:     
            q_new2 = Q(b, q_new.angle) 


        self.assy.rotateSpecifiedMovables(q_new2, chunkListForRotation, end1)

    def _orient_to_position_first_strandA_base_in_axis_plane(self, baseList, end1, end2):
        """
        The self._orient method orients the DNA duplex parallel to the screen
        (lengthwise) but it doesn't ensure align the vector
        through the strand end atom on StrandA and the corresponding axis end 
        atom  (at end1) , parallel to the screen. 

        This function does that ( it has some rare bugs which trigger where it
        doesn't do its job but overall works okay )

        What it does: After self._orient() is done orienting, it finds a Quat 
        that rotates between the 'desired vector' between strand and axis ends at
        end1(aligned to the screen)  and the actual vector based on the current
        positions of these atoms.  Using this quat we rotate all the chunks 
        (as a unit) around a common center.

        @BUG: The last part 'rotating as a unit' uses a readymade method in 
        ops_motion.py -- 'rotateSpecifiedMovables' . This method itself may have
        some bugs because the axis of the dna duplex is slightly offset to the
        original axis. 

        @see: self._determine_axis_and_strandA_endAtoms_at_end_1()
        @see: self.make()
        """

        #the vector between the two end points. these are more likely
        #points clicked by the user while creating dna duplex using endpoints
        #of a line. In genral, end1 and end2 are obtained from self.make()
        b = norm(end2 - end1)        

        axis_strand_vector = (self.strandA_atom_end1.posn() - \
                              self.axis_atom_end1.posn())

        vectorAlongLadderStep =  cross(-self.assy.o.lineOfSight, b)
        unitVectorAlongLadderStep = norm(vectorAlongLadderStep)

        self.final_pos_strand_end_atom = \
            self.axis_atom_end1.posn() + \
            vlen(axis_strand_vector)*unitVectorAlongLadderStep

        expected_vec = self.final_pos_strand_end_atom - self.axis_atom_end1.posn()

        q_new = Q(axis_strand_vector, expected_vec)

        if dot(axis_strand_vector, self.assy.o.lineOfSight) < 0:            
            q_new2 = Q(b, -q_new.angle)
        else:     
            q_new2 = Q(b, q_new.angle) 


        self.assy.rotateSpecifiedMovables(q_new2, baseList, end1)


    def _create_atomLists_for_regrouping(self, dnaGroup):
        """
        Creates and returns the atom lists that will be used to regroup the 
        chunks  within the DnaGroup. 

        @param dnaGroup: The DnaGroup whose atoms will be filtered and put into 
                         individual strand A or strandB or axis atom lists.
        @return: Returns a tuple containing three atom lists 
                 -- two atom lists for strand chunks and one for axis chunk. 
        @see: self._regroup()
        """
        _strandA_list  =  []
        _strandB_list  =  []
        _axis_list     =  []

        # Build strand and chunk atom lists.
        for m in dnaGroup.members:
            for atom in m.atoms.values():
                if atom.element.symbol in ('Ss3'):
                    if atom.getDnaBaseName() == 'a':
                        _strandA_list.append(atom)
                        #Now reset the DnaBaseName for the added atom 
                        # to 'unassigned' base i.e. 'X'
                        atom.setDnaBaseName('X')
                    elif atom.getDnaBaseName() == 'b':
                        _strandB_list.append(atom)
                        #Now reset the DnaBaseName for the added atom 
                        # to 'unassigned' base i.e. 'X'
                        atom.setDnaBaseName('X')
                    else:
                        msg = "Ss3 atom not assigned to strand 'a' or 'b'."
                        raise PluginBug(msg)
                elif atom.element.symbol in ('Ax3', 'Ae3'):
                    _axis_list.append(atom)

        return (_strandA_list, _strandB_list, _axis_list)



class Z_Dna(Dna):
    """
    Provides an atomistic model of the Z form of DNA.
    """

    form       =  "Z-DNA"
    baseRise   =  dnaDict['Z-DNA']['DuplexRise']
    handedness =  LEFT_HANDED

class Z_Dna_Atomistic(Z_Dna):
    """
    Provides an atomistic model of the Z form of DNA.

    @attention: This class will never be implemented.
    """
    model = "PAM5"

    def _strandAinfo(self, baseLetter, index):
        """
        Returns parameters needed to add a base to strand A.

        @param baseLetter: The base letter.
        @type  baseLetter: str

        @param index: Base-pair index.
        @type  index: int
        """

        thetaOffset  =  0.0
        basename  =  basesDict[baseLetter]['Name']

        if (index & 1) != 0: 
            # Index is odd.
            basename  +=  "-outer"
            zoffset    =  2.045
        else: 
            # Index is even.
            basename  +=  '-inner'
            zoffset    =  0.0

        basefile     =  self._baseFileName(basename)
        return (basefile, zoffset, thetaOffset)

    def _strandBinfo(self, baseLetter, index):
        """
        Returns parameters needed to add a base to strand B.

        @param baseLetter: The base letter.
        @type  baseLetter: str

        @param index: Base-pair index.
        @type  index: int
        """

        thetaOffset  =  0.5 * pi
        basename     =  basesDict[baseLetter]['Name']

        if (index & 1) != 0:
            basename  +=  '-inner'
            zoffset    =  -0.055
        else:
            basename  +=  "-outer"
            zoffset    =  -2.1

        basefile     = self._baseFileName(basename)
        return (basefile, zoffset, thetaOffset)

class Z_Dna_PAM5(Z_Dna):
    """
    Provides a PAM-5 reduced model of the Z form of DNA.

    @attention: This class is not implemented yet.
    """
    pass

