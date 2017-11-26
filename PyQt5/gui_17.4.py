import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from autobahn.twisted.websocket  import WebSocketClientFactory, WebSocketClientProtocol, connectWS
import json
import pandas as pd
import OPMMData_v2 as opd
import PandasModel as pdmodel
import PandasModel_R as pdrmodel
#from datetime import datetime, timedelta
#import paramiko

# http://eli.thegreenplace.net/2011/05/26/code-sample-socket-client-based-on-twisted-with-pyqt
# https://stackoverflow.com/questions/3142705/is-there-a-websocket-client-implemented-for-python

global morphGUI
morphGUI = None
activePlugins=["OptionTrader.OT01","OptionPricer.OP01","OrderForwarder.OF01"]

class MyClientProtocol(WebSocketClientProtocol):

    #def sendMessage(self, msg):
    #    msg = {k: str(v) for k, v in msg.iteritems()}
    #    self.sendMessage(msg)

    def onMessage(self, msg, binary):
        morphGUI.onMessage(msg)
        
    def onOpen(self):
        print ("Connected")
        morphGUI.listWidget.insertItem(0,"Connected")
        morphGUI.onConnection(self)

    def onClose(self, wasClean, code, reason):
        print ("Disconnected", wasClean, code, reason)
        morphGUI.listWidget.insertItem(0,"Disconnected")
        morphGUI.onDisconnection()

