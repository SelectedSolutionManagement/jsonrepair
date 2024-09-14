import json
from ssm_jsonrepair.stringutils import *


class JSONRepairError(Exception):
    pass


class JsonRepair:
    _controlCharacters = {
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t'
    }

    def controlCharacters(self, char):
        if char in self._controlCharacters:
            return self._controlCharacters[char]
        else:
            return None

    # map with all escape characters
    _escapeCharacters = {
        '"': '"',
        '\\': '\\',
        '/': '/',
        #    b: '\b',
        'f': "\x0c",
        'n': '\n',
        'r': '\r',
        't': '\t'
        # note that \u is handled separately in parseString()
    }

    def __init__(self):
        self.i = 0
        self.text = ""
        self.output = ""

    def escapeCharacters(self, char):
        if char in self._escapeCharacters:
            return self._escapeCharacters[char]
        else:
            return None

    def jsonrepair(self, text):
        self.i = 0  # current index in text
        self.output = ''  # generated output
        self.text = text

        processed = self.parseValue()
        if not processed:
            self.throwUnexpectedEnd()

        processedComma = self.parseCharacter(codeComma)
        if processedComma:
            self.parseWhitespaceAndSkipComments()

        if (self.i < len(self.text)) and isStartOfValue(self.text[self.i]) and endsWithCommaOrNewline(self.output):
            # // start of a new value after end of the root level object: looks like
            # // newline delimited JSON -> turn into a root level array
            if not processedComma:
                # // repair missing comma
                self.output = insertBeforeLastWhitespace(self.output, ',')

            self.parseNewlineDelimitedJSON()
        elif processedComma:
            # // repair: remove trailing comma
            self.output = stripLastOccurrence(self.output, ',')

        # // repair redundant end quotes
        while ((charCodeAt(self.text, self.i) == codeClosingBrace) or (
                charCodeAt(self.text, self.i) == codeClosingBracket)):
            self.i = self.i + 1
            self.parseWhitespaceAndSkipComments()

        if self.i >= len(self.text):
            # // reached the end of the document properly
            return self.output

        self.throwUnexpectedCharacter()

    def parseValue(self):
        self.parseWhitespaceAndSkipComments()
        processed = self.parseObject() or self.parseArray() or self.parseString() or self.parseNumber() or self.parseKeywords() or self.parseUnquotedString() or self.parseWhitespaceAndSkipComments()

        return processed

    def parseWhitespaceAndSkipComments(self):
        start = self.i

        changed = self.parseWhitespace()
        while True:
            changed = self.parseComment()
            if changed:
                changed = self.parseWhitespace()
            else:
                break

        return self.i > start

    def parseWhitespace(self):
        whitespace = ''
        normal = isWhitespace(charCodeAt(self.text, self.i))
        while normal or isSpecialWhitespace(charCodeAt(self.text, self.i)):
            if normal:
                whitespace = whitespace + self.text[self.i]
            else:
                # // repair special whitespace
                whitespace = whitespace + ' '
            normal = isWhitespace(charCodeAt(self.text, self.i))

            self.i = self.i + 1

        if len(whitespace) > 0:
            self.output = self.output + whitespace
            return True
        else:
            return False

    def parseComment(self):
        # // find a block comment '/* ... */'
        if (charCodeAt(self.text, self.i) == codeSlash) and charCodeAt(self.text, self.i + 1) == codeAsterisk:
            # // repair block comment by skipping it
            while self.i < len(self.text) and not self.atEndOfBlockComment(self.text, self.i):
                self.i = self.i + 1
            self.i = self.i + 2

            return True

        # // find a line comment '// ...'
        if (charCodeAt(self.text, self.i) == codeSlash) and (charCodeAt(self.text, self.i + 1) == codeSlash):
            # // repair line comment by skipping it
            while (self.i < len(self.text)) and (charCodeAt(self.text, self.i) != codeNewline):
                self.i = self.i + 1

            return True

        return False

    def parseCharacter(self, code):
        if charCodeAt(self.text, self.i) == code:
            self.output = self.output + self.text[self.i]
            self.i = self.i + 1
            return True
        else:
            return False

    def skipCharacter(self, code):
        if charCodeAt(self.text, self.i) == code:
            self.i = self.i + 1
            return True
        else:
            return False

    def skipEscapeCharacter(self):
        return self.skipCharacter(codeBackslash)

    # /**
    #  * Skip ellipsis like "[1,2,3,...]" or "[1,2,3,...,9]" or "[...,7,8,9]"
    #  * or a similar construct in objects.
    #  */
    def skipEllipsis(self):
        self.parseWhitespaceAndSkipComments()

        if (
                charCodeAt(self.text, self.i) == codeDot and
                charCodeAt(self.text, self.i + 1) == codeDot and
                charCodeAt(self.text, self.i + 2) == codeDot
        ):
            # // repair: remove the ellipsis (three dots) and optionally a comma
            self.i = self.i + 3
            self.parseWhitespaceAndSkipComments()
            self.skipCharacter(codeComma)

            return True
        else:
            return False

    # /**
    #  * Parse an object like '{"key": "value"}'
    #  */
    def parseObject(self):
        if charCodeAt(self.text, self.i) == codeOpeningBrace:
            self.output = self.output + '{'
            self.i = self.i + 1
            self.parseWhitespaceAndSkipComments()

            # // repair: skip leading comma like in {, message: "hi"}
            if self.skipCharacter(codeComma):
                self.parseWhitespaceAndSkipComments()

            initial = True
            while (self.i < len(self.text)) and (charCodeAt(self.text, self.i) != codeClosingBrace):
                if not initial:
                    processedComma = self.parseCharacter(codeComma)
                    if not processedComma:
                        # // repair missing comma
                        self.output = insertBeforeLastWhitespace(self.output, ',')
                    self.parseWhitespaceAndSkipComments()
                else:
                    processedComma = True
                    initial = False

                self.skipEllipsis()

                processedKey = self.parseString() or self.parseUnquotedString()
                if not processedKey:
                    if (
                            (charCodeAt(self.text, self.i) == codeClosingBrace) or
                            (charCodeAt(self.text, self.i) == codeOpeningBrace) or
                            (charCodeAt(self.text, self.i) == codeClosingBracket) or
                            (charCodeAt(self.text, self.i) == codeOpeningBracket) or
                            (self.i > len(self.text))
                    ):
                        # // repair trailing comma
                        self.output = stripLastOccurrence(self.output, ',')
                    else:
                        self.throwObjectKeyExpected()
                    break

                self.parseWhitespaceAndSkipComments()
                processedColon = self.parseCharacter(codeColon)
                truncatedText = (self.i >= len(self.text))
                if not processedColon:
                    if isStartOfValue(self.text[self.i]) or truncatedText:
                        # // repair missing colon
                        self.output = insertBeforeLastWhitespace(self.output, ':')
                    else:
                        self.throwColonExpected()
                processedValue = self.parseValue()
                if not processedValue:
                    if processedColon or truncatedText:
                        # // repair missing object value
                        self.output = self.output + 'null'
                    else:
                        self.throwColonExpected()

            if charCodeAt(self.text, self.i) == codeClosingBrace:
                self.output += '}'
                self.i = self.i + 1
            else:
                # // repair missing end bracket
                self.output = insertBeforeLastWhitespace(self.output, '}')

            return True

        return False

    # /**
    #  * Parse an array like '["item1", "item2", ...]'
    #  */
    def parseArray(self):
        if charCodeAt(self.text, self.i) == codeOpeningBracket:
            self.output += '['
            self.i = self.i + 1
            self.parseWhitespaceAndSkipComments()

            # // repair: skip leading comma like in [,1,2,3]
            if self.skipCharacter(codeComma):
                self.parseWhitespaceAndSkipComments()

            initial = True
            while self.i < len(self.text) and charCodeAt(self.text, self.i) != codeClosingBracket:
                if not initial:
                    processedComma = self.parseCharacter(codeComma)
                    if not processedComma:
                        # // repair missing comma
                        self.output = insertBeforeLastWhitespace(self.output, ',')
                else:
                    initial = False

                self.skipEllipsis()

                processedValue = self.parseValue()
                if not processedValue:
                    # // repair trailing comma
                    self.output = stripLastOccurrence(self.output, ',')
                    break

            if charCodeAt(self.text, self.i) == codeClosingBracket:
                self.output += ']'
                self.i = self.i + 1
            else:
                # // repair missing closing array bracket
                self.output = insertBeforeLastWhitespace(self.output, ']')

            return True

        return False

    # /**
    #  * Parse and repair Newline Delimited JSON (NDJSON):
    #  * multiple JSON objects separated by a newline character
    #  */
    def parseNewlineDelimitedJSON(self):
        # // repair NDJSON
        initial = True
        processedValue = True
        while processedValue:
            if not initial:
                # // parse optional comma, insert when missing
                processedComma = self.parseCharacter(codeComma)
                if not processedComma:
                    # // repair: add missing comma
                    self.output = insertBeforeLastWhitespace(self.output, ',')
            else:
                initial = False

            processedValue = self.parseValue()

        if not processedValue:
            # // repair: remove trailing comma
            self.output = stripLastOccurrence(self.output, ',')

        # // repair: wrap the output inside array brackets
        self.output = '[\n${self.output}\n]'

    # /**
    #  * Parse a string enclosed by double quotes "...". Can contain escaped quotes
    #  * Repair strings enclosed in single quotes or special quotes
    #  * Repair an escaped string
    #  *
    #  * The function can run in two stages:
    #  * - First, it assumes the string has a valid end quote
    #  * - If it turns out that the string does not have a valid end quote followed
    #  *   by a delimiter (which should be the case), the function runs again in a
    #  *   more conservative way, stopping the string at the first next delimiter
    #  *   and fixing the string by inserting a quote there.
    #  */
    def parseString(self, stopAtDelimiter=False):
        skipEscapeChars = charCodeAt(self.text, self.i) == codeBackslash
        if skipEscapeChars:
            # // repair: remove the first escape character
            self.i = self.i + 1
            skipEscapeChars = True

        if isQuote(charCodeAt(self.text, self.i)):
            # // double quotes are correct JSON,
            # // single quotes come from JavaScript for example, we assume it will have a correct single end quote too
            # // otherwise, we will match any double-quote-like start with a double-quote-like end,
            # // or any single-quote-like start with a single-quote-like end
            if isDoubleQuote(charCodeAt(self.text, self.i)):
                isEndQuote = isDoubleQuote
            elif isSingleQuote(charCodeAt(self.text, self.i)):
                isEndQuote = isSingleQuote
            elif isSingleQuoteLike(charCodeAt(self.text, self.i)):
                isEndQuote = isSingleQuoteLike
            else:
                isEndQuote = isDoubleQuoteLike

            iBefore = self.i
            oBefore = len(self.output)

            str1 = '"'
            self.i = self.i + 1

            while True:
                if self.i >= len(self.text):
                    # // end of text, we are missing an end quote
                    iPrev = self.prevNonWhitespaceIndex(self.i - 1)
                    if not stopAtDelimiter and isDelimiter(charAt(self.text, iPrev)):
                        # // if the text ends with a delimiter, like ["hello],
                        # // so the missing end quote should be inserted before this delimiter
                        # // retry parsing the string, stopping at the first next delimiter
                        self.i = iBefore
                        self.output = self.output.substring(0, oBefore)

                        return self.parseString(True)

                    # // repair missing quote
                    str1 = insertBeforeLastWhitespace(str1, '"')
                    self.output += str1

                    return True
                elif isEndQuote(charCodeAt(self.text, self.i)):
                    # // end quote
                    # // let us check what is before and after the quote to verify whether this is a legit end quote
                    iQuote = self.i
                    oQuote = len(str1)
                    str1 += '"'
                    self.i = self.i + 1
                    self.output += str1

                    self.parseWhitespaceAndSkipComments()

                    if (
                            stopAtDelimiter or
                            self.i >= len(self.text) or
                            isDelimiter(charAt(self.text, self.i)) or
                            isQuote(charCodeAt(self.text, self.i)) or
                            isDigit(charCodeAt(self.text, self.i))
                    ):
                        # // The quote is followed by the end of the text, a delimiter, or a next value
                        # // so the quote is indeed the end of the string
                        self.parseConcatenatedString()

                        return True

                    if isDelimiter(charAt(self.text, self.prevNonWhitespaceIndex(iQuote - 1))):
                        # // This is not the right end quote: it is preceded by a delimiter,
                        # // and NOT followed by a delimiter. So, there is an end quote missing
                        # // parse the string again and then stop at the first next delimiter
                        self.i = iBefore
                        self.output = self.output[0:oBefore]

                        return self.parseString(True)

                    # // revert to right after the quote but before any whitespace, and continue parsing the string
                    self.output = self.output[0:oBefore]
                    self.i = iQuote + 1

                    # // repair unescaped quote
                    str1 = str1.substring(0, oQuote) + '\\' + str1.substring(oQuote)
                elif stopAtDelimiter and isDelimiter(self.text[self.i]):
                    # // we're in the mode to stop the string at the first delimiter
                    # // because there is an end quote missing

                    # // repair missing quote
                    str1 = insertBeforeLastWhitespace(str1, '"')
                    self.output += str1

                    self.parseConcatenatedString()

                    return True
                elif charCodeAt(self.text, self.i) == codeBackslash:
                    # // handle escaped content like \n or \u2605
                    char = charAt(self.text, self.i + 1)
                    escapeChar = self.escapeCharacters(char)
                    if escapeChar is not None:
                        str1 += self.text[self.i:self.i + 2]
                        self.i += 2
                    elif char == 'u':
                        j = 2
                        while j < 6 and isHex(charCodeAt(self.text, self.i + j)):
                            j = j + 1

                        if j == 6:
                            str1 += self.text[self.i:self.i + 6]
                            self.i += 6
                        elif self.i + j >= len(self.text):
                            # // repair invalid or truncated unicode char at the end of the text
                            # // by removing the unicode char and ending the string here
                            self.i = len(self.text)
                        else:
                            self.throwInvalidUnicodeCharacter()
                    else:
                        # // repair invalid escape character: remove it
                        str1 += char
                        self.i += 2
                else:
                    # // handle regular characters
                    char = charAt(self.text, self.i)
                    code = charCodeAt(self.text, self.i)

                    if code == codeDoubleQuote and charCodeAt(self.text, self.i - 1) != codeBackslash:
                        # // repair unescaped double quote
                        str1 += '\\' + char
                        self.i = self.i + 1
                    elif isControlCharacter(code):
                        # // unescaped control character
                        str1 += self.controlCharacters(char)
                        self.i = self.i + 1
                    else:
                        if not isValidStringCharacter(code):
                            self.throwInvalidCharacter(char)
                        str1 += char
                        self.i = self.i + 1

                if skipEscapeChars:
                    # // repair: skipped escape character (nothing to do)
                    self.skipEscapeCharacter()

        return False

    # /**
    #  * Repair concatenated strings like "hello" + "world", change this into "helloworld"
    #  */
    def parseConcatenatedString(self):
        processed = False

        self.parseWhitespaceAndSkipComments()
        while charCodeAt(self.text, self.i) == codePlus:
            processed = True
            self.i = self.i + 1
            self.parseWhitespaceAndSkipComments()

            # // repair: remove the end quote of the first string
            self.output = stripLastOccurrence(self.output, '"', True)
            start = len(self.output)
            parsedStr = self.parseString()
            if parsedStr:
                # // repair: remove the start quote of the second string
                self.output = removeAtIndex(self.output, start, 1)
            else:
                # // repair: remove the + because it is not followed by a string
                self.output = insertBeforeLastWhitespace(self.output, '"')

        return processed

    # /**
    #  * Parse a number like 2.4 or 2.4e6
    #  */
    def parseNumber(self):
        start = self.i
        if charCodeAt(self.text, self.i) == codeMinus:
            self.i = self.i + 1
            if self.atEndOfNumber():
                self.repairNumberEndingWithNumericSymbol(start)
                return True
            if not isDigit(charCodeAt(self.text, self.i)):
                self.i = start
                return False

        # // Note that in JSON leading zeros like "00789" are not allowed.
        # // We will allow all leading zeros here though and at the end of parseNumber
        # // check against trailing zeros and repair that if needed.
        # // Leading zeros can have meaning, so we should not clear them.
        while isDigit(charCodeAt(self.text, self.i)):
            self.i = self.i + 1

        if charCodeAt(self.text, self.i) == codeDot:
            self.i = self.i + 1
            if self.atEndOfNumber():
                self.repairNumberEndingWithNumericSymbol(start)
                return True
            if not isDigit(charCodeAt(self.text, self.i)):
                self.i = start
                return False

            while isDigit(charCodeAt(self.text, self.i)):
                self.i = self.i + 1

        if (charCodeAt(self.text, self.i) == codeLowercaseE) or (charCodeAt(self.text, self.i) == codeUppercaseE):
            self.i = self.i + 1
            if (charCodeAt(self.text, self.i) == codeMinus) or (charCodeAt(self.text, self.i) == codePlus):
                self.i = self.i + 1

            if self.atEndOfNumber():
                self.repairNumberEndingWithNumericSymbol(start)
                return True

            if not isDigit(charCodeAt(self.text, self.i)):
                self.i = start
                return False

            while isDigit(charCodeAt(self.text, self.i)):
                self.i = self.i + 1

        # // if we're not at the end of the number by this point, allow this to be parsed as another type
        if not self.atEndOfNumber():
            self.i = start
            return False

        if self.i > start:
            # // repair a number with leading zeros like "00789"
            num = self.text[start:self.i]
            mask = re.compile(r'^0\d')
            hasInvalidLeadingZero = mask.match(num)

            if hasInvalidLeadingZero:
                self.output += f'"{num}"'
            else:
                self.output += num
            return True

        return False

    # /**
    #  * Parse keywords true, false, null
    #  * Repair Python keywords True, False, None
    #  */
    def parseKeywords(self):
        return (
                self.parseKeyword('true', 'true') or
                self.parseKeyword('false', 'false') or
                self.parseKeyword('null', 'null') or
                # // repair Python keywords True, False, None
                self.parseKeyword('True', 'true') or
                self.parseKeyword('False', 'false') or
                self.parseKeyword('None', 'null')
        )

    def parseKeyword(self, name, value):
        if self.text[self.i:self.i + len(name)] == name:
            self.output = self.output + value
            self.i = self.i + len(name)
            return True

        return False

    # /**
    #  * Repair an unquoted string by adding quotes around it
    #  * Repair a MongoDB function call like NumberLong("2")
    #  * Repair a JSONP function call like callback({...});
    #  */
    def parseUnquotedString(self):
        # // note that the symbol can end with whitespaces: we stop at the next delimiter
        # // also, note that we allow strings to contain a slash / in order to support repairing regular expressions
        start = self.i
        while ((self.i < len(self.text)) and not isDelimiterExceptSlash(self.text[self.i]) and not isQuote(
                charCodeAt(self.text, self.i))):
            self.i = self.i + 1

        if self.i > start:
            if ((charCodeAt(self.text, self.i) == codeOpenParenthesis) and isFunctionName(
                    self.text[start:self.i].strip())):
                # // repair a MongoDB function call like NumberLong("2")
                # // repair a JSONP function call like callback({...});
                self.i = self.i + 1

                self.parseValue()

                if charCodeAt(self.text, self.i) == codeCloseParenthesis:
                    # // repair: skip close bracket of function call
                    self.i = self.i + 1
                    if charCodeAt(self.text, self.i) == codeSemicolon:
                        # // repair: skip semicolon after JSONP call
                        self.i = self.i + 1

                return True
            else:
                # // repair unquoted string
                # // also, repair undefined into null

                # // first, go back to prevent getting trailing whitespaces in the string
                while isWhitespace(charCodeAt(self.text, self.i - 1)) and (self.i > 0):
                    self.i = self.i - 1

                symbol = self.text[start:self.i]
                if symbol is None:
                    self.output += 'null'
                else:
                    self.output += json.dumps(symbol)

                if charCodeAt(self.text, self.i) == codeDoubleQuote:
                    # // we had a missing start quote, but now we encountered the end quote, so we can skip that one
                    self.i = self.i + 1

                return True

    def prevNonWhitespaceIndex(self, start):
        prev = start

        while (prev > 0) and isWhitespace(charCodeAt(self.text, prev)):
            prev = prev - 1

        return prev

    def atEndOfNumber(self):
        return (self.i >= len(self.text)) or isDelimiter(self.text[self.i]) or isWhitespace(
            charCodeAt(self.text, self.i))

    def repairNumberEndingWithNumericSymbol(self, start):
        # // repair numbers cut off at the end
        # // this will only be called when we end after a '.', '-', or 'e' and does not
        # // change the number more than it needs to make it valid JSON
        self.output += self.text[start:self.i] + '0'

    def throwInvalidCharacter(self, char):
        raise JSONRepairError('Invalid character ' + json.dumps(char), self.i)

    def throwUnexpectedCharacter(self):
        raise JSONRepairError('Unexpected character ' + json.dumps(self.text[self.i]), self.i)

    def throwUnexpectedEnd(self):
        raise JSONRepairError('Unexpected end of json string', len(self.text))

    def throwObjectKeyExpected(self):
        raise JSONRepairError('Object key expected', self.i)

    def throwColonExpected(self):
        raise JSONRepairError('Colon expected', self.i)

    def throwInvalidUnicodeCharacter(self):
        chars = self.text[self.i:self.i + 6]
        raise JSONRepairError(f"Invalid unicode character {chars}", self.i)

    def atEndOfBlockComment(self, text, i):
        return text[i] == '*' and text[i + 1] == '/'


if __name__ == "__main__":
    data = '[[{"$match":{"agent.name":{"$exists":1}}}]]'
    jr = JsonRepair()
    corrected = jr.jsonrepair(data)
    print(corrected)
