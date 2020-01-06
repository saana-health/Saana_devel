# from mixpanel_api import Mixpanel
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def similar(s1, s2, _ratio):
    """
    A util function to check if two strings are 'similar',
    defined by the value below. This is used for mapping
    items to meals
    """
    return SequenceMatcher(None, s1, s2).ratio() > _ratio

