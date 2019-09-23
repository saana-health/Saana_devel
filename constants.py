class ConstantsWrapper:

    SCOREBOARD_FOLDER = 'scoreboard'
    SCOREBOARD_CSV_FILE_NAME_PATTERN = '{}/scoreboard_{}_{}.csv'

    ELEMENT_AVOID_KEY = 'A'
    ELEMENT_PRIORITIZE_KEY = 'P'
    ELEMENT_MINIMIZE_KEY = 'M'
    ELEMENT_OPT_KEYS = (
        ELEMENT_AVOID_KEY,
        ELEMENT_PRIORITIZE_KEY,
        ELEMENT_MINIMIZE_KEY,
    )


constants_wrapper = ConstantsWrapper()