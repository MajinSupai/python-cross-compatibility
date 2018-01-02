# Python Cross Compatibility

A module for simplifying the creation of cross-compatible scripts

Currently only working for Python versions under 3.6, as version 3.6 provided an overhaul of the underlying bytecode

# Cross.py

Cross.py is the main file which has the cross-compatibility functions.

It uses a regular expression-based system to check the current operating system. It stores the operating system and version number in a single reconciled string in the form of,

```
OS-with-Python-py.version.number
```

For example, my pc output,

```
Windows-10-some.version.numbers-with-Python-3.5.2
```

It includes a few defined regular expressions for catching the specific system, it includes,

```
WINDOWS = 'Windows.*'
LINUX = 'Linux.*'
OSX = 'Darwin.*'

PY1 = '.*Python-1.*'
PY2 = '.*Python-2.*'
PY3 = '.*Python-3.*'
```

Cross.py exposes a few functions,

```
addDefault  - Adds a system setup to the list of defaults
isOS        - Returns whether or not it is a specific system setup
combine     - Combines an OS and version regular expression into one
chooseOS    - Optimizes a function for a specific system setup
```

isOS can therefore be used inside of a function in order to achieve cross compatibility.
For example, integer division was changed in Python 3 to automatically cast into a float. Creating a function which always does this would look like this,

```
def div(x, y):
  if Cross.isOS(Cross.PY3):
    return x / y
    
  else:
    return float(x) / y
```

However, this is not recommended, as it will take a lot of time during every function call. The recommended function to use in this case is chooseOS.
The function chooseOS takes a function as an argument, optimizes it, then returns the optimized function. Therefore, it's recommended to use it as a decorator. The div example from before would look like this,

```
@Cross.chooseOS
def div(x, y):
  if PY3:
    return x / y
    
  else:
    return float(x) / y
```

It now simply uses PY3 as if it is a boolean. This can be done for all of the default system setups which were listed above. However, the addDefault function adds a function to the defaults, in order to use it within chooseOS.

The main difference between using isOS and chooseOS is when the system checking is happening. In the isOS example, the checking happens every time the function is run. However, chooseOS analyzes the function and rebuilds the bytecode for the correct system. Here's the dis output for the function above in PY3 and PY2,

```
PYTHON-3:
  3           0 LOAD_FAST                0 (x)
              3 LOAD_FAST                1 (y)

  4           6 BINARY_TRUE_DIVIDE
              7 RETURN_VALUE
```

```
PYTHON-2:
  4           0 LOAD_GLOBAL              1 (float)
              3 LOAD_FAST                0 (x)

  5           6 CALL_FUNCTION            1
              9 LOAD_FAST                1 (y)
             12 BINARY_DIVIDE       
             13 RETURN_VALUE   
```

As you can see, the disassembled bytecode is completely different depending on the function (You might also notice that the line numbers are not correct. I'm still working on correcting the lnotab.). And there is no version checking within the bytecode itself. All of it is done at the beginning of the program.

It does take a little bit of time at the very beginning to reassemble the functions. For the simple div example, it took roughly a tenth of a millisecond to reassemble the function. However, it takes absolutely no time at the time of using the function, so there will no-doubt be a speedup.

# Builtin.py

Builtin.py simply provides a few built-in functions that have changed from Python 2 to Python 3 in a form that is consistent. It contains the familiar functions,

```
keys - Pass a dictionary, like dict.keys
values - Pass a dictionary, like dict.values
items - Pass a dictionary, like dict.items
zip - Acts like zip in Python 3, izip in Python 2
```

# TODO

Correct the lnotab

Correct for Python 3.6

Fix and comment all code (Because it's currently a mess. No really. Don't go in there. I warned you.)
