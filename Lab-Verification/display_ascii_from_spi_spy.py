# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 16:44:13 2020

@author: timot
"""

import io
import sys
import re

class N25QCommand:
    def __init__(self, copi, cipo):
        self._copi = copi
        self._cipo = cipo
        self.lineFormat = 1
    
    def insertDashes(self, dashPos):
        for i in reversed(dashPos):
            self._copi.insert(i, '--')
            self._cipo.insert(i, '--')

    def __str__(self):
        if self.lineFormat == 2:
            return "N25Q 0x{1} {0:<30}\t(\nout: {2};\nin : {3})".format(self.CommandName, self.CommandByte, " ".join(self._copi), " ".join(self._cipo))
        else:
            return "N25Q 0x{1} {0:<30}\t(out: {2}; in: {3})".format(self.CommandName, self.CommandByte, " ".join(self._copi), " ".join(self._cipo))

class N25QUnknown(N25QCommand):
    CommandByte = "xx"
    CommandName = "Unknown Command / Spy Fail"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)

class N25QWriteEnable(N25QCommand):
    CommandByte = "06"
    CommandName = "WriteEnable"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, ))
    
class N25QReadStatusRegister(N25QCommand):
    CommandByte = "05"
    CommandName = "ReadStatusRegister"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 2))
 
class N25QReadFlagStatusRegister(N25QCommand):
    CommandByte = "70"
    CommandName = "ReadFlagStatusRegister"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 2))
        
class N25QSectorErase(N25QCommand):
    CommandByte = "D8"
    CommandName = "SectorErase"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 4))

class N25Q4ByteSubsectorErase(N25QCommand):
    CommandByte = "21"
    CommandName = "4ByteSubsectorErase"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 5))

class N25QPageProgram(N25QCommand):
    CommandByte = "02"
    CommandName = "PageProgram"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 4, 4+256))
        self.lineFormat = 2

class N25Q4BytePageProgram(N25QCommand):
    CommandByte = "12"
    CommandName = "4BytePageProgram"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 5, 5+256))
        self.lineFormat = 2

class N25QRead(N25QCommand):
    CommandByte = "03"
    CommandName = "Read"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 4, 4+256))
        self.lineFormat = 2
        
class N25Q4ByteFastRead(N25QCommand):
    CommandByte = "0C"
    CommandName = "4ByteFastRead"
    
    def __init__(self, copi, cipo):
        super().__init__(copi, cipo)
        self.insertDashes((1, 5, 6, 6+256))
        self.lineFormat = 2
        
class AnalogDiscoverySpiSpyParser:
    EscCharacters = ["1B",]
    PartsCopi = ["c", "cp"]
    PartsCipo = ["p", "cp"]
    rexData = re.compile(r"^Data[:][ ]")

    def __init__(self, fileName):
        self._currentLine = None
        self._ioParts = None
        self._fh = open(fileName, "r")
        self._strCopi = None
        self._strCipo = None
        self._asciiCopi = None
        self._asciiCipo = None

    def readCurrentLine(self):
        self._currentLine = self._fh.readline()
        if self._currentLine:
            return True
        else:
            return False
        
    def parseDataParts(self):
        if self._currentLine:
            if self.rexData.match(self._currentLine):
                dataParts = self._currentLine.split(":")
                lineParts = dataParts[1].split(",")
                self._ioParts = []
                for linePart in lineParts:
                    self._ioParts.append(linePart.split("|"))
                return True
            else:
                return False
        else:
            return False
    
    def close(self):
        self._fh.close()
        
    def getIoParts(self):
        return self._ioParts
    
    def getIoPartsAsN25Q(self):
        bCopi = []
        bCipo = []

        for ioPart in self.getIoParts():
            if (len(ioPart) == 2):
                bCopi.append(ioPart[0].strip())
                bCipo.append(ioPart[1].strip())
        
        cmd = N25QUnknown(bCopi, bCipo)

        if (len(bCopi) > 0):
            b = bCopi[0]
            if (b == N25QWriteEnable.CommandByte):
                cmd = N25QWriteEnable(bCopi, bCipo)
            elif (b == N25QReadStatusRegister.CommandByte):
                cmd = N25QReadStatusRegister(bCopi, bCipo)
            elif (b == N25QSectorErase.CommandByte):
                cmd = N25QSectorErase(bCopi, bCipo)
            elif (b == N25QPageProgram.CommandByte):
                cmd = N25QPageProgram(bCopi, bCipo)
            elif (b == N25QRead.CommandByte):
                cmd = N25QRead(bCopi, bCipo)
            elif (b == N25QReadFlagStatusRegister.CommandByte):
                cmd = N25QReadFlagStatusRegister(bCopi, bCipo)
            elif (b == N25Q4ByteSubsectorErase.CommandByte):
                cmd = N25Q4ByteSubsectorErase(bCopi, bCipo)
            elif (b == N25Q4BytePageProgram.CommandByte):
                cmd = N25Q4BytePageProgram(bCopi, bCipo)
            elif (b == N25Q4ByteFastRead.CommandByte):
                cmd = N25Q4ByteFastRead(bCopi, bCipo)

        return str(cmd)


    def getIoPartsAsEscAscii(self):
        self._strCopi = ""
        self._strCipo = ""
        cCopiEsc = []
        cCipoEsc = []
        self._asciiCopi = ""
        self._asciiCipo = ""
        
        for ioPart in self.getIoParts():
            if (len(ioPart) == 2):
                cCopi = ioPart[0].strip()
                cCipo = ioPart[1].strip()
                
                if (cCopi not in self.EscCharacters):
                    self._strCopi += cCopi
                else:
                    cCopiEsc.append(len(self._strCopi))
                    
                if (cCipo not in self.EscCharacters):
                    self._strCipo += cCipo
                else:
                    cCipoEsc.append(len(self._strCipo))
    
        ba = str(bytearray.fromhex(self._strCopi).decode())
        for b in range(len(ba)):
            if (len(cCopiEsc) > 0):
                l = cCopiEsc[0]
                while(b == l):
                    cCopiEsc.pop(0)
                    self._asciiCopi += r"\x"
                    if (len(cCopiEsc) > 0):
                        l = cCopiEsc[0]
                    else:
                        l = -1
                
            self._asciiCopi += ba[b]

        ba = bytearray.fromhex(self._strCipo).decode()
        for b in range(len(ba)):
            if (len(cCipoEsc) > 0):
                l = cCipoEsc[0]
                while(b == l):
                    cCipoEsc.pop(0)
                    self._asciiCipo += r"\x"
                    if (len(cCipoEsc) > 0):
                        l = cCipoEsc[0]
                    else:
                        l = -1
                
            self._asciiCipo += ba[b]

    def getCurrentLine(self):
        return self._currentLine
    
    def getStrCopi(self):
        return self._strCopi
    
    def getStrCipo(self):
        return self._strCipo
    
    def getAsciiCopi(self):
        return self._asciiCopi
    
    def getAsciiCipo(self):
        return self._asciiCipo
        

def usage():
    print("%s : <c | p | cp> <filename.txt>" % (sys.argv[0], ))
    sys.exit(1)

def mainPmodCLS(filename, partFlag):
    fh2 = io.open(filename + "_parse.txt", "w")
    i = 0
    
    adssp = AnalogDiscoverySpiSpyParser(filename)
    
    while(adssp.readCurrentLine()):
        i = i + 1
        if adssp.parseDataParts():            
            adssp.getIoPartsAsEscAscii()
            
            if (partFlag in adssp.PartsCopi):                
                fh2.write(adssp.getStrCopi())
                fh2.write("\n")
                fh2.write(adssp.getAsciiCopi())
                fh2.write("\n")

            if (partFlag in adssp.PartsCipo):
                fh2.write(adssp.getStrCipo())
                fh2.write("\n")
                fh2.write(adssp.getAsciiCipo())
                fh2.write("\n")

            fh2.write("\n")
            
    adssp.close()
    fh2.close()

def mainPmodSF3(filename, partFlag):
    fh2 = io.open(filename + "_parse.txt", "w")
    i = 0
    
    adssp = AnalogDiscoverySpiSpyParser(filename)
    
    while(adssp.readCurrentLine()):
        i = i + 1
        if adssp.parseDataParts():            
            s = adssp.getIoPartsAsN25Q()
            
            if s:
                fh2.write(s)
                fh2.write("\n")

            fh2.write("\n")
            
    adssp.close()
    fh2.close()

if __name__ == "__main__":
    if (len(sys.argv) == 3):
        mainPmodCLS(sys.argv[2], sys.argv[1])
    elif (len(sys.argv) == 1):
        partFlag = "c"
        pmodCLSfileNames = ["SF-Tester-Design-AXI/CLS SPI Spy Capture of Boot-Time Display at ext_spi_clk SCK.txt",
                     "SF-Tester-Design-AXI/CLS SPI Spy Capture of First-Iteration Display at ext_spi_clk SCK.txt",
                     "SF-Tester-Design-VHDL/CLS SPI Spy Capture of Boot-Time Display at 50 KHz SCK.txt",
                     "SF-Tester-Design-VHDL/CLS SPI Spy Capture of First-Iteration Display at 50 KHz SCK.txt"]
        
        for fileName in pmodCLSfileNames:
            mainPmodCLS(fileName, partFlag)
            
        partFlag = "cp"
        pmodSF3fileNames = ["SF-Tester-Design-AXI/SF3 SPI Spy Capture of Erase Subsector at ext_spi_clk SCK.txt",
                            "SF-Tester-Design-AXI/SF3 SPI Spy Capture of Page Program at ext_spi_clk SCK.txt",
                            "SF-Tester-Design-AXI/SF3 SPI Spy Capture of Random Read at ext_spi_clk SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Erase Subsector at 50 KHz SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Erase Subsector at 500 KHz SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Page Program at 50 KHz SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Page Program at 500 KHz SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Random Read at 50 KHz SCK.txt",
                            "SF-Tester-Design-VHDL/SF3 SPI Spy Capture of Random Read at 500 KHz SCK.txt"]
        
        for fileName in pmodSF3fileNames:
            mainPmodSF3(fileName, partFlag)
            
    else:
        usage()
