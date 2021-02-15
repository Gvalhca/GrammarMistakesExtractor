# Grammar Mistakes Extractor

This repository is a solution to JetBrains 2021 internship application task "Разработка системы для сбора данных из
открытых источников".

Solution goal is to generate dataset from compressed wikipedia revision history dump file
using [Wiki Edits](https://github.com/snukky/wikiedits) with sentences containing corrections of grammar-like mistakes.

As proposed in [Low Resource Grammatical Error Correction Using Wikipedia Edits](http://aclweb.org/anthology/W18-6111)
it is possible to achieve this goal with the [ERRANT](https://github.com/adrianeboyd/errant.git) tool.

According to the article we need to:
* Split extracted WikiEdits data into original and corrected sentences
* Analyze untokenized Wikipedia edits using ERRANT and tokenize the data with
  the [spaCy](https://github.com/explosion/spaCy.git) tokenizer
* Filter the Wikipedia edits with reference to the gold GEC training data
* Convert the filtered data to a plaintext of sentences pairs

## Requirements
As WikiEdits only supports Python 2.7 and spaCy requires Python>=3.3 it is necessary to install both of them.

For Ubuntu 20.04 commands are:
```
  add-apt-repository universe
  apt update
  apt install python2
  curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py
  python2 get-pip.py
  apt install python3 python3-dev python3-pip build-essential
```
Install packages for WikiEdits:
```
pip2 install -U numpy
pip2 install -U nltk==3.4.5
pip2 install -U python-Levenshtein
```
Install packages for ERRANT, spaCy and english NLP model for spaCy:
```
pip3 install -U nltk
pip3 install -U spacy==2.0.11
python3 -m spacy download en
```

## Gold GEC Data
In solution script filtering could be done with one of available gold GEC training datasets:
* [FCE v2.1](https://www.cl.cam.ac.uk/research/nl/bea2019st/data/fce_v2.1.bea19.tar.gz)
* [Lang-8 Corpus of Learner English](https://docs.google.com/forms/d/e/1FAIpQLSflRX3h5QYxegivjHN7SJ194OxZ4XN_7Rt0cNpR2YbmNV-7Ag/viewform)
* [W&I+LOCNESS v2.1](https://www.cl.cam.ac.uk/research/nl/bea2019st/data/wi+locness_v2.1.bea19.tar.gz)

Tokenized versions of FCE and LOCNESS datasets are located in `data/gold_data`. Lang-8 is too large and needs to be downloaded separately.

## Run solution
Init `errant` and `wikiedits` submodules:
```
git submodule update --init --recursive
```

Download [Lang-8 tokenized data](https://mega.nz/file/Dxkk2QqA#8gdzRTw1FN4y0VMeTBW6ck-9-2iHVmgd43P5vymY6n8) and move the file into `data/gold_data`

Download one of the compressed Wikipedia revision history dumps (ones containing `...-pages-meta-history...` in name).

Execute `extract_grammar_mistakes.py` and pass downloaded .7z or .bz2 archive to script:

```
python3 extract_grammar_mistakes.py -dump /path/to/compressed/dump.7z -gold locness
```

Flag `-gold` is optional and FCE v2.1 is using by default due to its small size. However with Lang-8 dataset filtering results are better by the cost of time.    
After script execution result dataset can be found in `data/errant_data/result`.

I have used these dumps for tests: 
* https://dumps.wikimedia.org/enwiki/20210101/enwiki-20210101-pages-meta-history2.xml-p150972p151573.bz2
* https://dumps.wikimedia.org/enwiki/20210101/enwiki-20210101-pages-meta-history14.xml-p14320517p14324602.bz2

Script execution results with flags `-gold locness` and `-gold lang8` for these dumps can be found in `data/prepared_results`