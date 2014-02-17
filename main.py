import sys
from PyQt4.QtCore import QCoreApplication
from threadedserver import Server

def main():
    # Creates a QCoreApplication object.
    app = QCoreApplication(sys.argv)
    server = Server()
    
    print "Process ID: %i" % app.applicationPid()
    
    # Run application.
    app.exec_()
    
main()
