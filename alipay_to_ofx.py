'''
2024-05-29 johnra

Purpose: Convert Alipay Statement TXT files into valid OFX files for importing into Accounting systems. 
Features: With the --translate command line switch, the Google Cloud Translations API will be queried to translate
counterparty names. Translations are saved to translations.txt so they are never performed twice, saving API usage. You can edit the file
to input your own translations. 

'''

import argparse
import csv
import os
import requests
from datetime import datetime



def parse_alipay_file(input_file):
    """
    Parse the Alipay transaction file and return the relevant data in a structured format.
    
    :param input_file: Path to the input text file containing Alipay transactions.
    :return: List of dictionaries representing transactions, along with metadata.
    """
    transactions = []
    metadata = {
        'account': '',
        'start_date': '',
        'end_date': '',
        'export_time': '',
        'total_in': '',
        'total_out': ''
    }


    encoding_list = ['utf-8', 'gbk', 'gb2312']  # Common encodings used in Chinese text files
    for encoding in encoding_list:
        try:
            with open(input_file, 'r', encoding=encoding) as file:
                lines = file.readlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError(f"Failed to decode {input_file} with available encodings.")
     

    for i, line in enumerate(lines):
        if line.startswith('账号'):
            metadata['account'] = line.split(':')[1].strip()
        elif line.startswith('起始日期'):
            dates = line.split()
            metadata['start_date'] = dates[0].split(':')[1].strip()[1:]
            metadata['end_date'] = dates[2].split('[')[1].strip().split()[0]  # Correctly split by '[' and take the date part

        elif line.startswith('共'):
            summary = line.strip()
            metadata['total_records'] = summary.split('笔记录')[0][1:]
            categories = summary.split(' ')
            for cat in categories:
                if cat.startswith('已收入:'):
                    metadata['total_in'] = cat.split(':')[1].split(',')[1]
                elif cat.startswith('已支出:'):
                    metadata['total_out'] = cat.split(':')[1].split(',')[1]
        elif line.strip().startswith('导出时间'):
            metadata['export_time'] = line.split(':')[1].strip().split()[0][1:]

        if line.startswith('交易号'):
            transaction_lines = lines[i+1:]
            break

    csv_reader = csv.reader(transaction_lines, delimiter=',')
    for row in csv_reader:
        if len(row) < 17:
            continue
        transactions.append({
            'transaction_id': row[0].strip(),
            'merchant_order_id': row[1].strip(),
            'transaction_create_time': row[2].strip(),
            'payment_time': row[3].strip(),
            'last_modified_time': row[4].strip(),
            'transaction_source': row[5].strip(),
            'type': row[6].strip(),
            'counterparty': row[7].strip(),
            'item_name': row[8].strip(),
            'amount_cny': row[9].strip(),
            'income_or_expense': row[10].strip(),
            'transaction_status': row[11].strip(),
            'service_fee': row[12].strip(),
            'successful_refund': row[13].strip(),
            'remarks': row[14].strip(),
            'fund_status': row[15].strip(),
        })        
    
    return transactions, metadata

