# macro
A simple macro recorder, and player CLI written in Python

# How to use it

First, clone the repo
```
git clone https://github.com/Linueue/macro.git
```

Then, install all the dependencies
```
pip install -r requirements.txt
```

Then, record
```
python main.py record
```

You can also add `-f <filename>`, but the default outputs to `records/record1.rd`

Then, play it
```
python main.py play
```

Again, you can add `-f <filename>`, but the default is the same as above
