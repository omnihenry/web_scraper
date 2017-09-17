# web_scrapper

<br />

## Description

This script scrapes web pages to get the information of interested items, and save the information in an output file.

It has been tested and works for the web site set in configuration.ini. 

However, the script can be generic to some extent. This means it can work (after changing the configurations) for other similar websites (not tested) as long as these websites follow the pattern listed below:

- Homepage contains such a <div> (with a css class) that has inner <a> tags that point to the second level pages in which there are the items needed

- Second level pages have such javasript (jQuery) that defines an AJAX call to retreive more items from server. The AJAX call must look like:
```
$.post("<url with reference to the root>" + <js param bearing the # of items to retreive each time>, {<other data in JSON format>}
```

<br />


## Prerequisite:

Python version 3.4.2+ (other versions not tested)

Python package: requests, BeautifulSoup and Tag in bs4

<br />

## Configuration:
config.ini

<br /> 

## Run

```
python scraper.py
```

Note: While the program doesn't show status in command line, it generates all the output in the log file: scraper.log

<br />

## License:

This project is under MIT License.

<br />

## Future work

- Robust error/exception handling

- More generic

- QA on other versions of Python

