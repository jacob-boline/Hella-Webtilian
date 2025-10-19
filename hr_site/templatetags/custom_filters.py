from django import template
import urllib.parse
import json

register = template.Library()


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def dollar_amount(stripe_price):
    return float(stripe_price)/100


@register.filter
def url_encode_quote_plus(unencoded_path):
    return urllib.parse.quote_plus(unencoded_path)


@register.filter
def parse_track_list(json_track_list):
    track_dict = json.loads(json_track_list.replace("'", '"'))
    return track_dict


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
