import time

from elasticsearch.client import Elasticsearch

geoip_pipeline_id = 'geoip_pipeline'


def transform_results(results):
    return [doc['_source'] for doc in results['hits']['hits']]


def transform_hl_results(results):
    ret = []
    for doc in results['hits']['hits']:
        d = {}
        for k, v in doc.items():
            if k.startswith('_'):
                k = k[1:]
            d[k] = v
        ret.append(d)
    return ret


def wait_es():
    for _ in range(100):
        try:
            client = Elasticsearch("http://elasticsearch:9200")
            client.cluster.health(wait_for_status='yellow')
            return client
        except Exception:
            print('Waiting for Elasticsearch')
            time.sleep(1.)
    else:
        # timeout
        raise Exception("Elasticsearch failed to start.")



def create_geoip_pipeline():
    client = wait_es()
    # Create pipeline
    pipeline = {
        "description": "Add geoip info",
        "processors": [
            {
                "geoip": {
                    "field": "result.dst.ip",
                    "ignore_missing": True,
                    "first_only": False,
                    "database_file": "GeoLite2-City.mmdb",
                    "target_field": "result.dst.geoip"
                }
            },
            {
                "geoip": {
                    "field": "result.dst.ip",
                    "ignore_missing": True,
                    "first_only": False,
                    "database_file": "GeoLite2-ASN.mmdb",
                    "target_field": "result.dst.geoip.asn"
                }
            },
            {
                "geoip": {
                    "field": "result.src.ip",
                    "ignore_missing": True,
                    "first_only": False,
                    "database_file": "GeoLite2-City.mmdb",
                    "target_field": "result.src.geoip"
                }
            },
            {
                "geoip": {
                    "field": "result.src.ip",
                    "ignore_missing": True,
                    "first_only": False,
                    "database_file": "GeoLite2-ASN.mmdb",
                    "target_field": "result.src.geoip.asn"
                }
            },
            {
                "network_direction": {
                    "internal_networks": ["private"],
                    "ignore_failure": True,
                    "source_ip": "result.src.ip",
                    "destination_ip": "result.dst.ip",
                    "target_field": "result.direction"
                }
            }
        ]
    }
    client.ingest.put_pipeline(id=geoip_pipeline_id, body=pipeline)
