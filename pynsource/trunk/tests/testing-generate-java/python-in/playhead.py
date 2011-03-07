"""
  Storyline Playhead class.

  Handles the logic of moving a playhead along a list.  0 based.
  It doesn't actually know the list nor of what items are in the list.
  No storage or list is kept by this class.

  SIMPLE OVERVIEW DOCUMENTATION
     0 .. MaxPosition
     __init__(maxitems) thus init of 10 gives 0 .. 9
   
     Position is -1 until Notify of insert called telling us of a valid position,
      then position moved to 0
    
     NotifyOfInsert says that position 'position' is now valid.
      E.g. NotifyOfInsert(0) says we are tracking one item
           the list is now 0..0 and MaxPosition is 0

  Discussion on design:
  ---------------------
  This solution (solution A) is: go to the new time point and play what is
  there.  You are always pointing to the thing you are looking at.
  You are never pointing to anything either before or after what you are
  looking at.  What you see is what you get.
  
  The idea, just like in a GUI is that you are always looking at what
  you are pointing at.

"""

class Playhead:
    def __init__(self, maxitems=0):
        """
        Position is -1 if unspecified (no commands issued to this class yet)
          otherwise  0 to MaxPosition (MaxPosition is maxitems -1)
        MaxPosition is -1 when no items in the list we are looking after.
        """
        self.Clear()
        assert maxitems >= 0

        # Add useful behaviour to initial position.        
        if maxitems > 0:
            self.Position = 0
            
        self._SetMaxItems(maxitems)
    def Clear(self):
        self.Position = -1
        self.MaxPosition = -1
        self._SetMaxItems(0)
    def _ClipPositionToMax(self):
        if self.Position > self.MaxPosition:
            self.Position = self.MaxPosition
    def _SetMaxItems(self, maxitems):
        """
        Sets the maximum poisition that the playhead will move over.
        For example, a list with 10 elements has an index range 0 to 9
        which incidentally is generated by the python code:
          >>> range(0,10)
          [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        If there are no items in the list, then max is -1 and pos is -1
        """
        assert maxitems >= 0
        self.MaxPosition = maxitems-1
        self._ClipPositionToMax()
        
    def IsEmpty(self):
        return self.MaxPosition <= -1
    def IsMoreToPlay(self):
        if self.IsEmpty():
            return 0
        if self.Position < self.MaxPosition:
            return 1
        else:
            return 0
          
    def NotifyPositionNowValid(self, position):
        self.NotifyOfInsert(position, noinsertJustValidate=1)
    def NotifyOfInsert(self, position, noinsertJustValidate=0):
        """
        Says that position 'position' is now valid and has been inserted, pushing all above it (if any) up.
          E.g. NotifyOfInsert(0) says we are tracking one item
               the list is now 0..0 and MaxPosition is 0
               
        Will adjust playback head as necessary so that
        as new elements are added to the story the index position
        is kept pointing at the same current element.

        You can notify of insert of a position that is > maxposition
        In this case we simply adjust maxposition.

        NOTE that insert notifications do not affect the event being
        pointed to by the current position index.
        (except for when position is -1 cos nothing in the playhead, then insert something)
        """
        if position == -1:
          return
        
        assert position >= 0, "Playhead's NotifyOfInsert error, attempt to position to negative value " + str(position)
        
        wasemptyPlayheadSituation = self.Position == -1 and self.IsEmpty()
        
        if position > self.MaxPosition:
            self.MaxPosition = position
        else:
            if noinsertJustValidate:
                pass
            else:
               if position <= self.Position:
                   self.Position += 1
               self.MaxPosition += 1
            
        # New extra helpful logic.  Automatically move the playhead to start if now non empty
        if wasemptyPlayheadSituation and not self.IsEmpty():
            self.GoStart()
        
    def GoStart(self):
        if self.MaxPosition == -1:
            self.Position = -1
        else:
            self.Position = 0
        self._ClipPositionToMax()
    def GoEnd(self):
        self.Position = self.MaxPosition
    def Go(self, position):
        """
        Jumps playhead to position in the range 0 to maxitems-1
        If are < 0 or > max, then go as far as you can in the intented direction.
        """
        if position < 0:
            position = 0
        if position > self.MaxPosition:
            position = self.MaxPosition
        self.Position = position
    def GoNext(self):
        if self.Position < self.MaxPosition:
            self.Position += 1
    def GoPrevious(self):
        if self.Position > 0:
            self.Position -= 1

import unittest, random

