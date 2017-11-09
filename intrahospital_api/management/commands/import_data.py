# so the theory is, we load in data, if they're the same, we're fine
# if they are different on first name last name hospital number, nhs number date of birth
# we blow up
# if they are the same what we would really like to do is mark them as resolved?

# curent plan, load in all demographics for patients
# store them in a seperate table
# we have a resolved tab and a to resolved


# other options, we automatically resolve all patients that match on 2 fields
# we update them accordingly and add in the external system, that's how we know they
# are resolved

# then we have partial demographics matches that we load in
# then we have missing demographics

# in terms of the code we look up via hosptial number,
# then by surname and date of birth as they have an index on hospital number

# we bring them all in and then display them as matches in its own page
# we then need to build the form part of it.
