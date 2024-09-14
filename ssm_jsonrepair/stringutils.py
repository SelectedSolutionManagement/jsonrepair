import re

codeBackslash = 0x5c
codeSlash = 0x2f
codeAsterisk = 0x2a
codeOpeningBrace = 0x7b
codeClosingBrace = 0x7d
codeOpeningBracket = 0x5b
codeClosingBracket = 0x5d
codeOpenParenthesis = 0x28
codeCloseParenthesis = 0x29
codeSpace = 0x20
codeNewline = 0x0a
codeTab = 0x09
codeReturn = 0x0d
codeBackspace = 0x08
codeFormFeed = 0x0c
codeDoubleQuote = 0x0022
codePlus = 0x2b
codeMinus = 0x2d
codeQuote = 0x27
codeZero = 0x30
codeNine = 0x39
codeComma = 0x2c
codeDot = 0x2e
codeColon = 0x3a
codeSemicolon = 0x3b
codeUppercaseA = 0x41
codeLowercaseA = 0x61
codeUppercaseE = 0x45
codeLowercaseE = 0x65
codeUppercaseF = 0x46
codeLowercaseF = 0x66
codeNonBreakingSpace = 0xa0
codeEnQuad = 0x2000
codeHairSpace = 0x200a
codeNarrowNoBreakSpace = 0x202f
codeMediumMathematicalSpace = 0x205f
codeIdeographicSpace = 0x3000
codeDoubleQuoteLeft = 0x201c
codeDoubleQuoteRight = 0x201d
codeQuoteLeft = 0x2018
codeQuoteRight = 0x2019
codeGraveAccent = 0x0060
codeAcuteAccent = 0x00b4
regexDelimiter = re.compile("^[,:[\]/{}()\n+]$")

# alpha, number, minus, or opening bracket or brace
regexStartOfValue = re.compile(r'^[\[\{\w\-]$')

def isHex(code):
  return (
    ((code >= codeZero) and (code <= codeNine)) or
    ((code >= codeUppercaseA) and (code <= codeUppercaseF)) or
    ((code >= codeLowercaseA) and (code <= codeLowercaseF))
  )


def isDigit(code):
  return (code >= codeZero) and (code <= codeNine)


def isValidStringCharacter(code):
  return (code >= 0x20) and (code <= 0x10ffff)


def isDelimiter(char):
  return regexDelimiter.match(char)


def isDelimiterExceptSlash(char):
  return isDelimiter(char) and (char != '/')


def isStartOfValue(char):
  return regexStartOfValue.match(char) or (char and isQuote(charCodeAt(char, 0)))


def isControlCharacter(code):
  return (
    (code == codeNewline) or
    (code == codeReturn) or
    (code == codeTab) or
    (code == codeBackspace) or
    (code == codeFormFeed)
  )


'''
 * Check if the given character is a whitespace character like space, tab, or
 * newline
'''
def isWhitespace(code):
  return (code == codeSpace) or (code == codeNewline) or (code == codeTab) or (code == codeReturn)


'''
 * Check if the given character is a special whitespace character, some
 * unicode variant
'''
def isSpecialWhitespace(code):
  return (
    (code == codeNonBreakingSpace) or
    #((code >= codeEnQuad) and (code <= codeHairSpace)) or
    (code == codeNarrowNoBreakSpace) or
    (code == codeMediumMathematicalSpace) or
    (code == codeIdeographicSpace)
  )


'''
 * Test whether the given character is a quote or double quote character.
 * Also tests for special variants of quotes.
 '''
def isQuote(code):
  # // the first check double quotes, since that occurs most often
  return isDoubleQuoteLike(code) or isSingleQuoteLike(code)


'''
 * Test whether the given character is a double quote character.
 * Also tests for special variants of double quotes.
 '''
def isDoubleQuoteLike(code):
  # // the first check double quotes, since that occurs most often
  return (code == codeDoubleQuote) or (code == codeDoubleQuoteLeft) or (code == codeDoubleQuoteRight)


# '''
#  * Test whether the given character is a double quote character.
#  * Does NOT test for special variants of double quotes.
#  '''
def isDoubleQuote(code):
  return code == codeDoubleQuote


# '''
#  * Test whether the given character is a single quote character.
#  * Also tests for special variants of single quotes.
#  '''
def isSingleQuoteLike(code):
  return (
    (code == codeQuote) or
    (code == codeQuoteLeft) or
    (code == codeQuoteRight) or
    (code == codeGraveAccent) or
    (code == codeAcuteAccent)
  )


# '''
#  * Test whether the given character is a single quote character.
#  * Does NOT test for special variants of single quotes.
#  '''
def isSingleQuote(code):
  return code == codeQuote


# '''
#  * Strip last occurrence of textToStrip from text
#  '''
def stripLastOccurrence(text, textToStrip, stripRemainingText = False):
  index = text.rfind(textToStrip)
  remtext = ''
  if not stripRemainingText:
    remtext = text[index+1:]
  if (index != -1):
    return text[0:index] + remtext
  else:
    return text

def charAt(text, i):
  if len(text)>i:
    return text[i]
  else:
    return None

def charCodeAt(text, i):
  if len(text)>i:
    return ord(text[i])
  else:
    return None


def insertBeforeLastWhitespace(text, textToInsert):
  index = len(text)

  if (not isWhitespace(charCodeAt(text, index - 1))):
    # // no trailing whitespaces
    return text + textToInsert

  while (isWhitespace(charCodeAt(text,index - 1))):
    index= index-1

  return text[0, index] + textToInsert + text[index,]

def removeAtIndex(text, start, count):
  return text[0, start] + text[start + count,]

# '''
#  * Test whether a string ends with a newline or comma character and optional whitespace
#  '''
def endsWithCommaOrNewline(text):
  regex = re.compile('[,\n][ \t\r]*$')
  return regex.match(text)

def isFunctionName(text):
  regex = '^\w+$'
  return regex.match(text)
