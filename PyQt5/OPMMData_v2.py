import pdb
import pandas as pd
from PyQt5 import QtGui, QtWidgets
import json

class VolCurve():
    def __init__(self, path, filename):
        ## key : portfolio id, values : 'atmStrike','atmVol','skew','leftCurve','leftRange','rightCurve','rightRange'
        vcData    = pd.read_csv(path + "/" + filename)
        vcData.rename(columns = {'PortfolioId':'portfolioId'}, inplace=True)
        vcData.columns = ["Strategy", "portfolioId", "atmStrike", "atmVol", "skew", "leftCurve",  "leftRange","rightCurve", "rightRange"]
        vcData.index = vcData.portfolioId
        self.data = vcData

class GlobalParams():
    def __init__(self, path, filename):
        gpData    = pd.read_csv(path + "/" + filename)
        gpData.rename(columns = {'PortfolioId':'portfolioId'}, inplace=True)
        gpData.columns = ["Strategy", "portfolioId", "maxBuyQty", "maxSellQty", "maxBuyValue", "maxSellValue", "maxDelta","maxVega", "maxGamma", "minPnl"]
        gpData.index = gpData.portfolioId
        self.data = gpData

class HedgingParams():
    def __init__(self, path, filename):
        hpData    = pd.read_csv(path + "/" + filename)
        hpData.rename(columns = {'PortfolioId':'portfolioId'}, inplace=True)
        hpData.columns = ["Strategy", "portfolioId","hedgeDelta","targetDelta","tolerance","offset","maxBid","maxAsk"]
        hpData.index = hpData.portfolioId
        self.data    = hpData

class OptionParams():
    def __init__(self, path, filename):
        self.data = {}
        opData    = pd.read_csv(path + "/" + filename, index_col=2)
        opData.columns = ['strategy','portfolioId','priceCorrection','volCorrection','deltaRetreat','vegaRetreat','deltaSpread','vegaSpread','multiplier','maxOpBuyQty','maxOpSellQty','maxOpNetQty','maxOpBuyValue','maxOpSellValue','spreadTolerance','taxCorrection','minDelta','strikeLimit','quoteBidQty','quoteAskQty']
        self.data = opData
        self.data.drop('strategy', inplace=True, axis=1)

class OPMMData():
    def __init__(self, path):
        ## hedging params
        self.minHedgingParams = HedgingParams(path, "min_opmm_hedging_params.csv")
        self.hedgingParams    = HedgingParams(path, "opmm_hedging_params.csv")
        self.maxHedgingParams = HedgingParams(path, "max_opmm_hedging_params.csv")

        ## vol curve
        self.minVolCurve  = VolCurve(path, "min_opmm_vol_curve.csv")
        self.volCurve     = VolCurve(path, "opmm_vol_curve.csv")
        self.maxVolCurve  = VolCurve(path, "max_opmm_vol_curve.csv")
        
        ## global params
        self.minGlobalParams = GlobalParams(path, "min_opmm_portfolio_params.csv")
        self.globalParams    = GlobalParams(path, "opmm_portfolio_params.csv")
        self.maxGlobalParams = GlobalParams(path, "max_opmm_portfolio_params.csv")

        ## option params
        minOptionParams    = OptionParams(path, "min_opmm_option_params.csv")
        optionParams       = OptionParams(path, "opmm_option_params.csv")
        maxOptionParams    = OptionParams(path, "max_opmm_option_params.csv")

        ## Realtime data
        portfolioList = self.volCurve.data.index
        optionList    = optionParams.data.index
        instruments   = pd.read_csv("%s/morph_contract_file.csv"%path,index_col=1)
        futureList    = instruments.index[ (instruments.InstrumentName == "FUTSTK") |\
                                           (instruments.InstrumentName == "FUTIDX") ]
        ## portfolio level rt data
        pfCols        = ['enabled','portfolioId', 'futureId','stockSymbol', 'expiry','state','buyQty','sellQty','netQty','delta','vega','gamma','buyValue','sellValue','mtmPnl','netPnl']
        self.pfData   = pd.DataFrame(columns = pfCols,  index=portfolioList)
        self.pfData.portfolioId = self.pfData.index

        chkBoxColIndex = 0
        for i in range(0, len(self.pfData)):
            self.pfData.iloc[i, chkBoxColIndex]  = QtWidgets.QCheckBox()
       
        ## instrument level writable data
        insList       = list(set(optionList) | set(futureList))
        insCols       = ['enabled','portfolioId','instrumentId','priceCorrection','volCorrection','deltaRetreat','vegaRetreat','deltaSpread','vegaSpread','multiplier','maxOpBuyQty','maxOpSellQty','maxOpNetQty','maxOpBuyValue','maxOpSellValue','spreadTolerance','taxCorrection','minDelta','strikeLimit','quoteBidQty','quoteAskQty'] #['','portfolioId','instrumentId','type','name','quoteBidQty','fvBidQty','fvBidPrice','bidPrice','fairPrice','askPrice','fvAskPrice','fvAskQty','quoteAskQty','bought','boughtValue','sold','soldValue','delta','vega','gamma','mtmPnl','netPnl','priceCorrection','volCorrection','deltaRetreat','vegaRetreat','deltaSpread','vegaSpread','multiplier','maxOpBuyQty','maxOpSellQty','maxOpNetQty','maxOpBuyValue','maxOpSellValue','spreadTolerance','taxCorrection','minDelta','strikeLimit']
        self.insData  = pd.DataFrame(columns = insCols, index=insList)
        self.insData[optionParams.data.columns] = optionParams.data
        self.insData.instrumentId = self.insData.index
        #self.insData.name = instruments.Name
        #self.insData.type = instruments.InstrumentName
        #self.insData.fvBidQty = instruments.MinimumLotQuantity
        #self.insData.fvAskQty = instruments.MinimumLotQuantity
        chkBoxColIndex = 0
        for i in range(0, len(self.insData)):
            self.insData.iloc[i, chkBoxColIndex]  = QtWidgets.QCheckBox()        

        self.insData.sort_values(['portfolioId','instrumentId'], axis=0, inplace=True)

        self.minInsData = pd.DataFrame(columns = self.insData.columns, index=self.insData.index)
        self.minInsData[minOptionParams.data.columns] = minOptionParams.data
        self.maxInsData = pd.DataFrame(columns = self.insData.columns, index=self.insData.index)
        self.maxInsData[maxOptionParams.data.columns] = maxOptionParams.data

        ## instrument level rt read-only data
        insrCols = ['portfolioId','instrumentId','type','name','fvBidQty','fvBidPrice','bidPrice','fairPrice','askPrice','fvAskPrice','fvAskQty','bought','boughtValue','sold','soldValue','delta','vega','gamma','mtmPnl','netPnl']
        self.insrData  = pd.DataFrame(columns = insrCols, index=insList)
        self.insrData.portfolioId = self.insData.portfolioId        
        self.insrData.instrumentId = self.insrData.index        
        self.insrData.name = instruments.Name
        self.insrData.type = instruments.InstrumentName
        self.insrData.fvBidQty = instruments.MinimumLotQuantity
        self.insrData.fvAskQty = instruments.MinimumLotQuantity

        self.insrData.sort_values(['portfolioId','instrumentId'], axis=0, inplace=True)


#if __name__ == "__main__":
#    path = "/home/ma/git/csvs"
#
#    op   = OPMMData(path)
#    print op.portfolioParams['hedgingParams'].data
#    print op.volCurve.data
#    print op.portfolioParams['globalParams'].data
#    print op.optionParams.data
#
#    print op.insData
#    print op.pfData