class MorphGUI(QtWidgets.QMainWindow):
    def __init__(self, reactor):
        QtWidgets.QMainWindow.__init__(self)
        ## Read csvs for inital values
        path = "~/Desktop/Pentagon/git/Nitin/git/csvs/"
        self.opmmData = opd.OPMMData(path)
        ## GUI setup
        self.setupGUI()
        self.client = None
        self.reactor = reactor
        self.setupConnection()

    def setupConnection(self):
        self.factory = WebSocketClientFactory("ws://49.248.124.188:5001")
        self.factory.protocol = MyClientProtocol
        print ("Trying to connect")
        self.connector = connectWS(self.factory)

    def onConnection(self, client):
        assert self.client is None
        self.client = client
        plugins = activePlugins[0] + "," + activePlugins[1] + "," + activePlugins[2]
        testMsg = json.dumps( {"MsgType":"Connect", "guiName": "test", "plugins": plugins}, sort_keys=True)

        #testMsg = json.dumps( {'MsgType':'XX'}, sort_keys=True )
        self.client.sendMessage(testMsg.encode('utf8'))

    def onMessage(self, msg):
        data = pd.read_json(msg, typ='series')

        if data["MsgType"] == "Connect":
            print ("Received connect msg")        
        elif data['MsgType'] == 'InstrumentData':
            self.onInstrumentDataMessage(msg)
        elif data['MsgType'] == 'PortfolioData':
            self.onPortfolioDataMessage(msg)
        elif data['MsgType'] == 'TradeData':
            self.onTradeDataMessage(msg)
        elif data['MsgType'] == 'PortfolioInfo':
            self.onPfInfoMessage(msg)
        elif data['MsgType'] == 'OrderNewRequest':
              self.onOrderRequestMessage(msg)
        elif data['MsgType'] == 'OrderModifyRequest':
            self.onOrderRequestMessage(msg)
        elif data['MsgType'] == 'OrderCancelRequest':
            self.onOrderRequestMessage(msg)
        elif data['MsgType'] == 'OrderAck':
            self.onOrderRespMessage(msg)
        elif data['MsgType'] == 'OrderCancel':
            self.onOrderRespMessage(msg)
        elif data['MsgType'] == 'OrderCancelReject':
            self.onOrderRespMessage(msg)
        elif data['MsgType'] == 'OrderReject':
            self.onOrderRespMessage(msg)
        elif data['MsgType'] == 'OrderFill':
            self.onOrderRespMessage(msg)
        else:
            print ("Unexpected message type!!!!!!")
            print ("Received message", msg)
        assert self.client is not None
        #print "Received message", msg

    def onDisconnection(self):
        assert self.client is not None
        self.client = None

    def setupGUI(self):
        self.setWindowTitle("Parameter Input Screen")
        self.resize(1200, 1200)
        self.showMaximized()
        self.centralwidget = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        #self.tabWidget  = QtGui.QTabWidget(self.centralwidget)

        ## Setup tabs (below methods put everything in self.tabWidget
        self.setupMonitorTab()
        
        self.setCentralWidget(self.centralwidget)

    def setupMonitorTab(self):
        self.Monitor    = QtWidgets.QWidget()
        self.mgridLayout = QtWidgets.QGridLayout(self.Monitor)
        
        ## Portfolios
        self.pfTable   = QtWidgets.QTableView(self.Monitor)
        self.pfTable.setMouseTracking(False)
        self.pfModel   = pdrmodel.PandasModel(self.opmmData.pfData)
        self.pfModel.dataChanged.connect(self.onPfItemChange)
        self.pfTable.setModel(self.pfModel)
        self.pfTable.setMinimumHeight(100)
        self.pfTable.setAlternatingRowColors(True)      
        self.pfTable.setStyleSheet("alternate-background-color: rgba(100,100,255,25); background-color: white; font: 14px")        
        self.pfTable.setShowGrid(False)
        self.pfTable.resizeColumnsToContents()
        self.pfTable.setColumnHidden(5,True) 
        self.pfTable.setColumnHidden(8,True)     
        self.pfTable.resizeRowsToContents()
        #self.pfTable.horizontalHeader().setSectionResizeMode(2)        
        self.pfTable.verticalHeader().setSectionResizeMode(2)
        self.mgridLayout.addWidget(self.pfTable,0,0,1,2)

        ### Instruments Read Only
        self.insTable  = QtWidgets.QTableView(self.Monitor)
        self.insrModel  = pdrmodel.PandasModel(self.opmmData.insrData)
        self.insTable.setModel(self.insrModel)
        self.insTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.insTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        insSelectionModel = self.insTable.selectionModel()
        insSelectionModel.selectionChanged.connect(self.onInsSelect)
        self.insTable.setMinimumHeight(700)  
        self.insTable.setAlternatingRowColors(True)
        self.insTable.setStyleSheet("alternate-background-color: rgba(100,100,255,25); background-color: white; font: 14px")
        self.insTable.setShowGrid(False)
        self.insTable.setColumnHidden(2,True)
        self.insTable.resizeColumnsToContents()
        #self.insTable.setColumnWidth(0,10)
        #self.insTable.setColumnWidth(1,40)
        self.insTable.resizeRowsToContents()
        self.insTable.horizontalHeader().setSectionResizeMode(2)        
        self.insTable.verticalHeader().setSectionResizeMode(2)        
        self.mgridLayout.addWidget(self.insTable,1,0,1,2)


        ### Instruments Params Dynamic
        self.insParTable  = QtWidgets.QTableView(self.Monitor)
        self.insModel  = pdmodel.PandasModel(self.opmmData.insData,
                                             self.opmmData.minInsData,
                                             self.opmmData.maxInsData)
        self.insModel.dataChanged.connect(self.onInsItemChange)
        self.insParTable.setModel(self.insModel)
        for i in range(0,self.insModel.rowCount()):
            self.insParTable.setRowHidden(i,True)
        self.insParTable.setStyleSheet("font: 14px")
        self.insParTable.resizeColumnsToContents()
        self.insParTable.resizeRowsToContents()
        self.insParTable.horizontalHeader().setSectionResizeMode(2)        
        self.insParTable.verticalHeader().setSectionResizeMode(2)
        self.insParTable.setMinimumHeight(30)  
        self.mgridLayout.addWidget(self.insParTable,2,0,1,2)


        ### PF Params Dynamic
        self.pfParamsTable  = QtWidgets.QTableView(self.Monitor)
        self.pfParamsModel  = pdmodel.PandasModel(self.opmmData.globalParams.data,
                                                  self.opmmData.minGlobalParams.data,
                                                  self.opmmData.maxGlobalParams.data)
        self.pfParamsModel.dataChanged.connect(self.onPfParamChange)
        self.pfParamsTable.setModel(self.pfParamsModel)
        self.pfParamsTable.setMinimumHeight(30)    
        self.pfParamsTable.setColumnHidden(0,True)
        for i in range(0,self.pfParamsModel.rowCount()):
            self.pfParamsTable.setRowHidden(i,True)     
        self.pfParamsTable.setStyleSheet("font: 14px")
        self.pfParamsTable.resizeColumnsToContents()
        self.pfParamsTable.resizeRowsToContents()
        self.pfParamsTable.horizontalHeader().setSectionResizeMode(2)        
        self.pfParamsTable.verticalHeader().setSectionResizeMode(2)        
        self.mgridLayout.addWidget(self.pfParamsTable,3,0,1,2)


        ### Vol Curve Dynamic
        self.vcTable        = QtWidgets.QTableView(self.Monitor)
        self.vcModel        = pdmodel.PandasModel(self.opmmData.volCurve.data,
                                                  self.opmmData.minVolCurve.data,
                                                  self.opmmData.maxVolCurve.data)
        self.vcModel.dataChanged.connect(self.onVolCurveChange)
        self.vcTable.setModel(self.vcModel)
        self.vcTable.setMinimumHeight(30)    
        for i in range(0,self.vcModel.rowCount()):
            self.vcTable.setRowHidden(i,True)
        self.vcTable.setStyleSheet("font: 14px")
        self.vcTable.resizeColumnsToContents()
        self.vcTable.resizeRowsToContents()
        self.vcTable.horizontalHeader().setSectionResizeMode(2)        
        self.vcTable.verticalHeader().setSectionResizeMode(2)
        self.vcTable.setColumnHidden(0,True)     
        self.mgridLayout.addWidget(self.vcTable,4,0,1,1)


        ### Hedging Params Dynamic
        self.hedgingParamsTable        = QtWidgets.QTableView(self.Monitor)
        self.hedgingParamsModel        = pdmodel.PandasModel(self.opmmData.hedgingParams.data,
                                                      self.opmmData.minHedgingParams.data,
                                                      self.opmmData.maxHedgingParams.data)
        self.hedgingParamsModel.dataChanged.connect(self.onHedgingParamChange)
        self.hedgingParamsTable.setModel(self.hedgingParamsModel)
        self.hedgingParamsTable.setMinimumHeight(30)
        for i in range(0,self.hedgingParamsModel.rowCount()):
            self.hedgingParamsTable.setRowHidden(i,True)
        self.hedgingParamsTable.setStyleSheet("font: 14px")
        self.hedgingParamsTable.resizeColumnsToContents()
        self.hedgingParamsTable.resizeRowsToContents()
        self.hedgingParamsTable.horizontalHeader().setSectionResizeMode(2)        
        self.hedgingParamsTable.verticalHeader().setSectionResizeMode(2)
        self.hedgingParamsTable.setColumnHidden(0,True)  
        #self.hedgingParamsTable.setColumnHidden(3,True)                
        self.mgridLayout.addWidget(self.hedgingParamsTable,4,1,1,1)


        ## Trades List
        self.tradeTable  = QtWidgets.QTableView(self.Monitor)
        tradeCols = ["instrumentId", "orderQty", "tradeId", "tradePrice", "tradeQty", "orderId"]
        self.tradeData  = pd.DataFrame(columns=tradeCols)
        self.tradeModel = pdmodel.PandasModel(self.tradeData)
        self.tradeTable.setModel(self.tradeModel)
        self.tradeTable.setMinimumHeight(30)        
        self.tradeTable.setStyleSheet("font: 14px")
        self.tradeTable.resizeColumnsToContents()
        self.tradeTable.resizeRowsToContents()
        self.tradeTable.horizontalHeader().setSectionResizeMode(2)        
        self.tradeTable.verticalHeader().setSectionResizeMode(2)
        self.mgridLayout.addWidget(self.tradeTable,5,0,1,1)
        
        ## Orders Requests List
        self.ordersTable  = QtWidgets.QTableView(self.Monitor)
        ordersCols = ["recvTimeNs", "instrId", "oldOrderId", "oldPrice", "orderId", "price", "side", "size"]
        self.ordersData  = pd.DataFrame(columns=ordersCols)
        self.ordersModel = pdmodel.PandasModel(self.ordersData)
        self.ordersTable.setModel(self.ordersModel)
        self.ordersTable.setMinimumHeight(30)  
        self.ordersTable.setStyleSheet("font: 14px")      
        self.ordersTable.setColumnHidden(0,True)
        self.ordersTable.horizontalHeader().setSectionResizeMode(2)        
        self.ordersTable.verticalHeader().setSectionResizeMode(2)
        self.mgridLayout.addWidget(self.ordersTable,5,1,1,1)     
           
        ## Orders Responses List
        self.ordersRespTable  = QtWidgets.QTableView(self.Monitor)
        ordersRespCols = ["recvTimeNs", "flags", "instrId", "orderId", "price", "side", "size"]
        self.ordersRespData  = pd.DataFrame(columns=ordersRespCols)
        self.ordersRespModel = pdmodel.PandasModel(self.ordersRespData)
        self.ordersRespTable.setModel(self.ordersRespModel)
        self.ordersRespTable.setMinimumHeight(30)
        self.ordersRespTable.setStyleSheet("font: 14px")              
        self.ordersRespTable.setColumnHidden(0,True)
        self.ordersRespTable.resizeRowsToContents()
        self.ordersRespTable.horizontalHeader().setSectionResizeMode(2)        
        self.ordersRespTable.verticalHeader().setSectionResizeMode(2)
        self.mgridLayout.addWidget(self.ordersRespTable,6,0,1,1)

        ## Alert monitor
        self.listWidget = QtWidgets.QListWidget(self.Monitor)
        self.listWidget.setMinimumHeight(30)
        self.mgridLayout.addWidget(self.listWidget,6,1,1,1)

        self.pfColumns = self.opmmData.pfData.columns   ## need to delete later
                
        
        self.gridLayout.addWidget(self.Monitor)


    def onPfItemChange(self, item):
        if (item.column() == 0):
            self.onPfStateChange(item)
        else:
            print ("Don't change pf level data, it's read only!!")

    def onPfStateChange(self, item):
        #cols = ['MsgType', 'portfolioId', 'optionId', 'state']
        data = {}
        data['MsgType'] = 'StateChange'
        data['portfolioId'] = (self.pfModel._data.iloc[item.row()]).portfolioId
        data['instrumentId'] = 0
        data["activePlugin"] = activePlugins[0]
        if self.pfModel._data.iloc[item.row(), 0].checkState() == QtCore.Qt.Checked:
            data['state'] = '4'#'Trading'
            data = {k: str(v) for k, v in data.items()}
            self.client.sendMessage(json.dumps(data).encode('utf8'))
        else:
            data['state'] = '1'#'Active'
            data = {k: str(v) for k, v in data.items()}
            self.client.sendMessage(json.dumps(data).encode('utf8'))
        print (json.dumps(data))

    def onInsItemChange(self, item):
        print ("Instrument level change")
        if (item.column() == 0):
            self.onInstrumentStateChange(item)
        else:
            rowIndex = item.row()
            msgType = "OptionParams"
            cols = ["MsgType","portfolioId","instrumentId","quoteBidQty","quoteAskQty","priceCorrection","volCorrection","deltaRetreat","vegaRetreat","deltaSpread","vegaSpread","multiplier","maxOpBuyQty","maxOpSellQty","maxOpNetQty","maxOpBuyValue","maxOpSellValue","spreadTolerance","taxCorrection","minDelta","strikeLimit"]
            tmp = self.insModel._data.iloc[rowIndex]
            dataToSend = tmp[cols]
            dataToSend['MsgType'] = msgType
            dataToSend["activePlugin"] = activePlugins[0]
            dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
            print (json.dumps(dataToSend))
            self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))


    def onInsSelect(self, itemSelect,itemDeselect):

        if not itemDeselect.isEmpty():
            indexDeSel = itemDeselect[0]
            rowIndex2 = indexDeSel.top()
            pfDeSelected = (self.insrModel._data._iloc[rowIndex2]).portfolioId -1

            self.vcTable.setRowHidden(pfDeSelected,True)
            self.hedgingParamsTable.setRowHidden(pfDeSelected,True)
            self.pfParamsTable.setRowHidden(pfDeSelected,True)
            self.insParTable.setRowHidden(rowIndex2,True)

        if not itemSelect.isEmpty():
            indexSel = itemSelect[0]
            rowIndex = indexSel.top()
            pfSelected = (self.insrModel._data._iloc[rowIndex]).portfolioId -1

            self.vcTable.setRowHidden(pfSelected,False)
            self.hedgingParamsTable.setRowHidden(pfSelected,False)
            self.pfParamsTable.setRowHidden(pfSelected,False)
            self.insParTable.setRowHidden(rowIndex,False)


    def onInstrumentStateChange(self, item):
        dataToSend = {}
        dataToSend['MsgType'] = 'StateChange'
        dataToSend['portfolioId'] = str((self.insModel._data.iloc[item.row()]).portfolioId)
        dataToSend['instrumentId'] = str((self.insModel._data.iloc[item.row()]).instrumentId)
        dataToSend["activePlugin"] = activePlugins[0]
        if self.insModel._data.iloc[item.row(), 0].checkState() == QtCore.Qt.Checked:
            dataToSend['state'] = '4'#'Trading'
            dataToSend = {k: str(v) for k, v in dataToSend.items()}
            self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
        else:
            dataToSend['state'] = '1'#'Active'
            dataToSend = {k: str(v) for k, v in dataToSend.items()}
            self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
        print (json.dumps(dataToSend))

    def onVolCurveChange(self, item):
        print ("Vol curve change")
        rowIndex = item.row()
        msgType = "VolCurve"
        cols = ["MsgType", "portfolioId", "atmStrike", "atmVol", "skew", "leftCurve", "leftRange","rightCurve", "rightRange"]
        tmp = self.vcModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = activePlugins[1]
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
        
    def onPfParamChange(self, item):
        print ("Global param change")
        rowIndex = item.row()
        msgType = "GlobalParams"
        cols = ["MsgType", "portfolioId", "maxBuyQty", "maxSellQty", "maxBuyValue", "maxSellValue", "maxDelta","maxVega", "maxGamma", "minPnl"]
        tmp = self.pfParamsModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = activePlugins[0]
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        print (json.dumps(dataToSend))
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))

    def onHedgingParamChange(self, item):
        print ("Hedging param change")
        rowIndex = item.row()
        msgType = "HedgingParams"
        cols =  ["MsgType","portfolioId","hedgeDelta","targetDelta","maxBid","maxAsk","tolerance","offset"]
        tmp = self.hedgingParamsModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = activePlugins[0]
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))

    def onPortfolioDataMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        pfId = int(data['portfolioId'])
        self.pfModel.updateRow(pfId, data)
        self.pfTable.model().layoutChanged.emit()

    def onPfInfoMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        pfId = int(data['portfolioId'])
        self.pfModel.updateRow(pfId, data)
        self.pfTable.model().layoutChanged.emit()

    def onInstrumentDataMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        insId = int(data['instrumentId'])
        self.insrModel.updateRow(insId, data)
        self.insTable.model().layoutChanged.emit()

    def onTradeDataMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        self.tradeModel.insertRow(data)
        self.tradeTable.model().layoutChanged.emit()
    
    def onOrderRequestMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        self.ordersModel.insertRow(data)
        self.ordersTable.resizeColumnsToContents()
        self.ordersTable.model().layoutChanged.emit()

    def onOrderRespMessage(self, jsonMsg):
        data = pd.read_json(jsonMsg, typ='series')
        self.ordersRespModel.insertRow(data)
        self.ordersRespTable.resizeColumnsToContents()
        self.ordersRespTable.model().layoutChanged.emit()

    def closeEvent(self, e):
        self.reactor.stop()


