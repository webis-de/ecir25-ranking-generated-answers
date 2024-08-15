# Web Document Crawler

This folder contains the scripts to download the html files from CommonCrawl.

First, the extracted_meta file containing all urls that were scraped for the original dataset is downloaded from https://github.com/CLEFeHealth/CHS-2021/tree/main/documents
Since we only want to download the html for files that were actually assessed by the annotators, we filter these urls by the ones of which the UUID is available and anotated in qrels.csv, which contains the relevance assessments.
The output of the script is a csv containing all urls that were assessed, combined with the UUID and the CommonCrawl URL.

Careful, this takes about 1 hour to run.

```bash
.\get_assessed_documents.sh
```

After getting the CommonCrawl URLs for all assessed documents, we can download the html files from CommonCrawl.

```bash
python download_warc_from_csv.py assessed_docs.csv -o crawl/warc
```

This returns a directory of subfolders, one for each domain, containing the html files.

Running the python script
```bash
python convert_to_txt.py
```
generates additional subfolder which only contain the text of the html files.
The default setting is to only keep text of html elements with 50 or more characters, this can be changed in the file.

Finally, the script
```bash
python format_as_tsv.py
```
produces a tsv file with columns docid and text, which can be used as input for the indexing.