import unittest

import sys
sys.path.append("../Research/layout force spring")

from overlap_removal import OverlapRemoval
from graph import Graph, GraphNode, Div

        
class OverlapTests(unittest.TestCase):

    def setUp(self):

        class FakeGui:
            def stateofthenation(self):
                pass

        self.g = Graph()
        self.overlap_remover = OverlapRemoval(self.g, gui=FakeGui())
        
    def test0_1OneNode(self):
        g = self.g
        g.addNode(Div('A', 0, 0, 250, 250))

        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertEqual(0, numfixed)

    def test0_2TwoNode_notoverlapping(self):
        g = self.g
        g.addNode(Div('A', 0, 0, 250, 250))
        g.addNode(Div('B', 260, 0, 250, 250))

        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertEqual(0, numfixed)

    def test0_3TwoNode_overlapping(self):
        g = self.g
        g.addNode(Div('A', 0, 0, 250, 250))
        g.addNode(Div('B', 200, 0, 250, 250))

        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertEqual(1, numfixed)

    def test0_4OverlapRemoverCreation(self):
        g = self.g
        a = Div('A', 0, 0, 250, 250)
        a1 = Div('A1', 0, 0)
        a2 = Div('A2', 0, 0)
        g.addEdge(a, a1)
        g.addEdge(a, a2)

        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertEqual(4, numfixed)

    """
    Smarter tests.
    Load scenarios from persistence and use special box comparison utility methods
    """

    def _ensureXorder(self, *args):
        nodes = [self.g.findNode(id) for id in args]
        assert len(nodes) >= 2
        for i in range(0,len(nodes)-1):
            if not nodes[i].value.right < nodes[i+1].value.left:
                return False
        return True

    def _ensureXorderLefts(self, *args):
        nodes = [self.g.findNode(id) for id in args]
        assert len(nodes) >= 2
        for i in range(0,len(nodes)-1):
            if not nodes[i].value.left < nodes[i+1].value.left:
                return False
        return True

    def _ensureYorder(self, *args):
        nodes = [self.g.findNode(id) for id in args]
        assert len(nodes) >= 2
        for i in range(0,len(nodes)-1):
            if not nodes[i].value.bottom < nodes[i+1].value.top:
                return False
        return True

    def _ensureYorderBottoms(self, *args):
        nodes = [self.g.findNode(id) for id in args]
        assert len(nodes) >= 2
        for i in range(0,len(nodes)-1):
            if not nodes[i].value.bottom < nodes[i+1].value.bottom:
                return False
        return True
    


    def _LoadScenario1(self):
        initial = """
{'type':'node', 'id':'D25', 'x':6, 'y':7, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':170, 'y':9, 'width':139, 'height':92}
"""
        self.g.LoadGraphFromStrings(initial)

    def test1_1MoveLeftPushedBackHorizontally01(self):
        self._LoadScenario1()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (150, 9)

        # assert m1 has been pushed back to the right
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(1, numfixed)
        self.assertTrue(node.value.left > self.g.findNode('D25').value.right)
        self.assertTrue(node.value.top < self.g.findNode('D25').value.bottom)

    def test1_2MoveLeftPushedBackDownRight02(self):
        self._LoadScenario1()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (106, 79)
        
        # assert m1 has been pushed back to the right but also down
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(1, numfixed)
        
        self.assertTrue(node.value.left > self.g.findNode('D13').value.right)
        self.assertTrue(node.value.top > self.g.findNode('D25').value.bottom)
        
    def test1_3MoveInsertedVertically1(self):
        self._LoadScenario1()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (16,74)
        
        # assert m1 has been squeezed in between the two existing
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(2, numfixed)
        
        #print self.g.GraphToString()
        self.assertTrue(node.value.top > self.g.findNode('D25').value.bottom)
        self.assertTrue(node.value.bottom < self.g.findNode('D13').value.top)
        self.assertTrue(self.g.findNode('D13').value.top > self.g.findNode('D25').value.bottom)
        self.assertTrue(node.value.left < self.g.findNode('D25').value.right)
        self.assertTrue(node.value.left < self.g.findNode('D13').value.right)
        
    def test1_4MovePushedVertically2(self):
        self._LoadScenario1()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (6,154)
        
        # assert m1 has been pushed vertically underneath the other two nodes
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(1, numfixed)

        self.assertTrue(self._ensureYorder('D25', 'D13', 'm1'))
        
        self.assertTrue(node.value.left < self.g.findNode('D25').value.right)
        self.assertTrue(node.value.left < self.g.findNode('D13').value.right)
        
        
    def _LoadScenario2(self):
        initial = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':146, 'y':179, 'width':139, 'height':92}
{'type':'node', 'id':'D97', 'x':213, 'y':6, 'width':85, 'height':159}
"""
        self.g.LoadGraphFromStrings(initial)        
        
    def test2_1InsertAndPushedRightHorizontally(self):
        self._LoadScenario2()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (121,14)
        
        # assert m1 has been inserted and node to the right pushed right
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(2, numfixed)
        
        self.assertTrue(self._ensureXorder('D25', 'm1', 'D97'))
        self.assertTrue(self._ensureYorderBottoms('m1', 'D97')) # m1 bottom above D97 bottom

    def test2_2PushedRightAndDownNicely(self):
        self._LoadScenario2()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (96, 114)
        
        # assert m1 has been pushed down and right nicely and snugly
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(1, numfixed)
        
        self.assertTrue(self._ensureXorder('D13', 'm1'))
        self.assertTrue(self._ensureXorderLefts('D13', 'm1', 'D97'))
        self.assertTrue(self._ensureXorderLefts('D25', 'm1', 'D97'))
        self.assertTrue(self._ensureYorderBottoms('D25', 'D97', 'm1'))
        self.assertTrue(self._ensureYorder('D25', 'm1'))
        self.assertTrue(self._ensureYorderBottoms('D25', 'D13', 'm1'))
        self.assertTrue(self._ensureYorderBottoms('D25', 'D97', 'm1'))


    def _LoadScenario3(self):
        initial = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':246, 'y':179, 'width':139, 'height':92}
{'type':'node', 'id':'D97', 'x':213, 'y':6, 'width':85, 'height':159}
{'type':'node', 'id':'D98', 'x':340, 'y':7, 'width':101, 'height':107}
"""
        self.g.LoadGraphFromStrings(initial)  
        
    def test3_1PushedBetweenLeftAndRight(self):
        self._LoadScenario3()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (266, 9)
        
        # assert m1 has been pushed between two nodes, horizontally.  Both left and right nodes moved left and right respectively.
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(2, numfixed)
        
        self.assertTrue(self._ensureXorder('D25', 'D97', 'm1', 'D98'))
        self.assertTrue(self._ensureYorder('D25', 'D13'))
        self.assertTrue(self._ensureYorderBottoms('D25', 'D97', 'D13'))

    def test3_2PushedBetweenLeftAndRightRefused(self):
        self._LoadScenario3()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (226, 14)
        
        # assert m1 has been not been inserted - refused and snuggled instead
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(1, numfixed)
        
        self.assertTrue(self._ensureXorder('D25', 'D97', 'D98'))
        self.assertTrue(self._ensureXorder('D25', 'D97', 'm1'))
        self.assertTrue(self._ensureYorder('D98', 'm1'))
        self.assertTrue(self._ensureYorderBottoms('D98', 'D97', 'm1'))
        
    def test3_3InsertedAndTwoPushedRight(self):
        self._LoadScenario3()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (146, 9)
        
        # assert m1 has been inserted - and two nodes pushed right
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(3, numfixed)
        
        self.assertTrue(self._ensureXorder('D25', 'm1', 'D97', 'D98'))
         
    def test3_4InsertedVerticallyNothingPushedRight(self):
        self._LoadScenario3()
        
        # move m1 to the left
        node = self.g.findNode('m1')
        node.value.left, node.value.top = (91, 64)
        
        # assert m1 has been inserted vertically - one node pushed down, NO nodes pushed right
        were_all_overlaps_removed, numfixed = self.overlap_remover.remove_overlaps()
        self.assertTrue(were_all_overlaps_removed)
        self.assertEqual(5, numfixed)

        d97 = self.g.findNode('D97')
        oldD97pos = (d97.value.left, d97.value.top)
        self.assertTrue(self._ensureXorder('D25', 'D97', 'D98'))
        self.assertTrue(self._ensureXorder('m1', 'D97', 'D98'))
        self.assertTrue(self._ensureYorder('D25', 'm1', 'D13'))
        self.assertTrue(self._ensureYorder('D25', 'm1', 'D13'))
        self.assertEqual(oldD97pos, (d97.value.left, d97.value.top)) # ensure D97 hasn't been pushed
                 
if __name__ == "__main__":
    unittest.main()