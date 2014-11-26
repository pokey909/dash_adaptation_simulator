__author__ = 'pokey'

import getopt
import sys
from simulator import Simulator

def usage():
    print("BLABLABLA")


def main(argv):
    fname = ""
    try:
        opts, args = getopt.getopt(argv, "hf:", ["help", "file="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-f", "--file"):
            fname = arg

    sim = Simulator()
    sim.run(fname)


if __name__ == "__main__":
    main(sys.argv[1:])