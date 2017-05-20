#!/usr/bin/env python3
import arrow
from arrow.parser import ParserError
import json
from uuid import uuid4
import re
from io import StringIO

with open('/home/fradeve/duck/SISTEMARE/done.txt', 'r') as todotxt:
    tasks = []
    r = re.compile(r"([+]\w+)\b")

    for line in todotxt:
        date = line.split(' ')[1]
        creation = None
        tags = None
        completion = arrow.get(date)
        activity = line[13:].strip('\n')

        try:
            creation = arrow.get(activity.split(' ')[0])
            activity = activity[11:]
        except ParserError:
            pass

        entry = creation or completion

        if '+' in activity:
            results = r.findall(activity)
            if len(results):
                for i, element in enumerate(results):
                    activity = activity.strip(element)[:-1]
                    results[i] = element.strip('+')
                tags = ','.join(results)

        data = {
            "description": activity,
            "due": completion.format('YYYYMMDDTHHmmss') + 'Z',
            "end": completion.format('YYYYMMDDTHHmmss') + 'Z',
            "entry": entry.format('YYYYMMDDTHHmmss') + 'Z',
            "modified": entry.format('YYYYMMDDTHHmmss') + 'Z',
            "status": "completed",
            "uuid": str(uuid4()),
        }

        if tags:
            data.update({'tags': tags})

        tasks.append(data)

    io = StringIO()
    json.dump(tasks, io)
    print(io.getvalue())