#class Login(QtGui.QDialog):
#    def __init__(self, parent=None):
#        super(Login, self).__init__(parent)

#        ssh = paramiko.SSHClient()
#        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#        ssh.connect('49.248.124.188', username='morphuser', password='123456')
#        sftp_client = ssh.open_sftp()

#        file1 = sftp_client.file('login.xml','r',-1)
#        deets = file1.readlines()
#        self.uname = deets[0].strip('\n')
#        self.pwd = deets[1].strip('\n')
#        self.lcdate = datetime.strptime(deets[2].strip('\n'),'%d-%m-%Y')
#        file1.close() 

#       self.textName = QtGui.QLineEdit(self)
#       self.textPass = QtGui.QLineEdit(self)
#        self.textChgPass = QtGui.QLineEdit(self)
#       self.textChgPass2 = QtGui.QLineEdit(self)
#       self.textChgPass.setEchoMode(QtGui.QLineEdit.Password)
#       self.textChgPass2.setEchoMode(QtGui.QLineEdit.Password)                
#       self.textPass.setEchoMode(QtGui.QLineEdit.Password)

#       self.buttonLogin = QtGui.QPushButton('Login', self)
#       self.buttonChgPwd = QtGui.QPushButton('Change Password', self)
#       self.buttonLogin.clicked.connect(self.handleLogin)
#       self.buttonChgPwd.clicked.connect(self.handleChgPwd)
#       layout = QtGui.QFormLayout(self)
#       layout.addRow("Username", self.textName)
#       layout.addRow("Password", self.textPass)
#       layout.addRow("New Password", self.textChgPass)
#       layout.addRow("Confirm Password", self.textChgPass2)
#       layout.addRow(self.buttonLogin, self.buttonChgPwd)        

