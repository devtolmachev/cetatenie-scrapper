# Bubble.io microservice

## This is microservice for web scrap data from `cetatenie.just.ro`

Provides a very simple REST API and subscription system.
You launch the first endpoint with the passed parameters - the URL to which we will send updates, and a list of data that you already have, and the process of collecting data from web pages begins.
Once the parsing process is complete, we send the data to the URL that you pass in the request parameters.

### Installation
```bash
# Clone repo
git clone <url of this repo>
# Change dir to cloned repository
cd <repo name>
# Install dependencies
poetry install --no-root
```

### Set custom port
replace `if __name__ = '__main__'` section in this files:

1. bubble_parser/api.py

replace `port` in files:

1. tests/server_receiver.py
2. tests/test_api.py


### Run microservice

1. With docker

```bash
docker build -t bubble_parser .
```

```bash
docker run -p 8000:8000 bubble_parser .
```

2. Without Docker

```bash
# Activate virtualenv
poetry shell
# Run microservice
fastapi run bubble_parser/api.py
```

### Used libraries:
1. pdfminer-six - for work with pdf
2. aiohttp - async parser
3. aiofiles - async work with files
4. fastapi - rest api framework
5. and other...

### Benchmarks
Collect 7320 lines of `json` data, in 17 seconds

### Example output
```json
// If successfull
{
  "ok": true, 
  "message": "the proccess finish successfully", 
  "data": {
    "articolul_10": [
      {
        "list_name": "1170P",
        "number_order": "(9977/2022)",
        "year": 2023,
        "date": "03.07.2023"
      },
      {
        "list_name": "1170P",
        "number_order": "(9994/2022)",
        "year": 2023,
        "date": "03.07.2023"
      },
      {
        "list_name": "1170P",
        "number_order": "(10064/2022)",
        "year": 2023,
        "date": "03.07.2023"
      }
    ],

    "articolul_11": [
      {
        "list_name": "1170P",
        "number_order": "(9972/2022)",
        "year": 2023,
        "date": "03.07.2023"
      },
      {
        "list_name": "1170P",
        "number_order": "(9975/2022)",
        "year": 2023,
        "date": "03.07.2023"
      },
      {
        "list_name": "1170P",
        "number_order": "(9978/2022)",
        "year": 2023,
        "date": "03.07.2023"
      },
      {
        "list_name": "1170P",
        "number_order": "(9997/2022)",
        "year": 2023,
        "date": "03.07.2023"
      }
    ]
  }
},
// Error
{
  "ok": false,
  "message": "<exception message>",
  "data": "<raw exception data>"
},
// Wrong result
{
  "ok": false,
  "message": "Wrong result",
  "data": "<raw result data>"
}
```