def translate_text(text, target_lang, api_key):
    """
    Translate text using Google Cloud Translation API.
    
    :param text: Text to translate.
    :param target_lang: Target language code.
    :param api_key: Google Cloud API key.
    :return: Translated text.
    """
    if not api_key:
        raise ValueError("Google Cloud API key is required for translation.")

    url = f"https://translation.googleapis.com/language/translate/v2"
    headers = {'Content-Type': 'application/json'}
    params = {
        'key': api_key
    }
    data = {
        'q': text,
        'target': target_lang,
        'format': 'text',
        'key': api_key
    }
    
    response = requests.post(url, headers=headers, params=params, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemError(f"Error while calling Google Translate API: {e}")
    
    translated_text = response.json()['data']['translations'][0]['translatedText']
    return translated_text


def load_translations_map(translation_file):
    """
    Load translations from a file into a dictionary.
    
    :param translation_file: Path to the translation file.
    :return: Dictionary of translations.
    """
    if not os.path.exists(translation_file):
        return {}

    with open(translation_file, 'r', encoding='utf-8') as file:
        translations = {}
        for line in file:
            original, translated = line.strip().split('|')
            translations[original] = translated
        return translations

def save_translations_map(translations, translation_file):
    """
    Save translations from a dictionary to a file.
    
    :param translations: Dictionary of translations.
    :param translation_file: Path to the translation file.
    """
    with open(translation_file, 'w', encoding='utf-8') as file:
        for original, translated in translations.items():
            file.write(f"{original}|{translated}\n")

def translate_field(translations, text, target_lang, api_key):
    """
    Translate a text field, using cached translations if available.
    
    :param translations: Dictionary of existing translations.
    :param text: Text to translate.
    :param target_lang: Target language code.
    :param api_key: Google Cloud API key.
    :return: Translated and original text.
    """
    if text not in translations:
        translations[text] = translate_text(text, target_lang, api_key)
    return f"{translations[text]} ({text})"




def generate_ofx(transactions, metadata, output_file, translations, target_lang, api_key):
    """
    Generate an OFX file from transaction data.

    :param transactions: List of transaction dictionaries.
    :param metadata: Metadata dictionary.
    :param output_file: Path to the output OFX file.
    :param translations: Dictionary of cached translations.
    :param target_lang: Target language code for translations.
    :param api_key: Google Cloud API key.
    """
    def format_ofx_datetime(dt_str):
        """
        Format date and time to OFX datetime format (YYYYMMDDHHMMSS.XXX[+/-TZ]).

        :param dt_str: Date string in '%Y-%m-%d %H:%M:%S' format.
        :return: Date string in OFX datetime format.
        """
        if not dt_str or dt_str.strip() == "":
            return ''
            
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y%m%d%H%M%S') + '.000[+8:CST]'

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("OFXHEADER:100\n")
        file.write("DATA:OFXSGML\n")
        file.write("VERSION:102\n")
        file.write("SECURITY:NONE\n")
        file.write("ENCODING:UTF-8\n")
        file.write("CHARSET:NONE\n")
        file.write("COMPRESSION:NONE\n")
        file.write("OLDFILEUID:NONE\n")
        file.write("NEWFILEUID:NONE\n")
        file.write("<OFX>\n")
        file.write("  <SIGNONMSGSRSV1>\n")
        file.write("    <SONRS>\n")
        file.write("      <STATUS>\n")
        file.write("        <CODE>0</CODE>\n")
        file.write("        <SEVERITY>INFO</SEVERITY>\n")
        file.write("      </STATUS>\n")

        # Format export time to OFX datetime format
        if metadata.get('export_time'):
            dt_server = format_ofx_datetime(metadata['export_time'])
        else:
            dt_server = '20240101000000.000[+8:CST]'  # Default value if export time is missing or empty

        file.write("      <DTSERVER>{}</DTSERVER>\n".format(dt_server))
        file.write("      <LANGUAGE>ENG</LANGUAGE>\n")
        file.write("      <FI>\n")
        file.write("        <ORG>ALIPAY</ORG>\n")
        file.write("        <FID>NOFID</FID>\n")
        file.write("      </FI>\n")
        file.write("    </SONRS>\n")
        file.write("  </SIGNONMSGSRSV1>\n")
        file.write("  <BANKMSGSRSV1>\n")
        file.write("    <STMTTRNRS>\n")
        file.write("      <TRNUID>1</TRNUID>\n")
        file.write("      <STATUS>\n")
        file.write("        <CODE>0</CODE>\n")
        file.write("        <SEVERITY>INFO</SEVERITY>\n")
        file.write("      </STATUS>\n")
        file.write("      <STMTRS>\n")
        file.write("        <CURDEF>CNY</CURDEF>\n")
        file.write("        <BANKACCTFROM>\n")
        file.write("          <BANKID>ALIPAY</BANKID>\n")
        file.write("          <ACCTID>{}</ACCTID>\n".format(metadata.get('account')))
        file.write("          <ACCTTYPE>CHECKING</ACCTTYPE>\n")
        file.write("        </BANKACCTFROM>\n")
        file.write("        <BANKTRANLIST>\n")
        file.write("          <DTSTART>{}</DTSTART>\n".format(metadata.get('start_date').replace("-", "") + '000000.000[+8:CST]'))
        file.write("          <DTEND>{}</DTEND>\n".format(metadata.get('end_date').replace("-", "") + '000000.000[+8:CST]'))
        
        for transaction in transactions:
            file.write("          <STMTTRN>\n")
            file.write("            <TRNTYPE>{}</TRNTYPE>\n".format("CREDIT" if transaction['income_or_expense'] == "收入" else "DEBIT"))

            # Try multiple date fields if payment_time is missing
            dt_posted = format_ofx_datetime(transaction.get('payment_time')) or \
                        format_ofx_datetime(transaction.get('transaction_create_time')) or \
                        format_ofx_datetime(transaction.get('last_modified_time'))

            if not dt_posted:
                dt_posted = '19700101000000.000[+0:GMT]'  # Default to Unix epoch if no date is available

            file.write("            <DTPOSTED>{}</DTPOSTED>\n".format(dt_posted))
            file.write("            <TRNAMT>{}</TRNAMT>\n".format(transaction['amount_cny']))
            file.write("            <FITID>{}</FITID>\n".format(transaction['transaction_id']))
            file.write("            <NAME>{}</NAME>\n".format(translate_field(translations, transaction['counterparty'], target_lang, api_key) if target_lang else transaction['counterparty']))
            file.write("            <MEMO>{}</MEMO>\n".format(translate_field(translations, transaction['item_name'], target_lang, api_key) if target_lang else transaction['item_name']))
            file.write("          </STMTTRN>\n")
        
        file.write("        </BANKTRANLIST>\n")
        file.write("        <LEDGERBAL>\n")
        file.write("          <BALAMT>{}</BALAMT>\n".format(metadata.get('total_in', '')))
        file.write("          <DTASOF>{}</DTASOF>\n".format(dt_server))
        file.write("        </LEDGERBAL>\n")
        file.write("        <AVAILBAL>\n")
        file.write("          <BALAMT>{}</BALAMT>\n".format(metadata.get('total_out', '')))
        file.write("          <DTASOF>{}</DTASOF>\n".format(dt_server))
        file.write("        </AVAILBAL>\n")
        file.write("      </STMTRS>\n")
        file.write("    </STMTTRNRS>\n")
        file.write("  </BANKMSGSRSV1>\n")
        file.write("</OFX>\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Alipay transaction records to OFX.')
    parser.add_argument('input_file', type=str, help='Path to the input txt file containing Alipay transactions.')
    parser.add_argument('output_file', type=str, help='Path to the output OFX file.')
    parser.add_argument('--translate', action='store_true', help='Translate transaction details.')
    parser.add_argument('--api_key', type=str, help='Google Cloud Translation API key.')
    args = parser.parse_args()

    # Fault tolerance: Ensure input file exists
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f'Input file not found: {args.input_file}')

    translation_file = 'translations.txt'
    translations = load_translations_map(translation_file)

    transactions, metadata = parse_alipay_file(args.input_file)

    generate_ofx(transactions, metadata, args.output_file, translations, 'en', args.api_key if args.translate else None)

    save_translations_map(translations, translation_file)
    print(f"OFX file generated successfully: {args.output_file}")