#   def handleLogin(self):
#                if ((datetime.today() - self.lcdate) > timedelta(days=15)):        
#                        QtGui.QMessageBox.warning(
#                            self, 'Password Expired', 'Please change your password')     
#                elif (self.textName.text() == self.uname and self.textPass.text() == self.pwd):
#                        self.accept()
#                else:
#                        QtGui.QMessageBox.warning(self, 'Error', 'Bad user or password')

#   def handleChgPwd(self):
#        if (self.textName.text() == self.uname and self.textPass.text() == self.pwd and self.textChgPass.text() == self.textChgPass2.text()):

#                ssh = paramiko.SSHClient()
#                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#                ssh.connect('49.248.124.188', username='morphuser', password='123456')
#                sftp_client = ssh.open_sftp()
#                file2 = sftp_client.file('login.xml','w',-1)

#                file2.write("%s\n%s\n%s\n" %(self.uname,self.textChgPass.text(),datetime.today().strftime('%d-%m-%Y')))
#                file2.close()
#                self.accept()

#        elif (self.textName.text() == self.uname and self.textPass.text() == self.pwd):
#                QtGui.QMessageBox.warning(self, 'Error', 'New Password & Confirm Password do not match')
#           else:
#               QtGui.QMessageBox.warning(self, 'Error', 'Bad user or password')


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    try:
        import qt5reactor
    except ImportError:
        from twisted.internet import qt4reactor
    qt5reactor.install()

    from twisted.internet import reactor

    #login = Login()

    #if login.exec_() == QtGui.QDialog.Accepted:
        #morphGUI = MorphGUI(reactor)
        #morphGUI.show()
        #reactor.run()

    morphGUI = MorphGUI(reactor)
    morphGUI.show()
    reactor.run()



