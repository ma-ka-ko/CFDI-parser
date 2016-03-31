import sys
import fnmatch
import os
import datetime
from collections import OrderedDict
import getopt


class Domicilio:
    def __init__(self):
        self.calle = ''
        self.noExterior=''
        self.colonia=''
        self.localidad=''
        self.municipio=''
        self.estado=''
        self.pais=''
        self.codigopostal=''
    def __str__(self):
        text = ''
        if self.calle:         text =  text + self.calle 
        if self.noExterior:    text =  text + ' ' + self.noExterior
        if self.colonia :      text =  text + ' ' + self.colonia
        if self.localidad :    text =  text + ' ' + self.localidad
        if self.municipio :    text =  text + ' ' + self.municipio
        if self.estado :       text =  text + ' ' + self.estado
        if self.pais :         text =  text + ' ' + self.pais
        if self.codigopostal : text =  text + ' ' + self.codigopostal
        return text#.encode('utf-8')

class Persona:
    def __init__(self,rfc,nombre):
        self.rfc = rfc
        self.nombre = nombre
        self.domicilio = None

    def __str__(self):
        
        text = "%s %s %s"%(self.rfc, self.nombre, self.domicilio)
        return text
    
class NominaItem:
    def __init__(self,concepto,importeExento,importeGravado):
        self.concepto = concepto
        self.importeExcento = importeExento
        self.importeGravado = importeGravado
        
    def __str__(self):
        total = float(self.importeExcento+self.importeGravado)
        return "%-40s $%s"%(self.concepto,'{:10,.2f}'.format(total))

class Factura:
    def __init__(self, dirname, filename, opciones):
        self.total = 0
        self.fecha = None
        self.conceptos = []
        self.filename = filename
        self.dirname  = dirname
        self.uuid = ''
        self.delta = None
        self.emisor = None
        self.receptor = None
        self.buzon = False
        self.opciones = opciones
        self.percepciones = []
        self.deducciones = []
        self.fecha_inicial = None
        self.fecha_final = None
                
    def __str__(self):
        header = "%s - %s - %s "%(os.path.basename(os.path.abspath(os.path.join(self.dirname,os.path.pardir))), os.path.basename(self.dirname), self.filename)
        header = "=== %-46s | %38s ==="%(header, self.uuid) 
        text =  "%i days: $%s (%7.2f)  %-25s"%(self.delta.days, '{:0,.2f}'.format(self.total), self.total,  self.fecha.date().strftime("%m/%d/%Y") )
        
        #text = "%s     %s"%(text,self.uuid)
        sep = '='*(len(header))

        if self.opciones.longnames:
            text = "%s\n%s"%(self.emisor,text)
        else:
            text = "%s\n%s"%(self.emisor.nombre,text)
            
        for concepto in self.conceptos:
            text = "%s\n    * %s"%(text,concepto)
        
        if self.opciones.longnames:
            text = "%s\n%s"%(self.receptor,text)
        #else:
        #    text = "%s\n%s"%(self.receptor.nombre,text)
            
        total_p = 0
        for percepcion in self.percepciones:
            text = "%s\n       + %s"%(text,percepcion)
            total_p = total_p + percepcion.importeExcento + percepcion.importeGravado
        if total_p > 0:
            text = "%s\n       %s $%s"%(text,"-"*50,'{:0,.2f}'.format(total_p))
        
        total_d = 0
        for deduccion in self.deducciones:
            text = "%s\n       - %s"%(text,deduccion)
            total_d = total_d +  deduccion.importeExcento + deduccion.importeGravado
        if total_d > 0:
            text = "%s\n       %s $%s"%(text,"-"*50,'{:0,.2f}'.format(total_d))
        all = "\n%s\n%s\n%s\n%s"%(sep,header,sep,text)
        return all #.encode('utf8')
        
    def loadPersona(self,root_persona):
        persona = None
        for _persona in root_persona:
            persona = Persona(_persona.get('rfc'), _persona.get('nombre'))
            _domicilio = _persona.find("{http://www.sat.gob.mx/cfd/3}Domicilio")
            print _domicilio
            if _domicilio == None:
                _domicilio = _persona.find("{http://www.sat.gob.mx/cfd/3}DomicilioFiscal")
            if _domicilio != None:
                persona.domicilio = Domicilio()
                persona.domicilio.calle = _domicilio.get("calle");
                print persona.domicilio.calle
                persona.domicilio.noExterior = _domicilio.get("noExterior");
                persona.domicilio.colonia = _domicilio.get("colonia");
                persona.domicilio.localidad = _domicilio.get("localidad");
                persona.domicilio.municipio = _domicilio.get("municipio");
                persona.domicilio.estado = _domicilio.get("estado");
                persona.domicilio.pais = _domicilio.get("pais");
                persona.domicilio.codigoPostal = _domicilio.get("codigoPostal");
        return persona
        
        
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
            
        self.emisor = self.loadPersona(root.iter("{http://www.sat.gob.mx/cfd/3}Emisor"))
        self.receptor = self.loadPersona(root.iter("{http://www.sat.gob.mx/cfd/3}Receptor"))
        

            
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

        for _nomina in root.iter("{http://www.sat.gob.mx/nomina}Nomina"):
            #print _nomina.get("FechaPago"), _nomina.get("FechaInicialPago"), _nomina.get("FechaFinalPago")
            self.fecha_inicial = datetime.datetime.strptime(_nomina.get("FechaInicialPago") , "%Y-%m-%d" )
            self.fecha_final   =   datetime.datetime.strptime(_nomina.get("FechaFinalPago") , "%Y-%m-%d" )
            for p in _nomina.iter("{http://www.sat.gob.mx/nomina}Percepcion"):
                x = NominaItem(p.get("Concepto"),float(p.get("ImporteExento")),float(p.get("ImporteGravado")))
                self.percepciones.append(x) 

            for d in _nomina.iter("{http://www.sat.gob.mx/nomina}Deduccion"):
                x = NominaItem(d.get("Concepto"),float(d.get("ImporteExento")),float(d.get("ImporteGravado")))
                self.deducciones.append(x) 

