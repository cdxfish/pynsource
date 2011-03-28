import wx
import wx.lib.ogl as ogl
import time
import thread

from graph import *
from layout_spring import GraphLayoutSpring
from overlap_removal import OverlapRemoval
import random

def setpos(shape, x, y):
    width, height = shape.GetBoundingBoxMax()
    shape.SetX( x + width/2 )
    shape.SetY( y + height/2 )
def getpos(shape):
    width, height = shape.GetBoundingBoxMax()
    x = shape.GetX()
    y = shape.GetY()
    return (x - width/2, y - height/2)


class MyEvtHandler(ogl.ShapeEvtHandler):
    def __init__(self, log, oglcanvas):
        ogl.ShapeEvtHandler.__init__(self)
        self.log = log
        self.oglcanvas = oglcanvas

    def UpdateStatusBar(self, shape):
        x, y = shape.GetX(), shape.GetY()
        x, y = getpos(shape)
        width, height = shape.GetBoundingBoxMax()
        frame = self.oglcanvas.GetTopLevelParent()
        frame.SetStatusText("Pos: (%d,%d)  Size: (%d, %d)  -  GraphNode is %s" % (x, y, width, height, shape.node))

    def OnLeftClick(self, x, y, keys = 0, attachment = 0):
        #print "OnLeftClick"
        shape = self.GetShape()
        
        # size handles
        shape.GetCanvas().graphrendererogl.DeselectAllShapes()
        shape.Select(True, None)
        shape.GetCanvas().graphrendererogl.stateofthenation()
        
        self.UpdateStatusBar(shape)
            
    def OnDrawOutline(self, dc, x, y, w, h):
        ogl.ShapeEvtHandler.OnDrawOutline(self, dc, x, y, w, h)
        shape = self.GetShape()
        x,y = (x - w/2, y - h/2) # correct to be top corner not centre
        frame.SetStatusText("Pos: (%d,%d)  Size: (%d, %d)  -  GraphNode is %s" % (x, y, w, h, shape.node))
        
    def OnDragLeft(self, draw, x, y, keys = 0, attachment = 0):
        ogl.ShapeEvtHandler.OnDragLeft(self, draw, x, y, keys = 0, attachment = 0)
        # x, y are the merely the mouse position thus useless for getting to shape x,y - intercept OnDrawOutline instead 
        
    def OnEndDragLeft(self, x, y, keys = 0, attachment = 0):
        shape = self.GetShape()

        # take care of selection points
        ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)
        if not shape.Selected():
            self.OnLeftClick(x, y, keys, attachment)
        
        oldpos = getpos(shape) # (int(shape.GetX()), int(shape.GetY()))
        ogl.ShapeEvtHandler.OnEndDragLeft(self, x, y, keys, attachment)  # super
        newpos = getpos(shape) # (int(shape.GetX()), int(shape.GetY()))

        print shape.node.id, "moved from", oldpos, "to", newpos
        
        # Adjust the GraphNode to match the shape x,y
        shape.node.left, shape.node.top = newpos

        self.UpdateStatusBar(shape)

        wx.SafeYield()
        time.sleep(0.2)
        
        shape.GetCanvas().graphrendererogl.stage2()

    def OnSizingEndDragLeft(self, pt, x, y, keys, attch):
        shape = self.GetShape()

        # super        
        ogl.ShapeEvtHandler.OnSizingEndDragLeft(self, pt, x, y, keys, attch)
        
        width, height = shape.GetBoundingBoxMin()
        print shape.node, "resized to", width, height
        #print shape.node.id, shape.node.left, shape.node.top, "resized to", width, height
        # Adjust the GraphNode to match the shape x,y
        shape.node.width, shape.node.height = width, height
        shape.node.left, shape.node.top = getpos(shape)
        
        self.UpdateStatusBar(self.GetShape())

        wx.SafeYield()
        time.sleep(0.2)
        
        shape.GetCanvas().graphrendererogl.stage2()

        
