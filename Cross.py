import platform, re, sys, dis, copy

version_info = sys.version_info
OS = platform.platform() + '-with-Python-{}.{}.{}'.format(version_info.major, version_info.minor, version_info.micro)
del version_info

WINDOWS = re.compile('Windows.*')
LINUX = re.compile('Linux.*')
OSX = re.compile('Darwin.*')

PY1 = re.compile('.*Python-1.*')
PY2 = re.compile('.*Python-2.*')
PY3 = re.compile('.*Python-3.*')

class BytecodeIterator(object):
    def __init__(self, codestring):
        self.code = codestring

    def __iter__(self):
        code = self.code
        codeLen = len(code)

        self.codespot = 0

        while self.codespot < codeLen:
            codespot = self.codespot

            op = code[codespot]

            if op >= dis.HAVE_ARGUMENT:
                returns = op, code[codespot + 1] + code[codespot + 2] * 256, codespot

                self.codespot += 3

            else:
                returns = op, None, codespot

                self.codespot += 1

            yield returns

class ReverseBytecodeIterator(object):
    def __init__(self, codestring, start=None):
        self.code = codestring

        bytecodePos = []

        index = 0

        if start == None:
            length = len(codestring)

        else:
            length = start

        while index <= length:
            bytecodePos.append(index)
            index += 3 if codestring[index] >= dis.HAVE_ARGUMENT else 1

        self.bytecodePos = bytecodePos

    def __iter__(self):
        code = self.code
        bytecodePos = self.bytecodePos
        codeLen = len(bytecodePos)

        self.codespot = 1

        while self.codespot <= codeLen:
            codespot = self.codespot
            bytecodeSpot = bytecodePos[codeLen - codespot]

            op = code[bytecodeSpot]

            if op >= dis.HAVE_ARGUMENT:
                yield op, code[bytecodeSpot + 1] + code[bytecodeSpot + 2] * 256, bytecodeSpot, codeLen - codespot

            else:
                yield op, None, bytecodeSpot, codeLen - codespot

            self.codespot += 1

class _Bytes(object):
    def __init__(self, string=b''):
        if PRE_CHECKED[PY3]:
            self.string = bytes(string)
            self.isPY3 = True

        else:
            self.string = bytes(bytearray(string))
            self.isPY3 = False

    def __str__(self):
        if self.isPY3:
            return str(self.string)

        else:
            return str(self.string)

    def __repr__(self):
        if self.isPY3:
            return str(self)

        else:
            return "'{}'".format(self.string)

    def __len__(self):
        return len(self.string)

    def __getitem__(self, index):
        if self.isPY3:
            return self.string[index]

        else:
            if isinstance(index, slice):
                return self.string[index]

            else:
                return ord(self.string[index])

    def __iadd__(self, other):
        if isinstance(other, _Bytes):
            self.string += other.string

        else:
            self.string += other

        return self


def _isOS(checkOS):
    return _testMatch(checkOS, OS)

def _items(adict):
    if PRE_CHECKED[PY3]:
        return adict.items()

    else:
        return adict.iteritems()

def _testMatch(pattern, string):
    if pattern is string:
        return True

    else:
        if isinstance(pattern, str):
            result = re.match(pattern, string)

        else:
            result = pattern.match(string)

        if result == None:
            return False

        else:
            span = result.span()

            return ((span[0] == 0) and (span[1] == len(string)))

