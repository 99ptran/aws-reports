# ebs-report

## requirements
* python 3.x
* aws profile setup correctly


### setup virtual environment; not required, but recommended
```sh
python3 -m venv .venv 
```

### activate virtual environment (mac); not required, but recommended
```sh
source .venv/bin/activate
```

### install requirements
```sh
pip install -r requirements.txt 
``` 

### run program
```sh
python3 ebs-report.py --help #show help
python3 ebs-report.py --profile profile1 #run for aws profile1
python3 ebs-report.py --profile profile1 profile2 #run for aws profile1, profile2
python3 ebs-report.py --profile profile1 --region us-west-1 #run for profile1 in us-west-1
python3 ebs-report.py --profile profile1 --region us-west-1 us-west-2 #run for profile1 in us-west-1 and us-west-2
```