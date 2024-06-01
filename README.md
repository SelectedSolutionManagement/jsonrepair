# Jsonr Repair

The project is created from https://github.com/josdejong/jsonrepair project, which is a Javascript based solution for repairing bad or incomplete json data.
It has been ported as python class.

The following issues can be fixed:

* Add missing quotes around keys
* Add missing escape characters
* Add missing commas
* Add missing closing brackets
* Repair truncated JSON
* Replace single quotes with double quotes
* Replace special quote characters like “...” with regular double quotes
* Replace special white space characters with regular spaces
* Replace Python constants None, True, and False with null, true, and false
* Strip trailing commas
* Strip comments like /* ... */ and // ...
* Strip ellipsis in arrays and objects like [1, 2, 3, ...]
* Strip JSONP notation like callback({ ... })
* Strip escape characters from an escaped string like {\"stringified\": \"content\"}
* Strip MongoDB data types like NumberLong(2) and ISODate("2012-12-19T06:01:17.171Z")
* Concatenate strings like "long text" + "more text on next line"
* Turn newline delimited JSON into a valid JSON array, for example:
```
{ "id": 1, "name": "John" }
{ "id": 2, "name": "Sarah" }
```

# Usage:
```
from jsonrepair import JsonRepair

data = '[[{"$match":{"agent.name:{"$exists":1}}}]]'
jr = JsonRepair()
corrected = jr.jsonrepair(data)
print(corrected)
```

# Error handling

In case of error there are 2 options:
* The program can correct the error => the corrected json is the result.
* The error cannot be repaired => JSONRepairError exception occurs.