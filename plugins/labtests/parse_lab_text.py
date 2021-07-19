from collections import defaultdict
import re


def get_organisms(observation_value):
    """
    Note: Checked with all TB Cultures. Appears to work with
    all cultures. Please check individual tests before you apply
    it in case there are differences in the tests you are applying it
    to.

    Organisms/resistances/sensitivities/intermediate come in a structure like
    '1) Mycobacterium abscessus
    This is the final reference lab. report


    1)
    Amikacin              S
    Tobramycin            R
    Cotrimoxazole         R
    Doxycycline           R',

    ie the form
    {{number}}) {{ organism }}
    {{ comment }}

    {{ number }}
    sensitivities/resistances/intermediates

    There can be more than 1 organism, therefore
    more than 1 set of resistances.

    Notable empty lines can include spaces.

    This would return
    {
        "Mycobacterium abscessus": {
            "sensitivities": ["Amikacin"],
            "resistances": [
                "Tobramycin", "Cotrimoxazole", "Doxycycline"
            ],
            "intermediate": []
            "comments": This is the final reference lab. report
        },
    }

    comments often refer to the organism so they are placed with
    the previous organism mentioned
    """
    obs_value = observation_value.strip()

    # if it doesn't beging with a 1) just return
    if not obs_value.startswith("1)"):
        return

    # we expect the obs value to end in double tilda, strip it.
    obs_value = obs_value.rstrip('~')
    # split by two tildas in a row with optional space in between
    obs_sections = re.match('(.*)\~\s*\~(.*)', obs_value)

    # no obs sections means no sensitivities/resistances
    if not obs_sections:
        organisms_and_comments = obs_value.split("~")
        sensitivies_and_resistances = []
    else:
        matches = obs_sections.groups()
        if len(matches) == 2:
            organisms_and_comments = matches[0].split("~")
            sensitivies_and_resistances = matches[1].split("~")

    key_to_organisms = {}
    key_to_comments = defaultdict(list)
    key = None
    # the first section is the organisms that start with [1-9])
    for line in organisms_and_comments:
        line = line.strip()
        if len(line) > 1 and line[0].isdigit() and line[1] == ")":
            key = line[0]
            organism = line[2:].strip()
            if organism:
                key_to_organisms[key] = line[2:].strip()
        else:
            key_to_comments[key].append(line)

    # the final section are the sensitivities
    key = None
    key_to_resistances = defaultdict(list)
    key_to_sensitivities = defaultdict(list)
    key_to_intermediate = defaultdict(list)
    for line in sensitivies_and_resistances:
        line = line.strip()
        if line and line[-1] == ")" and line[-2].isdigit():
            key = line[-2]
        if line.endswith("R"):
            resistance = line.rstrip("R").strip()
            key_to_resistances[key].append(resistance)
        if line.endswith("S"):
            sensitivity = line.rstrip("S").strip()
            key_to_sensitivities[key].append(sensitivity)
        if line.endswith("I"):
            intermediate = line.rstrip("I").strip()
            key_to_intermediate[key].append(intermediate)

    result = {}
    for key, organism in key_to_organisms.items():
        result[organism] = {
            "sensitivities": key_to_sensitivities[key],
            "resistances": key_to_resistances[key],
            "intermediate": key_to_intermediate[key],
            "comments": "\n".join(key_to_comments[key])
        }
    return result
