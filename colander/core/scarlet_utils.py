
def __remove_geojson(elt):
    try:
        elt['network']['location'].pop('geojson')
    except:
        pass
    return elt


def clean_results(api_response):
    if api_response['result_code'] != 1:
        return True, api_response['result']
    else:
        # Remove geojson
        if type(api_response['result']) is list:
            data = api_response['result'][0]
        else:
            data = api_response['result']
        data = __remove_geojson(data)
    return False, data
