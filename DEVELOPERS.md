# Developer Documentation for elCID

## Deployment

### Test

1. Deploying to test requires that you have a backup file around so find one you'd like to use
2. ./bin/deploy_test.sh /full/path/to/backup # The script moves around a bunch so relative paths will fail
3. Any routine or previous backup will then break the lab integration because it's too old. Run python manage.py batch_load --force