class Opciones:
    def __init__(self):
        self.print_buzon = False
        self.rename = None
        self.nomina = False
        self.longnames = False


class Facturas:
    def __init__(self):
        self.facturas = []
        self.repeated = []
        self.buzon    = []
        self.uuids=[]
        self.opciones = Opciones()
        

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
                    f = Factura( dirname, fnamex, self.opciones  )
                    f.load_xml()
                    f.buzon = buzon
                    if f.uuid in self.uuids:
                        self.repeated.append(f)
                    elif f.buzon:
                        self.buzon.append(f)
                    else:
                        self.facturas.append(f)
                    self.uuids.append(f.uuid)

    def process_facturas(self):
        if self.opciones.rename != None and self.opciones.nomina:
            for f in self.facturas:
                file,ext = os.path.splitext(f.filename)
                #print f.dirname, f.filename, "-->",os.path.join(f.dirname,"%s_%s_%s%s"%(self.rename, f.fecha_inicial.date().strftime("%Y-%m-%d"), f.fecha_final.date().strftime("%Y-%m-%d"),ext))
                old = os.path.join(f.dirname,f.filename)
                new = os.path.join(f.dirname,"%s_%s_%s%s"%(self.opciones.rename, f.fecha_inicial.date().strftime("%Y-%m-%d"), f.fecha_final.date().strftime("%Y-%m-%d"),ext))
                if old != new:
                    print old, "===>", new
                    os.rename(old,new)
                
                old_pdf = os.path.join(f.dirname,"%s%s"%(file,".pdf"))
                if os.path.exists(old_pdf):
                    new_pdf = os.path.join(f.dirname, "%s_%s_%s%s"%(self.opciones.rename, f.fecha_inicial.date().strftime("%Y-%m-%d"), f.fecha_final.date().strftime("%Y-%m-%d"),".pdf"))
                    if old_pdf != new_pdf:
                        print old_pdf,"===>",new_pdf
                        os.rename(old_pdf, new_pdf)
            
    def print_facturas(self):
        if self.opciones.rename == None:
            self.print_data(sorted(self.facturas, key=lambda x: x.fecha, reverse=False))
            print "-- loaded %i files --"%len(self.uuids)
            print "-- %i Pendings --"%len(self.facturas)
            print "-- %i Buzon    --"%len(self.buzon)
            print "-- %i Repeated --"%len(self.repeated)
            
            #for x in sorted(self.uuids): print x
            if len(self.repeated) >0:
                print "\nRepeated: %i"%len(self.repeated)
                self.print_data(sorted(self.repeated, key=lambda x: x.fecha, reverse=False))
                
            if self.opciones.print_buzon and len(self.buzon) > 0:
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
        print "%s\n\n--  TOTAL: $ %s --\n--  Delta: %i days --\n--  %i Facturas --\n"%(dir_text.encode('utf-8'),'{:0,.2f}'.format(total),max_delta,len(data))
    
    def sort_dict_data(self):
        self.facturas
        self.ordered = OrderedDict((k, v) for k, v in sorted(self.facturas.iteritems()))
        

    def usage(self):
        print "\nUSAGE: %.90s [options]" % sys.argv[0]
        print "options:"
        print "        -b, --buzon                   display files already sent"
        print "        -h, --help                    display this help and exit"
        print "        -r, --rename  <base>          Rename the files unsing <base>_date"
        print "        -n, --nomina                  Parse XMLs as nomina"
        print "        -n, --longnames               Print the names of the issuer and receiver with address"

    
    def parse_args(self,argv):
        try:
            opts, args = getopt.getopt(argv, "bhr:nl", ["buzon","help","rename=", "nomina","longnames"])
        except getopt.GetoptError, err:
            print str(err)
            self.usage()
            sys.exit(2)
        for o, a in opts:
            #print "o: ", o
            #print "a: ", a
            if o in ("-b", "--buzon"):
                self.opciones.print_buzon=True
            elif o in ("-r", "--rename"):
                self.opciones.rename = a
            elif o in ("-n","--nomina"):
                self.opciones.nomina = True
            elif o in ("-l","--longnames"):
                self.opciones.longnames = True
            elif o in ("-h","--help"):
                self.usage()
                sys.exit(0)

if __name__ == "__main__":
    print os.getcwd()
    f = Facturas()
    f.parse_args(sys.argv[1:])
    f.load_xmls(os.getcwd(),True)
    f.process_facturas()
    f.print_facturas()
   
    sys.exit(0)