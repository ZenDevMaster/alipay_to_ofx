'''
2024-05-21 johnra

Purpose: Validate output OFX file. Simply place your output_ofx_filename in the variable and run 

python ofx_validate.py

'''

output_ofx_filename = 'alipay_out5.ofx'

import io
try:
    from ofxparse import OfxParser
except ImportError:
    print("ofxparse not found.")
    OfxParser = None


def _check_ofx(data_file):
        print("Checking OFX File")
        if not OfxParser:
            print("Can't find OfxParser module.")
            return False
        try:
            ofx = OfxParser.parse(io.BytesIO(data_file))
            print("Seems like we successfully parsed the OFX.")

        except Exception as e:
            print("Exception in OFX.")

            print(e)
            return False
        return ofx

f = open(output_ofx_filename, "rb")
_check_ofx(f.read())