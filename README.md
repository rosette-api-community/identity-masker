# Identity Masker

This repository includes Python code demonstrating how to use Rosette API entity extraction results to mask personally identifying information in text.

## Setup

### Installing Dependencies with Virtualenv
The script is written for Python 3.  If you are alright with installing external Python packages globally, you may skip this section.

You can install the dependencies using `virtualenv` so that you don't alter your global site packages.

The process for installing the dependencies using `virtualenv` is as follows for `bash` or similar shells:

Ensure your `virtualenv` is up to date.

    $ pip install -U virtualenv

**Note**: You may need to use `pip3` depending on your Python installation.

`cd` into the repository directory (where this `README.md` file is located) and create a Python 3 virtual environment with:

    $ python3 $(which virtualenv) .

Activate the virtual environment:

    $ source bin/activate

Once you've activated the virtual environment you can proceed to install the requirements safely without affecting your globabl site packages.

### Installing the Dependencies
You can install the dependencies via `pip` (or `pip3` depending on your installation of Python 3) as follows using the provided `requirements.txt`:

    $ pip install -r requirements.txt

## Running `mask_identities.py`
You can use the script from the commandline as follows:

    $ ./mask_identities.py -h
    usage: mask_identities.py [-h] [-i INPUT] [-u] [-k KEY] [-a API_URL]
                          [-l LANGUAGE] [-t TYPE [TYPE ...]]
    
    Mask entities that potentially reveal personally identifying information.
    Note: You should NOT assume that the results are pefect nor that all
    personally identifying language has been removed!
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            Path to a file containing input data (if not specified
                            data is read from stdin) (default: None)
      -u, --content-uri     Specify that the input is a URI (otherwise load text
                            from file) (default: False)
      -k KEY, --key KEY     Rosette API Key (default: None)
      -a API_URL, --api-url API_URL
                            Alternative Rosette API URL (default:
                            https://api.rosette.com/rest/v1/)
      -l LANGUAGE, --language LANGUAGE
                            A three-letter (ISO 639-2 T) code that will override
                            automatic language detection (default: None)
      -t TYPE [TYPE ...], --entity-types TYPE [TYPE ...]
                            A list of named entity types to mask (refer to
                            https://developer.rosette.com/features-and-
                            functions#entity-extraction-entity-types for a full
                            description of supported entity types) (default:
                            ['ORGANIZATION', 'PERSON',
                            'IDENTIFIER:CREDIT_CARD_NUM', 'IDENTIFIER:EMAIL',
                            'IDENTIFIER:MONEY', 'IDENTIFIER:PERSONAL_ID_NUM',
                            'IDENTIFIER:PHONE_NUMBER', 'TEMPORAL:DATE',
                            'TEMPORAL:TIME', 'IDENTIFIER:LATITUDE_LONGITUDE'])

**Note**: If you prefer not to enter your Rosette API key every time you run the script you can set up an environment variable `$ROSETTE_USER_KEY`.

**Note**: This script is only for demonstration purposes.  You should **NOT** assume that the results are pefect nor that all personally identifying information has been removed!

### Examples
The simplest way to use the script is to simply pipe in a string:

    $ echo 'John Smith is accused of stealing $1,000,000.' | ./mask_identities.py
    Extracting entities via Rosette API ...
    Done!
    PERSON1 is accused of stealing IDENTIFIER:MONEY.

If there are multiple mentions of any the following entity types, they will be indexed so that distinct entities can still be distinguished, even if they can't be identified:

1. `LOCATION`
2. `ORGANIZATION`
3. `PERSON`
4. `PRODUCT`
5. `TITLE`
6. `NATIONALITY`
7. `RELIGION`


E.g.:

    $ echo "John Smith is accused of stealing \$1,000,000.  Jane Smith was John's accomplice." | ./mask_identities.py
    Extracting entities via Rosette API ...
    Done!
    PERSON1 is accused of stealing IDENTIFIER:MONEY.  PERSON2 was PERSON1's accomplice.

You can also read the input from a file:

    $ echo "John Smith is accused of stealing \$1,000,000.  Jane Smith was John's accomplice." > stealing.txt
    $ ./mask_identities.py -i stealing.txt
    Extracting entities via Rosette API ...
    Done!
    PERSON1 is accused of stealing IDENTIFIER:MONEY.  PERSON2 was PERSON1's accomplice.

Additionally you can rely on Rosette API extract content from a web page by supplying a URL and using the `-u/--content-uri` option:


    $ ./mask_identities.py -u -i 'https://www.reuters.com/article/cyber-attack-stgobain-idUSP6N1JF03T' >| news.txt
    Extracting entities via Rosette API ...
    Done!
    $ cat news.txt 
    French company ORGANIZATION1 says has been victim of cyberattack
    Market News | TEMPORAL:DATE | TEMPORAL:TIME
    French company ORGANIZATION1 says has been victim of cyberattack
    PARIS, TEMPORAL:DATE French construction materials company ORGANIZATION2 said on TEMPORAL:DATE that it had been a victim of a cyberattack, and it had isolated its computer systems in order to protect data.
    "Along with other big companies, ORGANIZATION1 has been the victim of a cyberattack. As a security measure and in order to protect our data, we have isolated our computer systems," said a company spokesman.
    The spokesman added ORGANIZATION1 was in the process of trying to fix the problem. (Reporting by PERSON1; Writing by PERSON2; Editing by PERSON3)

If you want to remove additional identifying information from the article by masking `LOCATION` and `NATIONALITY` types you can do so:

    $ ./mask_identities.py -u -i 'https://www.reuters.com/article/cyber-attack-stgobain-idUSP6N1JF03T' -t ORGANIZATION PERSON TEMPORAL:DATE TEMPORAL:TIME LOCATION NATIONALITY >| news.txt
    Extracting entities via Rosette API ...
    Done!
    $ cat news.txt 
    NATIONALITY1 company ORGANIZATION1 says has been victim of cyberattack
    Market News | TEMPORAL:DATE | TEMPORAL:TIME
    NATIONALITY1 company ORGANIZATION1 says has been victim of cyberattack
    LOCATION1, TEMPORAL:DATE NATIONALITY1 construction materials company ORGANIZATION2 said on TEMPORAL:DATE that it had been a victim of a cyberattack, and it had isolated its computer systems in order to protect data.
    "Along with other big companies, ORGANIZATION1 has been the victim of a cyberattack. As a security measure and in order to protect our data, we have isolated our computer systems," said a company spokesman.
    The spokesman added ORGANIZATION1 was in the process of trying to fix the problem. (Reporting by PERSON1; Writing by PERSON2; Editing by PERSON3)