class GraphShapeCanvas(ogl.ShapeCanvas):
    scrollStepX = 10
    scrollStepY = 10
    classnametoshape = {}

    def __init__(self, parent):
        ogl.ShapeCanvas.__init__(self, parent)

    def OnLeftClick(self, x, y, keys):  # Override of ShapeCanvas method
        # keys is a bit list of the following: KEY_SHIFT  KEY_CTRL
        self.graphrendererogl.DeselectAllShapes()

from coordinate_mapper import CoordinateMapper
        
class GraphRendererOgl:
    def __init__(self, graph, oglcanvas):
        self.graph = graph
        self.oglcanvas = oglcanvas
        self.oglcanvas.graphrendererogl = self
        self.coordmapper = CoordinateMapper(self.graph, self.oglcanvas.GetSize())

        self.oglcanvas.Bind(wx.EVT_MOUSEWHEEL, self.OnWheelZoom)
        self.oglcanvas.Bind(wx.EVT_RIGHT_DOWN, self.OnRightButtonMenu)
        self.oglcanvas.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        self.oglcanvas.Bind(wx.EVT_SIZE, self.OnResizeFrame)
        
        self.popupmenu = None
        self.need_abort = False

        self.overlap_remover = OverlapRemoval(self.graph, margin=50, gui=self)

    def AllToLayoutCoords(self):
            self.coordmapper.AllToLayoutCoords()

    def AllToWorldCoords(self):
            self.coordmapper.AllToWorldCoords()

    def DeselectAllShapes(self):
        selected = [s for s in self.oglcanvas.GetDiagram().GetShapeList() if s.Selected()]
        if selected:
            s = selected[0]
            canvas = s.GetCanvas()
            dc = wx.ClientDC(canvas)
            canvas.PrepareDC(dc)
            s.Select(False, dc)
            canvas.Refresh(False)   # Need this or else Control points ('handles') leave blank holes      

    def OnResizeFrame (self, event):   # ANDY  interesting - GetVirtualSize grows when resize frame
        frame = self.oglcanvas.GetTopLevelParent()
        print "frame resize", frame.GetClientSize()
        self.coordmapper.Recalibrate(frame.GetClientSize()) # may need to call self.CalcVirtSize() if scrolled window
   
    def onKeyPress(self, event):
        keycode = event.GetKeyCode()  # http://www.wxpython.org/docs/api/wx.KeyEvent-class.html
        #if event.ShiftDown():

        if keycode == wx.WXK_DOWN:
            print "DOWN"
            self.ReLayout(keep_current_positions=True, gui=self)

        elif keycode == wx.WXK_UP:
            print "UP"
            self.ReLayout(keep_current_positions=False, gui=self)
            
        elif keycode == wx.WXK_RIGHT:
            """
            print "RIGHT"
            self.ReLayout(keep_current_positions=False)
            self.ReLayout(keep_current_positions=True)
            self.ReLayout(keep_current_positions=True)
            self.ReLayout(keep_current_positions=True)
            self.ReLayout(keep_current_positions=True)
            self.ReLayout(keep_current_positions=True, gui=self)
            """
            self.ChangeScale(-0.2)
            
        elif keycode == wx.WXK_LEFT:
            self.ChangeScale(0.2)
            
            """            
            print "LEFT"
            if event.ShiftDown():
                scale_before = 1
                scale_after = 1
            if event.ControlDown():
                scale_before = 2
                scale_after = 1
            if event.ControlDown() and event.ShiftDown():
                scale_before = 2
                scale_after = 2
            else:
                scale_before = 1
                scale_after = 2
            
            self.stage2() # does overlap removal and stateofthenation

            def layoutandwatchat():
                self.coordmapper.Recalibrate(scale=scale_before)
                self.AllToLayoutCoords()
                layouter = GraphLayoutSpring(self.graph, gui=self)    # should keep this around
                layouter.layout(keep_current_positions=True)
            def layoutat():
                self.coordmapper.Recalibrate(scale=scale_before)
                self.AllToLayoutCoords()
                self.coordmapper.Recalibrate(scale=scale_after)  # watch at different res
                layouter = GraphLayoutSpring(self.graph, gui=self)    # should keep this around
                layouter.layout(keep_current_positions=True)
            def renderat():
                for i in range(20, 1, -1):
                    scale = i/10.0
                    self.coordmapper.Recalibrate(scale=scale)
                    self.AllToWorldCoords()
                    numoverlaps = self.overlap_remover.CountOverlaps()
                    print "Num Overlaps at scale", scale, numoverlaps
                    self.stage2() # does overlap removal and stateofthenation
                    time.sleep(0.2)
                    if numoverlaps < 2:
                        break
                    
                #self.coordmapper.Recalibrate(scale=scale_after)
                #self.AllToWorldCoords()
                #print "Num Overlaps at scale", scale_after, self.overlap_remover.CountOverlaps()
                #
                #self.stage2() # does overlap removal and stateofthenation

            layoutandwatchat()
            #layoutat()
            renderat()
            self.coordmapper.Recalibrate(scale=scale_after)
            """
            
            
        elif keycode == wx.WXK_DELETE:
            selected = [s for s in self.oglcanvas.GetDiagram().GetShapeList() if s.Selected()]
            if selected:
                shape = selected[0]
                print 'delete', shape.node.id

                # model
                self.graph.DeleteNodeById(shape.node.id)

                # view
                self.DeselectAllShapes()
                for line in shape.GetLines()[:]:
                    line.Delete()
                shape.Delete()

        elif keycode == wx.WXK_INSERT:
            id = 'D' + str(random.randint(1,99))
            dialog = wx.TextEntryDialog ( None, 'Enter an id string:', 'Create a new node', id )
            if dialog.ShowModal() == wx.ID_OK:
                id = dialog.GetValue()
                if self.graph.FindNodeById(id):
                    id += str(random.randint(1,9999))
                node = GraphNode(id, random.randint(0, 100),random.randint(0,100),random.randint(60, 160),random.randint(60,160))
                node = self.graph.AddNode(node)
                self.drawNode(node)
                node.shape.Show(True)
                self.stateofthenation()
            dialog.Destroy()
            
        event.Skip()

    def stateofthespring(self):
        self.coordmapper.Recalibrate()
        self.AllToWorldCoords()
        self.stateofthenation() # DON'T do overlap removal or it will get mad!

    def ChangeScale(self, delta):
        self.coordmapper.Recalibrate(scale=self.coordmapper.scale+delta)
        self.AllToWorldCoords()
        numoverlaps = self.overlap_remover.CountOverlaps()
        print "Num Overlaps at scale", self.coordmapper.scale, numoverlaps
        
        saveit = self.overlap_remover.gui
        self.overlap_remover.gui = None
        self.stage2() # does overlap removal and stateofthenation
        self.overlap_remover.gui = saveit
        
    def ReLayout(self, keep_current_positions=False, gui=None):
        # layout again
        print "spring layout again!"
        self.AllToLayoutCoords()

        layouter = GraphLayoutSpring(self.graph, gui)    # should keep this around
        layouter.layout(keep_current_positions)
        
        self.AllToWorldCoords()
        self.stage2() # does overlap removal and stateofthenation
        #self.stateofthenation()
        # self.draw() - this recreates everything again!! - should rename
        
    def OnRightButtonMenu(self, event):   # Menu

        x, y = event.GetPosition()
        frame = self.oglcanvas.GetTopLevelParent()
        
        if self.popupmenu:
            self.popupmenu.Destroy()    # wx.Menu objects need to be explicitly destroyed (e.g. menu.Destroy()) in this situation. Otherwise, they will rack up the USER Objects count on Windows; eventually crashing a program when USER Objects is maxed out. -- U. Artie Eoff  http://wiki.wxpython.org/index.cgi/PopupMenuOnRightClick
        self.popupmenu = wx.Menu()     # Create a menu
        
        item = self.popupmenu.Append(2015, "Load Graph from text...")
        frame.Bind(wx.EVT_MENU, self.OnLoadGraphFromText, item)
        
        item = self.popupmenu.Append(2017, "Dump Graph to console")
        frame.Bind(wx.EVT_MENU, self.OnSaveGraphToConsole, item)

        self.popupmenu.AppendSeparator()

        item = self.popupmenu.Append(2011, "Load Graph...")
        frame.Bind(wx.EVT_MENU, self.OnLoadGraph, item)
        
        item = self.popupmenu.Append(2012, "Save Graph...")
        frame.Bind(wx.EVT_MENU, self.OnSaveGraph, item)

        self.popupmenu.AppendSeparator()

        item = self.popupmenu.Append(2016, "Load Test Graph 1")
        frame.Bind(wx.EVT_MENU, self.OnLoadTestGraph1, item)

        item = self.popupmenu.Append(2018, "Load Test Graph 2")
        frame.Bind(wx.EVT_MENU, self.OnLoadTestGraph2, item)

        item = self.popupmenu.Append(2019, "Load Test Graph 3")
        frame.Bind(wx.EVT_MENU, self.OnLoadTestGraph3, item)

        item = self.popupmenu.Append(2020, "Load Test Graph 4")
        frame.Bind(wx.EVT_MENU, self.OnLoadTestGraph4, item)

        self.popupmenu.AppendSeparator()

        item = self.popupmenu.Append(2014, "Clear")
        frame.Bind(wx.EVT_MENU, self.OnClear, item)  # must pass item

        item = self.popupmenu.Append(2013, "Cancel")
        #frame.Bind(wx.EVT_MENU, self.OnPopupItemSelected, item)
        
        frame.PopupMenu(self.popupmenu, wx.Point(x,y))

            
    def OnSaveGraphToConsole(self, event):
        print self.graph.GraphToString()

    def OnSaveGraph(self, event):
        frame = self.oglcanvas.GetTopLevelParent()
        dlg = wx.FileDialog(parent=frame, message="choose", defaultDir='.',
            defaultFile="", wildcard="*.txt", style=wx.FD_SAVE, pos=wx.DefaultPosition)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            
            fp = open(filename, "w")
            fp.write(self.graph.GraphToString())
            fp.close()
            
        dlg.Destroy()
        
    def OnLoadTestGraph1(self, event):
        filedata = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':171, 'y':9, 'width':139, 'height':92}
        """
        self.LoadGraph(filedata)
        
    def OnLoadTestGraph2(self, event):
        filedata = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':146, 'y':179, 'width':139, 'height':92}
{'type':'node', 'id':'D97', 'x':213, 'y':6, 'width':85, 'height':159}
        """
        self.LoadGraph(filedata)
        
    def OnLoadTestGraph3(self, event):
        filedata = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':246, 'y':179, 'width':139, 'height':92}
{'type':'node', 'id':'D97', 'x':213, 'y':6, 'width':85, 'height':159}
{'type':'node', 'id':'D98', 'x':340, 'y':7, 'width':101, 'height':107}
        """
        self.LoadGraph(filedata)

    def OnLoadTestGraph4(self, event):
        filedata = """
{'type':'node', 'id':'D25', 'x':7, 'y':6, 'width':159, 'height':106}
{'type':'node', 'id':'D13', 'x':6, 'y':119, 'width':119, 'height':73}
{'type':'node', 'id':'m1', 'x':6, 'y':214, 'width':139, 'height':92}
{'type':'node', 'id':'D97', 'x':213, 'y':6, 'width':85, 'height':159}
{'type':'node', 'id':'D98', 'x':305, 'y':57, 'width':101, 'height':107}
{'type':'node', 'id':'D50', 'x':149, 'y':184, 'width':242, 'height':112}
{'type':'node', 'id':'D51', 'x':189, 'y':302, 'width':162, 'height':66}
        """
        self.LoadGraph(filedata)

    def OnLoadGraphFromText(self, event):
        eg = "{'type':'node', 'id':'A', 'x':142, 'y':129, 'width':250, 'height':250}"
        dialog = wx.TextEntryDialog ( None, 'Enter an node/edge persistence strings:', 'Create a new node', eg,  style=wx.OK|wx.CANCEL|wx.TE_MULTILINE )
        if dialog.ShowModal() == wx.ID_OK:
            txt = dialog.GetValue()
            self.LoadGraph(txt)
            
    def OnLoadGraph(self, event):
        frame = self.oglcanvas.GetTopLevelParent()
        dlg = wx.FileDialog(parent=frame, message="choose", defaultDir='.',
            defaultFile="", wildcard="*.txt", style=wx.OPEN, pos=wx.DefaultPosition)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

            fp = open(filename, "r")
            s = fp.read()
            fp.close()

            self.LoadGraph(s)
        dlg.Destroy()

    def LoadGraph(self, filedata=""):
        self.Clear()
        
        self.graph.LoadGraphFromStrings(filedata)
                
        # build view from model
        self.draw(translatecoords=False)
        
        # refresh view
        self.oglcanvas.GetDiagram().ShowAll(1) # need this, yes
        self.stateofthenation()


    def OnClear(self, event):
        self.Clear()
        
    def Clear(self):
        # Clear view        
        self.oglcanvas.GetDiagram().DeleteAllShapes()
        dc = wx.ClientDC(self.oglcanvas)
        self.oglcanvas.GetDiagram().Clear(dc)   # only ends up calling dc.Clear() - I wonder if this clears the screen?
        
        # clear model
        self.graph.Clear()
        
            
    def OnWheelZoom(self, event):
        self.stage2()
        print self.overlap_remover.GetStats()

    def stage1(self, translatecoords=True):
        import time
        
        if translatecoords:
            self.AllToWorldCoords()

        for node in self.graph.nodes:
            self.drawNode(node)
        for edge in self.graph.edges:
            self.drawEdge(edge)

        self.Redraw()
        #time.sleep(1)

    def stage2(self):
        self.overlap_remover.RemoveOverlaps()
        if self.overlap_remover.GetStats()['total_overlaps_found'] > 0:
            self.stateofthenation()
        
    def stateofthenation(self):
        for node in self.graph.nodes:
            self.moveNode(node)
        self.Redraw()
        wx.SafeYield()
        #time.sleep(0.2)
        
        
    def draw(self, translatecoords=True):
        self.stage1(translatecoords=translatecoords)
        #thread.start_new_thread(self.DoSomeLongTask, ())


    def DoSomeLongTask(self):
        
        for i in range(1,50):
            if self.need_abort:
                print "aborted."
                return
            wx.CallAfter(self.stage2)
            #print '*',
            #wx.CallAfter(self.DoStuff)
            time.sleep(2)   # lets events through to the main wx thread and paints/messages get through ok
        print "Done."
        
        """
        print "Task started"
        if self.need_abort:
            print "aborted."
            return
        wx.CallAfter(self.stage1)
        #time.sleep(0.5)   # lets events through to the main wx thread and paints/messages get through ok
        #wx.CallAfter(self.stage2)
        print "Done."
        """
        
        
    def moveNode(self, node):
        assert node.shape
        
        # Don't need to use node.shape.Move(dc, x, y, False)
        setpos(node.shape, node.left, node.top)

        # But you DO need to use a dc to adjust the links
        dc = wx.ClientDC(self.oglcanvas)
        self.oglcanvas.PrepareDC(dc)
        node.shape.MoveLinks(dc)

        
    def Redraw(self):
        
        diagram = self.oglcanvas.GetDiagram()
        canvas = self.oglcanvas
        assert canvas == diagram.GetCanvas()

        dc = wx.ClientDC(canvas)
        canvas.PrepareDC(dc)
        
        #for node in self.graph.nodes:    # TODO am still moving nodes in the pynsourcegui version?
        #    shape = node.shape
        #    shape.Move(dc, shape.GetX(), shape.GetY())
        diagram.Clear(dc)
        diagram.Redraw(dc)

     
    def drawNode(self, node):
        shape = ogl.RectangleShape( node.width, node.height )
        shape.AddText(node.id)
        setpos(shape, node.left, node.top)
        #shape.SetDraggable(True, True)
        self.oglcanvas.AddShape( shape )
        node.shape = shape
        shape.node = node
        
        # wire in the event handler for the new shape
        evthandler = MyEvtHandler(None, self.oglcanvas)
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
       
    def drawEdge(self, edge):
        line = ogl.LineShape()
        line.SetCanvas(self.oglcanvas)
        line.SetPen(wx.BLACK_PEN)
        line.SetBrush(wx.BLACK_BRUSH)
        line.MakeLineControlPoints(2)
       
        fromShape = edge['source'].shape
        toShape = edge['target'].shape
        fromShape.AddLine(line, toShape)
        self.oglcanvas.GetDiagram().AddShape(line)
        line.Show(True)        
        

class AppFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__( self,
                          None, -1, "Demo",
                          size=(800,800),
                          style=wx.DEFAULT_FRAME_STYLE )
        sizer = wx.BoxSizer( wx.VERTICAL )
        # put stuff into sizer

        self.CreateStatusBar()

        canvas = GraphShapeCanvas(self) # ogl.ShapeCanvas( self )
        sizer.Add( canvas, 1, wx.GROW )

        canvas.SetBackgroundColour( "LIGHT BLUE" ) #

        diagram = ogl.Diagram()
        canvas.SetDiagram( diagram )
        diagram.SetCanvas( canvas )

        ## ==========================================
        
        g = Graph()
        
        a = GraphNode('A', 0, 0, 250, 250)
        a1 = GraphNode('A1', 0, 0)
        a2 = GraphNode('A2', 0, 0)
        g.AddEdge(a, a1)
        g.AddEdge(a, a2)

        b = GraphNode('B', 0, 0)
        b1 = GraphNode('B1', 0, 0)
        b2 = GraphNode('B2', 0, 0)
        g.AddEdge(b, b1)
        g.AddEdge(b, b2)

        b21 = GraphNode('B21', 0, 0)
        b22 = GraphNode('B22', 0, 0, 100, 200)
        g.AddEdge(b2, b21)
        g.AddEdge(b2, b22)

        c = GraphNode('c', 0, 0)
        c1 = GraphNode('c1', 0, 0)
        c2 = GraphNode('c2', 0, 0)
        c3 = GraphNode('c3', 0, 0)
        c4 = GraphNode('c4', 0, 0)
        c5 = GraphNode('c5', 0, 0, 60, 120)
        g.AddEdge(c, c1)
        g.AddEdge(c, c2)
        g.AddEdge(c, c3)
        g.AddEdge(c, c4)
        g.AddEdge(c, c5)
        g.AddEdge(a, c)
        
        g.AddEdge(b2, c)
        g.AddEdge(b2, c5)
        g.AddEdge(a, c5)

        layouter = GraphLayoutSpring(g)
        layouter.layout()
        
        for node in g.nodes:
            print node.id, (node.layoutPosX, node.layoutPosY)
        
        ## ==========================================
        
        # apply sizer
        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.Show(1)

        ## ==========================================

        renderer = GraphRendererOgl(g, canvas);
        renderer.draw();
        
        diagram.ShowAll( 1 )
        

app = wx.PySimpleApp()
ogl.OGLInitialize()
frame = AppFrame()
app.MainLoop()
app.Destroy()
