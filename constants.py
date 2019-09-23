class ConstantsWrapper:

    SCOREBOARD_FOLDER = 'scoreboard'
    SCOREBOARD_CSV_FILE_NAME_PATTERN = '{}/scoreboard_{}_{}.csv'

    ELEMENT_AVOID_ACTION_KEY = 'A'
    ELEMENT_PRIORITIZE_ACTION_KEY = 'P'
    ELEMENT_MINIMIZE_ACTION_KEY = 'M'
    ELEMENT_REMOVE_ACTION_KEY = 'R'
    ELEMENT_ACTION_KEYS = (
        (ELEMENT_AVOID_ACTION_KEY, 'avoid'),
        (ELEMENT_PRIORITIZE_ACTION_KEY, 'prior'),
        (ELEMENT_MINIMIZE_ACTION_KEY, 'minimize'),
    )


constants_wrapper = ConstantsWrapper()