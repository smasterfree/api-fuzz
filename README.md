# PyJFAPI
Python JSON API Fuzzer based on PyJFuzz

## Installation 
Trival as:

```
git clone https://github.com/dzonerzy/PyJFAPI.git
```

## How to use
In order to use PyJFAPI users must provide a request template, templates are just raw http messages like following

```
POST /page.php HTTP/1.1
Host: example.com
Connection: close

{"name": "John", "surname": "Smith"}
```

Templates must define **one** injection point, there are defined by a sequence of three stars at the start and at the and of the selected input, ie:

```
POST /page.php HTTP/1.1
Host: example.com
Connection: close

***{"name": "John", "surname": "Smith"}***
```
Using this template PyJFAPI will fuzz **{"name": "John", "surname": "Smith"}** command line would be something similar

```
python pjfapi.py -H example.com -P 443 -T request.txt --ssl
```

> Remember when you need to fuzz over ssl , you need to specify **--ssl** flag too, this is not implicit when using port 443!

## CLI
[![PyJFAPI](https://s28.postimg.org/gknb4imh9/Schermata_2017_01_02_alle_01_52_26.png)](https://s28.postimg.org/gknb4imh9/Schermata_2017_01_02_alle_01_52_26.png)

## Screenshot
[![PyJFAPI](https://s29.postimg.org/ocofjqdon/pjfapi.png)](https://s29.postimg.org/ocofjqdon/pjfapi.png)