class TestCase00(unittest.TestCase):
    def checkInit(self):
        p = Playhead(10) # Means handling a list positions 0 to 9
        assert p.Position == 0
    def checkInitZero(self):
        p = Playhead(0) # Means nothing in list (though we don't actually allocate or track any list)
        assert p.Position == -1
    def checkGoEnd(self):
        p = Playhead(10)
        p.GoEnd()
        assert p.Position == 9
    def checkAdvance(self):
        p = Playhead(10)
        p.GoNext()
        assert p.Position == 1
    def checkAdvanceMore(self):
        p = Playhead(10)
        p.GoNext()
        p.GoNext()
        assert p.Position == 2
    def checkGo(self):
        p = Playhead(10)
        p.Go(5)
        assert p.Position == 5
    def checkGoTooFar(self):
        p = Playhead(10)
        p.Go(10)
        assert p.Position == 9
        p.Go(0)
        assert p.Position == 0
    def checkRewindMore(self):
        p = Playhead(10)
        p.Go(9)
        p.GoNext()
        assert p.Position == 9
        p.GoPrevious()
        assert p.Position == 8
        p.GoStart()
        p.GoPrevious()
        assert p.Position == 0
    def checkNotifyInsert(self):
        p = Playhead(10)
        assert p.MaxPosition == 9
        p.Go(6)
        assert p.Position == 6
        p.NotifyOfInsert(1)
        assert p.Position == 7
        assert p.MaxPosition == 10
        p.NotifyOfInsert(7)  # this will insert as pos 7 and push old 7 and rest up
        assert p.Position == 8
        # Inserting after the current position does not affect current position
        p.NotifyOfInsert(9)
        assert p.Position == 8
        assert p.MaxPosition == 12
    def checkNotifyInsertZero(self):
        p = Playhead(0)
        assert p.Position == -1
        p.NotifyOfInsert(0)
        assert p.Position == 0  # position automoved for us to a useful position
        assert p.MaxPosition == 0
        p.NotifyOfInsert(0)  # this will insert at pos 0 and push old 0 and rest up
        assert p.Position == 1  # what position was pointing to shouldn't be affected by insert (except for when position is -1 cos nothing in the playhead, then insert something)
        assert p.MaxPosition == 1
    def checkIsMoretoplay(self):
        p = Playhead(0)
        assert p.IsEmpty()
        assert not p.IsMoreToPlay()
        p.NotifyOfInsert(0)
        assert not p.IsEmpty()
        assert not p.IsMoreToPlay() # already at last pos cos position automoved for us to a useful position 0
        p.GoNext()
        assert not p.IsEmpty()
        assert not p.IsMoreToPlay()
    def checkClear(self):
        p = Playhead(0)
        a = p.MaxPosition
        b = p.Position
        assert p.IsEmpty()
        assert not p.IsMoreToPlay()
        p.NotifyOfInsert(0)
        p.NotifyOfInsert(10)

        p.Clear()
        assert p.IsEmpty()
        assert not p.IsMoreToPlay()
        assert a == p.MaxPosition
        assert b == p.Position

    def checkInsertPastMaximum(self):
        p = Playhead(0)
        assert p.Position == -1
        
        p.NotifyOfInsert(0)
        assert p.MaxPosition == 0
        assert p.Position == 0 # position automoved for us to a useful position
        
        p.Go(0)
        assert p.MaxPosition == 0
        assert p.Position == 0
        
        p.NotifyOfInsert(10)
        assert p.Position == 0
        assert p.MaxPosition == 10
        
        p.Go(10)
        assert p.Position == 10
        assert p.MaxPosition == 10

    def checkGoStartWithNoItems(self):
        p = Playhead(0)
        assert p.Position == -1
        p.GoStart()
        assert p.Position == -1
    def checkGoEndWithNoItems(self):
        p = Playhead(0)
        assert p.Position == -1
        p.GoEnd()
        assert p.Position == -1
    def checkGoEndWithSomeItems(self):
        p = Playhead(10)  # this will be 0..9
        assert p.Position == 0
        assert p.MaxPosition == 9

        p.NotifyOfInsert(10)  # tells us that pos 10 is now valid pos
        assert p.Position == 0
        assert p.MaxPosition == 10
        
        p.GoEnd()
        assert p.Position == 10

    def checkNotifyNoInsertJustValidate(self):
        p = Playhead(10)  # this will be 0..9
        p.Go(5)
        assert p.Position == 5
        
        p.NotifyOfInsert(5)
        assert p.Position == 6
        assert p.MaxPosition == 10

        p.NotifyPositionNowValid(8)
        assert p.Position == 6
        assert p.MaxPosition == 10
        
        p.NotifyPositionNowValid(12)
        assert p.Position == 6
        assert p.MaxPosition == 12

        p.NotifyOfInsert(15)
        assert p.Position == 6
        assert p.MaxPosition == 15

        p.NotifyOfInsert(6)
        assert p.Position == 7
        assert p.MaxPosition == 16

def suite():
    suite1 = unittest.makeSuite(TestCase00,'check')
    alltests = unittest.TestSuite( (suite1,) )
    return alltests
    
def main():
    """ Run all the suites.  To run via a gui, then
            python unittestgui.py NestedDictionaryTest.suite
        Note that I run with VERBOSITY on HIGH  :-) just like in the old days
        with pyUnit for python 2.0
        Simply call
          runner = unittest.TextTestRunner(descriptions=0, verbosity=2)
        The default arguments are descriptions=1, verbosity=1
    """
    runner = unittest.TextTestRunner(descriptions=0, verbosity=2) # default is descriptions=1, verbosity=1
    #runner = unittest.TextTestRunner(descriptions=0, verbosity=1) # default is descriptions=1, verbosity=1
    runner.run( suite() )

if __name__ == '__main__':
    main()
        
#print __name__

