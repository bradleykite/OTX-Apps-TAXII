from StixExport import StixExport
from OTXv2 import OTXv2
from taxii_client import Client, check_taxii_response
import ConfigParser
import datetime
import sys

OTX_FILE = 'timestamp'


def saveTimestamp(mtimestamp=None):
    if not mtimestamp:
        mtimestamp = datetime.datetime.now().isoformat()

    try:
        with open(OTX_FILE, "w") as f:
            f.write(mtimestamp)
        return mtimestamp

    except:
        print 'Unable to find/open %s' % OTX_FILE


def readTimestamp():
    try:
        with open(OTX_FILE, "r") as f:
            mtimestamp = f.read()
        return mtimestamp

    except:
        print "No %s found:\n\tIt appears 'otx-taxii.py first_run' has not been run" % OTX_FILE


def sendTAXII(first=True):

    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    otx = OTXv2(config.get('otx', 'key'))

    if first:
        pulses = otx.getall_iter()
        mtimestamp = None
    else:
        mtimestamp = readTimestamp()
        pulses = otx.getsince(mtimestamp)

    if pulses:
        client = Client()
        client.from_dict(dict(config.items('taxii')))

        for pulse in pulses:
            if not mtimestamp:
                mtimestamp = pulse["modified"]
            st = StixExport(pulse)
            st.build()

            # Majority of TAXII server today (2017Q1) only support STIX 1.1.1
            st.stix_package.version = '1.1.1'

            print "Sending %s" % pulse["name"]
            print "\t %s" % check_taxii_response(client.snd_post('inbox', st.to_xml()))

        saveTimestamp(mtimestamp)
        print "%d new pulses" % len(pulses)


def usage():
    print "Usage:\n\totx-taxii.py [first_run|check_new]"
    sys.exit(0)


if __name__ == "__main__":
    if sys.argv[1] == "first_run":
        sendTAXII(True)
    elif sys.argv[1] == "check_new":
        sendTAXII(False)
    else:
        usage()

