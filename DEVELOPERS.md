# Developer Documentation for elCID

## Deployment

### Test

1. Deploying to test requires that you have a backup file around so find one you'd like to use
2. ./bin/deploy_test.sh /full/path/to/backup # The script moves around a bunch so relative paths will fail
3. Any routine or previous backup will then break the lab integration because it's too old. Run python manage.py batch_load --force


## Integration

elCID integrates with a number of upstream systems

* Cerner Demographics
* Cerner Appointments
* Winpath Labs
* Freenet ICU Handover

The mechanics of communicating with upstream databases is handled by
the `intrahospital_api` module, which exposes some interfaces for making
queries, and creating patients.

The appointment and ICU integrations are self-contained within their
respective plugins and use the `intrahospital` API to initiate creating
a patient and configuring connections to upstream databases.

The lab and demographic integrations are split between the elcid,
intrahospital_api and plugins.labtests modules.

### Key interfaces

The intrahospital_api package exposes the function
`create_rfh_patient_from_hospital_number(hospital_number, episode_category)`
which ensures that a patient will have their integrations set up correctly.

### Sync mechanisms

Keeping data in elCID in sync with upstream sources is done via periodic
tasks run by cron jobs on the server.
