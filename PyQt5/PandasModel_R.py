from PyQt5 import QtCore, QtGui
import sys
import numpy as np
from PyQt5.QtGui import *   

import pdb

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, minData=None, maxData=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self._min  = minData
        self._max  = maxData

    def rowCount(self, parent=None):
        return len(self._data.index)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        column = index.column()
        if (self._data.columns[column] == 'enabled'):
            value = self._data.iloc[index.row() ,column]
        else:
            value  = str(self._data.values[index.row()][column])
        if role == QtCore.Qt.DisplayRole:
            return value
        elif role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.CheckStateRole:
            if (self._data.columns[column] == 'enabled'):
                if self._data.iloc[index.row(), column].isChecked():
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

        ctrct = str(self._data.iloc[index.row(), 3])
        
        ##Coloring Rows, Bid-Ask

        if role == QtCore.Qt.BackgroundRole:
            if (ctrct[-2:] == 'UT'):
                return QBrush(QColor(0,125,255,100))

            elif (self._data.columns[column] == 'fvBidPrice'):
                if (self._data.iloc[index.row() ,column] >= self._data.iloc[index.row() ,column+3]):
                    return QBrush(QColor(255,0,0,50))
                elif (self._data.iloc[index.row() ,column] >= self._data.iloc[index.row() ,column+1]):
                    return QBrush(QColor(255,100,100,20))
                elif (self._data.iloc[index.row() ,column] >= self._data.iloc[index.row() ,column+1] - 0.2):
                    return QBrush(QColor(100,255,100,50))
                else:
                    return QBrush(QColor(0,0,255,50))

            elif (self._data.columns[column] == 'fvAskPrice'):
                if (self._data.iloc[index.row() ,column] <= self._data.iloc[index.row() ,column-3]):
                    return QBrush(QColor(255,0,0,50))
                elif (self._data.iloc[index.row() ,column] <= self._data.iloc[index.row() ,column-1]):
                    return QBrush(QColor(255,100,100,20))
                elif (self._data.iloc[index.row() ,column] <= self._data.iloc[index.row() ,column-1] + 0.2):
                    return QBrush(QColor(100,255,100,50))
                else:
                    return QBrush(QColor(0,0,255,50))
                        
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None


    def flags(self, index):
        flags = super(self.__class__,self).flags(index)
        flags |= QtCore.Qt.ItemIsSelectable
        flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def updateRow(self, key, data, role=QtCore.Qt.EditRole):
        if (not key in self._data.index):
            return False
        if role != QtCore.Qt.EditRole:
            return False
        for col in data.keys():
            self._data.loc[key,col] = data[col]
        return True
