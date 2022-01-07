import json

output_json = False

def progress(format, *values, **keyedvalues):
    message = format.format(*values, **keyedvalues)
    if output_json:
        payload = {
            'message': message,
            'format': format,
            'values': list(values),
            'keyedvalues':dict(keyedvalues)
        }
        print(json.dumps(payload, sort_keys=True), flush=True)
    else:
        print(message)
