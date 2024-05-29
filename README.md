# alipay_to_ofx

alipay_to_ofx is a Python application that converts Alipay transaction records into a valid OFX format for import into financial software. This tool is particularly useful for users making purchases in China and needing to integrate their Alipay transactions into their accounting systems.

## Features

- Parses Alipay transaction records from a TXT file
- Produces a valid OFX file suitable for import into various financial and accounting software
- Supports translations using the Google Translate API to convert transactions from Mandarin to English
- Caches translations to minimize API usage and save costs

## Getting Started

### Prerequisites

- Python 3.10.x
- Google Cloud Translation API key (if using translation feature)
- Alipay transaction records in TXT format

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ZenDevMaster/alipay_to_ofx.git
    cd alipay_to_ofx
    ```

2. Create a virtual environment (recommended)

   ```sh
    python3 -m venv venv
    ```

Start the virtual environemnt:

    ```sh
    source venv/bin/activate
    ```


3. Install required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

### Usage

1. Download transaction records from Alipay:
   - Visit [Alipay Transaction Records](https://consumeprod.alipay.com/record/advanced.htm)
   - Look for 查看所有交易记录 and download the transaction records as a TXT file.

2. Run the application:

    ```sh
    python alipay_to_ofx.py input_file.txt output_file.ofx --translate --api_key YOUR_GOOGLE_API_KEY
    ```

### Important Notes

- Get a Google Translate API key from here: https://console.cloud.google.com/apis/credentials, and Enable the  Cloud Translation API here: https://console.cloud.google.com/apis/api/translate.googleapis.com/
- Ensure the bank name and account name in the resulting OFX file match those in your accounting system for proper importation.
- Alipay does not include a balance in the downloaded TXT file. You may need to manually find it from the account history and enter it in the `<LEDGERBAL>` section of the OFX file.
- During development, we tested the resulting OFX files using the `ofxparse` Python module for correctness. However, there may still be latent bugs in formatting.

## Example

Here is an example command to convert an Alipay transaction record to an OFX file with translation enabled:

```sh
python alipay_to_ofx.py alipay_record_20240521_1034.txt alipay_out.ofx --translate --api_key YOUR_GOOGLE_API_KEY
```


## Checking your OFX File for Validitiy

Once you've output your OFX file, you can check if it can be parsed with `ofxparse` before trying to use it with your accounting system. Edit 'ofx_validate.py' and replace 

```sh
output_ofx_filename = 'alipay_out.ofx'
``` 

with your actual filename. Then run:

```sh
    python ofx_validate.py
```

You should see:

```sh
    python ofx_validate.py 
    Checking OFX File
    Seems like we successfully parsed the OFX.
```


### Required Command-line Parameters

- `input_file`: Path to the input TXT file containing Alipay transactions.
- `output_file`: Path to the output OFX file.

### Optional Parameters

- `--translate`: Enable translation of transaction details from Mandarin to English.
- `--api_key`: Google Cloud Translation API key.

## Keywords

- Alipay to OFX
- Alipay transaction import
- OFX converter
- Financial software import
- Accounting integration
- Alipay statement converter
- Mandarin to English translation
- Google Translate API
- Python finance tools

## Disclaimer

This tool was tested using the `ofxparse` Python module for correctness. However, there may still be some latent bugs in formatting. Use it at your own risk and always back up your data before making imports into your accounting software.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

If you are using Alipay to make purchases in China and need to import your account into your accounting software, this tool will convert the Alipay downloaded statement into a valid OFX file for importation.