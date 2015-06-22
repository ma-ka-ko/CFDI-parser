import sys
import fnmatch
import os
import datetime
from collections import OrderedDict
import getopt

class Factura:
    def __init__(self, dirname, filename):
        self.total = 0
        self.fecha = None
        self.conceptos = []
        self.filename = filename
        self.dirname  = dirname
        self.uuid = ''
        self.delta = None
        self.emisor = ''
        self.buzon = False
                
    def __str__(self):
        header = "%s - %s - %s "%(os.path.basename(os.path.abspath(os.path.join(self.dirname,os.path.pardir))), os.path.basename(self.dirname), self.filename)
        header = "=== %-46s | %38s ==="%(header, self.uuid) 
        text =  "%i days: %7.2f - [%s] --- %-25s"%(self.delta.days, self.total, self.fecha.date(), self.fecha.date().strftime("%m/%d/%Y") )
        #text = "%s     %s"%(text,self.uuid)
        sep = '='*(len(header))

        text = "%s\n%s"%(self.emisor,text)
        for concepto in self.conceptos:
            text = "%s\n    * %s"%(text,concepto)
        all = "\n%s\n%s\n%s\n%s"%(sep,header,sep,text)
        return all #.encode('utf8')
        
        
    def load_xml(self):
        now = datetime.datetime.now()
        import xml.etree.ElementTree as ET
        tree = ET.parse(os.path.join( self.dirname, self.filename ))
        root = tree.getroot()
        
        #print "\n--- %s ---"%os.path.basename(dirname)
        comprobantes=0
        for _cmp in root.iter("{http://www.sat.gob.mx/cfd/3}Comprobante"):
            comprobantes += 1
            x = _cmp.get('total')
            self.total = float(x)
            fecha = _cmp.get('fecha')
            d = datetime.datetime.strptime( fecha, "%Y-%m-%dT%H:%M:%S" )
            self.fecha = d
            self.delta = (now.date() - self.fecha.date())
            
        for _emisor in root.iter("{http://www.sat.gob.mx/cfd/3}Emisor"):
            self.emisor = _emisor.get('nombre')
            
    #        print text
        if comprobantes != 1:
            print "\n\n*************************************\n"
            print      "***              ERROR           ***\n"
            print      "*************************************\n"
            print      "*  Comprobantes = %i\n"%(comprobantes)
            print      "*  File=%s/%s\n"%(self.dirname,self.filename)
            print      "*************************************\n"
    
        for _comple in root.iter("{http://www.sat.gob.mx/cfd/3}Complemento"):
            for x in _comple.iter("{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital"):
                self.uuid = x.get('UUID')

        for _concepto in root.iter("{http://www.sat.gob.mx/cfd/3}Conceptos"):
            for x in _concepto.iter("{http://www.sat.gob.mx/cfd/3}Concepto"):
                descripcion = x.get('descripcion')
                self.conceptos.append(descripcion)
        
                

class Facturas:
    def __init__(self):
        self.facturas = []
        self.repeated = []
        self.buzon    = []
        self.uuids=[]
        self.print_buzon=False

    def load_xmls(self, from_path, recursive):
        for dirname, subdirs, fnames in os.walk( os.path.abspath( from_path ) ) :
            if not recursive:  
                while len(subdirs) > 0:  
                    subdirs.pop()
            #print dirname, subdirs
            buzon =  "buzon" in dirname or "_too_late" in dirname
            
            #dir_head="\n--- %s - %s ---"%(os.path.basename(os.path.abspath(os.path.join(dirname,os.path.pardir))), os.path.basename(dirname))
            for fnamex in fnames:
                if fnmatch.fnmatch( fnamex, '*.xml' ):
                    #print dirname,fnamex
                    f = Factura( dirname, fnamex  )
                    f.load_xml()
                    f.buzon = buzon
                    if f.uuid in self.uuids:
                        self.repeated.append(f)
                    elif f.buzon:
                        self.buzon.append(f)
                    else:
                        self.facturas.append(f)
                    self.uuids.append(f.uuid)
                    
    def print_facturas(self):
        self.print_data(sorted(self.facturas, key=lambda x: x.fecha, reverse=False))
        print "-- loaded %i files --"%len(self.uuids)
        print "-- %i Pendings --"%len(self.facturas)
        print "-- %i Buzon    --"%len(self.buzon)
        print "-- %i Repeated --"%len(self.repeated)
        
        #for x in sorted(self.uuids): print x
        if len(self.repeated) >0:
            print "\nRepeated: %i"%len(self.repeated)
            self.print_data(sorted(self.repeated, key=lambda x: x.fecha, reverse=False))
            
        if self.print_buzon and len(self.buzon) > 0:
            print "\n Buzon: %i"%len(self.buzon)
            self.print_data(sorted(self.buzon, key=lambda x: x.fecha, reverse=False))

    def print_data(self, data):
        total =0
        max_delta = 0
        dir_text = ''
        for f in data:
            max_delta = max(max_delta,f.delta.days)
            total += f.total
            dir_text = "%s\n%s"%(dir_text,f)
        #dir_text = "%s%s\n%s"%('#'*len(dir_head),dir_head,'#'*len(dir_head)) + dir_text 
        print "%s\n\n--  TOTAL: $ %0.2f --\n--  Delta: %i days --\n--  %i Facturas --\n"%(dir_text,total,max_delta,len(data))
    
    def sort_dict_data(self):
        self.facturas
        self.ordered = OrderedDict((k, v) for k, v in sorted(self.facturas.iteritems()))
        

    def usage(self):
        print "\nUSAGE: %.90s [options]" % sys.argv[0]
        print "options:"
        print "        -b, --buzon                   display files already sent"
        print "        -h, --help                    display this help and exit"
    
    def parse_args(self,argv):
        try:
            opts, args = getopt.getopt(argv, "b", ["buzon"])
        except getopt.GetoptError, err:
            print str(err)
            self.usage()
            sys.exit(2)
        for o, a in opts:
            #print "o: ", o
            #print "a: ", a
            if o in ("-b", "--buzon"):
                self.print_buzon=True
            if o in ("-h","--help"):
                self.usage()
                sys.exit(0)

if __name__ == "__main__":
    print os.getcwd()
    f = Facturas()
    f.parse_args(sys.argv[1:])
    f.load_xmls(os.getcwd(),True)
    f.print_facturas()
   
    sys.exit(0)