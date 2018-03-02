## intrahospital_api

This loaded in demographics and tests from the upstream system.

Its read only, it does not write.

#### Basic Overview
There are 4 types of load.

1. Demographics
When you add a patient we search for the patient in the upstream system. If the patient is found. We return the demographics and mark the external system
for these demographics as `RFH Database`.

2. Load all tests for patient
If the external system is `RFH Database`, when we save the patient, via the admin or via the inital load management command we load in all lab tests for a patient for the past year.

This means we query via hospital number and now - 1 year. We update all of their test results.

3. Batch load
Every 5 mins we load in all test data since the beginning of the previous batch run. IE we overlap.
This excludes patients currently being loaded in by 2.

#### More detail.
The cron job that takes backups waits for all loads to finish. As does the deployment.