def _reoptimize(codestring, consts, names):
    codeList = []

    for op, arg, index in BytecodeIterator(codestring):
        codeList.append([index, op, arg, False, False])

    _markCode(codeList, consts, names)

    nums = {x[0]: index for index, x in enumerate(codeList)}
    
    _fixJumps(codeList, nums)

    changesPresent = True
    while changesPresent:
        changesPresent = False
        
        for index, code in enumerate(codeList):
            op = dis.opname[code[1]]
            arg = code[2]

            if code[-2]:
                if op == 'JUMP_FORWARD':
                    if not any(x[-2] for x in codeList[index + 1: nums[code[0] + arg] - 1]):
                        code[-2] = False

                        changesPresent = True

                elif op == 'JUMP_ABSOLUTE' and arg > code[0]:
                    if not any(x[-2] for x in codeList[index + 1: nums[arg] - 1]):
                        code[-2] = False

                        changesPresent = True

                elif op == 'POP_JUMP_IF_FALSE' and arg > code[0]:
                    if not any(x[-2] for x in codeList[index + 1: nums[arg] - 1]):
                        code[-2] = False

                        origin = _traceStack(codestring, code[0] - 1, 1, False)

                        for x in range(origin, index):
                            codeList[x][-2] = False

                        changesPresent = True

                elif op == 'POP_JUMP_IF_TRUE' and arg > code[0]:
                    if not any(x[-2] for x in codeList[index + 1: nums[arg]]):
                        code[-2] = False

                        origin = _traceStack(codestring, code[0] - 1, 1, False)

                        for x in range(origin, index):
                            codeList[x][-2] = False

                        changesPresent = True

    codeList = [code for code in codeList if code[-2]]

    newPos = {}
    curPos = 0

    for code in codeList:
        newPos[code[0]] = curPos

        curPos += 1 if code[2] == None else 3
    
    for code in codeList:
        if code[1] in ABSOLUTE_MARKS:
            line = code[2]
            try:
                code[2] = newPos[line]

            except KeyError:
                broke = False
                
                for key, val in sorted(newPos.items(), key=lambda x: x[0]):
                    if key >= line:
                        code[2] = val

                        broke = True
                        break

                if not broke:
                    code[2] = val
            

        elif code[1] in RELATIVE_MARKS:
            line = code[0] + code[2]
            
            try:
                code[2] = newPos[line]

            except KeyError:
                broke = False
                
                for key, val in sorted(newPos.items(), key=lambda x: x[0]):
                    if key >= line:
                        code[2] = val

                        broke = True
                        break

                if not broke:
                    code[2] = val

            code[2] -= newPos[code[0]] + 3
                

        code[0] = newPos[code[0]]

    return b''.join(_Bytes([x[1], x[2] % 256, x[3] // 256]).string if x[2] != None else _Bytes([x[1]]).string for x in codeList)

def _markCode(codeList, consts, names, start=0, loopStack=None):
    if loopStack == None:
        loopStack = []
    
    constOnTop = False
    top = None
    constHeight = 1
    nums = {x[0]: index for index, x in enumerate(codeList)}

    index = start
    codeLen = len(codeList)
    
    while index < codeLen:
        code = codeList[index]

        if code[-1] == True:
            return

        code[-1] = True

        if code[1] in RELATIVE_MARKS:
            code[2] += 3
        
        op = dis.opname[code[1]]
        arg = code[2]
            
        if op == 'LOAD_CONST':
            code[-2] = True
            
            constOnTop = True
            top = consts[arg]

        elif op == 'POP_JUMP_IF_TRUE':
            if constOnTop:
                for x in range(1, constHeight + 1):
                    codeList[index - x][-2] = False

                constHeight = 1

                if top:
                    code[-2] = True
                    code[1] = 113
                    
                    index = nums[arg] - 1

            else:
                code[-2] = True
                    
                _markCode(codeList, consts, names, nums[arg], copy.copy(loopStack))

        elif op == 'POP_JUMP_IF_FALSE':
            if constOnTop:
                for x in range(1, constHeight + 1):
                    codeList[index - x][-2] = False

                constHeight = 1

                if not top:
                    code[-2] = True
                    code[1] = 113
                    
                    index = nums[arg] - 1

            else:
                code[-2] = True
                    
                _markCode(codeList, consts, names, nums[arg], copy.copy(loopStack))
                
        elif op == 'JUMP_ABSOLUTE':
            code[-2] = True
                
            index = nums[arg] - 1

        elif op == 'JUMP_FORWARD':
            code[-2] = True
            
            index = nums[code[0] + arg] - 1

        elif op == 'RETURN_VALUE':
            code[-2] = True

            return

        elif op == 'SETUP_LOOP':
            code[-2] = True
            
            loopStack.append(arg + code[0])

        elif op == 'BREAK_LOOP':
            code[-2] = True
            
            index = nums[loopStack[-1] - 1] - 1
            del loopStack[-1]

        elif op == 'FOR_ITER':
            code[-2] = True

            _markCode(codeList, consts, names, nums[code[0] + code[2]], copy.copy(loopStack))

            loopStack.append(arg + code[0])

        elif op == 'SETUP_EXCEPT':
            code[-2] = True

            _markCode(codeList, consts, names, nums[code[0] + code[2]], copy.copy(loopStack))

        elif op == 'LOAD_GLOBAL':
            code[-2] = True
            
            glob = names[arg]

            try:
                top = DEFAULTS[glob]

            except KeyError:
                pass

            else:
                constOnTop = True

        elif op == 'UNARY_NOT':
            code[-2] = True

            if constOnTop:
                top = not top
                constHeight += 1

        else:
            code[-2] = True

            constOnTop = False

        if loopStack and loopStack[-1] == code[0]:
            del loopStack[-1]
            
        index += 1

def _traceStack(codestring, start, count, returnBytecodeIndex=True, layer=0):
    countFound = 0

    codeIterator = ReverseBytecodeIterator(codestring, start)

    for op, arg, bytecodeIndex, index in codeIterator:
        op = dis.opname[op]
        args = 0

        if op.startswith('BINARY'):
            args = 2

        elif op.startswith('UNARY'):
            args = 1

        else:
            try:
                args = OP_ARGS[op]

            except KeyError:
                if op == 'CALL_FUNCTION':
                    args = (arg % 256) + (arg // 256) * 2 + 1

                elif op == 'BUILD_LIST':
                    args = arg

                elif op == 'BUILD_TUPLE':
                    args = arg

        if args != 0:
            index = _traceStack(codestring, bytecodeIndex - 1, args, False, layer + 1)
            bytecodeIndex = codeIterator.bytecodePos[index]
            codeIterator.codespot = len(codeIterator.bytecodePos) - index
            
        countFound += 1

        if countFound == count:
            break

    if returnBytecodeIndex:
        return bytecodeIndex

    else:
        return index

def _fixJumps(codeList, nums):
    for index, code in enumerate(codeList):
        if code[-2]:
            op = dis.opname[code[1]]
            arg = code[2]
            
            if op == 'POP_JUMP_IF_TRUE':
                jumpLoc = nums[arg]
                
                if not any(x[-2] for x in codeList[index + 1: jumpLoc - 1]) and codeList[jumpLoc - 1][1] == 113:
                    jumpCode = codeList[jumpLoc - 1]
                    
                    jumpCode[-2] = False

                    
                    code[1] = 114
                    code[2] = jumpCode[2]

            if op == 'POP_JUMP_IF_FALSE' and arg == code[0] + 6:
                jumpLoc = nums[arg]
                
                if not any(x[-2] for x in codeList[index + 1: jumpLoc - 1]) and codeList[jumpLoc - 1][1] == 113:
                    jumpCode = codeList[jumpLoc - 1]
                    
                    jumpCode[-2] = False

                    
                    code[1] = 114
                    code[2] = jumpCode[2]
        
    
def addDefault(name, string):
    """Adds a system setup to the list of defaults"""
    
    DEFAULTS[name] = _isOS(string)

#Memoized version of _isOS
def isOS(checkOS):
    """Returns if it is a specific OS"""
    
    try:
        return PRE_CHECKED[checkOS]

    except KeyError:
        result = _testMatch(checkOS, OS)
        PRE_CHECKED[checkOS] = result

        return result

def combine(OS, version):
    """Combines an OS regular expression with a version regular expression"""
    
    return re.compile(OS.pattern + version.pattern)

def chooseOS(function):
    """Optimizes a function for a specific system setup"""
    
    code = function.__code__

    codeOutput = _Bytes(code.co_code)
                
    codeObj = type(chooseOS.__code__)
    functionObj = type(chooseOS)

    argcount = code.co_argcount

    if PRE_CHECKED[PY3]:
        kwonlyargcount = code.co_kwonlyargcount
    
    nlocals = code.co_nlocals
    stacksize = code.co_stacksize
    flags = code.co_flags
    codestring = _reoptimize(_Bytes(code.co_code), code.co_consts, code.co_names)
    constants = code.co_consts
    names = code.co_names
    varnames = code.co_varnames
    filename = code.co_filename
    name = code.co_name
    firstlineno = code.co_firstlineno
    lnotab = code.co_lnotab
    freevars = code.co_freevars
    cellvars = code.co_cellvars

    if PRE_CHECKED[PY3]:
        code = codeObj(argcount, kwonlyargcount, nlocals, stacksize, flags, codestring, constants,
                       names, varnames, filename, name, firstlineno, lnotab, freevars, cellvars)

    else:
        code = codeObj(argcount, nlocals, stacksize, flags, codestring, constants, names,
                       varnames, filename, name, firstlineno, lnotab, freevars, cellvars)

    function = functionObj(code, function.__globals__)

    return function


PRE_CHECKED = {WINDOWS: _isOS(WINDOWS), LINUX: _isOS(LINUX), OSX: _isOS(OSX), PY2: _isOS(PY2), PY3: _isOS(PY3), PY1: _isOS(PY1)}
DEFAULTS = {'WINDOWS': PRE_CHECKED[WINDOWS], 'LINUX': PRE_CHECKED[LINUX], 'OSX': PRE_CHECKED[OSX], 'PY2': PRE_CHECKED[PY2], 'PY3': PRE_CHECKED[PY3], 'PY1': PRE_CHECKED[PY1]}

ABSOLUTE_MARKS = (113, 114, 115)
RELATIVE_MARKS = (110, 120, 93, 121)
OP_ARGS = {'COMPARE_OP': 2, 'GET_ITER': 1, 'MAKE_FUNCTION': 2, 'LOAD_ATTR': 1}
